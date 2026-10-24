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
| disconnect | Bağlantı kaynağını bırakır; RAM bağlamını silmez |
| new_chat (internal/test) | RAM reset uyumluluk endpoint'i; UI düğmesi kaldırıldı |
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

Core isteği (principal, request_id) ile kalıcı günlüğe bağlanır; aynı kimlik ve
içerik restart sonrası da eski sonucu verir, yeni komut sayılmaz. Yeni gözlem/
işlem için giriş adaptörü yeni request_id üretir. RAM'den çıkarılmış terminal
görevler sorgulanabilir. Timer/sohbet RAM durumu restart'ta yeniden kurulmaz;
eski başarılı kayıt bunları tekrar oluşturma talimatı değildir. Günlük arızası
veya eski unknown yeni araçları kilitler; UI bunu başarı veya otomatik tekrar
olarak sunamaz. Yan etkiyle günlük commit'i tek atomik işlem değildir.

Mic Off yalnız kullanıcı girişini keser, Mute yalnız çıkışı susturur. Sleep aracı pending
istektir; model yanıtı/oynatma bitince mevcut host uygular. Tek seferlik/persistent uyku
ve bağımsız idle timer ayrıdır. Shutdown da yanıt bitişini bekler; Stop/unknown/geç
istek kapanışa izin vermez. Yerel KWS/Stop/UI kontrolleri doğal dil router'ı değildir.

Settings Audio altında Vex reply volume, `replyVolume` sayısı olarak 0–1 arasında
kaydedilir. Native şema tür/aralık dışını reddeder; UI snapshot doğrulayıcısı
geçersiz alanı atlar. Eski kayıtta yoksa %100; kısmi snapshot'ta yoksa mevcut
değer korunur. Sıfır sessiz çıkıştır, eksik veri değildir. Reset %100'e döner.
Yeni bir olay/TTS sahibi yoktur; aynı PCM gain'i anlık değişir, Mute seçili
seviyeyi kaybetmez. Effects volume ve mikrofon etkilenmez.

setCatalog.voices yalnız belgelenmiş hazır Live seçenekleridir; UI [LIVE] etiketi
basar. conn.voice aynı genel ayar kaydıyla saklanır; sonraki Live turunun setup
speech_config alanına gider. Yeni bir voice olayı/yürütücü yoktur. Değişiklik
aktif yanıtı kesmez; yeni tur eski resume token'ını kullanmaz. API model keşfi
ile belgelerden alınan sabit ses listesi birbirinden ayrıdır. REST TTS değişmez.

API anahtarı input'u value alanını boş tutar; configured onayı yalnız
placeholder içinde gösterilir. Kayıt/erişim belirsizliğinde bu ibare başarı gibi
gösterilmez; API erişimi ayrıca doğrulanmış sayılmaz. Anahtar veya son karakterleri
placeholder/localStorage/snapshot'a konmaz.

## Doğrulama sınırı

Sentetik provider ile WebView2, Python ve JS regresyonları gerçek dış işlem yapmadan
çalışır. Ücretli hesap, canlı GoAway/resume, fiziksel akustik/echo/cihaz doğruluğu bu
bakımda yeniden test edilmedi. Sonuçlar [AUDIT](AUDIT.md) ve reports/ içindedir.


## Kullanıcı hafızası — 6.1.1/2

prof.pMemory boolean ve prof.pMem en çok 16.000 karakter metindir. Genel
save/profil snapshot'ı, doğrulama, yedek ve native tercih deposu kullanılır;
not deposu veya ikinci hafıza otoritesi değildir. Checkbox varsayılan
false; pMem mevcut olsa bile açık onay olmadan sağlayıcıya gitmez.

Düzeltme/boş metin/kapatma sonraki turda eski Live ve RAM bağlamını temizler.
Devam eden yanıtın eski snapshot'ı sonradan değiştirilmez; UI geçmişinin veya
sağlayıcıya daha önce gitmiş verinin silindiği söylenmez. Başarısız profil kaydı
unutma başarısı değildir. memory.read/patch mevcut registry/policy/TaskManager üzerinden aynı belgeyi
kullanır. Model çıkarımı otomatik kaydedilmez.

Model kataloğu: pMemory=true ise memory.read({}) ve memory.patch açılır.
patch.action append/replace/forget/clear; expected_snapshot zorunludur.
append text, replace text+replacement, forget text alır; clear başka metin almaz.
ModelTools aynı turda okunan snapshot'ı ister, alan aracı diskte tekrar kontrol
eder. Hedef tam metinle tek eşleşme olmalıdır; sıfır/çoklu eşleşme ret verir.
Başarı persisted/read_back ve gerçek belge snapshot'ıyla doğrulanır; mevcut
TaskManager tekrar/iptal/unknown kuralları aynen geçerlidir.

Generic save payload'ına UI'ın son onaylı {pMem,pMemory} değeri memoryBase
olarak eklenir; bu alan settings.json'a veya yedeğe yazılmaz. Dolu/etkin mevcut
hafızayı değiştiren profilde base eşleşmezse memory_changed ve güncel
memory_profile döner; dosyaya yazılmaz. İlk boş/kapalı profil legacy kayıtla
kurulabilir; aynı hafızayla yapılan diğer ayar kayıtları bundan etkilenmez.
Başarılı save memory_base döndürür. UI geç gelen eski ack ile daha yeni
snapshot'ın base'ini ezmez. Çakışmada otomatik retry/merge yapılmaz; uygulamayı
yeniden açıp güncel profilden düzenlemek gerekir.

Hafıza araçları kullanılan sohbet yanıtına bridge güncel memory_profile ekler;
UI, unknown/Stop kontrolünden önce aynı loadStore({prof}) yoluyla uygular.
Yerel görünüm kaydı yapılır, backend'e ikinci save yollanmaz. Açık formdaki
kaydedilmemiş profil taslağı korunur; eski hafıza base'iyle sessiz overwrite
yetkisi kazanmaz. Eski sağlayıcı
bağlamı sonraki turda bırakılır; mevcut yanıt bitene kadar profil snapshot'ı
sabittir. pMemory=false metni yerelde tutar, modelden okuyup değiştirmez.
