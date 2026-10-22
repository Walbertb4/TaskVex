"""Aynı masaüstü sohbetinin sınırlı, yalnız RAM'de yaşayan konuşma kaydı.

Live socket'i geçicidir; bu kayıt TextChat'e aittir. Eski mesajlar yeni araç
isteği veya sağlayıcı functionCall nesnesi değildir. Özetlemek için model/API
çalıştırmaz; en eski turları bırakır. Kalıcı kullanıcı profili/not deposu değildir.
"""
import json


class ConversationMemory:
    """TextChat'in tek sohbet kilidi altında kullan; kendi worker/kilidi yoktur."""

    def __init__(self):
        self._turns: list[dict] = []

    def clear(self):
        """Yeni sohbet/kapanış/anahtar değişiminde yalnız RAM kaydını bırak."""
        self._turns.clear()

    def snapshot(self) -> str:
        """Değişmez veri kopyası; boş kayıtta sağlayıcıya içerik gönderilmez."""
        return json.dumps(self._turns, ensure_ascii=False) if self._turns else ''

    def remember(self, user: str, report: dict):
        """Sonucu başarılı varsaymadan metin ve sınırlı araç durumunu sakla.

        Sesli mesajda gerçek input_text kullanılır; ham PCM, sır deposu,
        tool arguments/result.data veya resume handle bu kayda alınmaz.
        Kesilmiş yanıt kesilmiş olarak kalır. 12 tur / 16.000 JSON karakteri
        sınırı aşılırsa en eski tur tamamen çıkarılır, yeni komut üretilmez.
        """
        def clip(value):
            return value[:2000] + (' [truncated]' if len(value) > 2000 else '') if isinstance(value, str) else ''

        tools = [{'name': item.get('name'), 'status': item.get('status'),
                  'verified': (item.get('result') or {}).get('verified') is True}
                 for item in report.get('tool_results', [])[:8]]
        if not user and not report.get('text') and not tools:
            return
        self._turns.append({'user': clip(user), 'assistant': clip(report.get('text')),
            'outcome': 'unknown' if report.get('unknown') else 'stopped' if report.get('stopped')
                       else 'completed' if report.get('ok') else 'failed', 'tools': tools})
        while len(self._turns) > 12 or len(self.snapshot()) > 16000:
            self._turns.pop(0)
