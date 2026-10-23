# TaskVex UI

Framework içermeyen HTML/CSS ve ES modülü arayüzü. Tasarım korunmuştur; Python backend bu klasöre dahil değildir.

İlk native host artık `v1/app/` altında vardır. `v1` dizininde
`.\.venv\Scripts\python.exe -m app.main` ile açılır. Ayar/durum köprüsü, elle
test adımları ve henüz desteklenmeyen işlemler [native rehberde](../../docs/STAGE2_NATIVE.md).

Native notlar artık backend'e bağlıdır. İlk kullanımda Use backend notes ile
yerel not aktarımını onaylayın; iptalde eski notlar değişmez. Sonraki açılışta
backend kayıtları okunur. Tarayıcı-only yerel mod korunur. [Not devri ve güncel
kabul sonuçları](../../docs/STAGE3_NOTES.md) aktarım, yedek ve hata sınırlarını açıklar.

Native timer/stopwatch artık çokludur: backend Clocks tek durum sahibidir;
UI dropdown/New ve Vex aynı kayıtlı araçları kullanır. Model işlemi doğru sekmeyi
otomatik seçer. Kayıtlar yalnız uygulama açıkken RAM'dedir. Native başladıktan
sonra köprü kaybı ikinci yerel sayaç motoru açmaz. Tarayıcı-only tekli mod korunur.

## Açılış

Test edilen yöntem: klasörü yerel HTTP üzerinden sunmak ve Edge/Chromium ile açmak. Testler Node HTTP sunucusu ve Playwright ile çalıştırıldı. ES modülleri için HTML dosyasını doğrudan file:// ile açmak yerine HTTP kullanın. Harici font isteği başarısız olursa sistem fontu kullanılır; testlerde dış ağ istekleri engellendi.

## Modüller

| Modül | Yetkili olduğu alan |
|---|---|
| app.js | Başlatma, modül bağlantıları, sohbet ve snapshot uygulama sırası |
| api.js | Native/fallback taşıma, güvenli hata gösterimi, public bridge, bağlantı durumu |
| schema.js | Yan etkisiz snapshot/skill doğrulama ve layout normalizasyonu |
| storage.js | Yerel kayıt ve silme; görünür hata ve boolean sonuç |
| settings.js | Tema, profil, cihaz tercihi, layout ve kayıt nesnesi |
| credentials.js | Native API anahtarının açık kaydı, password input temizliği ve sır içermeyen kayıt durumu |
| notes.js / skills.js / routines.js | Kendi koleksiyonlarının canlı tek kaynağı; kayıt sırasında getter ile alınır |
| connections.js | Kataloglar, telemetri/ağ/medya/takvim görünümü ve konum isteği |
| panels.js | Modallar, komut paleti, drawer ve timeline |
| reactor.js | Görsel durum ve animasyon |
| timers.js / clocks.js / sfx.js | Native backend sayaç görünümü/komutları; yalnız tarayıcıda tekli yerel motor; ses efektleri |

Backend setter'ları UI'a veri uygular; kullanıcı komutu üretmez. Koleksiyonlar elle `settings.store` üzerinden değiştirilmemelidir.

## Backend olmadan

Tema, profil, widget düzeni, notlar, skill/rutin tanımları, yedekler, modallar, Ctrl+K, Escape ve yerel sayaç/kronometre çalışır. Kalıcılık tarayıcı depolamasına bağlıdır; hata görünür olur. Skill/rutin çalıştırma, sohbet modeli, gerçek mikrofon/kamera/sistem sesi, Google OAuth/konum ve cihaz tarama backend gerektirir. Mikrofon/mute düğmeleri kullanıcı tercihidir; gerçek ses yakalandığını kanıtlamaz. Başlangıçtaki boş takvim/hatırlatıcı listeleri backend senkronizasyonu kanıtı değildir.

## Sözleşme ve test sınırı

[UI/backend sözleşmesi](docs/UI_BACKEND_CONTRACT.md).

[Bağımsız denetim düzeltmeleri](docs/AUDIT_FIXES.md).

UI hazırlık kapsamı kapatıldı. Son eklemeler: hava null temizleme, sonlu SFX seviyesi, reactor ses kaynağı temizliği ve kamera/konum için 12 saniye sonrası belirsiz durumdan salt okunur sorguyla kurtarma. `query_camera` / `query_location` backend sözleşmeleri yukarıdaki belgede tanımlıdır; backend bu olayları ayrıca uygulamalıdır. Public eval kaldırıldı.

Gerçek PyWebView penceresi, donanım sinyalleri, Google hesapları, canlı hava servisi ve gerçek masaüstü işlemleri bu UI kabul turunda çalıştırılmadı. Tarayıcıda sentetik bridge ile doğrulama yapıldı. UI testlerinin geçmesi, bu entegrasyonların uçtan uca onayı değildir.
