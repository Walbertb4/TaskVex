# UI / backend sözleşmesi

Bu belge çalışan masaüstü sınırını tarif eder; planlı API taslakları sözleşme değildir.
Kod sahipleri [mimaride](ARCHITECTURE.md), açık işler [planda](PLAN.md) bulunur.

## Taşıma ve hazır olma

UI `api.js:emit(name, data)` üzerinden `pywebview.api.event` çağırır. Dönüş
`{ok, response, error}` taşıma zarfıdır; response içindeki `completed`, doğrulanmış
alan sonucu ve `unknown` ayrıca değerlendirilir. Promise reddi yakalanır; sırlar
maskelenir. Native varken onEvent yalnız observer'dır; observer hatası native
komutu tekrar göndermez. Bağımsız tarayıcıda dış host onEvent sağlayabilir; bu
TaskVex native backend'iyle aynı yetki veya entegrasyon garantisi değildir.

`window.vex === window.jarvis` uyumluluk alias'ıdır. Köprü metotları atandıktan sonra
ui_ready bir kez gönderilir. Startup hazır durumu modelin bağlı olduğunu kanıtlamaz.
Native host hazır değilse mutasyonlar korunur; bozuk ayarlar açık kurtarma ister.

## UI → native olayları

| Olaylar | Anlam / sınır |
|---|---|
| ui_ready, retry_startup, recover_settings | Başlangıç snapshot'ı; kurtarma açık onay gerektirir |
| save, reset, ontop | İzinli ayarlar; sır/not/skill/rutin mutasyonu değildir |
| query_apikey, apikey | Sır içermeyen durum / Windows Credentials'a açık kayıt; anahtar geri yollanmaz |
| query_catalog, model | API'den Live katalog ve izinli seçim; statik başarılı liste uydurulmaz |
| text, live_text | İstek kimlikli REST / kalıcı Live metin turu |
| live_audio, live_audio_start, live_audio_feed | Sınırlı PCM girişi, sıra ve istek kimliği; bitiş paketi ayrıca doğrulanır |
| stop_task | Hedef request_id zorunlu; kabul gerçek bitiş değildir |
| read_reply | REST yanıtına mevcut tek ses hattında araçsız ses üretimi |
| new_chat, disconnect | RAM bağlamını temizleme / bağlantı kaynağını bırakma ayrı işlemlerdir |
| sleep_start, wake_feed, wake_close, wake | Yerel KWS oturumu ve doğrulanmış ses sınırı; sıradan uyku sesi ağa gitmez |
| notes_init, note_add, note_done, note_del, notes_replace | Onaylı backend not sahipliği; ID/snapshot ve readback doğrulaması |
| query_clocks, clock_command | Aynı Clocks durumunu okuma / core üzerinden mutasyon; delete yalnız UI |
| clock_finished | Gerçek id/generation doğrulandıktan sonra araçsız bildirim; tekrar yok |
| system_status | Core üzerinden temel OS bilgisi; sahte CPU/GPU kullanım yüzdesi yok |
| fullscreen, shutdown, restart | Pencere işlemleri; kapanış aktif işi sahipsiz bırakmaz |

Kamera/konum/Google/skill_run/routine_run/inspect/screen_share/media komutları native
tarafında uygulanmadı. UI bunları çalışan özellik gibi başlatmaz. Timeline/drawer
yereldir; native komut veya başarılı dış işlem bildirimi üretmez.

## Native → UI

Aktif push'lar initApp/startupStatus, canlı transkript ve audioChunk gibi görünüm
güncellemeleridir. Transkript request_id/role/sequence ile aynı balonu günceller;
eski tur yeni balona/sese karışmaz. PCM çıktı sınırlı, 24 kHz mono; giriş 16 kHz mono.

`initApp` ve `loadStore` aynı doğrulayıcı/snapshot yolunu kullanır. Koleksiyonlarda
eksik alan korur, açık null temizler, dizi değiştirir. Geçersiz iç kayıt tüm snapshot'ı
uygulamadan reddeder. Setters backend'e save/komut geri beslemesi üretmez. Yerel yedek
uygulaması toplu kayıttır; backend not restore ayrı doğrulanan depoya geçer ve kısmi
depo hatası tam başarı sayılmaz. İki depoyu kapsayan gerçek ACID transaction yoktur.

telemetry/network/weather/media/calendar/reminder ve skill/routine sonuç setter'ları
salt görünüm/uyumluluk girişleridir; sağlayıcı entegre edildiğini göstermez.
Kısmi ölçümde eksik alan korunur; null kullanılamaz görünür. Sıfır geçerli ölçümdür.
İnternet offline bilgisi çalışan yerel CPU ölçümünü geçersiz saymaz.

## Tek durum sahibi

- Tercihler preferences.store; settings doğrular/kaydeder, devices/layout paylaşır.
- Native notlar notes.json; UI ilk aktarım onayı sonrası backend'den yenilenir.
- Skill/rutin tanımları yerel koleksiyon/localStorage; yürütme henüz yok.
- Native sayaçlar Python Clocks; UI polling salt okunur. Native kaybı ikinci JS
  motoru açmaz. Bağımsız tarayıcıda tekli yerel timer/stopwatch ayrı moddur.
- Sohbet kilidi TextChat, socket PersistentLive, UI tur/mic/wake sahibi assistant_session.
- Anahtar Credentials; JSON, localStorage, yedek ve hata metninde bulunmaz.

## Stop, sleep ve ses

Stop sonrası yeni retry/fallback/araç başlatılmaz; başlamış işin gerçek sonucu korunur.
Senkron REST isteği anında kesilemeyebilir. Kontroller gerçek terminal sonuca kadar
bekler; belirsiz durumda kilit korunur. Geç Stop yeni request_id'yi durduramaz.
Resume bağlantı kapsamı/model/key/tools ile bağlıdır; kopan mesaj körlemesine tekrar
yollanmaz, yan etkili araç replay kaydı korunur. Otomatik bağlantı denemesi sınırlıdır.

Mic Off yalnız kullanıcı girişini keser, Mute yalnız çıkışı susturur. Sleep aracı pending
istektir; model yanıtı/oynatma bitince mevcut host uygular. Tek seferlik/persistent uyku
ve bağımsız idle timer ayrıdır. Shutdown da yanıt bitişini bekler; Stop/unknown/geç
istek kapanışa izin vermez. Yerel KWS/Stop/UI kontrolleri doğal dil router'ı değildir.

## Doğrulama sınırı

Sentetik provider ile WebView2, Python ve JS regresyonları gerçek dış işlem yapmadan
çalışır. Ücretli hesap, canlı GoAway/resume, fiziksel akustik/echo/cihaz doğruluğu bu
bakımda yeniden test edilmedi. Sonuçlar [AUDIT](AUDIT.md) ve reports/ içindedir.
