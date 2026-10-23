# TaskVex UI

Vanilla HTML/CSS ve ES modülleri. Native açılış v1 içinde
`.\.venv\Scripts\python.exe -m app.main`; [backend rehberi](../README.md).
Bu README kullanım/modül haritasıdır; değişiklik günlüğü değildir.

## Tarayıcıda görünüm

v1 içinde:

```powershell
.\.venv\Scripts\python.exe -m http.server 8000 --directory ui --bind 127.0.0.1
```

Edge/Chrome ile http://127.0.0.1:8000 açın. ES modülleri için file:// kullanmayın.
Bu modda tema/profil/layout, yerel notlar, skill/rutin editörleri, yedek, palet ve
tekli yerel sayaç çalışır. Native sohbet, backend notları, çoklu sayaç, Credentials
ve yerel KWS entegrasyonu kazanmaz. Harici font erişilemezse sistem fontu kullanılır.

## Modül sahipliği

| Modül | Görev |
|---|---|
| app.js | Başlatma, modül bağlantıları, toplu snapshot |
| assistant_session.js | Tek sohbet/mikrofon/uyku/Stop tur yaşam döngüsü |
| shell.js | Metin balonları, başlangıç/kapanış görünümü, saat |
| api.js | Taşıma ve public bridge; kabul/bitiş ayrımı, hata maskeleme |
| schema.js / storage.js | Saf doğrulama / görünür hata veren localStorage |
| preferences.js / settings.js | Tek tercih nesnesi / ayarlar, profil, yedek ve native save |
| devices.js / layout.js | Aynı nesne üzerinden cihaz listesi/seçimi ve widget düzeni |
| credentials.js | Windows key kayıt UI'ı; sır tarayıcı deposuna girmez |
| notes.js | Yerel veya onaylı native not görünümü; çift mutasyon yok |
| skills.js / routines.js | Yerel tanım editörleri; backend yürütme yok |
| connections.js | API Live katalog ve salt okunur widget setter'ları |
| panels.js | Modal, palet, drawer, yerel timeline |
| reactor.js / sfx.js | Görsel durum/animasyon ve yerel efektler |
| live_mic.js / mic_worklet.js | Tek AudioWorklet PCM girişi, VAD/seviye |
| live_audio.js / live_transcript.js | İstek kimlikli çıktı ve transkript |
| clocks.js / timers.js | Native çoklu sayaç görünümü / tarayıcı tekli fallback |

Native başladıktan sonra köprü kaybı ikinci sayaç/not otoritesi açmaz. Setters
backend'e ikinci save/komut göndermez. Google/konum/voice/kamera/ekran/media ve
uygulanmamış profil alanları açıkça planlı/disabled; kayıtlı metinler korunur.

[Sözleşme](../../docs/UI_BACKEND_CONTRACT.md), [komutlar](../../docs/COMMANDS.md),
[testler](tests/README.md), [açık sınırlar](../../docs/AUDIT.md).
