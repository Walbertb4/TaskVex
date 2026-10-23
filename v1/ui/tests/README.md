# UI regresyonları

Bu testler UI sözleşmesini gerçek hesap ve fiziksel cihaz açmadan doğrular.
Komutlar v1 içinde çalıştırılır. Test değişiklikleri ilerleme günlüğüne değil
kök CHANGELOG.md'ye yazılır.

```powershell
node ui/tests/live-audio.mjs
node ui/tests/live-stream.mjs
node ui/tests/live-transcript.mjs
node ui/tests/live-status.mjs
node ui/tests/wake-recovery.mjs
node ui/tests/note-timestamps.mjs
node ui/tests/shutdown.mjs
node ui/tests/clocks.mjs
node ui/tests/catalog.mjs
```

Bu 9 suite; PCM kaynak/oynatma, VAD/metre, geç transkript, Stop/unknown,
uyku/wake toparlanması, tarihli notlar, kapanış, çoklu sayaç/sağ tık silme,
tema ve katalog kapsamını sınar. Eski MediaRecorder yolu uygulamada kullanılmadığı
için kaldırıldı; ilgili self-test'in yerine gerçek AudioWorklet regresyonları korunur.
VM/sentetik nesneler gerçek akustik, WebView2 veya sağlayıcı kabulü değildir.

## Gerçek tarayıcı

Kurulu playwright-core yolunu kullanın; UI'a runtime bağımlılık eklenmez:

```powershell
$env:PLAYWRIGHT_MODULE = 'C:\path\to\node_modules\playwright-core\index.mjs'
node ui/tests/audit-fixes.mjs
```

BROWSER_PATH gerekirse Edge/Chromium exe yolunu seçer. Test kendi yerel sunucusu ve
izole profiliyle çalışır, dış ağı engeller; gerçek kullanıcı localStorage'ına erişmez.
Dört grup: planlı kontrollerde dürüst durum/olmayan scheduler, tek tercih nesnesi ve
eski metni koruma, yerel not CRUD/yenileme, legacy anahtar okuma/tek yeni anahtar yazma.

Python native kabul: v1/tests/native_smoke.py; senaryolar native_scenarios.py'dedir.
Native rapor aynı core/gerçek WebView2 üzerinde sentetik provider/PCM kullanır.
Fiziksel mikrofon/echo/cihaz geçişi ve canlı API ayrı kullanıcı kabulüdür.
