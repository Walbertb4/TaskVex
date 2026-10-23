"""Uyku tek sohbet kontrolüdür; yalnız açık ve tam ifadeler eşleşir.

Alıntı, soru veya içinde ek iş bulunan cümleden niyet tahmin edilmez. Kalıcı
geri-uyuma bu dilimde yoktur; bu ifadeler ayrı sonraki adımda ele alınacaktır.
"""
import re


def wants_sleep(text: str, wake_word: str = 'Vex') -> bool:
    """Dar Türkçe/İngilizce uyku ifadeleri; tarihçe yerine güncel mesajı denetle."""
    value = text.casefold().replace('i\u0307', 'i').strip(' \t\r\n.!?,')
    # Veks Türkçe ses yazımıdır; Rex/Max diğer gözlenen transkripsiyonlardır.
    # genel komutlarda ve yerel wake algısında bulanık isim eşleştirmesi yapılmaz.
    names = {'vex', 'veks', 'rex', 'max', wake_word.casefold()}
    value = re.sub(r'^(?:' + '|'.join(re.escape(n) for n in names) + r')[ ,:]+', '', value)
    return value in {'uyku moduna geç', 'uykuya geç', 'uykuya dal', 'uyu', 'go to sleep', 'enter sleep mode', 'sleep'}
