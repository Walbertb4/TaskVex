"""Uyku sohbet kontrolünün Türkçe/İngilizce tam cümle niyetini ayırır.

Hitap, nezaket ve yaygın fiil varyantları aynı denetimden geçer. Alıntı,
soru veya ek iş bulunan cümleden niyet tahmin edilmez. Bu modül yalnız
once/persistent/off döndürür; gerçek geçiş host/UI sahibinin sorumluluğudur.
"""
import re

# Alt kalıplar sadece fullmatch içinde kullanılır: cümlenin bir yerinde
# "uyu" geçmesi komut değildir. Negatif/soru eklerini silip anlam değiştirme.
_ONCE_TR = r'(?:uyku moduna (?:geç|gir)|uykuya (?:geç|dal)|uyu)'
_ONCE_EN = r'(?:go to sleep|(?:enter|switch to) sleep mode|sleep)'
_PERMANENT_TR = r'kal[ıi]c[ıi] olarak'


def _normalized(text: str, wake_word: str) -> str:
    """Güncel mesajın boşluk/hitap/nezaketini eşitle; olumsuzluğu koru.

    Soru işareti noktalama diye atılmaz. Tırnaklar da kalır; böylece örnek
    olarak söylenen/yazılan bir komut tam eşleşme denetiminden geçmez.
    """
    value = ' '.join(text.casefold().replace('i\u0307', 'i').split()).strip(' .!,')
    if '?' in value:
        return ''
    # Veks Türkçe ses yazımıdır; Rex/Max diğer gözlenen transkripsiyonlardır.
    # genel komutlarda ve yerel wake algısında bulanık isim eşleştirmesi yapılmaz.
    names = {'vex', 'veks', 'rex', 'max', wake_word.casefold()}
    value = re.sub(r'^(?:(?:lütfen|please)[ ,:]+)?(?:' +
                   '|'.join(re.escape(n) for n in names) + r')[ ,:]+', '', value)
    value = re.sub(r'^(?:lütfen|please)[ ,:]+', '', value)
    value = re.sub(r'[ ,]+(?:lütfen|please)$', '', value)
    return value


def wants_sleep(text: str, wake_word: str = 'Vex') -> bool:
    """Geriye uyumlu tek seferlik uyku denetimi; kalıcı tercihi kapsamaz."""
    return sleep_mode(text, wake_word) == 'once'


def sleep_mode(text: str, wake_word: str = 'Vex') -> str | None:
    """Tam komut için once/persistent/off; soru ve birleşik istekte None.

    Bu yalnız niyet ayrımıdır. Uykuya geçiş ve güvenli boşta zamanlayıcı
    host/UI sahibinde kalır; model araç yetkisi kazanmaz.
    """
    value = _normalized(text, wake_word)
    if re.fullmatch(
            rf'(?:(?:bundan sonra|artık|{_PERMANENT_TR}) {_ONCE_TR}|'
            rf'(?:(?:bundan sonra|artık|{_PERMANENT_TR}) )?uyku modunda kal|'
            r'(?:from now on )?stay (?:in )?sleep mode|'
            r'return to sleep after (?:each|every) (?:interaction|task)|'
            r'permanently (?:enter|switch to) sleep mode)', value):
        return 'persistent'
    if re.fullmatch(
            rf'(?:uyku modundan {_PERMANENT_TR} çık|{_PERMANENT_TR} uyku modundan çık|'
            r'kal[ıi]c[ıi] uyku modunu kapat|otomatik geri uyumayı kapat|'
            r'stop returning to sleep|disable automatic sleep)', value):
        return 'off'
    return 'once' if re.fullmatch(rf'(?:{_ONCE_TR}|{_ONCE_EN})', value) else None
