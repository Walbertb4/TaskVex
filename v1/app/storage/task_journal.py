"""TaskManager'ın tekrar korumasını SQLite transaction'larıyla kalıcı tutar.

Bu depo araç çalıştırmaz. Aynı profilin tek yöneticisi OS kilidini tutar;
her yazma FULL senkron transaction ile tamamlanmadan yürütücü ilerlemez.
Restart'ta queued işler iptal, başlamış işler unknown olur; yeniden oynatılmaz.
Kayıtlar diskten silinmez: RAM temizliği eski isteği yeni iş haline getiremez.
"""

from contextlib import contextmanager
from dataclasses import replace
import json
from pathlib import Path
import sqlite3

from app.core.contracts import Task, TaskStatus, ToolError, ToolRequest, ToolResult
from app.storage.instance_lock import SingleInstance


class JournalError(RuntimeError):
    """Depo güvenilir değil; ham SQL, dosya yolu veya kullanıcı verisi sızdırma."""


def _encode(task: Task) -> str:
    """Sabit alan sırası ve sıkı JSON ile diskteki tek görev biçimini üret."""
    return json.dumps(task.to_dict(), sort_keys=True, ensure_ascii=True, allow_nan=False)


def _decode(row) -> Task:
    """JSON ile indeks kimliklerini birlikte doğrula; bozuk kayıt boş sayılmaz."""
    principal, request_id, task_id, status, document = row
    data = json.loads(document)
    data['request'] = ToolRequest(**data['request'])
    data['status'] = TaskStatus(data['status'])
    if data['result'] is not None:
        result = data['result']
        result['status'] = TaskStatus(result['status'])
        if result['error'] is not None:
            result['error'] = ToolError(**result['error'])
        data['result'] = ToolResult(**result)
    task = Task(**data)
    if (principal, request_id, task_id, status) != (
            task.request.principal, task.request.request_id, task.task_id, task.status.value
    ) or _encode(task) != document:
        raise ValueError('Invalid task journal record')
    return task


class TaskJournal:
    """Güvenilir host'un seçtiği dizinde tek yazıcı ve sınırlı SQLite sayfa cache'i.

    Her işlem bağlantısını kapatır; thread'ler arasında SQLite nesnesi paylaşılmaz.
    Çağrılar TaskManager Condition kilidi altında sıralanır. close yalnız sahipliği
    bırakır; kapatılmış manager'ın salt sonuç sorguları çalışmaya devam edebilir.
    """

    def __init__(self, home: Path) -> None:
        self.path = home / 'tasks.sqlite3'
        self._owner = SingleInstance(home)
        self._owner.__enter__()
        try:
            fresh = not self.path.exists()
            with self._connect(create=fresh) as db:
                if fresh:
                    db.execute('CREATE TABLE tasks (principal TEXT NOT NULL, request_id TEXT NOT NULL, '
                               'task_id TEXT NOT NULL UNIQUE, status TEXT NOT NULL, document TEXT NOT NULL, '
                               'PRIMARY KEY (principal, request_id))')
                    db.execute('PRAGMA user_version=1')
                if db.execute('PRAGMA user_version').fetchone()[0] != 1:
                    raise ValueError('Unsupported journal version')
                if db.execute('PRAGMA quick_check').fetchone()[0] != 'ok':
                    raise ValueError('Corrupt journal')
                # Tüm kayıtları tek tek doğrula; geçmişin tamamını RAM'e yükleme.
                self.uncertain = False
                for row in db.execute('SELECT principal, request_id, task_id, status, document FROM tasks'):
                    task = _decode(row)
                    if not task.status.terminal:
                        status = (TaskStatus.CANCELLED if task.status == TaskStatus.QUEUED
                                  else TaskStatus.UNKNOWN)
                        result = ToolResult(task_id=task.task_id, status=status,
                            error=ToolError(code='process_interrupted',
                                            message='Previous process ended before completion'))
                        task = replace(task, status=status, result=result)
                        db.execute('UPDATE tasks SET status=?, document=? WHERE task_id=?',
                                   (status.value, _encode(task), task.task_id))
                    self.uncertain |= task.status == TaskStatus.UNKNOWN
        except BaseException:
            self.close()
            raise

    @contextmanager
    def _connect(self, *, create: bool = False):
        """Eksik dosyayı çalışma sırasında yeniden yaratma; sessiz dedup kaybı yasak."""
        try:
            db = sqlite3.connect(self.path.as_uri() + ('?mode=rwc' if create else '?mode=rw'),
                                 uri=True, timeout=2)
            try:
                db.execute('PRAGMA synchronous=FULL')
                db.execute('PRAGMA cache_size=-1024')
                with db:
                    yield db
            finally:
                db.close()
        except (sqlite3.Error, ValueError, TypeError, KeyError, RecursionError):
            raise JournalError('Task journal could not be verified or saved') from None

    def find(self, principal: str, request_id: str) -> Task | None:
        """Aynı kullanıcı/isteğin eski kaydını disk indeksinden oku; yürütme yapma."""
        with self._connect() as db:
            row = db.execute('SELECT principal, request_id, task_id, status, document FROM tasks '
                             'WHERE principal=? AND request_id=?', (principal, request_id)).fetchone()
            return _decode(row) if row else None

    def get(self, task_id: str) -> Task | None:
        """RAM'den ayrılmış terminal görevleri gerçek task_id ile sorgula."""
        with self._connect() as db:
            row = db.execute('SELECT principal, request_id, task_id, status, document FROM tasks '
                             'WHERE task_id=?', (task_id,)).fetchone()
            return _decode(row) if row else None

    def save(self, task: Task) -> None:
        """Kimlikleri koruyarak tek görev durumunu atomik kaydet; commit hatası yükselir."""
        with self._connect() as db:
            db.execute('INSERT INTO tasks VALUES (?, ?, ?, ?, ?) ON CONFLICT(task_id) '
                       'DO UPDATE SET status=excluded.status, document=excluded.document',
                       (task.request.principal, task.request.request_id, task.task_id,
                        task.status.value, _encode(task)))

    def close(self) -> None:
        """Worker gerçekten durduktan sonra kilidi bırak; dosyaları silme."""
        self._owner.__exit__(None, None, None)
