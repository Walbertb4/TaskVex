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
| memory_decision | UI onay/ret: request_id + arguments{id,approve}; memory.decide ortak core hattı; model sonraki kullanıcı yanıtında aynı aracı kullanır |
| query_clocks, clock_command | Aynı Clocks durumunu okuma / core üzerinden mutasyon; delete yalnız UI |
| clock_finished | Gerçek id/generation doğrulandıktan sonra araçsız bildirim; tekrar yok |
| system_status | Core üzerinden ortak yerel CPU/RAM/disk/pil/aktif süreç örneği |
| query_system | Hazır native UI için aynı Telemetry sahibinden salt snapshot; payload yok, poll task/journal oluşturmaz |
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


## Hafıza önerileri — 6.1.3

prof.pLearn boolean varsayılan false; eksik/eski profilde önceki açık tercih
miras kalmaz. Save profile, snapshot/yedek ve aynı native şema ile saklanır;
pMemory kapalıysa tek başına araç açmaz. pLearn değişimi model snapshot'ını ve
araç kapsamını sonraki turda etkiler. memory_snapshot izin değişimini de kapsar.

Model için memory.propose({text,expected_snapshot}) en fazla bir
aday oluşturur. Önce aynı turda memory.read zorunludur. Host mevcut user metnini/ASR transkriptini doğrudan source_quote olarak bağlar;
modelin alıntıyı aynı sözlerle yeniden üretmesine bağımlı değildir. İç
source_verified ve source_quote alanları model şemasında yoktur. Sağlayıcının
kaynak kanıtı belirlemesi reddedilir; eski source_quote ipucu gelirse yok
sayılır, gerçek girdinin yerine geçmez. Replay eski host kaynağını korur.
Sesli girişte gerçek ASR yoksa ortak voice_transcript_required koruması araç
başlatmaz. Diğer kaynaksız öneriler source_unavailable ile kontrollü reddedilir.
Kaynak göstermek adayın anlamının doğru olduğunu ispatlamaz. Kaynak en çok
20.000 karakterdir; aynı kullanıcı mesajı sınırı korunur.

İnceleme kipinde başarılı sonuç data.proposal={id,text,source_quote,snapshot}; persisted=false,
approval_required=true. Bilgi zaten kayıtlıysa proposal=null. Yeni öneri
eskisinin ID'sini geçersiz kılar; RAM'de tek aday ve restart'ta kayıp. Stop/hata/
unknown raporundaki aday UI'da otomatik gösterilmez; profil değişmez. TaskManager
tekrar kaydı tutulur; eski öneri sonucu yeni bir kalıcı kayıt yetkisi değildir.

Onay gereken öneri sohbet altındaki dört kontrolün sağında ayrı Save/Dismiss
grubunda görünür; Personalization açılmaz. Metin ve kaynak güvenli
textContent ile gösterilir. Save/Dismiss memory_decision({request_id,
arguments:{id,approve}}) gönderir. Kimlik ve metin tahmin edilmez; approve gerçek
boolean olmalıdır. Model yalnız sonraki gerçek kullanıcı turunda taze memory.read
sonucundaki bekleyen ID için memory.decide({id,approve}) kullanabilir. Aynı
turda propose çağrısı yapılmışsa onay kapalıdır; tekrar read bu kilidi aşmaz.
Model kendiliğinden onay üretmemeli, belirsiz yanıtta açıklama istemelidir. Öğrenme açıkken tüm model eklemeleri (açık hatırla dahil) memory.propose
hattına gider; inceleme veya doğrudan kaydı depodaki tercih belirler; memory.patch enum'undan append çıkarılır ve submit'te de engellenir.

Karar sonrası completed+verified ve güncel memory_profile gelmeden başarı
sunulmaz. Eski ID/değişmiş belge/izin/ret/restart otomatik ekleme yapmaz.
Bilinmeyen sonuç tekrar edilmez; native yeni model mesajını engeller. Bilinen
terminal ret/eski aday görünümden kaldırılır; meşgul ret daha sonra kullanıcı
tekrar deneyebilir. Doğrulanmış karar decided_id taşır; UI yalnız aynı adayı
gizler. Stop'tan önce tamamlanmış karar geri alınmaz. Yeni sağlayıcı bağlantısı/ücretli
çıkarım servisi yoktur; öneri mevcut konuşmanın araç adımlarıdır.


Araç hatalarında Engine & Skill Log, yalnız güvenli biçimdeki hata kodunu da
basar (ör. source_unavailable). Ham argüman/konuşma/sır veya exception metni
loglanmaz. Böylece failed/not verified tek başına tanısız kalmaz.


## Öğrenilen bilgide onay tercihi

prof.pMemoryConfirm boolean, eksik/eski profilde true. Genel profil kaydı,
snapshot/yedek ve native şema aynı tercihi taşır; legacy profil eski false
seçimini miras almaz. pMemory/pLearn kapalıysa bu checkbox tek başına kayıt açmaz.

true: memory.propose persisted=false/approval_required=true adayı döndürür ve
UI alt kontrol grubunun sağında adayın metnini/kaynağını ve Save/Dismiss
düğmelerini gösterir. Vex normal metin/ses yanıtında doğal olarak izin ister;
sabit TTS veya ikinci ses hattı yoktur. Sonraki kullanıcı yanıtı aynı karar
aracını kullanır. memory.read saved text/snapshot yanında ayrı proposal alanı
döndürür; bekleyen aday onaylı hafıza değildir. Değişmiş snapshot adayı düşürür.

false: memory.propose mevcut _apply append/readback ile diske yazar;
data.proposal=null, saved_automatically=true ve verified/persisted/read_back
kanıtı döner. UI memory_profile ile editörü yeniler; yeni onay penceresi açmaz,
ikinci mutasyon/save üretmez. Araç memory.write yetkisi ister. Stop gerçek
kaydı geri almaz; replay ikinci kayıt üretmez. Hatalı/belirsiz yazı başarı
sayılmaz, otomatik tekrar yoktur. Tercih snapshot'a dahildir: sonradan değişen
onay seçeneği eski taze okumayla yapılan kaydı da reddeder.

Model tercih seçemez veya değiştiremez. Yeni bilgilerin tümü hâlâ memory.propose
hattından geçer; memory.patch append ile bu tercih atlanamaz. Kullanıcının
sormadan kayda açık tercihi, önceki sürümün her aday için Save zorunluluğunun
isteğe bağlı alternatifi olmuştur. Anlamsal çıkarım doğruluğu garanti edilmez.


## Token kullanımı — uygulama oturumu toplamı

Python tarafındaki ayrıştırma, güvenli sayı denetimi ve toplama yalnız
app/session/gemini.py içindedir: gemini_token_count ve GeminiUsage.
TextChat tek uygulama ömrü için bir sayaç tutar; adaptörler veriyi bu sahibine
iletir. Yeni token.py, kalıcı kullanım dosyası veya genel sağlayıcı framework'ü yoktur.

REST her gerçek HTTP yanıtının usage_metadata.total_token_count değerini
(araç döngüleri dahil) bir kez ekler. Live aynı üretimin ara bildirimlerini
birbirine eklemez; son snapshot'ı araç çağrısı/üretim bitiş sınırında bir kez
sayar. Tur özeti uygulama toplamına bir kez katılır. Interactions TTS ayrı
isteğinin usage.total_tokens değeri de aynı toplama eklenir; ses oynatılmasa
veya Stop gelmiş olsa da alınmış kullanım kanıtı silinmez.

Sohbet/ses raporu usage_tokens (güvenli tam sayı veya null),
usage_scope='session', usage_partial boolean alanlarını taşır. Gösterge
uygulama açılışından kapanışına kadardır; Stop, Disconnect, model/anahtar veya
sohbet bağlamı değişimi sıfırlamaz. Yeniden başlatma yeni sayaç oluşturur.
Sayaç JavaScript'te tekrar toplanmaz; istek kimliği denetiminden sonra gösterilir.
Yeni mesaj sırasında önceki oturum toplamı görünmeye devam eder.

Eksik/geçersiz metadata veya belirsiz ağ denemesi sıfır sayılmaz: bilinen toplam
korunur, usage_partial=true kalır; UI ≥ değeri ve Incomplete açıklamasını gösterir.
Hiç geçerli bildirim yoksa — gösterilir. Gerçek 0 geçerlidir. Bu, sağlayıcının
raporladığı kullanımların toplamıdır; hesap kotası, ücret/fatura veya mevcut
context doluluğu değildir. Sağlayıcı kayıp/geç bildirimi geri sorgulanmaz.
Transport'un idle kontrolünde tüketilen geç metadata ayrıca hesaba katılmaz;
usage eksik gelen tur bu yüzden kesin toplam olarak işaretlenmez.
Mevcut tokens(used,max,isEst) uyumluluk setter'ı korunur; uygulama sohbeti
setSessionTokens ile backend toplamını gösterir. Ek countTokens API çağrısı yoktur.

Sağlayıcı sözleşmesi: https://ai.google.dev/api/live#UsageMetadata


## Yerel telemetri — 6.2.1

main, tek Telemetry örneğini create_core ve NativeBridge'e enjekte eder.
query_system → {ok,completed,data}; hazır olmayan bridge veya payload reddedilir.
data: sampled_at (monoton saniye), os/os_release/architecture/logical_cpu_count,
cpu_percent, memory_percent, memory_total/memory_used (bayt), disk_total/disk_used
(bayt), disk_volume (yalnız sürücü harfi), battery_percent/battery_present,
ac_connected, active_process (exe adı), gpu_percent/cpu_temperature/gpu_temperature
ve unavailable alan adları. CPU sıcaklığı destekli kaynak yoksa None'dır;
GPU alanları aşağıdaki Windows sayaç sözleşmesi kapsamındadır. CPU ilk ölçümde
veya desteklenmeyen kapsamda None'dır; pil yok ve pil bilinmiyor farklıdır.

system_view.js güvenli sayı ve alan tiplerini denetler; geçmiş sampled_at kabul
etmez, RAM/disk değerlerini GiB'ye dönüştürür. Başlık için güvenli textContent
kullanır. Query başarısız veya on iki saniyedir yeni sonuç yoksa metrikler — olur;
geç cevap yeni örneği geriye götüremez. pagehide sonuç teslimini durdurur.
Native başlangıcı/kurtarma sonrası açılır; bağımsız tarayıcı sahte CPU üretmez.
CPU/GPU sıcaklığı, uzak internet yoklamaları ve media henüz bağlı değildir. Modelin offline durumu
yerel ölçümü ve oturum token toplamını silmez.

Win32 kaynakları: https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getsystemtimes
ve https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getforegroundwindow


## Windows GPU alanları — 6.2.2

query_system ve model system.status aynı örneği kullanır:
- gpu_source='windows-pdh', gpu_status=ok/warming_up/unavailable.
- gpu_devices=[{id,utilization_percent}]. id, Windows adaptör/fiziksel cihaz
  sayaç kimliğidir; ürün adı veya Task Manager GPU indeksi olduğu varsayılmaz.
- gpu_percent: listelenen kartların en yüksek motor kullanım yüzdesi; liste
  boşsa None. Aynı motordaki süreçler toplanır, farklı motorlar toplanmaz.
- gpu_sampled_at: ortak sampled_at ile aynı monoton saniye. İki saniyelik
  cache ve mevcut UI polling sıklığı korunur. İlk referans örneği yüzde değildir.
- gpu_temperature/cpu_temperature=None; VRAM kapasitesi/ürün adı/üretici
  indeksi bu kaynaktan üretilmez. Önceki yayınlanmamış vendor alanları kaldırıldı.

Sayaç API hatası/boş veya geçersiz örnek unavailable olur; önceki GPU değeri
saklanmaz, CPU/RAM silinmez. Gerçek sıfır geçerlidir. UI üst açıklama satırı
kaldırılmıştır; GPU etiketi sabit, bar yüzdesi clamp(0,100)'dür. Kayıp veri —
ve boş barla ayrılır; boş bar tek başına hata anlamına gelmez.

Kaynaklar:
- https://devblogs.microsoft.com/directx/gpus-in-the-task-manager/
- https://learn.microsoft.com/en-us/windows/win32/api/pdh/nf-pdh-pdhaddenglishcounterw
- https://learn.microsoft.com/en-us/windows/win32/api/pdh/nf-pdh-pdhgetformattedcounterarrayw


## Pasif ağ alanları — 6.2.3a

Mevcut query_system/system.status data alanına eklenir:
- network_source='windows-iphelper'.
- network_link: true aktif fiziksel kart, false bilinen aktif kart yok,
  None kaynak/operasyonel durum bilinmiyor. İnternet erişimi kanıtı değildir.
- network_kind: wifi/ethernet/other/multiple veya None.
- network_wifi_connected: true/false/None; sinyal yüzdesi değildir.
- network_receive_bps/network_send_bps: byte/s, ilk/eksik/reset/değişmiş
  arabirim kümesinde None. Birim bps burada byte/s; Mbps dönüşümü ×8/1_000_000.
- unavailable listesi kayıp network_link ve hız alanlarını da içerir.

Alanlar ortak iki saniyelik örnek ve sampled_at ile gelir. UI Receive/Send
iki ondalık Mbps, Local link ve Wi-Fi bağlılık etiketlerini gösterir. Küçük
trafik 0.00 Mbps olarak yuvarlanabilir; model tam byte/s değerini görür.
Hız testi, data plan kotası, paket içeriği veya internet erişimi ölçülmez.
Kaynak/stale hatasında yalnız yerel ağ alanları — yapılır; API gecikmesi ayrı
sahibindedir. Model offline olması yerel ağ ve CPU/RAM ölçümünü temizlemez.
setNetwork eski ping/down/wifi/api alanlarını korur; up (Mbps), link enum'u ve
wifiConnected boolean/null alanları eklenir. Wi-Fi sinyal ve ping aşağıdaki kalite adaptöründen gelir; pasif trafik
sayacından türetilmez. Ağ yapılandırması veya radyo değiştirilmez.

Kaynaklar:
- https://learn.microsoft.com/en-us/windows/win32/api/netioapi/nf-netioapi-getiftable2
- https://learn.microsoft.com/en-us/windows/win32/api/netioapi/ns-netioapi-mib_if_row2


## Ağ kalitesi alanları — 6.2.3b

Aynı query_system/system.status data içinde:
- network_ping_ms: IPv4 fiziksel default gateway ICMP RTT ms veya None.
- network_ping_status: ok/timeout/unreachable/no_gateway/no_link/unavailable.
- network_wifi_signal: 0–100, en düşük bağlı fiziksel Wi-Fi kalite yüzdesi veya None.
- network_wifi_status: ok/unsupported/access_denied/not_connected/unavailable.
- network_quality_sampled_at: monoton saniye; network.sample cache üretim zamanı.

Kalite örneği en çok on saniye saklanır; kart/rota değişikliği anında yeniler.
Temel sampled_at ile aynı olmak zorunda değildir, geçmişte/eşit olmalıdır;
UI tooltip kalite yaşını sampled_at ile farkından gösterir. Global 12 s staleness
kalite değerlerini ve tooltip'lerini de temizler. Sıfır geçerlidir.

UI Gateway ping etiketini kullanır; bu genel internet/API gecikmesi değildir.
Timeout None gösterir, internet offline/bağlı değil kararı üretmez. Wi-Fi bağlı
ve kalite okunamıyorsa Connected · —; bağlı değilse Not connected; kaynak
bilinmiyorsa —. Yüzde kalite alanından gelir, trafik veya link hızından hesaplanmaz.
setNetwork legacy wifi yüzde/ping ms setter'ları korunur. API alanı ayrı kalır.

GetIpForwardTable rotası yalnız aktif fiziksel kartlardan seçilir; ham hedef
adresinin UI/tool çıktısı yoktur. Model istenen host'a ping atamaz; araç parametresizdir.
WLAN opcode 19 konum gerektirmez; destek yoksa/izin reddedilirse hassas fallback
çağrısı yapılmaz. Windows handle/buffer'ları finally'de bırakılır.

Kaynaklar:
- https://learn.microsoft.com/en-us/windows/win32/api/iphlpapi/nf-iphlpapi-getipforwardtable
- https://learn.microsoft.com/en-us/windows/win32/api/icmpapi/nf-icmpapi-icmpsendecho
- https://learn.microsoft.com/en-us/windows/win32/api/wlanapi/ne-wlanapi-wlan_intf_opcode
- https://learn.microsoft.com/en-us/windows/win32/api/wlanapi/ns-wlanapi-wlan_realtime_connection_quality
