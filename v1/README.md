# TaskVex v1 geliştirme ve çalıştırma

Bu rehber mevcut uygulamanın açılışını anlatır; ilerleme günlüğü değildir.
[Mimari](../docs/ARCHITECTURE.md), [plan](../docs/PLAN.md), [sözleşme](../docs/UI_BACKEND_CONTRACT.md).

## Ortam

Windows, Edge WebView2 Runtime ve Python gerekir. Bildirilen minimum Python 3.11;
bu bakımda kullanılan interpreter 3.14'tür. Aşağıdaki komutlar v1 içindedir:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.lock.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m app.main
```

Mevcut .venv varsa yeniden oluşturmayın. Aktivasyon zorunlu değildir; interpreter'ı
bu yolla doğrudan çağırmak PowerShell execution-policy değişikliği gerektirmez.
`--debug` geliştirme araçlarını açar. API anahtarı UI Settings üzerinden kaydedilir;
anahtarın kendisi geri gösterilmez. Live katalog otomatik yüklenir, kayıtlı model
API'de hâlâ varsa seçilir. API/hesap erişimi garanti değildir.

pyproject.toml bağımlılık beyanının kaynağıdır. requirements-dev.lock.txt test edilen
runtime+dev ortamının tam sürüm snapshot'ıdır; artifact hash'i ve platformlar arası
release kilidi değildir. Bağımlılık değişimi sonrası kontrollü ortamdan yeniden
üretilir; ikinci elle bakılan bağımlılık listesi değildir. .venv yerel kurulumdur,
Git'e girmez. Referans projenin requirements dosyasını buraya kurmayın.

## Yerel wake modeli

İlk kurulumda, kullanıcı açıkça isterse:

```powershell
.\.venv\Scripts\python.exe -m app.session.wake_word --setup
```

Bu komut upstream'den sabit/hash doğrulanan modeli indirir; açılış sessiz indirme
yapmaz. Ağ ve indirme gerektirir. Model cache'i TaskVex veri kökünde, repo dışındadır.
Vex/Veks/Rex ailesi ve desteklenen İngilizce sözlük sözcükleri kullanılır. Ağırlıkların
paketleme/lisans sınırı [üçüncü taraf notlarında](../docs/THIRD_PARTY_NOTES.md) açıktır.

## Veri

Varsayılan `%LOCALAPPDATA%\TaskVex`; izole ortam için TASKVEX_HOME. settings.json
izinli tercihleri, notes.json notları saklar. Sırlar Windows Credentials'dadır.
Skill/rutin tanımları localStorage; sayaç ve sohbet hafızası RAM'dir. Aynı veri kökünde ikinci native TaskVex örneği OS kilidiyle engellenir.
Core görev günlüğü `tasks/tasks.sqlite3` içindedir; ikinci core da ayrı OS kilidiyle
engellenir. Günlük eski sonuçları korur; aktif/RAM kayıt sınırı 256'dır, toplam
görev sayısı sınırı değildir. Unknown işlem restart sonrası kilidi korur.
Günlük şifrelenmemiştir ve eski not metnini tutabilir; otomatik silinmez, JSON
yedeğine girmez. Günlük silmek güvenli kurtarma sayılmaz.
Ayrı veri profilleri açılabilir; doğrudan core/script yazıcıları host kilidini atlamamalıdır.

## Doğrulama

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe tests/native_smoke.py --report ../docs/reports/cleanup-native.json
```

Native smoke geçici veri/kimlik profili ve sentetik HTTP/WebSocket/ses kullanır;
ücretli API çağırmaz. Windows/WebView2 gerekir. Çalışan gerçek uygulamadan ayrı
veri kökünde açılır. Gerçek kullanıcı notları test girdisi yapılmaz.
[JS/browser testleri](ui/tests/README.md) ayrıca çalışır. Gerçek API smoke dosyası
manuel/ücretli olabilen bir araçtır; genel regresyonun parçası değildir.
