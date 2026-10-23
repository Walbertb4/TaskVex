# TaskVex — Mimari ve geliştirme rehberi

## Güncel öncelik — 5.R2 sesli tur sınırı

Yazı çalışırken sesli girişte 25 s bekleme kullanıcı tarafından tekrar bildirildi.
Tek Live sahibi, ses setup'ında otomatik VAD'yi kapatır; LiveInput sırayla
activityStart → PCM → activityEnd gönderir. Yerel 700 ms sessizlik, ön tampon,
15 s sınırı ve Stop/unknown kuralları korunur; audioStreamEnd ile karıştırılmaz.
921 pytest, 7 JS ve 10/10 native geçti; gerçek sağlayıcı/fiziksel kabul açık.
Güncel durum [aşamalar.md](aşamalar.md), eski protokol aşağıda tarihsel kayıttır.

## Önceki uygulama — 5.R1 uyku/algılama kararlılığı

Yeni özellik sırası durduruldu; kullanıcıdaki gecikme/Stopped/Idle bildirimi
incelendi. Açık EOS, yanıt sonrası gürültü sınırı, tek wake motoru cache'i ve
host sonrası sabit yerel onay sesleri uygulandı. Live/core/kaynak sahipliği ve
Stop/unknown korunur; otomatik araç replay yoktur. Gerçek mikrofon/sağlayıcı
kabulü açık. Kanıt/karar: [inceleme](docs/STAGE5_SLEEP_STABILITY_REVIEW.md),
güncel sıra [aşamalar.md](aşamalar.md). Runtime manuel kabul bekler.

## Önceki uygulama — 5.F3

Metin ve kesin ses transkriptindeki uyku niyeti ortak host parser'da
once/persistent/off olarak ayrılır. TR/EN fiil/nezaket/boşluk varyantları
tam cümlede tanınır; soru/olumsuz/alıntı/ek iş reddedilir. Model onayı
gerçek uyku kabulü sayılmaz; sleep_start, tek Live/core/kaynak sahipliği
korundu. F2 fiziksel uyanış/25 s ve F4 telaffuz açık. Güncel kayıt
[aşamalar.md](aşamalar.md) içindedir; runtime manuel kabul bekler.

## Önceki uygulama — 5.F2

Tek mikrofon sahibi AudioContext statechange ile aynı kaynağı sınırlı resume
eder; başarısızlıkta kaynak kapanır ve açık hata gösterilir. PCM/metin
saklamayan tur ölçümleri 25 s beklemeyi ayırır; otomatik istek/araç replay
eklenmedi. Uyanınca komut alamama fiziksel bildirimi henüz kapanmadı.
Güncel kabul/açıklar [aşamalar.md](aşamalar.md) içindedir; commit yok.

## Önceki uygulama — 5.F1

5.F1 kod/hedefli regresyon/native doğrulaması tamam; manuel kabul bekler.
Kesin konuşma bitişi eski PCM'i kapatır, model/araç sonucu devam eder.
UI uyku hazırlığını gerçek host kabulünden ayırır; belirsizlikte kilitlenir.
Wake-only bir görev tamamlaması değildir. Tek Live/core/mikrofon sahipliği
korundu; yeni framework/servis yok. Güncel sıra [aşamalar.md](aşamalar.md)
içindedir; sıradaki 5.F2, mevcut Idle/25 s sorunlarıdır.

## Güncel durum — 23 Ekim genel denetim

Güncel aşama/alt adım kaydı artık [aşamalar.md](aşamalar.md) içindedir.
Uyku/ses katmanında beş yeniden üretilmiş runtime açığı açıktır; kodun varlığı
ve geçen regresyon bunları kapatmaz. Ayrıntı: [uyku/genel denetim](docs/STAGE5_SLEEP_AUDIT.md).
Bu tur uygulama kodu değiştirilmedi; aşama güncelleme zorunluluğu AGENTS.md'ye
kaydedildi. Aşama 5 kapanmadı, Aşama 6'ya geçilmedi. Önceki alt başlıklar
tarihsel çalışma kayıtlarıdır; güncel sıra aşamalar.md içindeki 5.F1–5.F6'dır.

## Güncel kapsam — uyku davranışını düzeltme / ilk adım

Kullanıcının anlam düzeltmesiyle Stay asleep, görev/yanıt bitince hemen geri
uyuma; sleepDelay ise normal konuşmada tek seferlik idle uyku olarak ayrıldı.
Yanıtta persistent barge-in açılmaz; mevcut tek mikrofon/Live/core hattı,
aktif/unknown/eski kaynak engelleri korunur. Süre 0 ile kapatılabilir.
Bu dilim manuel kabul bekler, önceki dilim tam kabul/commit sayılmadı.
Kalan sıra: (2) wake/idle giriş yaşam döngüsü, (3) esnek TR/EN uyku niyeti,
(4) yerel wake telaffuzu ve yanlış uyanma, (5) birleşik kabul. Ayrıntı
ve kanıt docs/STAGE5_MODEL.md'de; sonraki aşama açılmadı.

## Güncel dilim — otomatik geri uyuma ve saniye ayarı

Uyku/giriş düzeltmeleri kullanıcı onayıyla `701f33f` commit'ine alındı; push
yok. Kalıcı uyku tercihi ve açık kapatma, aynı host kontrol hattına eklendi.
Tercih sohbet RAM'inde, sleepDelay (1–300 s/default 10) ayarlar dosyasında
kalır. Tek UI timer'ı yalnız kesin bitiş/idle sonrasında mevcut sleep_start
kullanır; aktif/unknown/konuşma atlanmaz, yeni worker veya araç replay yoktur.
Mic On/Off kamera efektiyle eşlendi. Bu dilim manuel kabul bekler; sonraki
adım Aşama 5 açık sınırları/genel kabul ve debloat kontrolüdür. Kanıt ve
sınırlar docs/STAGE5_MODEL.md'de; alttaki eski dilimler tarihsel kayıttır.

## Güncel kabul — wake giriş sonu ve sade mikrofon

R4–R5 ve bildirilen uyku ret çıktısı için düzeltmeler yapıldı; fiziksel kabul
bekler. micB yalnız kullanıcı On/Off tercihidir; hata/bağlantı ayrı durumda
kalır. thought-only giriş kapatmaz, wake sessizliği ve 15 s sınırı yalnız EOS
üretir. Uyku adayı çıktısı host kararı için sınırlı RAM'de bekler. Tek Live /
mikrofon/core sahipliği ve Stop güvenliği korunur. Kullanıcı önceki dilimde
sorun bildirdiğinden yeni commit yok; ayrıntı docs/STAGE5_MODEL.md'dedir.

## Güncel öncelik — 23 Ekim R1–R3 kabulü

R0 kullanıcı onayıyla `616125d` commit'ine alındı; push yok. R2–R3 yerel wake
hata sınıfları, en fazla iki kaynak yenilemesi ve doğru mikrofon durumları
ile küçük R1 Veks uyku hitabı uygulandı; manuel kabul bekler. Tek mikrofon,
tek Live sahibi ve core araç hattı korunur; eski PCM/araç/model replay yoktur.
Sırada R4–R5 giriş sınırları ve erken thought kapanması vardır. Bunlar ve
son kabul bitmeden otomatik geri uyuma veya sonraki özellik aşaması açılmaz.
Ayrıntı/kanıt: docs/STAGE5_MODEL.md. Alttaki eski dilimler tarihsel kayıttır.

İnceleme düzeltme sırası başladı: bu tur yalnız R0 yerel wake zaman hizalaması
ve UI/backend hit kabulü. Tek mikrofon/Live/core sahipliği korundu; yeni worker,
API/araç replay veya bağımlılık yok. Hata sonrası toparlanma ve diğer inceleme
bulguları sonraki adımdır. Ayrıntı ve açık kabul sınırları STAGE5_MODEL.md'de.

23 Ekim uyku kabul düzeltmesi: fiziksel kullanıcı testinde bildirilen sorunlar
nedeniyle sonraki adım açılmadı. Wake yerel motor hatasının mikrofon engelinden
kurtarır; SLEEPING ayrı renk/durumdur. Dar uyku hitapları genişletildi, araç
izinleri değişmedi. Ayrıntı ve fiziksel kabul sınırı STAGE5_MODEL.md içindedir.

## Güncel dilim — tek seferlik uyku ve yerel wake-word

Stop göstergeleri kullanıcı onayıyla 515a531 commit'ine alındı; push yok.
Bu yeni dilim manuel kabul bekler. Uyurken PCM yalnız yerel sherpa-onnx'e
gider; hit veya açık Wake/yazılı istek sonrasında tek mevcut Live hattı açılır.
Kişiselleştirme pWake seçimi kaydedilir; default Vex, destekli İngilizce sözlük
sözcükleri. Aynı mikrofon/AudioWorklet ve sınırlı tampon kullanılır; yeni core
worker yoktur. Model dosyaları yerel veri cache'indedir ve MIT diye
etiketlenmez. Fiziksel mikrofon kabulü açık. Sonraki adım otomatik geri uyuma
ve saniye ayarıdır; UI temizliği Aşama 5 sonunda. Ayrıntı STAGE5_MODEL.md.

## Güncel küçük düzeltme — Stop göstergeleri

Geçici hafıza kullanıcı kabulüyle dc79318 commit'ine alındı; push yok.
Bu tur yalnız mikrofon On ışığının kaynak devrinde sabit kalması ve normal
kesmenin bağlantı hatası yerine nötr LIVE READY gösterilmesi uygulandı.
Fiziksel capture/Stop protokolü değişmedi; gerçek kaynak/unknown engeli ve
hatalar korunur. Yeni dilim manuel kabul bekler. Yerel wake-word ve tek
seferlik uyku sonraki ayrı uygulama adımıdır.

## Güncel uygulama dilimi — geçici sohbet hafızası

Komut rehberi/ayar yerleşimi kullanıcı onayıyla d4ffb16 commit'ine alındı;
push yok. Bu yeni uygulama dilimi manuel kabul bekler. TextChat'in tek
kilidinde sınırlı RAM geçmişi tutulur; fresh Live socket'e yalnız tarihçe
verisi aktarılır, eski araçlar çalıştırılmaz. Stop/Disconnect korur; New Chat,
kapanış ve anahtar güncellemesi temizler. Mevcut core/not otoritesi değişmedi.
Sınır: 12 tur/16.000 JSON karakteri ve metin başına 2.000 karakter; özet API
isteği veya kalıcı profil yoktur. commands.md güncellendi. Sıradaki ayrı iş
yerel wake-word/tek seferlik uyku; tam davranış STAGE5_MODEL.md'dedir.

## Güncel kapsam kararı — Live ana ürün, hafıza ve uyku

22 Ekim 2026: önceki ses/Mic Off dilimi kullanıcı kabulüyle `ba47710`
commit'ine alındı; push yok. Ana masaüstü deneyimi yalnız Live olacak;
REST daha sonra farklı araç/kanal kullanımları için korunacak. Ana UI'daki
REST test kontrolü hedefli temizliğe alındı; henüz koddan kaldırılmadı.

Güncel yürütme sırası: Aşama 5'e uygulama sahipliğinde sınırlı geçici sohbet
hafızası, yerel wake-word ile tek seferlik uyku, ardından her işten sonra
uykuya dönme tercihi ayrı adımlar olarak eklenir. Sonra bütünleşik kabul,
hedefli UI/debloat ve son regresyon/belge kapanışı gelir. Kalıcı kullanıcı
bilgisi/çıkarım hafızası Aşama 6 başına, entegrasyonlardan önce planlanır.
Kullanıcı hafızası yönetimi ve wake-word seçimi Kişiselleştirme'ye; otomatik
uykuya dönüş süresi saniye cinsinden Ayarlar'a yerleştirilecek. Çalışan
konuşma komutları kökteki commands.md içinde İngilizce belgelenir; her komut
değişiminde güncellenmesi zorunludur. Bu özellikler henüz uygulanmadı.
Ayrıntılı davranış ve sınırlar:
[STAGE5_MODEL.md](docs/STAGE5_MODEL.md), "22 Ekim 2026" kapsam kararı.
Sonraki uygulama adımı geçici sohbet hafızasıdır. İleriki uygulama adımlarında
CORE_START_PLAN.md güncel işlem sırası izlenir; aşağıdaki eski hedef aşamalar
bu yeni kapsamı uygulanmış özellik olarak göstermemelidir.

## Güncel dilim — REST ses çıkışı ve Mic Off giriş sonu

Önceki mikrofon tercihi kullanıcı kabulüyle `f35a13e` olarak commit edildi;
push yapılmadı. Bu dilim kullanıcı tarafından 22 Ekim 2026 tarihinde
manuel testleri başarılı bildirilerek kabul edildi.
REST metni önce UI'a döner. Native UI, host'ta o request_id için saklanan
başarılı cevabı `read_reply` ile yalnız bir kez seslendirir. Mevcut TextChat
kilidi/Stop kimliği ve PCM çıkışı kullanılır; yeni araç yürütücüsü yoktur.
Araçsız Gemini TTS ayrı API isteğidir; başarısızlığı metni veya tamamlanan
notu geri almaz, model/araç retry'si başlatmaz. CLI/bot açıkça read_reply
çağırmadığında sessizdir. REST mikrofon/STT eklenmedi.

Microphone Off artık yalnız capture'ı kapatır ve mevcut sıralı Live girişine
`audio_stream_end` bildirir; setup beklerken de Stop göndermez. Live yanıtı
ve çalması devam eder. Stop ayrı iptal davranışını korur. Ayrıntı ve sınırlar
STAGE5_MODEL.md ile UI/backend sözleşmesindedir. Sonraki adım gerçek bütünleşik
kullanıcı kabulüdür; Aşama 5 kapanışı ve UI/debloat henüz yapılmadı.

Bu belge ajanlar ve geliştiriciler için mimari başvuru kaynağıdır. Genel çalışma kuralları `AGENTS.md` içindedir. Buradaki hedef ağaç ve aşamalar, bütün bileşenlerin bugün var olduğu anlamına gelmez; yalnız kullanıcı tarafından istenen aşama uygulanır.

Kaynak: `JARVIS_AKIS_DIYAGRAMLARI.html` içindeki proje notları ve 16 diyagram. Aktarım tarihi: 20 Ekim 2026. HTML değiştirilmedi. Kaynakta kalan Jarvis, JARVIS_HOME, jarvis.spec gibi adlar eski planın adlarıdır; bunlar mevcut kodu veya veri yollarını topluca yeniden adlandırma talimatı değildir. Ürün adı TaskVex'tir.

## 1. Bugünkü durum ve belgeyi kullanma

En güncel ara düzeltme mikrofon On/Off tercihidir: Stop ve kesin biten model
hatası tercihi kapatmaz; yalnız yeni konuşma beklenir, eski istek tekrarlanmaz.
Donanım/izin/Disconnect ve unknown capture engeli ayrı tutulur; On kilidi aşamaz.
UI değişikliğidir, yeni araç/worker veya REST ses yolu yoktur. Adım 5 kullanıcı
onayından sonra 78c292a commit'ine alındı. REST ses adımı sonraya bırakıldı.

En güncel dilim adım 5'tir: sessiz hazır mikrofon idle, yerel konuşma listening,
model bekleme thinking, ses çıkışı speaking gösterir. Aktivite bir gösterimdir;
yeni yürütücü veya sunucu VAD yerine geçmez. Normal Stop/kapanış hata logundan
ayrıldı, Engine log sınırlı tutulur. Live olay sessizliği/toplam tur süreleri
25/120 s, UI Live/REST beklemesi 210/240 s'dir; timeout belirsizlik kilidini
açmaz. Adım 4 kullanıcı kabulünden sonra 73a87df ile commit edildi.

En güncel dilim adım 4'tür: kaydedilmiş pLang/pIns aynı ortak model_instruction
üreticisinden REST ve Live'a gider. Host profil snapshot'ını diskten alır;
tercihler araç yetkisi vermez. Etkili talimat değişimi sonraki Live mesajında
eski resume/çağrı kapsamını bırakır ve yeni bağlam açar. Dil tanıma otomatik
kalır; seçilen yanıt dili promptla yönlendirilir. Diğer profil alanları modele
aktarılmaz. Adım 3 kullanıcı kabulünü geçti ve 85648b9 ile commit edildi.

En güncel dilim adım 3'tür: yerel konuşma adayı yanıt sırasında daha uzun ve
kuvvetli olmalıdır; düşük frekans/ofset ve arka plan enerjisi dikkate alınır.
Başarılı yanıt sonundaki mikrofon/ön tampon artık aynı kaynakla boşta beklemeye
geçer. Core, backend olayları ve not iş mantığı değişmedi. Sıralı Stop/bitiş/yeni
tur devri korunur; tam çift yönlü aynı socket protokolü ve fiziksel yankı kabulü
açık sınırdır. Transkript adım 2 kullanıcı kabulünü geçti (`3daf152`).

Son UI/model dilimi: Live giriş/çıkış transkripti artık tur sonunu beklemez;
tek Live sahibi kimlik/sıra taşıyan metin snapshot'larını UI'a iletir. Her rol
tek balonda güncellenir, kesilen metin korunur, eski tur yeni mesaja yazamaz.
Gösterim live_transcript.js'tedir; ses, core ve not iş mantığı değişmedi.
Kullanıcının açıklamasıyla önceki not şüphesi doğrulanmış hata sayılmadı;
not incelemesi ertelendi. Bu adım yalnız transkript gösterimidir.

Son adım: kullanıcı otomatik dinlemeyi onayladı. Live yanıtı sırasında yerel
ses adayı algılandığında oynatma kesilir; eski turun gerçek Stop/bitiş sonucu
beklenir ve aynı tek model/core hattında yeni konuşmaya geçilir. Belirsiz
sonuçta veya bağlantı/izin/cihaz hatasında bekleyen ses atılır. Bu, sıralı tur
devridir; aynı socket'te eşzamanlı çok turlu protokol değildir ve aktif Stop
mantıksal bağlamı sıfırlayabilir. Yeni backend olayı/worker eklenmedi. Gerçek
mikrofon/yankı kabulü açık; ayrıntılar STAGE5_MODEL.md'nin başındadır.

Güncel küçük ses dilimi: Live katalog/model hazır olunca yerel otomatik
dinleme açılır; her konuşmada Mic tıklaması gerekmez. Sessizlik API'ye gitmez;
yerel sınırlı ön tamponla bulunan ses adayı aynı tek Live/core hattını açar.
Yanıt sırasında giriş kapanır, ses bittikten sonra otomatik yeniden dinler.
Üst düğme Pause/Resume'dur; Stop/hata/Disconnect otomatik modu durdurur.
Bu yarı çift yönlü kullanım olup konuşarak araya girme ayrı sonraki adımdır.
Yeni framework, backend yürütücüsü veya L0 entegrasyonu eklenmedi.

Son dilim: otomatik cihaz listesi kullanıcı tarafından onaylandı. Mic şimdi
konuşurken 100 ms PCM paketlerini aynı Live sahibine gönderir; otomatik VAD
tek konuşmayı bitirir. Giriş/çıkış aynı sohbet kilidi ve core araç hattındadır.
İlk araç/model yanıtında giriş kapanır; 15 saniye ve sınırlı RAM kuyruğu,
kimlikle Stop, transkript kapısı ve belirsizlik kuralları korunur. Kontrollü
testler mevcut; gerçek hesap/fiziksel VAD kabulü açık. Sıradaki ayrı adım
konuşarak araya girmedir; aşama 5 kapanmadı. Aşağıdaki başlat/bitir klip
açıklaması önceki kabul diliminin tarihçesidir.

22 Ekim güncellemesi: kullanıcı Live ses çıkışı ve açık başlat/bitir mikrofon
kabulünü tamamladı. `live_mic.js` en çok 15 saniye RAM kaydını bitişte PCM'e
çevirip aynı Live sahibine gönderir. Sonraki tek dilim cihaz yönlendirmesidir:
native dIn/dOut browser kimliğiyle seçilir; exact giriş/setSinkId çıkışında
sessiz cihaz fallback'i yapılmaz. Tercihler mevcut ayar hattında kalır.
Otomatik/sürekli dinleme henüz eklenmedi. Ses/metin setup değişimi ayrı
mantıksal oturum açar. Cihaz testleri kullanıcı tarafından onaylandı; Scan
düğmesi kaldırıldı. Liste açılışta/ayarlarda/devicechange'de otomatik yenilenir;
listeleme mikrofon açmaz, ilk izin yalnız Mic düğmesindedir. Sıradaki adım VAD'dır.

- Aşama 4'ün planlı kabulü tamamlandı; kullanıcıyla kapatıp tekrar açma raporları doğrulandı. Aşama 5'te `v1/app/session/model_tools.py` ortak araç adaptörü ve `gemini.py` SDK metin/araç turları hazırdır. Gerçek SDK/HTTP taşıma sınırı kontrollü testlerle denendi; 3.5 Flash-Lite ile canlı katalog ve sentetik not kabulü geçti. 3.8 Flash ana model olarak korunur; araç öncesi sınırlı retry/alternatif model geçişi kontrollü testlerle doğrulandı. Tek mesaj UI/model/not yenileme hazır; not aktarımı beklerken genel sohbet çalışır. Live model listesi açık API sorgusuyla yüklenir, REST metin tercihinden ayrıdır. Kalıcı Live oturumu, bağlantı yeniden kullanımı ve açık Disconnect hazırdır. Live `notes.add/list/update/delete`, `apps.catalog`, `system.status` çağrılarını aynı core'a taşır; notlar ilk aktarım onayı ister. Kimlikle eşleşen REST/Live Stop ve güvenli idle checkpoint ile GoAway/resumption hazırdır; modelden not düzenleme/tamamlama/silme kullanıcı tarafından REST/Live’da onaylandı; oluşturulma zamanı ve tek kısmi metin/son not seçimi kontrollü testlerle hazır; yeni seçim kullanıcı tarafından onaylandı; Live ses çıkışı kullanıcı tarafından onaylandı; başlat/bitir mikrofon kullanıcı tarafından onaylandı; cihaz seçimi kontrollü testlerle hazır, gerçek çoklu cihaz/VAD kabulü açık. [Aşama 5](docs/STAGE5_MODEL.md) güncel sınırı, [kullanıcı kabul planı](docs/USER_ACCEPTANCE.md) gerçek kullanım denemelerini açıklar.

- Aşama 3 planlı otomatik ve görünür kabul tamam: native notlar backend otoritesinde; sabit kimlikli CRUD, açık onaylı tek seferlik eski veri aktarımı ve yedek restore bağlandı. Tarayıcı-only yerel mod korunur. Güncel sınırlar [STAGE3_NOTES.md](docs/STAGE3_NOTES.md), gerçek diyalog/restart kabulü [STAGE3_VISIBLE_ACCEPTANCE.md](docs/STAGE3_VISIBLE_ACCEPTANCE.md) içindedir.
- Aşama 4: `apps.catalog/status/open` aynı registry/policy/TaskManager hattındadır. OS paket/sistem yolu kimliği denetlenir; başlık veya basename tek başına kanıt değildir. Açma apps.read+apps.launch ister, Windows'un sistem başlatıcısı bir kez çağrılır ve pencere ayrıca doğrulanır. Katalog kurulum tespiti, WS_VISIBLE ise etkileşime hazır garantisi değildir; [Aşama 4 adımları](docs/STAGE4_APPS.md) kabul sınırlarını açıklar.

- UI `v1/ui/` altında HTML/CSS ve vanilla JavaScript ES modülleridir. İlk native host ve dar ayar/durum köprüsü `v1/app/main.py` ile açılır; [Aşama 2 planı ve test](docs/STAGE2_NATIVE.md) güncel kapsamı açıklar.
- Aşama 1 tamamlandı: ortak veri tipleri, ToolRegistry, tek worker'lı TaskManager, ilk yerel policy, atomik kayıt ve gerçek not/sistem araçları hazır. `v1/app/bootstrap.py` core'u kurar. Aşama 2 ayar/durum ve Aşama 3 not UI bağlantıları hazır. [Aşama 1 kabulü](docs/STAGE1_CORE.md), [Core sözleşmeleri](docs/CORE_CONTRACTS.md), [ToolRegistry](docs/TOOL_REGISTRY.md), [TaskManager](docs/TASK_MANAGER.md), [Policy](docs/POLICY.md) ve [Kayıt](docs/STORAGE.md) ilgili sınırları açıklar.
- UI dosyaları: `index.html`, `styles.css`, `assets/`; JS modülleri: `api`, `app`, `connections`, `credentials`, `notes`, `panels`, `reactor`, `routines`, `schema`, `settings`, `sfx`, `live_audio`, `live_mic`, `skills`, `storage`, `timers`. Aşağıdaki eski hedef ağaçta schema.js ve storage.js bulunmaması, bu modülleri silme gerekçesi değildir.
- Mevcut köprü ve veri davranışlarının ayrıntıları: [UI/backend sözleşmesi](v1/ui/docs/UI_BACKEND_CONTRACT.md). UI üzerinde çalışırken önce bu sözleşmeyi ve ilgili kodu oku. Bu belgenin eski diyagramları mevcut olay payload'larını kendiliğinden değiştirmez.
- Tarihsel inceleme ve düzeltme notları: [UI düzeltmeleri](v1/ui/docs/AUDIT_FIXES.md); açılış bilgileri: [UI README](v1/ui/README.md).
- Tasarım hedefi ile mevcut sözleşme arasında fark varsa farkı açıkça belirt. Mimariyi hayata geçirmek için sözleşme değişikliği gerekiyorsa ilgili çağıranları, testleri ve belgeleri aynı değişiklik kapsamında güncelle; sessiz uyumsuzluk oluşturma.
- Tam hedef klasör ağacı bir yol haritasıdır. Boş klasör, kullanılmayan arayüz veya henüz gerekmeyen servis üretme. Mevcut v1/ui yerleşimini sırf ağaca benzetmek için taşıma.

## 2. Ajanların koruyacağı mimari sınırlar

1. **L0 doğrudan yeteneklerdir:** notlar, dosya/uygulama işlemleri ve servis API araçları. L1–L4 ise GUI hedef çözümleme/otomasyon yöntemleridir. Google Drive, Calendar, Gmail için yeni L0.5 katmanı açılmaz.
2. **Kanal, araç ve istemci farklı sorumluluklardır:** Telegram/Discord gelen komutu kullanıcı bağlamıyla ortak hatta taşır; mesaj gönderme bir araç veya izinli bildirimdir; sağlayıcı API ayrıntısı integrations içinde kalır.
3. **TaskManager yürütmeyi yönetir:** görev kimliği, sıra, durum, iptal, süre ve kaynak sahipliği. İş mantığını, Google istemcisini veya GUI locator çözümünü içine toplama. Resolver aday bulur; policy izin kararı verir; yürütücü uygular; doğrulama sonucu belirler.
4. **Ortak iş mantığı girişe bağlı değildir:** UI, ses ve bot aynı araç/servis hattını kullanır. Bridge yalnız taşıma, doğrulama ve yönlendirme yapar; araçlar masaüstü UI nesnesini import etmez.
5. **Yan etkiyi iki kez yürütme:** kabul ile tamamlanmayı ayır; belirsiz sonuçta yeniden göndermeden önce durumu gözlemle. Görev/çağrı kimliğini ve kullanıcı bağlamını koru. Rutin tetikleme sahibi tek olmalı; backend scheduler eklenirken UI zamanlayıcısının ikinci kez çalıştırması önlenmeli.
6. **Durum ve kayıt ayrıdır:** mevcut UI'ın yerel kayıt davranışını koru; backend eklendiğinde kalıcı otorite ve senkronizasyon açık sözleşmeyle belirlensin. Backend setter'ları outbound komut/save döngüsü oluşturmasın. Eksik alan, null ve sıfır aynı kabul edilmesin.
7. **Güven sınırlarında doğrula ve veri zehirlenmesini (Indirect Prompt Injection) engelle:** model çıktısı, bot mesajı, HTML sayfası, taranan ekran metni ve import dosyası yürütme yetkisi değildir. Kullanıcı/hesap/hedef/kapsam bağlamını policy'de değerlendir; sırları loglara ve sıradan JSON yedeklerine yazma. L2 (DOM), L4 (ekran/OCR), Web, e-posta veya harici dosyalardan okunan tüm içerik modele daima açıkça "güvenilmeyen dış veri" (untrusted data) olarak işaretlenir. Bu veriler model bağlamındayken oturum kirlenmiş (tainted) sayılır; kritik/geri alınamaz işlemler (terminal çalıştırma, dosya/not silme, mesaj/e-posta gönderme, dış ağ istekleri) PolicyEngine tarafından otomatik olarak `CONFIRM` (arayüzde kullanıcıdan açık onay alma) seviyesine yükseltilir. Model, dış içerikten okuduğu komutlarla kullanıcının yerine sessizce tehlikeli eylem yürütemez.
8. **Kaynağın sahibi kapatır:** görev iptali ve uygulama kapanışında zamanlayıcı, ses, model oturumu ve abonelikler doğru sırada temizlensin. Başkasına ait MediaStream track'i gibi kaynakları sahiplik sözleşmesi olmadan kapatma.
9. **API değişimini adaptörde tut:** sağlayıcı SDK ayrıntıları ortak iş mantığına sızmasın. Yerel model hedefi ileride aynı model/araç sözleşmesini kullanabilir; sırf API kullanıyor diye model eğitimi veya yeni katman ekleme.
10. **Başarıyı kanıtla:** değişen davranışı hedefli testle doğrula; mock köprü testini gerçek PyWebView, donanım veya gerçek hesap testi diye sunma. Var olan görünüm, hata yönetimi, veri bütünlüğü ve erişilebilirliği koru.

## 3. HTML'den aktarılan proje notları

Aşağıdaki notlar kaynak HTML'nin içeriğidir. Numaralandırma ve tarihsel adlar korunmuştur.

## Tüm proje için klasör düzeni

### 2. Tam hedef klasör düzeni

Bu bir hedef haritasıdır. Bütün klasör ve dosyalar ilk gün oluşturulmayacak; ihtiyaç duyulan aşamada eklenecek. Küçük uygulamada aynı sorumluluğa ait birkaç yapı birlikte başlayabilir.

```text
jarvis/
├─ app/
│  ├─ __init__.py
│  ├─ main.py                      # giriş noktası
│  ├─ bootstrap.py                 # bileşenleri oluştur ve birbirine bağla
│  ├─ lifecycle.py                 # başlatma ve sıralı kapatma
│  ├─ config.py                    # yollar, ortam ve uygulama ayarları
│  ├─ logging_setup.py             # dönen dosya logu ve maskeleme
│  │
│  ├─ core/
│  │  ├─ contracts.py              # ortak istek, sonuç, hata ve olay tipleri
│  │  ├─ request_context.py        # kullanıcı, kaynak, sohbet, hesap ve kimlikler
│  │  ├─ command_service.py        # bütün girişler için ortak komut kabulü
│  │  ├─ response_router.py        # yanıtı doğru kullanıcı ve kanala yönlendir
│  │  ├─ events.py                 # sınırlı olay aktarımı ve abonelikler
│  │  ├─ state.py                  # Python'daki canlı uygulama durumu
│  │  └─ profile.py                # kişiselleştirme ve profil davranışı
│  │
│  ├─ tasks/
│  │  ├─ manager.py                # görev sırası ve yaşam döngüsü
│  │  ├─ models.py                 # görev, adım, sonuç ve iptal durumu
│  │  ├─ resources.py              # masaüstü ve diğer ortak kaynak sahipliği
│  │  └─ journal.py                # gerektiğinde kalıcı işlem/adım günlüğü
│  │
│  ├─ policy/
│  │  ├─ engine.py                 # allow / confirm / deny kararı
│  │  ├─ rules.py                  # yetenek, eylem, hedef ve kapsam kuralları
│  │  └─ approvals.py              # belirli işlem ve kullanıcıya bağlı onaylar
│  │
│  ├─ identity/
│  │  ├─ principals.py             # Jarvis kullanıcı kimliği ve yetkileri
│  │  ├─ bindings.py               # Telegram/Discord kimliğini kullanıcıya bağla
│  │  └─ accounts.py               # kullanıcının bağlı servis hesapları
│  │
│  ├─ bridge/
│  │  ├─ webview_bridge.py         # Python ↔ mevcut HTML/JS köprüsü
│  │  ├─ dispatcher.py             # mevcut emit olaylarını handler'a yönlendir
│  │  ├─ schemas.py                # UI payload doğrulaması ve sürüm bilgisi
│  │  └─ handlers/
│  │     ├─ settings.py
│  │     ├─ notes.py
│  │     ├─ timers.py
│  │     ├─ session.py
│  │     ├─ audio.py
│  │     ├─ skills.py
│  │     ├─ routines.py
│  │     └─ connections.py         # hesap bağlama ve bağlantı durumları
│  │
│  ├─ channels/
│  │  ├─ base.py                   # ortak giriş/çıkış adaptörü sözleşmesi
│  │  ├─ desktop.py                # masaüstü istek/yanıt bağlamı adaptörü
│  │  ├─ telegram.py               # güncelleme alma, kimlik ve cevap adaptörü
│  │  └─ discord.py                # bot komutları ve cevap adaptörü
│  │
│  ├─ session/
│  │  ├─ model_gateway.py          # model sağlayıcısını ortak akışa bağla
│  │  ├─ live_session.py           # Gemini Live oturumunun tek sahibi
│  │  ├─ text_agent.py             # UI olmadan da metin komutu yorumlama yolu
│  │  ├─ conversation_store.py     # kullanıcı ve sohbet bazında konuşma bağlamı
│  │  └─ tool_registry.py          # araç şeması ve yönlendirme
│  │
│  ├─ tools/                       # L0: modelin ve komut servisinin çağırdığı araçlar
│  │  ├─ local/
│  │  │  ├─ notes.py
│  │  │  ├─ timers.py
│  │  │  ├─ weather.py
│  │  │  ├─ telemetry.py
│  │  │  ├─ media.py
│  │  │  ├─ apps.py
│  │  │  ├─ files.py
│  │  │  ├─ search.py
│  │  │  └─ terminal.py
│  │  ├─ google/
│  │  │  ├─ drive.py
│  │  │  ├─ calendar.py
│  │  │  └─ gmail.py
│  │  └─ messaging.py              # kullanıcı isteğiyle mesaj gönderme araçları
│  │
│  ├─ integrations/                # dış servislerin somut API istemcileri
│  │  ├─ google/
│  │  │  ├─ oauth.py               # Google hesap bağlantısı ve token yenileme
│  │  │  ├─ drive_client.py
│  │  │  ├─ calendar_client.py
│  │  │  └─ gmail_client.py
│  │  ├─ telegram_client.py        # gelen kanal ve gönderme aracı ortak kullanır
│  │  ├─ discord_client.py
│  │  └─ weather_client.py
│  │
│  ├─ audio/
│  │  ├─ engine.py                 # mikrofon/hoparlör, kapı ve ön-tampon
│  │  ├─ devices.py                # cihaz envanteri ve değişim yönetimi
│  │  ├─ loopback.py               # tüm sistem sesi analizi
│  │  └─ process_loopback.py       # tek uygulama sesi; destek ayrıca doğrulanır
│  │
│  ├─ automation/                  # GUI otomasyonu: dört katman
│  │  ├─ contracts.py              # hedef adayı, işlem ve doğrulama sözleşmesi
│  │  ├─ resolver.py               # yöntem ve hedef seçimi
│  │  ├─ verification.py           # başarı / uygulanmadı / belirsiz / iptal
│  │  ├─ skills.py                 # öğrenme ve sürümlü self-heal
│  │  └─ layers/
│  │     ├─ l1_memory.py
│  │     ├─ l2_dom.py
│  │     ├─ l3_uia.py
│  │     └─ l4_vision.py
│  │
│  ├─ platform/
│  │  └─ windows/
│  │     ├─ windows.py             # pencere bulma ve odak
│  │     ├─ applications.py        # Start menüsü ve UWP başlatma
│  │     ├─ media.py               # SMTC ve medya kontrolleri
│  │     ├─ clipboard.py           # pano değişikliklerini koruma
│  │     ├─ capture.py             # DPI/monitör bilgisiyle ekran yakalama
│  │     └─ telemetry.py           # işletim sistemi ölçümleri
│  │
│  ├─ services/
│  │  ├─ notes.py                  # ortak not iş mantığı
│  │  ├─ timers.py                 # ortak sayaç iş mantığı
│  │  ├─ catalog.py                # model/ses katalogları
│  │  └─ sync.py                   # gerektiğinde arka plan veri eşitleme
│  │
│  ├─ scheduling/
│  │  ├─ routines.py               # rutin tanımı ve yaşam döngüsü
│  │  ├─ triggers.py               # saat, uygulama ve Wi-Fi tetikleyicileri
│  │  └─ scheduler.py              # tetiklenen işi TaskManager'a ilet
│  │
│  ├─ notifications/
│  │  ├─ service.py                # bildirim tercihi ve hedef dağıtımı
│  │  └─ delivery.py               # teslimat sonucu ve kontrollü tekrar
│  │
│  └─ storage/
│     ├─ json_store.py             # atomik yazma, kilit, bozuk veri kurtarma
│     ├─ migrations.py             # kalıcı veri şema geçişleri
│     ├─ credentials.py            # işletim sistemi gizli bilgi deposu adaptörü
│     └─ repositories/
│        ├─ settings.py
│        ├─ profiles.py
│        ├─ notes.py
│        ├─ skills.py
│        ├─ routines.py
│        └─ identities.py
│
├─ ui/
│  ├─ index.html                   # mevcut görünümün HTML iskeleti
│  ├─ styles.css                   # mevcut stil
│  ├─ assets/                      # mevcut ikon, ses, görsel ve fontlar
│  └─ js/
│     ├─ api.js                    # mevcut köprü fonksiyonları
│     ├─ app.js
│     ├─ reactor.js
│     ├─ settings.js
│     ├─ panels.js
│     ├─ notes.js
│     ├─ timers.js
│     ├─ skills.js
│     ├─ routines.js
│     ├─ connections.js
│     └─ sfx.js
│
├─ tests/
│  ├─ conftest.py                  # izole JARVIS_HOME ve ortak fixture'lar
│  ├─ unit/                       # iş mantığı ve sözleşmeler
│  ├─ integration/                # köprü, kayıt ve istemci sınırları
│  ├─ scenarios/                  # uçtan uca kabul ve hata senaryoları
│  └─ fixtures/                   # örnek kayıtlar ve sahte API cevapları
├─ docs/
│  ├─ ARCHITECTURE.md
│  ├─ UI_CONTRACT.md
│  ├─ TOOL_CONTRACT.md
│  ├─ PERMISSIONS.md
│  ├─ DEVELOPMENT_STAGES.md
│  └─ ACCEPTANCE.md
├─ scripts/
│  ├─ run_dev.ps1
│  ├─ run_bot.ps1
│  └─ build.ps1
├─ packaging/
│  ├─ jarvis.spec
│  └─ assets/
├─ pyproject.toml                  # proje metadata ve araç yapılandırmaları
├─ requirements.txt               # sabitlenmiş üretim bağımlılıkları
├─ requirements-dev.txt           # test ve geliştirme bağımlılıkları
├─ .env.example                    # sadece örnek adlar; gerçek sırlar yok
├─ .gitignore
└─ README.md
```

`__init__.py` dosyaları gerekli Python paketlerinde eklenir; ağaçta tekrar etmemek için yalnız kökte gösterilmiştir. Bağımlılıkların hangi dosyada tanımlanıp nasıl sabitlendiği bir kez belirlenir; pyproject ve requirements arasında elle yönetilen iki farklı liste oluşturulmaz.

### 3. Sorumluluk sınırları

| Klasör | Ne yapar? | Sınır |
| --- | --- | --- |
| `bridge` | Mevcut HTML/JS ile Python arasında taşıma | İş mantığını veya Google API çağrısını içine almaz. |
| `channels` | Komutu kimden/nereden aldığını ve cevabın nereye gideceğini belirler | Her bot için ayrı asistan mantığı yazmaz. |
| `core` | Ortak istek ve cevap akışı | Somut webview veya Discord nesnelerine bağımlı olmaz. |
| `tasks` | Sıra, kaynak sahipliği, görev durumu ve iptal | Hedef düğmenin locator'ını bulmaz. |
| `policy` | Belirli işlem için yetki kararı | OAuth bağlantısını sınırsız eylem onayı saymaz. |
| `identity` | Platform kimlikleri ile Jarvis kullanıcı/hesap eşleştirmesi | Sohbet adını güvenilir kullanıcı kimliği saymaz. |
| `tools` | Yetenek adı, parametre, doğrulama ve sonuç sözleşmesi | UI'a doğrudan çağrı yapmaz. |
| `integrations` | Sağlayıcıya özgü API ve bağlantı davranışı | Kullanıcı niyeti veya masaüstü sırası kararı vermez. |
| `services` | Birden fazla girişten kullanılabilen iş mantığı | Her tek satırlık istemci çağrısına gereksiz servis katmanı eklenmez. |
| `automation` | GUI hedef çözme, uygulama kanıtı ve öğrenme | API izinlerini UI yoluyla aşmaya çalışmaz. |
| `platform/windows` | Windows'a özgü erişim | UI veya model bağlamı saklamaz. |
| `storage` | Kalıcı dosyalar ve gizli bilgi deposu | Uygulamanın canlı durumunun yerine geçmez. |
| `scheduling` | Zaman/olay tetikleme | Araçları TaskManager'ı atlayarak çalıştırmaz. |
| `notifications` | İzinli bildirimleri ilgili kanala dağıtma | Her bildirimi yeni bir kullanıcı komutu gibi yorumlatmaz. |

Mevcut birleşik plandaki `policy.py`, bu hedefte ihtiyaç büyüdüğünde `policy/` paketine dönüşebilir. Aynı şekilde tek state dosyasıyla başlanabilir; kalıcılık ve profil ayrımı ihtiyaçla büyür. İlk gün tek bir kural için üç policy dosyası açmak zorunlu değildir.

Bağımlılık yönü: **giriş adaptörleri → ortak komut/görev hattı → policy ve araçlar → iş mantığı/API/Windows adaptörleri**. UI ve botlar ortak sonuç/olayları alır. Başlatma dosyası somut bileşenleri bağlar; araçlar masaüstü UI nesnesini import etmez.

### 4. Çalışma verisinin yeri

```text
%APPDATA%/JARVIS/
├─ app_state.json                 # kalıcı kullanıcı ayarları
├─ profiles/                      # gerektiğinde kullanıcı bazında profil
├─ notes.json
├─ skills/
├─ routines/
├─ identities.json                # eşlenmiş kullanıcı ve kanal kimlikleri
├─ accounts.json                  # sır olmayan hesap tanımları
├─ task_journal/                  # gerektiğinde kalıcı görev/adım kayıtları
└─ logs/
```

API anahtarları, bot token'ları ve OAuth refresh token'ları sır olmayan hesap dosyasına açık yazılmaz; credential adaptörü üzerinden işletim sistemi deposunda tutulur. İlk tek kullanıcılı sürüm `profile.json` ile başlayabilir; çok kullanıcıya geçiş veri şeması değişikliğiyle yapılır. Geçici test verileri gerçek JARVIS_HOME'dan ayrılır.

### 5. İlk gün için küçük iskelet

Tam hedef ağacını ilk gün açmak yerine şu kadar dosyayla başlanabilir:

```text
jarvis/
├─ app/
│  ├─ main.py
│  ├─ bootstrap.py
│  ├─ config.py
│  ├─ logging_setup.py
│  ├─ core/contracts.py
│  ├─ core/events.py
│  ├─ core/state.py
│  ├─ tasks/manager.py
│  ├─ policy/engine.py
│  ├─ bridge/webview_bridge.py
│  ├─ bridge/dispatcher.py
│  ├─ bridge/handlers/notes.py
│  ├─ session/tool_registry.py
│  ├─ tools/local/notes.py
│  └─ storage/json_store.py
├─ ui/                            # hazır arayüz ve varlıkları
├─ tests/                         # izole not/kayıt ve köprü senaryosu
├─ requirements.txt
├─ requirements-dev.txt
└─ README.md
```

Buradaki TaskManager başlangıçta kuyruk, kimlik, durum ve iptal sinyaliyle sınırlı olabilir. Policy önce bilinen güvenli not ekleme işlemine izin verir. Tool registry bir araçla başlayabilir. İşlev artmadan çok kullanıcılı altyapı veya genel eklenti sistemi yazılmaz.

## Projede ilerleme aşamaları

### 1. Önerilen başlangıç

Hazır UI'ı entegre etmek ve L0 ile başlamak doğru tercih. İlk hedef bütün UI'ı çalışır göstermek veya bütün araçları yazmak değil; mevcut bir UI eyleminin gerçek bir L0 işlemini uçtan uca tamamlaması olmalı.

İlk çalışan dilim: **mevcut UI'daki not ekleme → bridge → görev kaydı → politika → notes.add → kalıcı kayıt → olay → UI'da gerçek sonuç**.

Bu yolun çalışması için ilk günden Gemini, mikrofon, Google hesabı veya ekran otomasyonu gerekmiyor. İlk L0 çağrısı mevcut not formundan gelebilir. Doğal dil yorumlama daha sonra aynı araç sözleşmesine bağlanır; ilk aşama için geçici bir anahtar kelime botu yazılmaz.

TaskManager, policy ve tool registry ilk araçla birlikte küçük kurulmalı. Bütün L0 tamamlandıktan sonra bunları eklemek geri dönüp aynı araçları yeniden bağlamayı gerektirir.

### 6. Projede ilerleme aşamaları

#### Aşama 0 — Mevcut UI'ın çalışan referansını al

**Yapılacak:** UI dosyaları ve varlıklarını envanterle. Ana ekran, notlar, ayarlar ve önemli panellerin aynı boyut/ölçekte görüntülerini al. UI'nın hangi `emit` olaylarını gönderdiğini ve hangi `jarvis.*` fonksiyonlarını beklediğini belgeleyip mevcut görünümü yeni repoda aç.

**Kabul:** Görünüm ve varlıklar korunuyor. Backend hazır olmayan kontroller anlaşılır biçimde kullanılamıyor; sahte başarı veya demo verisi göstermiyor. HTML/CSS/JS ayrımı küçük adımlarla yapılabiliyor.

**İlk commit:** `UI referansı ve temiz uygulama iskeleti`.

#### Aşama 1 — UI köprüsü, ayar ve kayıt

**Yapılacak:** Config, log, canlı state, atomik JSON, bridge, dispatcher ve olay akışını kur. Önce tema gibi tek ayarı bağla. `initApp` ile UI'ı backend durumundan başlat. Handler hatasını görünür yap.

**Kabul:** Tema değiştirilir, kapat-aç sonrası korunur. Hatalı handler uygulamayı dondurmaz. Log dosyası oluşur. UI'a sahte veri aktarılmaz. Yazma hatası başarı diye gösterilmez.

**Bu aşamada yok:** Gemini, Google, Telegram veya ekran otomasyonu zorunluluğu.

#### Aşama 2 — İlk gerçek L0: not ekleme

**Yapılacak:** Küçük TaskManager, policy ve tool registry'yi kur. Mevcut `note_add` eylemini `notes.add` aracına bağla. İstek ve sonucu ortak tiplerle taşı. İptal edilmiş/biten aynı çağrıyı yeniden yürütme. Sonucu olay olarak UI'a yansıt.

**Kabul:** UI'dan eklenen not gerçekten kaydedilir ve yeniden açılışta görünür. Aynı çağrı kimliğinin tekrarı ikinci not üretmez. Geçersiz veri anlaşılır hata verir. Kayıt hatası doğru raporlanır. Testler izole veride çalışır.

**İlk büyük kilometre taşı:** UI'daki bir eylemin gerçek bir L0 işlemini tamamladığı çalışan uygulama.

#### Aşama 3 — Yerel L0 araçlarını küçük gruplarla tamamla

**Önerilen sıra:** Not listeleme/düzenleme → sayaç → hava → telemetri → medya → uygulama başlatma → dosya listeleme/okuma → arama → dosya değiştirme → terminal.

**Yapılacak:** Her araç için ad/parametre/sonuç sözleşmesi, ortak hata davranışı, gerekli policy kuralı ve ilgili UI sonucu ekle. Araca ihtiyaç oldukça servis veya Windows adaptörünü ayır. İş mantığını doğrudan handler'ın içine koyma.

**Kabul:** Her yeni araç küçük gerçek senaryoda çalışır. Salt okunur bağımsız işler paralel yürüyebilir. İptal yeni adımları keser. Dosya değiştirme/terminal tam hedef ve kapsamla değerlendirilir. Desteklenmeyen ölçüm uydurulmaz.

**Neden terminal en sonda?** Parametre, yan etki, iptal ve sonuç belirsizliği diğer araçlardan daha fazla dikkat ister.

#### Aşama 4 — Doğal dil ve ses

**Yapılacak:** Önce yazılı doğal dili mevcut araç şemalarına bağla. Sonra Gemini Live, mikrofon/hoparlör, cihaz seçimi ve sesli yanıtı ekle. Bütün araçlar önceki TaskManager/policy hattını kullanır. Konuşma oturumu ile görev durumu ayrılır. Ortak komut hizmeti UI nesnesine bağımlı olmaz.

**Kabul:** Aynı not/sayaç işlemi UI ve doğal dil yolundan çalışır. Hızlı model/ses değişimi sonrası tek etkin oturum kalır. Yanlış API anahtarı görünür hata verir. Buton/kısayolla durdurma çalışır; yarım kalan işlemler yanlış başarılı sayılmaz.

#### Aşama 5 — Google hesapları ve bulut L0

**Önerilen sıra:** Takvim listeleme/okuma → Drive arama/okuma → mail arama/okuma → taslak → etkinlik oluşturma/değiştirme → yükleme ve gönderme.

**Yapılacak:** Google OAuth ve hesap seçimini ortak kur. Her servis için gereken erişim kapsamını ayrı belirle. Google istemcilerini tool/handler kodundan ayır. Başlangıçta tek hesap olabilir; istek bağlamı hangi hesabın kullanıldığını açıkça taşısın.

**Kabul:** Doğru hesap ve takvim seçilir. Yetki iptali/yenileme hatası açıkça raporlanır. Okuma izni gönderme veya silme yetkisine dönüşmez. Drive bütün dosyaları arama kapsamı ile seçilmiş dosya erişimi karıştırılmaz. Mail içeriği araç kullanma talimatı sayılmaz.

#### Aşama 6 — Telegram ile tek kullanıcılı uzaktan erişim

**Yapılacak:** Önce izinli tek kullanıcı ve özel sohbet eşleştir. Gelen mesajı ortak istek bağlamına çevir. Yanıtı kaynak sohbete yönlendir. İlk bot sürümü için long polling seçilebilir. Bildirim tercihleri ve istek üzerine mesaj gönderme aracı aynı Telegram istemcisini kullansın.

**Kabul:** İzinli kullanıcı takvimini sorabilir; yetkisiz kullanıcı bilgisayarda iş başlatamaz. Tekrar gelen aynı güncelleme çift görev oluşturmaz. Yanıt başka sohbete gitmez. Kullanıcı komutu ile okunmuş mail/video içeriği ayrılır. Bilgisayar veya bot işleyicisi kapalıyken 24 saat erişim varmış gibi sunulmaz.

#### Aşama 7 — GUI otomasyonu: önce L3, sonra L1

**Yapılacak:** Resolver/katman sözleşmesini fake katmanlarla sınayarak başlat. İlk gerçek hedef Not Defteri olsun. UIA ile hedef bul, yaz ve metni okuyarak doğrula. Ardından aynı doğrulanmış tarifi L1'e kaydet. Masaüstü kaynak sahipliğini ekle; hedefi işlem öncesi yeniden kontrol et.

**Kabul:** İlk iş L3 ile, tekrarı L1 tarifi üzerinden L3 ile çalışır. Aynı anda iki görev yanlış pencereye yazmaz. Doğrulama geciktiğinde ikinci kez yazılmaz. Bozuk tarif doğrulanmış yeni sürümle onarılır; önceki sürüm tutulur.

#### Aşama 8 — L2 DOM ve L4 Vision

**Yapılacak:** İsteğe bağlı CDP erişimi ve uygulama yetenek seçimini ekle. Vision'ı yalnız gerekli durumda çağır. DPI, çoklu monitör, görüntü tazeliği, çağrı bütçesi ve pano korumayı tamamla.

**Kabul:** DOM yoksa diğer yollar çalışır. Etiketsiz hedef güncel görüntüyle bulunabilir. Ekran değiştiyse eski kutuya tıklanmaz. Sonucu belirsiz eylem diğer katmanda tekrar edilmez. Vision kaydından sahte DOM locator'ı üretilmez.

#### Aşama 9 — Discord ve UI olmadan çalışma

**Yapılacak:** Discord komut adaptörünü aynı çekirdeğe bağla. İlk sürümde açık bot komutlarıyla başla. Kullanıcı/sunucu/kanal ve bağlı hesap kapsamını uygula. Masaüstü uygulaması ve bot çalışma modu aynı iş mantığını kullansın. UI olmadan başlatılan süreç yalnız yapılandırılmış yetenekleri sunsun.

**Kabul:** Aynı takvim aracı masaüstü, Telegram ve Discord'dan çağrılabilir. Kişisel cevaplar yanlış ortak kanala gönderilmez. Discord kullanıcısı otomatik olarak masaüstü sahibinin yetkisini almaz. Windows erişimi olmayan ortamda GUI işi açıkça kullanılamaz sonucunu verir.

#### Aşama 10 — Rutinler, bildirimler ve dinleme modları

**Yapılacak:** Saat/uygulama/Wi-Fi tetikleyicilerini TaskManager'a bağla. Tekrar tetikleme ve uyku sonrası kuralları belirle. Görev tamamlanınca izinli Telegram/Discord bildirimini gönder. Tüm sistem loopback ve uygulama bazında ses yakalamayı ayrı yetenekler olarak ekle.

**Kabul:** Silinen rutin yeni görev üretmez. Aynı tetikleme çift işlem üretmez. Gönderim sonucu belirsizse mesaj körlemesine tekrar edilmez. Video konuşması komut olmaz. Process loopback desteklenmiyorsa başka modu gizlice kullanmak yerine açık hata gösterilir.

#### Aşama 11 — Paketleme ve dayanıklılık

**Yapılacak:** Temiz Windows ortamında paketleme, sürüm bilgisi, veri şeması geçişi ve kapanış akışını tamamla. Önceki aşamaların testlerini birlikte çalıştır. Gerekli kalıcı işlem günlüğü ve uzun süreli çalışma sınırlarını somutlaştır. Belgeleri gerçek uygulamaya göre güncelle.

**Kabul:** Paket geliştirme araçları olmadan açılır. Ağ kesilmesi, cihaz kaybı, bozuk JSON, uygulama kapanırken aktif görev, eski oturumdan geç cevap, onay beklerken hedef değişimi ve belirsiz dış işlem senaryoları doğru sonuç verir.

### 7. Sırayı esnetme kuralları

- Telegram'dan yalnız bildirim istiyorsan tam uzaktan komut desteğinden önce, yerel L0 tamamlanınca basit bildirim çıkışı eklenebilir. Kimden komut alacağını belirleyen giriş adaptörü ayrı iştir.
- Google entegrasyonu için sesin bitmesi teknik zorunluluk değildir; araç sözleşmesi hazır olduğunda eklenebilir. Yukarıdaki sıra aynı anda çok fazla hata kaynağı açmamak için önerilmiştir.
- Discord desteği çekirdek UI'dan bağımsız kaldığında daha erkene çekilebilir. Her bot için yeni TaskManager veya ayrı araç mantığı yazılmaz.
- Satır sayısı veya bütün klasörlerin dolması ilerleme ölçütü değildir. Çalışan ve doğrulanmış kullanıcı senaryosu ölçüttür.
- Bu aşamalar, eski plandaki Stage numaralarını değiştirerek silmez; UI + L0 başlangıcını ve yeni entegrasyonları kapsayan güncel ilerleme önerisidir.

### 8. İlk üç somut iş

1. Hazır UI'ı yeni uygulamada aç; görünüm referansını ve UI sözleşmesini kaydet.
2. Tema ayarını backend'e bağla; atomik kayıt ve kapat-aç davranışını doğrula.
3. `note_add` eylemini küçük TaskManager/policy/registry üzerinden gerçek `notes.add` aracına bağla; kayıt ve UI sonucunu göster.

Bu üç iş tamamlanınca geliştirmeyi üzerine kurabileceğin gerçek bir uygulama omurgası oluşur.

### 9. TaskVex için iki kalıcı mimari kararı

20 Ekim 2026 tarihinde geliştirme planına eklenen kararlar. Bunlar hedef mimaridir; uygulanmış özellik olarak değerlendirilmez.

### Karar 1 — Dış servisleri adaptörlerle ayır

API kullanımı projenin değerini azaltmaz. Amaç, API değiştiğinde değişikliğin uygulamanın tamamına yayılmasını önlemektir. İş akışı, izinler, iptal ve doğrulama TaskVex çekirdeğinin sorumluluğudur.

**Çağrı yolu:** TaskManager → TaskVex araç sözleşmesi (ör. `calendar.create_event`) → servis adaptörü → Google API.

- Google, Telegram ve Discord'a özgü SDK çağrıları, veri biçimleri ve hata çevirileri ilgili entegrasyon adaptöründe kalır. UI ve TaskManager doğrudan sağlayıcı SDK'sına bağlanmaz.
- Adaptör, dış servis sonucunu ortak araç sonucuna çevirir. Kullanılan hesap, kaynak ve yetki kapsamı istek bağlamında açıkça taşınır.
- Bağımlılık sürümleri kilitlenir; güncellemeler değişiklik notları ve testlerle kontrollü alınır. Sürüm kilitleme, sunucudaki API değişikliklerini, servis kapanışını veya yetki iptalini engellemez.
- Zaman aşımı, kota, ağ kesintisi ve OAuth hataları anlaşılır sonuç üretir. Bir servisin bozulması bağımsız yerel araçları durdurmaz.
- Yeniden deneme, işlemin güvenliğine göre belirlenir. Mesaj gönderme veya etkinlik oluşturma sonucu belirsizse işlem körlemesine tekrarlanmaz; mümkünse işlem kimliğiyle çift yürütme engellenir ve sonuç uzlaştırılır.

**Ne zaman?** Aşama 3'te araç sınırları kurulur; Aşama 5, 6 ve 9'da her servis bu sınır üzerinden eklenir. Adaptör sözleşmesi değişmedikçe sağlayıcı değişikliği çekirdeğin yeniden yazılmasını gerektirmemelidir.

**Kabul:** Adaptör testlerinde sağlayıcı yanıtları ortak sonuca çevrilir; ağ/yetki hatası görünür olur; takvim servisi erişilemezken yerel not ekleme çalışır; belirsiz gönderim çift işlem üretmez. Gerçek hesapla entegrasyon doğrulaması ayrıca yapılır.

### Karar 2 — Model sağlayıcısını değiştirilebilir tut; yerel modeli aşamalı ekle

**Çağrı yolu:** Bulut veya yerel model → ortak görev/araç önerisi → Policy + TaskManager → araç adaptörleri → doğrulanmış sonuç.

Model, araç isteği önerir; yetki ve yürütme denetimini devralmaz. Yerel model de aynı policy, iptal, kaynak kilidi ve doğrulama kurallarına tabidir. Modelin değişmesi görev durumlarını veya araç sözleşmelerini değiştirmemelidir.

- Metin/görev yorumlama için ortak sağlayıcı arayüzü kurulur. Araç çağrısı, yapılandırılmış çıktı ve vision gibi yetenekler açıkça bildirilir; desteklenmeyen özellik varmış gibi sunulmaz.
- Gerçek zamanlı ses/Live oturumu gibi sağlayıcıya özel yetenekler ayrı yetenek sınırında kalır. Bütün modellerin aynı ses veya vision özelliklerini desteklediği varsayılmaz.
- Açık ve belirli UI işlemleri modele ihtiyaç duymadan mevcut TaskManager hattından çalışabilir.
- Yerel model, Google takvimi veya mail erişimini yerelleştirmez. Bulut servis işlemleri hâlâ ilgili servis bağlantısını gerektirir. Yerelde çalışma da kullanılan diğer araçlar bulut çağrısı yapıyorsa tek başına tam çevrimdışı çalışma garantisi değildir.
- Sağlayıcı değiştirme veya buluta geçiş kullanıcı tercihine uyar; özel içerik sessizce buluta gönderilmez. Model değişiminde sonucu belirsiz bir araç işlemi yeniden yürütülmez.

**Geliştirme sırası:**

1. Aşama 4'te bulut modeliyle ortak model sözleşmesini ve ölçülebilir görev örneklerini kur.
2. Çalışan temel akışlardan sonra hazır bir modeli yerelde çalıştırmayı ayrı kilometre taşı olarak ekle. Bu adım eğitim değildir; donanım ve lisans uygunluğu model seçerken değerlendirilir.
3. Aynı görev setinde bulut ve yerel seçeneklerin görev başarısını, araç/parametre doğruluğunu, gecikmesini, kaynak tüketimini ve maliyetini karşılaştır.
4. Tekrarlayan ve veriyle gösterilmiş eksik varsa temiz eğitim örnekleriyle LoRA/ince ayar değerlendir. Eğitimden ayrı tutulan değerlendirme setiyle kazanımı ve gerilemeleri ölç. Kullanıcının değişen notları/bilgileri için önce bellek ve gerektiğinde bilgi getirme yaklaşımını değerlendir.
5. Sıfırdan temel model eğitimi mevcut proje kapsamına alınmaz. İnce ayar, çalışan ürünün zorunlu tamamlanma şartı değildir.

**Kabul:** Desteklenen ortak görevler model sağlayıcısı değiştirilerek çalışır; her iki yol aynı güvenlik ve yürütme kurallarını kullanır; desteklenmeyen yetenek açık hata verir; karşılaştırma sonuçları raporlanır. İnce ayar ancak ölçülmüş iyileşme sağlıyorsa ürün seçeneği olur.

**Resmî başvuru kaynakları:** [Google bağımlılık yönetimi](https://docs.cloud.google.com/apis/docs/client-libraries-best-practices), [Ollama araç çağrısı desteği](https://ollama.com/blog/tool-support), [PEFT / LoRA](https://github.com/huggingface/peft/blob/main/docs/source/quicktour.md).


## 4. Akış diyagramları

Mermaid destekleyen bir Markdown görüntüleyicide çizilirler; düz metin olarak da ajanlar tarafından okunabilirler.

### 1. Uygulamanın bütünü

```mermaid
flowchart LR
    START["Uygulamayı başlat"] --> BOOT["Config, log, kalıcı durum ve UI"]
    BOOT --> READY["Çekirdek hazır; uygun servisleri başlat"]
    READY --> USER["Kullanıcı: ses, yazı veya UI eylemi"]
    READY --> AUTO["Etkin rutin: saat, uygulama veya Wi-Fi"]
    USER --> KIND{"İstek türü?"}
    KIND -->|"Konuşma / doğal dil"| LIVE["Gemini Live: isteği anla"]
    LIVE --> CALL{"Araç çağrısı var mı?"}
    CALL -->|"Hayır"| ANSWER["Metin / sesli yanıt"]
    CALL -->|"Evet"| REG["Tool Registry: araç ve parametre sözleşmesi"]
    KIND -->|"Ayar / durum kontrolü"| HANDLER["Bridge ve ilgili handler"]
    HANDLER --> STATE["Canlı durum / kalıcılık / oturum kontrolü"]
    KIND -->|"Doğrudan işlem / skill"| REG
    AUTO --> REG
    REG --> TM["TaskManager: kaydet, sırala, iptal ve süreyi izle"]
    TM --> ROUTE{"Ekran etkileşimi gerekli mi?"}
    ROUTE -->|"Hayır"| L0["L0: doğrudan araç"]
    ROUTE -->|"Evet"| RES["Resolver: L1 veya L2 / L3 / L4"]
    L0 --> POL["Policy ve güncel ön koşul kontrolü"]
    RES --> POL
    POL --> EXEC["İzin varsa işlemi uygula"]
    EXEC --> VERIFY["Sonucu doğrula; belirsizse önce gözlemle"]
    VERIFY --> RESULT["Görev sonucu; uygunsa L1 öğrenme"]
    RESULT --> OUT["Araç sonucu ve kullanıcıya bildirim"]
    OUT --> ANSWER
    STATE -.-> EVENTS["Event bus, maskelenmiş log ve UI güncellemeleri"]
    TM -.-> EVENTS
    RESULT -.-> EVENTS
    READY --> EXIT["Kapatma isteği"]
    EXIT --> CLOSE["Görevleri durdur, kaynakları kapat, durumu kaydet"]
```



### 2. Açılış ve hazır duruma gelme

```mermaid
flowchart LR
    A["main.py: uygulamayı oluştur"] --> B["Config ve JARVIS_HOME yollarını çöz"]
    B --> C["Dönen log dosyasını ve hata akışını kur"]
    C --> D["Ayar, profil, skill ve rutin kayıtlarını oku"]
    D --> E{"Veri ve şema geçerli mi?"}
    E -->|"Evet"| G["Python canlı durumunu oluştur"]
    E -->|"Hayır"| F["Bozuk veriyi koru; kurtarma / varsayılan ve görünür hata"]
    F --> G
    G --> H["Event bus, bridge ve dispatcher oluştur"]
    H --> I["TaskManager, araçlar, policy ve resolver bağla"]
    I --> J["HTML, CSS ve JS arayüzünü aç"]
    J --> K["initApp ile backend durumunu UI'a uygula"]
    K --> L["Cihaz ve katalog tercihlerini kontrol et"]
    L --> M{"Seçili cihaz kullanılabilir mi?"}
    M -->|"Hayır"| N["Açık fallback ve cihaz bilgisi"]
    M -->|"Evet"| O["Uygun yerel servisleri hazırla"]
    N --> O
    O --> P{"Live bağlantısı kullanılabilir mi?"}
    P -->|"Evet"| Q["Tek etkin Live oturumu ve ses akışı"]
    P -->|"Hayır"| R["Bağlantı hatasını göster; yerel çekirdeği kullanılabilir tut"]
    Q --> S["Hazır: kullanıcı girdisi ve etkin tetikleyicileri bekle"]
    R --> S
```



### 3. Komut girişi ve güven sınırı

```mermaid
flowchart LR
    MIC["Kullanıcının mikrofon sesi"] --> AUDIO["Ses motoru: kapı, ön-tampon, cihaz yönetimi"]
    AUDIO --> LIVE["Gemini Live: ses / metin oturumu"]
    TEXT["UI'da yazılı doğal dil komutu"] --> BR["Bridge: olay ve payload doğrulama"]
    BR --> LIVE
    LIVE --> DEC{"Yanıt mı, araç çağrısı mı?"}
    DEC -->|"Yanıt"| RESP["Metin / ses ve UI"]
    DEC -->|"Araç"| REG["Tool Registry: araç adı ve parametreler"]
    DIRECT["UI'dan run_skill veya doğrudan işlem"] --> DBR["Bridge ve ilgili handler"]
    DBR --> REG
    ROUTINE["Etkin rutin tetiklendi"] --> REG
    REG --> VAL{"Araç ve parametre sözleşmesi geçerli mi?"}
    VAL -->|"Hayır"| ERR["Anlaşılır hata; işlem başlatma"]
    VAL -->|"Evet"| TASK["TaskManager'a görev isteği"]
    WEB["Web (L2), dosya, ekran (L4) veya e-posta"] --> DATA["Güvenilmeyen veri / Tainted Context"]
    DATA -.-> LIVE
    DATA -.-> RULE["İçerikteki talimat yetki vermez; Tainted bağlamda kritik araçlar zorunlu CONFIRM olur"]
    TASK --> POLICY["İşlem öncesinde bağımsız policy kontrolü"]
    POLICY --> ESCALATE["Tainted oturumda yan etkili kritik araçlar CONFIRM onayına yükselir"]
```



#### Dolaylı Prompt Enjeksiyonu (Indirect Prompt Injection) ve Taint Tracking Savunması

Modelin dış dünyadan (web sayfaları, gelen e-postalar, harici dosyalar veya ekrandaki OCR/Vision metinleri) okuduğu içerik saldırganlar tarafından manipüle edilmiş olabilir ("Önceki talimatları unut, şu dosyayı sil / şuraya gönder"). Model bu metinleri okuduğunda bunları kullanıcının gerçek niyeti zannederek araç çağrısı (`terminal.exec`, `gmail.send`, `notes.delete` vb.) üretebilir.

TaskVex bu riski yalnızca prompt mühendisliğiyle değil, **mimari güven sınırları ve PolicyEngine** ile kesin olarak engeller:
1. **Veri ve Talimat Ayrımı (Data vs Instruction Boundary):** Dış kaynaktan okunan tüm metinler model oturumuna sistem/kullanıcı talimatı olarak değil, açıkça izole edilmiş "untrusted_data" rolüyle ve veri zarfı içinde verilir.
2. **Kirlenme Takibi (Taint Tracking):** Oturum geçmişine veya aktif tur bağlamına güvenilmeyen bir dış kaynak (L2 DOM, L4 Ekran/OCR, E-posta, Pano, Harici Dosya) girdiğinde, `RequestContext` veya aktif oturum `is_tainted = True` olarak işaretlenir.
3. **Zorunlu Onay Yükseltmesi (Policy Escalation to CONFIRM):** Oturum `tainted` durumundayken, yan etki doğuran veya dışa veri aktaran araçlar (terminal komutu, mesaj/e-posta gönderme, dosya/not silme veya üzerine yazma, harici ağ istekleri) PolicyEngine tarafından otomatik olarak `CONFIRM` seviyesine çekilir. Model kullanıcının yerine bu işlemleri sessizce çalıştıramaz; UI üzerinde tetikleyicinin dış bir içerikten geldiğini belirten onay modalı açılmadan ve kullanıcı fiziksel olarak onaylamadan TaskManager eylemi icra etmez.

### 4. TaskManager: sıra, kaynak sahipliği ve onay

```mermaid
flowchart LR
    A["Geçerli görev isteği"] --> B["request_id ve varsa çağrı kimliğini kontrol et"]
    B --> C{"Aynı çağrı daha önce kabul edilmiş mi?"}
    C -->|"Evet"| D["Mevcut görev durumunu / sonucunu döndür; yeniden yürütme"]
    C -->|"Hayır"| E["task_id, kaynak, session_id ve son tarih oluştur"]
    E --> Q["queued: görev sırada"]
    Q --> LIMIT{"İptal veya süre sınırı var mı?"}
    LIMIT -->|"Evet"| STOP["İptal / süre akışı; yan etki durumunu koru"]
    LIMIT -->|"Hayır"| TYPE{"Masaüstünü değiştiriyor mu?"}
    TYPE -->|"Evet"| LOCK["Tek masaüstü sırasını bekle ve sahipliği al"]
    TYPE -->|"Hayır"| INDEP["Bağımsızsa paralel; ortak kaynak varsa uygun kilit"]
    LOCK --> RUN["running: hedefi / araç işlemini hazırla"]
    INDEP --> RUN
    RUN --> P["Policy: eylem, hedef, parametre, kapsam"]
    P --> PD{"Karar?"}
    PD -->|"deny"| DENY["İşlem yapma; ret sonucunu kaydet"]
    PD -->|"confirm"| WAIT["waiting_approval; kaynak kilitlerini bırak"]
    WAIT --> APPROVE{"Kullanıcı bu işlemi onayladı mı?"}
    APPROVE -->|"Hayır / iptal"| STOP
    APPROVE -->|"Evet"| REACQ["Gerekli kaynakları yeniden al"]
    REACQ --> REFRESH["Hedefi ve ön koşulları yeniden gözlemle"]
    REFRESH --> P
    PD -->|"allow veya geçerli kapsamlı onay"| CHECK["İptal, süre, hedef ve ön koşulları son kez kontrol et"]
    CHECK --> EXEC["Uygula ve sonucu doğrula"]
    EXEC --> SAVE["Durumu, sonucu ve adım kanıtlarını kaydet"]
    SAVE --> RELEASE["Kaynak sahipliğini bırak; olayları yayınla"]
    STOP --> RELEASE
    DENY --> RELEASE
```



### 5. L0 ve dört katmanlı hedef çözümleme

```mermaid
flowchart LR
    A["Görev / skill adımı"] --> B{"Doğrudan araç uygun mu?"}
    B -->|"Evet"| L0["L0: sayaç, not, hava, medya, uygulama, dosya, arama, terminal"]
    L0 --> READY["Araç veya hedef adayı hazır; ortak policy hattına dön"]
    B -->|"Hayır; GUI gerekiyor"| L1["L1: uygulama ve hedef bağlamında kayıt ara"]
    L1 --> MEM{"Kayıt geçerli mi?"}
    MEM -->|"Evet"| METHOD["Kayıtlı yöntemi seç: L2, L3 veya L4"]
    METHOD --> REFIND["Güncel hedefi ilgili yürütücüyle yeniden bul"]
    REFIND --> MATCH{"Hedef ve ön koşullar uygun mu?"}
    MATCH -->|"Evet"| READY
    MATCH -->|"Hayır"| CDP{"L2 erişimi kullanılabilir mi?"}
    MEM -->|"Yok / geçersiz"| CDP
    CDP -->|"Evet"| DOM["DOM içinde hedefi ara"]
    DOM --> FOUND2{"Bulundu mu?"}
    FOUND2 -->|"Evet"| READY
    FOUND2 -->|"Hayır"| UIA["L3: Windows erişilebilirlik ağacında ara"]
    CDP -->|"Hayır"| UIA
    UIA --> FOUND3{"Bulundu mu?"}
    FOUND3 -->|"Evet"| READY
    FOUND3 -->|"Hayır"| BUDGET{"L4 süre / çağrı bütçesi uygun mu?"}
    BUDGET -->|"Evet"| VISION["L4: güncel ekran görüntüsünden hedef kutusunu bul"]
    VISION --> FOUND4{"Hedef güvenilir ve güncel mi?"}
    FOUND4 -->|"Evet"| READY
    FOUND4 -->|"Hayır"| FAIL["Bulunamadı; denenen yolları raporla"]
    BUDGET -->|"Hayır"| FAIL
```



### 6. İşlemi uygula, sonucu doğrula, güvenle karar ver

```mermaid
flowchart LR
    A["Policy geçti; güncel hedef / araç hazır"] --> B["İptal, süre ve ön koşulları kontrol et"]
    B --> GO{"Devam edilebilir mi?"}
    GO -->|"Hayır"| NO["Yeni işlem başlatma; gerekçeyi kaydet"]
    GO -->|"Evet"| ACT["İşlemi uygula; başlatılma ve yan etki bilgisini kaydet"]
    ACT --> OBS["Beklenen sonucu gözlemle"]
    OBS --> V{"Doğrulama sonucu?"}
    V -->|"succeeded"| SUCCESS["İstenen sonuç kanıtlandı"]
    V -->|"not_applied"| RETRY{"İşlem uygulanmadı; sınırlı tekrar uygun mu?"}
    RETRY -->|"Hayır"| FAIL["Başarısız sonucu bildir"]
    RETRY -->|"Evet"| TYPE{"İşlem yolu?"}
    TYPE -->|"GUI"| GUI["Resolver ile hedefi yeniden çöz"]
    TYPE -->|"L0"| TOOL["Araç sözleşmesine göre yeniden hazırla"]
    GUI --> POLICY["Policy ve ön koşulları yeniden değerlendir"]
    TOOL --> POLICY
    POLICY --> A
    V -->|"uncertain"| RECON["Yalnız gözlemle; mevcut durumla sonucu uzlaştır"]
    RECON --> PROOF{"Yeni kanıt ne söylüyor?"}
    PROOF -->|"Başarı"| SUCCESS
    PROOF -->|"Uygulanmadı"| RETRY
    PROOF -->|"Hâlâ belirsiz"| UNCERTAIN["Belirsiz sonucu bildir; eylemi tekrarlama"]
    V -->|"cancelled"| CANCEL["Yeni adım yok; önceki etkiler ve belirsizlik ayrıca kaydedilir"]
    SUCCESS --> LEARN["Uygunsa öğrenme adayı; görev başarısı ayrı korunur"]
    LEARN --> RESULT["Sonucu TaskManager, UI ve gerekiyorsa modele ilet"]
    FAIL --> RESULT
    UNCERTAIN --> RESULT
    CANCEL --> RESULT
    NO --> RESULT
```



### 7. L1 öğrenme ve self-heal

```mermaid
flowchart LR
    A["İşlemin başarısı kanıtlandı"] --> B{"Tekrar kullanılabilir güvenilir tarif var mı?"}
    B -->|"Hayır"| ENDOK["Görev başarılı; yeni kayıt oluşturma"]
    B -->|"Evet"| C["Bağlam, yöntem, hedef tarifi, parametre ve sonuç koşulunu hazırla"]
    C --> D{"Tarif kaynağı?"}
    D -->|"DOM / UIA"| SEM["Semantik hedef tarifi"]
    D -->|"Vision"| VIS["Güvenilir ise yeniden görsel bulma tarifi"]
    SEM --> NEW["Yeni skill veya yeni kayıt sürümü adayı"]
    VIS --> NEW
    NEW --> VAL["Şemayı, hedefi ve sonuç kanıtını doğrula"]
    VAL --> GOOD{"Aday geçerli mi?"}
    GOOD -->|"Hayır"| REJECT["Adayı etkinleştirme; görev sonucunu değiştirme"]
    GOOD -->|"Evet"| SAVE[("Sürümlü skills JSON; önceki sürümü koru")]
    SAVE --> USE["Sonraki görevde L1 eşleştirmesi"]
    USE --> FIND["Kayıtlı yöntemle güncel hedefi bul"]
    FIND --> WORKS{"Kayıt hâlâ uygun mu?"}
    WORKS -->|"Evet"| RUN["Ortak policy, uygulama ve doğrulama hattı"]
    WORKS -->|"Hayır"| HEAL["Resolver ile yeniden çöz; self-heal adayı oluştur"]
    HEAL --> PROVEN["Yeni yöntemle uygulama ve sonuç doğrulaması"]
    PROVEN --> VERIFIED{"Başarı kanıtlandı mı?"}
    VERIFIED -->|"Evet"| C
    VERIFIED -->|"Hayır / belirsiz"| BAD["Yanlış tarifi etkinleştirme; sınırlı başarısızlık takibi"]
    BAD --> DISABLE["Tekrarlayan bozuk kaydı devre dışı bırakabil"]
```



### 8. Ses, Gemini Live ve yeniden bağlantı

```mermaid
flowchart LR
    A["Model, ses ve cihaz tercihleri"] --> B["Tek oturum sahibi; hızlı değişiklikleri birleştir"]
    B --> C["Gerekirse eski Live görevini ve ses kaynaklarını kapat"]
    C --> D["Yeni etkin oturum kimliğiyle bağlan / oturumu sürdür"]
    D --> CONN{"Bağlantı sonucu?"}
    CONN -->|"Başarılı"| ACTIVE["Etkin Live oturumu; greeted durumunu koru"]
    CONN -->|"Geçici hata"| BACKOFF["Sınırlı geri çekilme ve yeniden deneme"]
    BACKOFF --> D
    CONN -->|"Kalıcı anahtar / yetki hatası"| ERR["UI ve log hatası; sonsuz tekrar yok"]
    ACTIVE --> MIC["Mikrofon: kapı, ön-tampon ve sınırlı tampon"]
    MIC --> SEND["Kullanıcı sesini Live'a aktar"]
    SEND --> REPLY["Modelden ses, metin, araç çağrısı veya usage metadata"]
    REPLY --> OUT{"Çıktı türü?"}
    OUT -->|"Ses"| PLAY["Çalma tamponu ve hoparlör"]
    OUT -->|"Metin / transkript"| UI["streamMsg ve UI durumları"]
    OUT -->|"Araç çağrısı"| TM["Registry ve TaskManager"]
    OUT -->|"Token kullanımı"| USAGE["Gerçek usage metadata üzerinden gösterim"]
    PLAY --> HALF["Half-duplex sırasında mikrofon gönderimini yönet"]
    HALF --> MIC
    CHANGE["Model / ses / cihaz değişikliği"] --> B
    STOP["Ses çıkışını durdur"] --> SILENCE["Çalma tamponunu boşalt"]
    TASKSTOP["Bilgisayar görevini durdur"] --> CANCEL["TaskManager iptal akışı"]
```



### 9. Sistem sesi analizi ve uygulama bazında dinleme

```mermaid
flowchart LR
    A["Kullanıcı dinleme modunu seçer"] --> B{"İstenen mod?"}
    B -->|"Kapalı"| OFF["Yakalamayı durdur ve kaynakları bırak"]
    B -->|"Tüm bilgisayar"| SYS["Sistem loopback yeteneğini kontrol et"]
    B -->|"Belirli uygulama"| PROC["Uygulamayı / süreci belirle; process loopback kontrol et"]
    SYS --> SUPPORT{"İstenen yakalama gerçekten destekleniyor mu?"}
    PROC --> SUPPORT
    SUPPORT -->|"Hayır"| ERROR["Açık destek / erişim hatası; başka modmuş gibi davranma"]
    SUPPORT -->|"Evet"| CAPTURE["Seçilen kaynaktan sınırlı ses tamponuyla yakala"]
    CAPTURE --> DATA["Analiz verisi olarak işle / modele sun"]
    DATA --> RESULT["İstenen analiz veya açıklamayı kullanıcıya ilet"]
    DATA -.-> BOUNDARY["Videodaki sözler doğrudan araç yürütme yetkisi değildir"]
    CAPTURE --> CHANGE{"Kapatma veya kaynak değişimi istendi mi?"}
    CHANGE -->|"Kapat"| OFF
    CHANGE -->|"Değiştir"| A
    CHANGE -->|"Hayır"| CAPTURE
```



### 10. UI köprüsü, olaylar, kuyruklar ve kalıcı durum

```mermaid
flowchart LR
    UI["Kullanıcı UI eylemi"] --> EMIT["emit: olay adı, payload ve request_id"]
    EMIT --> BRIDGE["Bridge: sınırlı kuyruk"]
    BRIDGE --> DISP["Dispatcher: şema ve handler yönlendirmesi"]
    DISP --> KIND{"İş türü?"}
    KIND -->|"Bilgisayarda işlem"| TM["TaskManager ve ortak yürütme hattı"]
    KIND -->|"Ayar / profil / durum"| VALIDATE["Alanları ve değerleri doğrula"]
    VALIDATE --> STATE["Python canlı durumunu güncelle"]
    STATE --> PERSIST{"Alan kalıcı mı?"}
    PERSIST -->|"Evet"| WRITE["Kilitli ve atomik kayıt; şema sürümünü koru"]
    WRITE --> JSON[("app_state / profile / notes / routines / skills")]
    PERSIST -->|"Hayır"| EVENT["Durum olayı yayınla"]
    WRITE --> EVENT
    TM -.-> EVENT
    SERVICES["Telemetri, hava, medya ve takvim olayları"] --> EVENT
    DISP -->|"Handler hatası"| ERROR["Maskelenmiş log ve anlaşılır hata"]
    WRITE -->|"Kayıt hatası"| ERROR
    ERROR --> EVENT
    EVENT --> Q{"Olay kuyruk davranışı?"}
    Q -->|"Seviye / telemetri gibi son değer"| COAL["Güncellemeleri birleştir"]
    Q -->|"Onay / hata / görev sonucu"| CRIT["Sessizce düşürme; geri basınç veya açık hata"]
    COAL --> JS["Webview thread kurallarına uygun tek köprü"]
    CRIT --> JS
    JS --> APPLY["jarvis.* ile UI'ı güncelle"]
    JSON -->|"Sonraki açılış"| INIT["initApp: backend durumu yerel yedeğin üzerine"]
    INIT --> APPLY
```



### 11. Arka plan servisleri, rutinler ve çok adımlı işler

```mermaid
flowchart LR
    CONFIG[("Kayıtlı servis ve rutin tercihleri")] --> ENABLE{"Servis / rutin etkin mi?"}
    ENABLE -->|"Hayır"| IDLE["İlgili çalışmayı başlatma"]
    ENABLE -->|"Evet"| TYPE{"İşlev?"}
    TYPE -->|"Telemetri / hava / medya"| READ["Servisten gerçek veriyi oku"]
    READ --> DATA{"Veri alınabildi mi?"}
    DATA -->|"Evet"| EVENT["Event bus üzerinden UI güncelle"]
    DATA -->|"Hayır"| MISSING["Kullanılamıyor / çevrimdışı durumu; veri uydurma"]
    MISSING --> EVENT
    TYPE -->|"Google bağlantısı"| OAUTH["Gerekli dar kapsamlı OAuth izni ve bağlantı"]
    OAUTH --> CAL["Desteklenen takvim / anımsatıcı verisini al"]
    CAL --> EVENT
    TYPE -->|"Rutin"| WATCH["Saat / uygulama / Wi-Fi tetikleyicisini izle"]
    WATCH --> CHECK["Etkinlik, tekrar tetikleme, saat dilimi ve uyku sonrası kural"]
    CHECK --> FIRE{"Çalıştırılmalı mı?"}
    FIRE -->|"Hayır"| WATCH
    FIRE -->|"Evet"| TM["TaskManager'a rutin görevi gönder"]
    TM --> STEP["Sıradaki skill / rutin adımını hazırla"]
    STEP --> PIPE["Resolver veya L0; policy; uygulama; doğrulama"]
    PIPE --> OK{"Adım sonucu?"}
    OK -->|"Başarılı"| SAVE["Adımın sonucunu ve kanıtını kaydet"]
    SAVE --> MORE{"Başka adım var mı?"}
    MORE -->|"Evet"| STEP
    MORE -->|"Hayır"| DONE["Rutin tamamlandı"]
    OK -->|"Hata / belirsiz / iptal"| HOLD["Körlemesine baştan başlama; mevcut durumdan karar ver"]
    DELETE["Rutin silindi / devre dışı bırakıldı"] --> UNSUB["Kaydı güncelle; yeni tetiklemeyi kaldır"]
    UNSUB -.-> WATCH
```



### 12. İptal, zaman aşımı ve güvenli kapanış

```mermaid
flowchart LR
    USER["stop_task / düğme / kısayol"] --> CANCEL["İlgili görevin iptal sinyalini işaretle"]
    TIME["Görev süre sınırı doldu"] --> CANCEL
    CANCEL --> NEW["Yeni adımların başlamasını engelle"]
    NEW --> ACTIVE{"İşlem başlamış mı?"}
    ACTIVE -->|"Hayır"| CLEAN["Bekleyen işi kaldır; kaynakları bırak"]
    ACTIVE -->|"Evet"| COOP["Yürütücüye iptal isteğini ilet"]
    COOP --> OBS["Bilinen etkileri kaydet; gerekirse yalnız gözlemle"]
    OBS --> RESULT["İptal / süre durumunu ve ayrı etki belirsizliğini bildir"]
    CLEAN --> RESULT
    BLOCK["Dış çağrı bloklandı"] --> STRATEGY["Uygun izolasyon / kapatma stratejisi; sadece timeout yeterli değil"]
    STRATEGY --> OBS
    CLOSE["Uygulamayı kapatma isteği"] --> ACCEPT["Yeni görev kabulünü ve tetiklemeleri durdur"]
    ACCEPT --> ALL["Aktif görevlere iptal isteği ilet"]
    ALL --> STATUS["Tamamlanan ve belirsiz etkileri kaydet"]
    STATUS --> AUDIO["Live bağlantısı, ses çalma ve loopback kaynaklarını kapat"]
    AUDIO --> STATE["Kalıcı durumu atomik yaz"]
    STATE --> QUEUE["Kritik olay / logları işle; kuyrukları sonlandır"]
    QUEUE --> RELEASE["Kilitleri, servisleri ve UI kaynaklarını bırak"]
    RELEASE --> END["Uygulama kapalı"]
```



### 13. Görev durumlarının sade görünümü

```mermaid
stateDiagram-v2
    direction LR
    [*] --> Queued: Geçerli görev kabul edildi
    Queued --> Running: Gerekli kaynaklar uygun
    Queued --> Cancelled: Başlamadan iptal
    Queued --> Failed: Başlamadan süre sınırı / hata
    Running --> WaitingApproval: Policy onay istiyor
    WaitingApproval --> Running: Onay, kaynak ve hedef yeniden kontrol edildi
    WaitingApproval --> Cancelled: Kullanıcı iptal etti
    WaitingApproval --> Failed: Onay reddi veya süre dolması
    Running --> Succeeded: Beklenen sonuç kanıtlandı
    Running --> Failed: Tamamlanamadı; hata kaydedildi
    Running --> Uncertain: İşlem sonucu çözülemedi
    Running --> Cancelled: İptal; önceki etkiler ayrıca saklanır
    Succeeded --> [*]
    Failed --> [*]
    Uncertain --> [*]
    Cancelled --> [*]
```



### 14. Somut örnek: Not Defteri'ne yazma

```mermaid
flowchart LR
    U["Kullanıcı: Not Defteri'ne toplantı notlarını yaz"] --> G["Komutu anla ve araç isteği oluştur"]
    G --> T["TaskManager: çağrı kimliği ve masaüstü sırası"]
    T --> R["Resolver: L1 belleğini kontrol et"]
    R --> M{"Geçerli tarif var mı?"}
    M -->|"Evet"| L1["Kayıtlı L3 hedef tarifi"]
    M -->|"Hayır"| NEW["Bu uygulama için L3 yöntemini seç"]
    L1 --> FIND["L3 UIA: güncel pencere ve alanı bul"]
    NEW --> FIND
    FIND --> P["Policy, iptal, süre ve ön koşul kontrolü"]
    P --> A["Metni yaz"]
    A --> V["Alanı yeniden oku ve sonucu doğrula"]
    V --> D{"Sonuç kanıtlandı mı?"}
    D -->|"Başarı"| SUCCESS["Başarılı görev ve uygunsa L1 öğrenme"]
    D -->|"Belirsiz"| OBS["Önce yalnız gözlemle ve sonucu uzlaştır"]
    OBS --> UQ["Çözülemiyorsa belirsizliği bildir, tekrar yazma"]
    SUCCESS --> OUT["Kaynağı bırak ve kullanıcıya sonucu ilet"]
    UQ --> OUT
```



### 15. Öneri: entegrasyonlar ve iletişim kanalları

```mermaid
flowchart LR
    UI["Masaüstü UI ve mikrofon"] --> INPUT["Komut girişi"]
    TG["Telegram kanalı"] --> AUTH["İzinli kullanıcı, sohbet ve mesaj kimliği"]
    DC["Discord kanalı"] --> AUTH
    AUTH --> INPUT
    INPUT --> CORE["Ortak yorumlama ve TaskManager"]
    CORE --> POLICY["Policy: kullanıcı, kaynak, hesap, eylem ve kapsam"]
    POLICY --> CHOICE{"İşlem yolu?"}
    CHOICE -->|"API / ekransız"| L0["L0 araç yetenekleri"]
    CHOICE -->|"GUI gerekli"| RES["Resolver ve L1–L4"]
    L0 --> LOCAL["Yerel araçlar"]
    L0 --> DRIVE["Drive arama, okuma ve yükleme"]
    L0 --> CAL["Takvim okuma ve etkinlik işlemleri"]
    L0 --> MAIL["Mail arama, okuma ve gönderme"]
    L0 --> MSG["İstek üzerine mesaj gönderme"]
    DRIVE --> INTEGRATION["Servis istemcileri ve hesap / OAuth yönetimi"]
    CAL --> INTEGRATION
    MAIL --> INTEGRATION
    MSG --> CHANNEL["Telegram / Discord çıkış adaptörü"]
    INTEGRATION --> RESULT["Sonucu doğrula ve göreve bağla"]
    LOCAL --> RESULT
    RES --> RESULT
    CHANNEL --> RESULT
    RESULT --> ROUTE["Yanıt yönlendirme: kaynak sohbet ve kullanıcı"]
    ROUTE --> TG
    ROUTE --> DC
    ROUTE --> UI
    RESULT -.-> NOTIFY["Yetkili bildirim kuralı varsa bildirim dağıtımı"]
    NOTIFY -.-> CHANNEL
```

Yeni entegrasyonlar için mimari öneri; orijinal planın uygulanmış bir parçası değildir.

### 16. Önerilen geliştirme sırası: hazır UI ve L0 ile başla

```mermaid
flowchart LR
    A["0 · UI referansı ve temiz repo"] --> B["1 · UI köprüsü, tema ve atomik kayıt"]
    B --> C["2 · Küçük TaskManager, policy ve gerçek not ekleme"]
    C --> D["3 · Yerel L0 araçlarını sırayla tamamla"]
    D --> E["4 · Yazılı doğal dil, ardından ses ve Live"]
    E --> F["5 · Google hesapları ve bulut L0"]
    F --> G["6 · Telegram giriş, yanıt ve bildirim"]
    G --> H["7 · L3 UIA, ardından L1 bellek"]
    H --> I["8 · İsteğe bağlı L2 DOM ve L4 Vision"]
    I --> J["9 · Discord ve UI olmadan çalışma"]
    J --> K["10 · Rutinler, bildirimler ve dinleme modları"]
    K --> L["11 · Paketleme ve dayanıklılık"]
```



## AGENTS.md için önerilen bağlantı

Mevcut genel kuralların sonuna şu kısa bölümü eklemek yeterlidir. Bir Markdown dosyasını yanına koymak, her ajanın o dosyayı kendiliğinden okuyacağı anlamına gelmez.

```markdown
## TaskVex project context

- Before changing code, read ARCHITECTURE.md at the repository root and the code relevant to the task.
- For UI/backend work, also read v1/ui/docs/UI_BACKEND_CONTRACT.md.
- ARCHITECTURE.md describes both current state and future plans. Implement only the requested stage; do not scaffold the entire target tree.
- Preserve the architecture's responsibility boundaries and existing UI contracts. Report conflicts; update affected callers, tests and docs together when a change requires it.
- Do not claim native, hardware or external-service integration was verified when only mocks were tested.
```
