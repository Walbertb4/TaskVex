"""Uyku tek sohbet kontrolüdür; yalnız açık ve tam ifadeler eşleşir.

Alıntı, soru veya içinde ek iş bulunan cümleden niyet tahmin edilmez. Kalıcı
geri-uyuma bu dilimde yoktur; bu ifadeler ayrı sonraki adımda ele alınacaktır.
"""
import re


def wants_sleep(text: str) -> bool:
    """Dar Türkçe/İngilizce uyku ifadeleri; tarihçe yerine güncel mesajı denetle."""
    value = text.casefold().replace('i\u0307', 'i').strip(' \t\r\n.!?,')
    value = re.sub(r'^vex[ ,:]+', '', value)
    return value in {'uyku moduna geç', 'uykuya geç', 'uyu', 'go to sleep', 'enter sleep mode', 'sleep'}
