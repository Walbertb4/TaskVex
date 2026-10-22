# TaskVex — Mark LVI incelemesi ve core başlangıç planı

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
Bu özellikler henüz uygulanmadı. Ayrıntılı davranış ve sınırlar:
[STAGE5_MODEL.md](docs/STAGE5_MODEL.md), "22 Ekim 2026" kapsam kararı.
Sonraki uygulama adımı geçici sohbet hafızasıdır. İleriki uygulama adımlarında
CORE_START_PLAN.md güncel işlem sırası izlenir; aşağıdaki eski hedef aşamalar
bu yeni kapsamı uygulanmış özellik olarak göstermemelidir.

## Güncel ilerleme — Aşama 5 REST ses dilimi

Kullanıcı önceki mikrofon tercihi düzeltmesini kabul etti; `f35a13e` commit'i
kaydedildi, push yok. Sıradaki REST ses boşluğu aynı TextChat/PCM yoluyla,
araçsız ayrı TTS isteği olarak tamamlandı. Metin önce görünür; ses hatası metni
ve tamamlanan notları bozmaz. Mic Off yalnız giriş sonu bildirir, Live yanıtını
kesmez. Bu yeni dilim manuel kabul bekler. Sonraki ayrı adım bütünleşik gerçek
kabul; sonra hedefli UI/debloat ve son regresyon/belge kapanışı. Aşama 5 açık.

Güncel ara istek: Microphone On/Off tercihi Stop/model hatasından ayrıldı;
kesin bitişte yeni konuşma beklenir. Eski komut tekrar edilmez, kaynak/unknown
engelleri korunur. Adım 5 kullanıcı kabulüyle 78c292a commit'ine alındı.
Bu dilimin manuel kabulünden sonra sıradaki ayrı iş hâlâ REST ses çıkışıdır.

En güncel adım 5: durum/log/süre yönetimi ve istenen idle/listening ayrımı
uygulandı. Araç ve iptal kanıtı korunur; normal Stop hata sayılmaz. Kanıtlar
STAGE5_MODEL.md'dedir. Adım 4 kullanıcı onayıyla 73a87df commit'ine alındı.
Sonraki ayrı iş REST ses çıkışı, sonra entegre kabul ve hedefli debloat/kapanıştır.

En güncel adım 4: pLang/pIns ortak REST/Live talimatına bağlandı. Kaydedilmiş
profil tura özel snapshot'tır; Live'da etkili değişiklik yeni bağlam açar.
Core/araç yetkileri aynı kalır. Kontrollü test kanıtı STAGE5_MODEL.md'dedir;
gerçek hesap dil/stil kabulü bekleniyor. Adım 3 kabulünden sonra 85648b9 ile
commit edildi. Sonraki ayrı adım durum/log/zaman sınırıdır; Aşama 5 kapanmadı.

En güncel adım 3: yerel VAD adayı güçlendirildi; yanıt sonundaki mikrofon ve
ön tampon kapatılmadan boşta dinlemeye devredilir. Hedefli/otomatik test kanıtı
docs/STAGE5_MODEL.md'dedir; gerçek donanım kabulü bekleniyor. Adım 2 kullanıcı
onayından sonra 3daf152 ile commit edildi. Bu yeni adım onaysız commit edilmez.
Sonraki ayrı adım 4 dil ve temel kişiselleştirmedir. Aşağıdaki kayıtlar tarihçedir.


Güncel düzeltme sırası: kullanıcı not şüphesini açıkladı, adım 1 ertelendi.
Adım 2 Live anlık kullanıcı/model transkripti ve kesilen metnin korunması
uygulandı. Kontrollü kanıt docs/STAGE5_MODEL.md'dedir; fiziksel kabul açık.
Sonraki ayrı iş önce belirlenen adım 3 VAD/barge-in düzeltmesidir; kişiselleştirme,
log/süre bakımı, entegre kabul ve debloat henüz bu promptta yapılmadı.

Güncel ses adımı: otomatik dinleme kullanıcı kabulü geçti. Konuşarak yanıtı
kesme mevcut Stop ve tek Live/core hattıyla sıralı tur devri olarak uygulandı;
eski sonuç belirsizse yeni ses gönderilmez. Gerçek hesap/yankı kabulü açık.
Sonraki iş kapanış kabul kontrolleri ve planlı hedefli bakım/debloat kapsamıdır;
bu promptta debloat veya yeni özellik yapılmadı. Aşama 5 henüz kapanmadı.

Son küçük ses dilimi: her konuşmada Mic tıklaması kaldırıldı. Live model hazır
olunca yerel otomatik bekleme, konuşmada aynı Live akışı ve yanıt sonrası
yeniden bekleme vardır. Stop/hata/Disconnect duraklatır; Pause/Resume korunur.
Sessizlik API'ye gönderilmez. Barge-in ayrı sonraki adımdır; aşama 5 kapanmadı.
Kontrol ve fiziksel kabul sınırları docs/STAGE5_MODEL.md'nin başındadır.

Güncel dilim: otomatik cihaz listesi kullanıcı kabulü geçti. Tek konuşmada
gerçek zamanlı PCM ve sunucu VAD'si uygulandı; 737 pytest, 4 Node süiti,
10/10 hidden native faz ve tip kontrolü geçti. Kanıtları docs/STAGE5_MODEL.md'dedir.
Gerçek hesap/VAD kabulü açık. Sonraki
ayrı adım barge-in; aşama 5 kapanışı veya yeni entegrasyonlara geçilmedi.

Son güncelleme: kullanıcı Live ses çıkışı, sınırlı başlat/bitir mikrofon ve
cihaz testlerini onayladı. dIn/dOut aynı ayar/kayıt ve Live/core hattındadır.
Scan düğmesi kaldırıldı; cihaz listesi açılış/ayar/devicechange'de otomatik,
mikrofon izni yalnız Mic düğmesindedir. Sıradaki adım sürekli akış/VAD'dır.
Toplu not silme ayrı iyileştirme olarak STAGE5_MODEL.md'ye
kaydedildi; henüz uygulanmadı. Aşama 5 kapanmadı.

Güncelleme: 22 Ekim 2026. Durum: Aşama 0–4 planlı kabul tamamlandı. Aşama 5'te ortak araç adaptörü ve Gemini SDK metin turları hazırdır; kontrollü testler geçti. 3.5 Flash-Lite ile canlı katalog/not kabulü geçti. Ana model 3.8 Flash korunarak güvenli retry/fallback eklendi; birleşik politikanın canlı kabulü açık. Kalıcı Live, Disconnect ve katalog/sistem/not ekleme-listeleme araç bağlantısı hazır; REST/Live Stop ve güvenli idle resumption hazır; modelden not düzenleme/tamamlama/silme kullanıcı tarafından REST/Live’da onaylandı; oluşturulma zamanı ve tek kısmi metin/son not seçimi kontrollü testlerle hazır; yeni seçim kullanıcı tarafından onaylandı; Live ses çıkışı kullanıcı tarafından onaylandı; başlat/bitir mikrofon kullanıcı tarafından onaylandı; cihaz seçimi kontrollü testlerle hazır, gerçek çoklu cihaz/VAD kabulü açık.

Aşama 0 başlangıç kararları kaydedildi: [STAGE0_DECISIONS.md](docs/STAGE0_DECISIONS.md). Kullanıcı TaskVex'in özgün katkıları için MIT seçti; root LICENSE eklendi. Mark kaynakları referans olarak ayrı tutulacak. İlk kapsam ve güncel baz test kanıtı bu karar belgesindedir.

İlerleme: güncel 727 pytest kontrolü geçti; yeni Live araç sınırındaki 15 test buna dahildir. apps.open gerçek Windows'ta bir kez başlatma, süreç/pencere kanıtı, replay ve mevcut pencereyi kullanma ile doğrulandı. Aşama 3'ün sekiz hidden native süreci ve iki tarayıcı senaryosuna ek olarak [görünür Windows kabulü](docs/STAGE3_VISIBLE_ACCEPTANCE.md) gerçek diyaloglar ve restart ile tamamlandı. [STAGE4_APPS.md](docs/STAGE4_APPS.md) uygulama plugini kabulünü; [STAGE5_MODEL.md](docs/STAGE5_MODEL.md) model bağlantısının güncel dilimini açıklar.

| Aşama | Tamamlananlar | Durum |
|---|---|---|
| 0 — Temel kararlar | MIT, kapsam, mimari/sorumluluk ve UI veri sahipliği, baz test | Tamamlandı |
| 1 — Modelden bağımsız core | Ortam, sözleşmeler, registry, TaskManager, policy, atomik JSON, gerçek notes.add/list ve system.status | Tamamlandı |
| 2 — Native UI | PyWebView, ui_ready/snapshot, ayar kaydı, sistem durumu, pencere kontrolleri, hata/kurtarma, sıraya alınmış save ve onaylı import/export | Planlı otomatik ve görünür kabul tamam |
| 3 — UI notlarını backend'e devretme | Sabit kimlikli CRUD, native komutlar, onaylı tek seferlik eski veri aktarımı, yedek import/export | Planlı otomatik ve görünür kabul tamam |
| 4 — İlk uygulama plugini | apps.catalog/status/open, OS kimliğiyle doğrulama, ayrı açma izni, hata/tekrar/iptal ve kullanıcıyla kapat/yeniden aç | Planlı kabul tamamlandı |
| 5 — Model ve ses | Ortak araç hattı; Gemini SDK metin turları; Windows kimlik deposu; UI ve kalıcı Live araçları | 5.1 tamam; REST canlı kabul alternatif modelle geçti; Live araçları kontrollü testlerle hazır; REST/Live Stop ve güvenli idle resumption hazır; modelden not düzenleme/tamamlama/silme kullanıcı tarafından REST/Live’da onaylandı; oluşturulma zamanı ve tek kısmi metin/son not seçimi kontrollü testlerle hazır; yeni seçim kullanıcı tarafından onaylandı; Live ses ve başlat/bitir mikrofon kullanıcı tarafından onaylandı; cihaz seçimi kontrollü testlerle hazır; sürekli VAD/çoklu cihaz ve eksik hesap kabulleri açık |
| 6–8 | Diğer L0 entegrasyonları, GUI/skill, rutinler/paketleme | Başlamadı |

Bu plan mevcut ARCHITECTURE.md ve v1/ui/docs/UI_BACKEND_CONTRACT.md üzerine kuruludur. Hermes kullanılmayacak. Mark LVI referans olarak incelendi; TaskVex'in backend'i olarak benimsenmedi. Plan gelecekteki dosyaları tarif eder; bugün var olduklarını iddia etmez.

## 1. Karar ve ilk hedef

TaskVex kendi küçük Python core'una sahip olacak. Hazır HTML/JS UI korunacak. Uygulamaya özgü doğrudan yetenekler plugin olarak L0 araç kaydına katılacak; skill bir veya birden fazla araç/GUI adımını bir göreve dönüştürebilecek. Pluginin desteklemediği GUI işlemleri mevcut L1–L4 resolver hattına gidecek.

İlk hedef: modeli ve mikrofonu bağlamadan, mevcut UI'ı native pencerede açan, durum yükleyen, bir yerel araç ve bir uygulama pluginini aynı görev hattından çalıştıran uygulama. Önce çekirdek davranışını doğrula, ardından Gemini Live ekle. Bütün hedef klasörleri ilk gün oluşturma.

## 2. Kaynak ve incelemenin sınırı

Referans dizini: Mark-LVI-main/. README'nin gösterdiği upstream: https://github.com/FatihMakes/Mark-LVI . İnceleme yerel dosyaların bu andaki içeriğine dayanır; ZIP klasöründe Git revizyon kimliği doğrulanmadı.

Dosya ağacı, giriş akışı, action/plugin yükleme, sonuç biçimi, onay, kayıt, sağlayıcı sözleşmeleri ve seçili araçların ilgili kod yolları incelendi. Tüm Python dosyaları için güvenlik veya davranış doğrulaması yapılmış değildir. Uygulama, setup.py ve araçlar çalıştırılmadı; bağımlılık kurulmadı, gerçek hesap ve donanım kullanılmadı.

### Lisans kararı

Mark-LVI-main/LICENSE, FatihMakes adına CC BY-NC 4.0 bildiriyor. Ticari olmayan kullanım ve atıf koşulları var; değiştirmek bu koşulları kendiliğinden kaldırmaz. Resmî özet: https://creativecommons.org/licenses/by-nc/4.0/ .

Bu nedenle aşağıdaki teknik aktarım adayları otomatik kopyalama izni olarak okunmamalı. Varsayılan başlangıç: TaskVex sözleşmelerini kendi gereksinimlerimize göre yaz; dış kod aktarma. Aktarım seçilirse kaynak dosya, sürüm/hash, değişiklikler, telif ve lisans kaydı tut. Ticari hedef varsa ilgili kod için uygun izin veya başka lisanslı alternatif değerlendirilmeden taşıma. Bu not bütün projenin lisans uyumluluğu hakkında hukukî güvence değildir.

## 3. Mark LVI'dan ne alınabilir?

### Core ve sağlayıcılar

| Kaynak | Gözlenen yararlı nokta | TaskVex kararı |
|---|---|---|
| core/action_loader.py, core/plugin_loader.py | Araç adı/şema/handler bildirimi, çakışma kontrolü, yükleme hatalarının ayrılması | Tasarımını kullan; iki paralel dispatcher yerine tek ToolRegistry kur. İlk sürüm açık kayıt listesi kullansın. |
| plugins/_template.py | Tek dosyada açıklama, parametre ve çalıştırma girişi | Bizim ToolSpec + ToolContext + ToolResult sözleşmesine göre yeni şablon yaz; player/speak nesneleri verme. |
| core/outcome.py | done, unverified, failed, ask, started ayrımı | Fikri kullan; makine sözleşmesini doğal dil/key=value yerine tipli sonuç olarak tanımla. |
| core/appidentity.py, actions/open_app.py | Uygulama adı eşleme, çalışan süreç/pencere gözlemi, açılış sonrası kontrol | Windows adaptörü için güçlü uyarlama adayı; ilk sürümde sınırlı uygulama kataloğu ve tek hedef kullan. |
| core/confirm.py | Modelin kendi kendine onay verememesi | İlkeyi kullan; tek global bekleyen callable yerine kullanıcıya, göreve, parametrelere ve süreye bağlı approval kaydı tasarla. |
| core/undo.py | Bazı dosya/ayar işlemleri için telafi kaydı | Dosya değiştirme aşamasında ele al. Her işlemi geri alınabilir sayma; telafi öncesi mevcut veriyi doğrula. |
| core/audio_devices.py, core/echo.py, core/hotkey.py, core/wake_word.py | Cihaz seçimi, yankı ve dinleme deneyimi | Ses aşamasında ayrı incele/ölç; şimdi core bağımlılığı yapma. |
| core/gemini.py | Model çağrılarında süre, kota ve sağlayıcı erişimini merkezileştirme | ModelGateway tasarımı için referans. Eski model listesini taşımadan güncel SDK/modeli entegrasyonda doğrula. |
| providers/base.py, providers/registry.py | LLM/STT/TTS/Engine yetenekleri ve isteğe bağlı yükleme | İlk gün çoklu sağlayıcı sistemi kurma. Gemini ve yardımcı metin istemcisi için gereken küçük sınırı kur; ileride genişlet. |
| providers/schema.py | Araç şemasını sağlayıcı biçimine çevirme, araç bütçesi | İç şemayı sağlayıcıdan bağımsız tut; çeviriciyi model adaptörüne koy. Görünür araç listesi izin yerine geçmez. |
| providers/llm_openai.py, engine_pipeline.py | Uyumlu endpoint ve STT→LLM→TTS yolu | Yerel model aşamasına ertele; Gemini Live ile aynı özelliklere sahip varsayma. |
| memory/memory_manager.py | Kullanıcı bilgisi ve geçmiş arama fikri | İhtiyaç olduğunda ayrı kullanıcı hafızası tasarla. Notes, görev günlüğü ve L1 locator hafızasıyla birleştirme. |
| memory/config_manager.py | Ayar okuma/yazma ihtiyacının listesi | Yazma kodunu taşıma; TaskVex'e ait atomik kayıt ve ayrı credential deposu kur. |
| main.py, ui.py | Live, ses ve araçların birlikte çalışma örneği | Taşıma. PyQt UI ve geniş orkestrasyonu bizim main.py içine getirme. |
| dashboard/server.py | Uzak kontrol örneği | İlk sürüme alma; native masaüstü köprüsü için sunucu/uzak erişim gerekmiyor. |
| core/installer.py, setup.py | Kurulum otomasyonu | Çalıştırma/taşıma. Bağımlılıklar geliştirme ortamında açık komutla kurulmalı; core açılışında pip çalışmamalı. |
| core/avatar*.py, core/viseme.py, ui.py | Avatar ve Qt görsel davranışı | Mevcut UI ile ilgisiz; dışarıda bırak. |

### actions klasöründeki 21 dosyanın yerleşimi

| Dosya | TaskVex'teki yer / karar |
|---|---|
| open_app.py | L0 apps.open için davranış referansı; süreç/pencere kanıtı ve hedef kataloğuyla yeniden tasarla. |
| system_monitor.py | L0 system.status + isteğe bağlı telemetri servisi; UI nesnesinden bağımsız ölçüm adaptörü. Kaynak kodun get_system_status fonksiyonu eksik GPU/sıcaklığı None'a çeviriyor. |
| computer_settings.py | Windows ayar araçları; her eylem için ayrı kapsam/policy. Güç, ağ ve benzeri etkileri ilk dilime alma. |
| file_controller.py | Dosya araçları; izinli kök, symlink/junction, üzerine yazma ve telafi denetimleri eklenmeden taşıma. |
| file_processor.py | Belge okuma/analiz servisi; dosya okuma ile model analizini ayır. |
| browser_control.py | Tarayıcı adaptörü ve ileride L2 için referans. Gerçek kullanıcı profilini açma/kilitleme davranışını kopyalama; sahipliği belirli test profiliyle başla. |
| computer_control.py | Genel GUI uygulama ilkelleri; doğrudan güvenilir uygulama API'si gibi L0'a sokma. Resolver/policy/verification hattının arkasında kullan. |
| screen_processor.py | Ekran/kamera yakalama ve vision girdisi; tek başına doğrulanmış GUI işlemi veya L4 resolver değildir. |
| send_message.py | PyAutoGUI/pano tabanlı mesajlaşma yolu. Telegram/Discord API entegrasyonu değildir; doğrudan L0 mesaj aracı olarak taşınmayacak. |
| weather_report.py | Google hava araması açıyor; widget'ın ihtiyacı olan sıcaklık/koşul verisini üretmiyor. TaskVex hava adaptörü ayrıca yazılmalı. |
| web_search.py | Arama sağlayıcısı/fallback referansı; model çağrısı, kota ve gösterim kodundan ayrıştırılmadan taşıma. |
| reminder.py | OS zamanlama referansı. Bizim rutin/scheduler sahipliğine paralel ikinci yürütücü oluşturma. |
| background_monitor.py | İsteğe bağlı izleme servisi; ilk core kapsamı dışında. |
| proactive.py | İsteğe bağlı davranış servisi; varsayılan açılış davranışına ekleme. |
| desktop.py | Windows masaüstü yeteneklerini eylem bazında ayır; geniş tek araç olarak taşıma. |
| game_updater.py | Gelecekte Steam/oyun pluginine aday; başarı kanıtı ve istemci/GUI yolları ayrıca incelenmeli. |
| video_player.py | Qt oynatıcı/UI bağımlı; mevcut HTML medya alanına doğrudan uymaz. Ertele. |
| youtube_video.py | YouTube işlemlerini sağlayıcı/medya adaptörüne ayır; ilk core dışında. |
| flight_finder.py | Arama/alan pluginine aday; ilk core dışında, işlem/satın alma yetkisi varsayılmaz. |
| code_helper.py | Kod üretimi ve çalıştırmayı ayır; model çıktısını doğrudan yerel yürütme yetkisi sayma. Ertele. |
| dev_agent.py | Genel kod ajanı; ilk kişisel asistan core'u için gerekmiyor. Ertele. |

Yerel plugins klasöründe yalnız __init__.py ve _template.py var. README'deki plugin desteği, bu klasörde hazır uygulama pluginleri bulunduğu anlamına gelmiyor. actions modülleriyle plugin şablonu farklı.

## 4. Aynen taşımayacağımız somut davranışlar

- plugin_loader.py:117–128: boş/dönüşsüz handler sonucu "Done." oluyor. TaskVex'te boş veya sözleşme dışı sonuç doğrulanmış başarıya çevrilmez.
- plugin_loader.py:288 ve devamı: modül exec_module ile yükleniyor, ardından bildirimi doğrulanıyor. İçe aktarma sırasında kod zaten çalışmış olabilir. İlk sürüm yalnız uygulamayla gelen, açıkça kaydedilmiş güvenilir pluginleri yükler. Bu bir sandbox değildir.
- _template.py: handler'a player/UI nesnesi ve kullanıcıya okunacak metin veriliyor. Bizim plugin UI'a veya model oturumuna doğrudan erişmez; veri ve olay döndürür.
- confirm.py: tek global _pending kaydı var; yeni istek eskisini değiştirebilir. İleride birden fazla görev/kanal için aynı modeli kullanma. Onaydan sonra güncel hedef ve ön koşullar yeniden kontrol edilmeli.
- memory/config_manager.py ayarları doğrudan JSON'a yazıyor; API anahtarlarını da aynı veri alanında tutuyor. memory_manager.py:118–127 write_text kullanıyor. Bizim kalıcılıkta atomik değiştirme, sürüm, kurtarma ve görünür yazma hatası gerekli.
- main.py başında subprocess.Popen global olarak değiştiriliyor. Bizim Windows adaptörü yalnız kendi alt süreçlerini uygun bayraklarla açar; global monkey patch yapılmaz.
- main.py:_execute_tool, model SDK tipi ve self.ui ile iç içe. TaskVex yürütücüsü model SDK'sından ve HTML/PyQt'den bağımsız olmalı.

Bunlar ilgili koddan saptanan uyumsuzluklardır; tüm uygulamanın güvensiz veya bozuk olduğu iddiası değildir.

## 5. Core sözleşmesi

### Araçlar ve pluginler

- ToolSpec: name, description, input_schema, handler; gerektiğinde required_capabilities ve exclusive_resources. Yerleşik araçlar ve plugin araçları aynı registry'ye kaydolur.
- Plugin: id, version, sunduğu ToolSpec kayıtları; ilk sürüm uygulamayla gelen açık kayıt. Dinamik dosya taraması, hot reload ve plugin mağazası yok.
- Araç adı uygulamaya/işleme özgü olmalı: notes.add, system.status, apps.open, ileride spotify.play. Aynı ada ikinci kayıt sessizce üzerine yazamaz.
- İç şema standart JSON Schema biçiminde tutulur; Gemini'nin OBJECT/STRING biçimi adaptör sınırında üretilir. UI schema.js dosyası Python yürütme doğrulamasının yerine geçmez.
- ToolContext yalnız görev/istek/kullanıcı kimliği, iptal sinyali, son süre ve gerekli dar servisleri taşır. Başlangıçta kullanılmayan genel context servis ağı yazılmaz.
- Plugin gerektirdiği yetkiyi bildirir; yetkiyi kullanıcı/core policy verir. Bir plugin kendisine izin veremez. Yerel Python kodu süreç içinde çalışıyorsa OS yetkisine erişebilir; ToolContext bunu güvenlik sandbox'ına dönüştürmez.

### Görev ve sonuç

- İstek: request_id, source, principal, tool, arguments. Kullanıcı kimliği modelin gönderdiği metinden değil giriş adaptöründen gelir.
- Görev: queued → running → terminal; gerekirse awaiting_approval. Terminal durumlar succeeded, failed, cancelled, unknown. Cancel_requested bir talep; terminal başarı değildir.
- Sonuç: task_id, status, data, error, verification/evidence. Kullanıcıya söylenecek cümle, makine sonucunun tek otoritesi değildir.
- Parametreler başvuruda doğrulanır; yürütme anında plugin etkinliği, policy ve değişebilen hedef/ön koşullar tekrar kontrol edilir.
- Masaüstü girişine ihtiyaç duyan işler aynı desktop kaynağında sıralanır. İlk sürümde basit tek worker yeterli; dağıtık kuyruk veya genel DAG yok.
- İş başlamadan iptal yan etki üretmez. Çalışan iş işbirlikçi iptal noktaları kullanır. Bir Python thread'ine timeout uygulamak thread'i durdurmaz. Fiziksel işlem sürüyorsa desktop kilidi serbest bırakılıp ikinci işlem başlatılmaz; durum izlenir veya kaynak kullanılamaz tutulur.
- Aynı request_id + aynı içerik yeniden geldiğinde mevcut görev/sonuç döner; farklı içerikle aynı kimlik reddedilir. İlk sürümde oturum içi tekrar önleme açık sınırdır. Çökme sonrası global exactly-once vaat edilmez; dış yan etkilerde kayıt/sağlayıcı anahtarı ve sorgulama gerekir.
- Belirsiz sonuç otomatik tekrar edilmez. Method unsupported/işlem uygulanmadı kanıtı gibi uygun durumda GUI alternatifine geçilebilir. Yetki reddi alternatif GUI ile aşılmaz.

### Plugin, skill ve L1–L4

Plugin kurulu olması her işlemi desteklediğini göstermez. Seçim işlem/yetenek bazındadır. Gerçekte klavye/koordinat kullanan plugin de desktop kilidi ve GUI doğrulaması ister; isminin plugin olması doğrudan API garantisi değildir.

Skill görev tarifi/planıdır; plugin aracı veya GUI adımı çağırabilir. L1 öğrenilen GUI hedef bilgisi, L2 DOM, L3 UIA ve L4 vision çözümleme hattıdır. Mark'ın generic click/screenshot fonksiyonları bu dört katmanın hazır uygulaması değildir.

## 6. UI entegrasyonunda önce çözülecek konu

Mevcut notes.js kullanıcı eyleminde önce yerel koleksiyonu değiştiriyor, saveStoreCb({emitSave:true}) ile tam save üretiyor, sonra note_add/note_done/note_del yayımlıyor. Kimlik yerine metin kullanan silme ve {t,d} kayıtları mevcut. İki backend handler'ı ayrı ayrı yazarsa çift not veya çakışan otorite oluşabilir.

Önerilen sözleşme geçişi:

1. Önce mevcut olayların hangi alanı yazdığını bir tabloda belirle; tek bir alan için hem snapshot save hem komut handler'ı mutasyon sahibi olmasın.
2. Native not modunda backend otorite olacak: notes CRUD açık request_id ve note_id taşıyacak; tam save not koleksiyonunu tekrar yazmayacak. Backend kesin sonucu/snapshot'ı gönderir. Bekleyen/hatalı kayıt kullanıcıya görünür; giriş başarısızlıkta korunur.
3. Tarayıcıda backend olmadan çalışan mevcut yerel not modu korunur. Native/yerel mod açık bir başlangıç anlaşmasıyla seçilir; bir taşıma hatası sessizce diğer yazma moduna düşürülmez.
4. UI api.js, app.js, notes.js, schema.js ve settings.js içindeki ilgili yollar birlikte güncellenir; mevcut payload'lar sessizce farklı yorumlanmaz. Yeni sözleşme sürümlenir ve UI_BACKEND_CONTRACT.md güncellenir.
5. İlk native açılışta mevcut tarayıcı notları otomatik silinmez. Backend veri dosyası yokluğu ile geçerli boş koleksiyon ayrılır; yerel veriyi içe alma kullanıcıya açık bir aktarım olur. Mevcut JSON yedek içe aktarma yolu kullanılabilir.
6. ui_ready yalnız bridge hazır demektir; online(true) ancak gerçek model oturumu doğrulandığında gönderilir.
7. Rutin sahipliği backend'e geçtiği aşamada stopRoutineScheduler çağrılır; takvim de devralınırsa stopCalendarScheduler çağrılır. Bu sahiplik her sayfa yüklemesinde yeniden kurulur.

Bu protokol değişikliğinden önce native not yazmayı bağlamayacağız. İlk güvenli bridge denemesi ayarlar ve salt okunur system.status olabilir.

## 7. Önerilen küçük başlangıç ağacı

Mevcut v1/ui taşınmaz. Aşağıdaki dosyalar ilgili aşamada, kullanılacak içerikleriyle oluşturulur; peşinen boş iskelet açılmaz.

```text
TaskVex/
├─ AGENTS.md
├─ ARCHITECTURE.md
├─ CORE_START_PLAN.md
├─ Mark-LVI-main/                    # referans; import edilmez, dağıtıma alınmaz
└─ v1/
   ├─ app/
   │  ├─ __init__.py
   │  ├─ main.py                    # native pencere ve uygulama girişi
   │  ├─ bootstrap.py               # somut bileşenlerin kurulması
   │  ├─ config.py                  # TASKVEX_HOME, ortam ve sürüm
   │  ├─ core/
   │  │  ├─ contracts.py            # istek, araç, görev, sonuç
   │  │  └─ events.py               # yalnız ihtiyaç duyulan olay aktarımı
   │  ├─ tasks/manager.py           # sıra, durum, iptal ve kaynak sahipliği
   │  ├─ policy/engine.py           # ilk araçların açık izin/ret kuralları
   │  ├─ session/tool_registry.py   # tek kayıt ve parametre doğrulama noktası
   │  ├─ bridge/webview_bridge.py   # event(name,data), güvenli UI güncellemesi
   │  ├─ bridge/dispatcher.py      # UI olayını ilgili işleve yönlendir
   │  ├─ tools/local/notes.py       # notes.add/update/delete/list
   │  ├─ tools/local/telemetry.py   # system.status
   │  ├─ integrations/plugins.py  # ihtiyaç doğunca güvenilir plugin kayıt listesi
   │  ├─ integrations/apps.py      # ilk uygulama plugininin araçları
   │  ├─ platform/windows/applications.py
   │  ├─ services/notes.py          # UI/model ortak not iş mantığı
   │  └─ storage/json_store.py      # atomik ve sürümlü veri dosyası
   ├─ ui/                          # mevcut HTML/CSS/JS
   ├─ tests/                       # aşamalara göre az sayıda anlamlı test
   └─ pyproject.toml               # proje, bağımlılık ve test yapılandırması
```

Bu bir dosya sayısı hedefi değildir. İlk ayar diliminde notes/platform/plugins dosyaları henüz gerekmiyorsa oluşturulmaz. Basit yardımcılar sorumluluğun sahibi dosyada kalır. main.py iş mantığını toplamaz.

Kalıcı çalışma verisi için öneri: TASKVEX_HOME varsa o yol; Windows varsayılanı %LOCALAPPDATA%/TaskVex. Testler geçici ayrı kök kullanır. Kaynak dizinine veya referans reponun config/ alanına kullanıcı verisi yazılmaz. Mevcut JARVIS_HOME adları otomatik veri taşıma talimatı sayılmaz.

## 8. Geliştirme aşamaları ve kabul koşulları

### Aşama 0 — Baz çizgi ve sözleşme kararı

- Mevcut UI dosyalarının hash/yedek referansını ve mevcut test sonuçlarını al. Önceki başarı raporunu bugün çalıştırılmış test sayma.
- UI olaylarını ayar, koleksiyon komutu, model oturumu, donanım ve görünüm olarak sorumluluklarına ayır; hangi alanı kimin yazdığını belgeye işle.
- Mark aktarım matrisini ve lisans tercihini kaydet. Başlangıç kendi core kodumuzla ilerleyebilir; bu adım diğer geliştirmeyi durdurmaz.
- Kabul: ilk dilimin girdisi, çıktısı, persist sahibi ve desteklenmeyen olay yanıtı belli. Mark dizininden import yok.

### Aşama 1 — Modelden bağımsız core

Tamamlandı: [kabul sonuçları ve gerçek araç sözleşmeleri](docs/STAGE1_CORE.md).

- contracts, tek registry, küçük TaskManager, ilk policy ve atomik JSON store'u yaz.
- Önce tests içinden çağrılan notes.add/list ve salt okunur system.status ile hattı kur; UI henüz bunlara bağlı değil.
- Durum ve olaylar için kalıcı framework kurma; dar callback/abonelik yeterli. Olay abonesi hatası yürütülmüş işlemi tekrar çalıştırmasın.
- Test: geçersiz parametre handler'a ulaşmaz; isim çakışması reddedilir; aynı istek iki mutasyon yapmaz; kuyrukta iptal yürütülmez; yazma hatası başarı değildir; bozuk JSON aslı korunarak kurtarılır.
- Kabul: model, mikrofon ve UI olmadan gerçek geçici dosyada araç çağrısı ve sonuç doğrulanır.

### Aşama 2 — Hazır UI'ı native uygulama olarak aç

- PyWebView ile mevcut index.html'i aç; mevcut API beklentisine uygun event(name,data) sun. Yerel ES modülleri için açılış yöntemini gerçek native ortamda doğrula.
- UI ana thread'ini bloklamadan core'a ilet. UI güncellemeleri izinli metot isimleri ve JSON serileştirmesiyle yapılır; ham veri JS kaynak metnine birleştirilmez.
- İlk olarak ayar snapshot'ı ve salt okunur durum bağla. Model bağlı değilken online gösterme. Henüz desteklenmeyen olaya açık not_implemented sonucu ver.
- Test: erken/geç ui_ready, initApp/no-echo, ayar kaydet-kapat-aç, bozuk ayar, yazma hatası, tekrar açılış, handler hatası ve native pencere kapanışı.
- Kabul: görünüm korunur, native bridge gerçekten çalışır ve settings verisi yeniden açılışta gelir. Mock tarayıcı testi native test yerine sayılmaz.

### Aşama 3 — Notları tek otoriteyle backend'e bağla

Planlı otomatik ve görünür kabul tamamlandı: [güncel sözleşme ve test](docs/STAGE3_NOTES.md).

- Bölüm 6'daki sürümlü not komutlarını ve sabit kimlikleri uygula. Backend kesin sonucuna göre UI güncellensin; generic save aynı notu tekrar yazmasın.
- Eski {t,d} yedeklerine kimlik üretme geçişi ve kullanıcı kontrollü yerel veri aktarımını ekle. Aynı metinli iki not ayrı kimliklerle çalışabilsin.
- Test: ekle/tamamla/sil, restart, gecikmiş yanıt, çift tıklama, yinelenen istek, eski yedek, geçersiz kayıt, disk hatası ve tarayıcı-only regresyonu.
- Kabul: UI → bridge → TaskManager → policy → notes aracı → kayıt → kesin UI sonucu akışı bir kez çalışır; model olmadan kullanılabilir.

### Aşama 4 — İlk gerçek uygulama plugini

Adım adım plan: [STAGE4_APPS.md](docs/STAGE4_APPS.md). Katalog/kimlik, çalışma
durumu sorgusu ve doğrulanmış açma hazır. Hata/tekrar/iptal testleri de geçti;
gerçek kapat/yeniden aç kontrolü kullanıcı tarafından tamamlandı ve raporları doğrulandı.

- Önerilen ilk hedef: apps.open ile katalogdaki Not Defteri'ni aç ve apps.status ile durumunu sorgula. Yeni özel plugin UI paneli gerekmez; kabul senaryosu önce test/komut çağrısıyla yapılabilir.
- Aynı ToolRegistry/TaskManager/policy hattını kullan. UI araması veya rastgele koordinat fallback'i ekleme; desteklenen Windows başlatma yöntemi ve hedef kanıtı seç.
- Süreç başladı, pencere bulundu ve hedef belge hazır gibi kanıtlar farklıdır. Aracın garanti ettiği seviyeyi sonuçta belirt; sadece Popen döndü diye done verme.
- Test: desteklenmeyen uygulama, zaten açık uygulama, başlatma başarısızlığı, geciken açılış, timeout/belirsiz sonuç ve iptal. Gerçek Windows testi ayrıca yapılır.
- Kabul: yerleşik notes aracıyla uygulama plugini aynı yürütme sözleşmesine uyar; plugin core/UI nesnesini ele geçirmez.

### Aşama 5 — Gemini metin/Live ve ses

- Önce metin→tool call→aynı TaskManager→tool result turunu bağla. Model ayrı bir yürütücü olmaz. Bilinmeyen araç ve schema dışı parametreler reddedilir.
- İlk dar model araçlarından sonra iptal hattı tamamlanır; ardından notes.update/delete modele ayrı dilimde açılır. Aşama 3'teki CRUD yeniden yazılmaz; gerçek kayıt ID'si, belirsiz hedefi açıklatma ve sonuç/UI doğrulaması korunur.
- Sonra tek Live oturumu sahibi, mikrofon/hoparlör yaşam döngüsü, sınırlı kuyruklar ve yeniden bağlantı ekle. Live ilk sağlayıcı olabilir; metin turu ayrı ikinci ürün özelliği olmak zorunda değil.
- Kimlikler model→core→sağlayıcı dönüşünde korunur. Yeniden bağlantıda önceki yan etkili araç otomatik yeniden yürütülmez.
- Test: hatalı tool call, kota/ağ hatası, oturum kapatma, stop_task'ın gerçek tamamlanması ve bağlantı koparken araç sonucu. Fiziksel ses testini mock'tan ayrı raporla.
- Kabul: ses ve UI aynı gerçek aracı çağırır; online yalnız doğrulanmış oturumu temsil eder.

### Aşama 6 — İşlem bazında daha fazla L0 ve entegrasyon

- Sıra: telemetri/sayaç → uygulama/medya → dosya okuma → kontrollü dosya değiştirme → hava/arama → Google → Telegram/Discord.
- Her entegrasyonda önce tek işlem; örneğin takvim listeleme. Hesap/yetki yenileme, hata ve doğrulama görülmeden toplu araç ekleme.
- Sırlar için OS credential adaptörünü ilk gerçek secret gerektiğinde ekle; UI/localStorage/yedek sır deposu değildir.
- Mesaj gönderme açık kullanıcı/kanal/hedef/kapsam ve sonuç kanıtı taşır. Genel GUI send_message.py bu aşamanın API yerine geçen altyapısı değildir.
- Kabul: dış servis kesilince yerel notlar çalışır; belirsiz gönderim ikinci kez yapılmaz; bir plugin arızası core'u kapatmaz.

### Aşama 7 — GUI resolver ve skill yürütme

- L3 UIA ile tek uygulama senaryosu kur; doğrulanan hedefleri L1'e öğren. Sonra tarayıcı L2 DOM ve son çare L4 vision ekle.
- Snapshot/pencere/monitör/DPI kanıtını hedefe bağla. Çalıştırmadan önce hedefi yeniden doğrula; eski koordinatı körlemesine kullanma.
- Skill adımlarını aynı TaskManager'a ver. GUI ve doğrudan plugin adımları aynı görevde bulunabilir; alt adımların izin ve kaynak kuralları korunur.
- Kabul: pluginin desteklemediği işlem GUI hattına gidebilir; belirsiz yan etki veya policy reddi otomatik fallback üretmez.

### Aşama 8 — Rutinler, arka plan servisleri ve paketleme

- Tek scheduler sahibi kur; UI zamanlayıcı sahipliğini açıkça devral. Tetikleme kimliğiyle tekrar önle; bildirim teslimatı ile iş tamamlanmasını ayır.
- Günlük döndürme/maskeleme, veri şeması geçişleri, normal kapanış, çökme kurtarma ve paketlenmiş native açılış doğrulansın.
- Uygulamayı açmak kendi kendine proaktif istek, gerçek mesaj, yeni izleme veya bağımlılık kurulumu başlatmasın; etkin özellikler kullanıcı ayarına bağlı olsun.
- Kabul: paketleme referans repoyu ve test verilerini içermez; native testler ile gerçek hesap/donanım sınırları açıkça raporlanır.

## 9. İlk çalışma paketimiz

İlk uygulama turunun kapsamı Aşama 0 + Aşama 1 + Aşama 2'deki ayar/read-only dilimidir. Ardından Aşama 3 not sözleşmesi; ardından ilk uygulama plugini gelir. İlk turda Gemini, ses, Google, bot, GUI otomasyonu veya plugin mağazası yazılmaz.

Gerekli bağımlılıklar aşamayla eklenir. Öneri: proje ortamı ve test aracı; native aşamada pywebview; parametre doğrulamasında seçilecek tek şema doğrulayıcı; telemetri aşamasında psutil. Mark requirements.txt topluca kurulmaz. Yeni SDK sürümleri gerçek uygulama turunda doğrulanıp tek bağımlılık kaynağında sabitlenir; burada doğrulanmamış sürüm numarası önerilmiyor.

İlk tur tamam sayılması için: Python core testleri geçer; gerçek PyWebView penceresi mevcut UI'ı açar; bir ayar kalıcıdır; salt okunur araç sonucu görülür; unsupported olay açık hata verir; kapanışta worker/subscription bırakılmaz; mock başarıyla gerçek entegrasyon karıştırılmaz.

## 10. Her aşamayı bitirme kuralı

Bir çalışan akış + ilgili hata/iptal senaryoları + gerekli sözleşme belgesi. Değişen kritik yola anlamlı test ekle; sırf test sayısı veya satır sayısı hedefleme. Yeni bir neden yokken aynı kapsamı sınırsız denetim döngüsüne sokma.

Bu tur yalnız plan ve kaynak incelemesidir. TaskVex üretim koduna veya Mark kaynaklarına değişiklik yapılmadı; native/hesap/donanım test sonucu iddia edilmiyor.


### 22 Ekim — Not kullanıcı kabulü ve oluşturulma zamanı

REST/Live not CRUD, aynı metinli hedefte açıklama/ID ile seçim ve Stop sonrası
yeni mesaj kullanıcı tarafından geçti diye bildirildi. Bu kabul önceki
notes.update/delete dilimini kapatır; GoAway/resumption hesabı ve fiziksel ses
ayrıca açık kalır. Tek prompt/tek adım kuralıyla yeni notlara UTC created_at
eklendi; eski tarihsiz kayda yapay tarih/ID atanmıyor. UI cache, yedek ve açık
restore tarih bilgisini korur. Sonraki ayrı dilimde “son not” ve tek kısmi metin eşleşmesi uygulandı;
707 test ve native paketle doğrulandı. Yeni seçim için kısa kullanıcı kabulünden
sonra planlı Live ses adımı gelir. Ayrıntılar STAGE5_MODEL.md’dedir.


### 22 Ekim — Live PCM çıkışı ve API anahtarı kalıcılığı

Not hedefi seçimi kullanıcı tarafından tamamen çalışıyor diye kabul edildi.
Tek sonraki dilimde yazılı Live yanıta PCM çıkışı bağlandı. Kuyruklu Web Audio,
Mute ve Stop; aynı request_id, gerçek metin/araç sonucu, unknown ve Live kaynak
sahipliğiyle birlikte çalışır. Yeni bağımlılık yoktur. 727 pytest, JS ses/tarih
kontrolleri, seçili Pyright 0 hata ve native 10/10 geçti. Fiziksel ses kabulü
kullanıcıdan bekleniyor. Önceden kaydedilmiş API anahtarı Windows kimlik
deposunda mevcut olarak doğrulandı; kayıt gösterilmedi/değiştirilmedi. Sonraki
tek adım kısa ses kabulünden sonra mikrofon/cihaz/VAD'dir. Aşama 5 kapanış
listesindeki son bütünleşik kullanım, hedefli UI bakım/debloat ve belge/yeniden
başlatma sınırlarının incelemesi henüz bitmedi; Aşama 6'ya geçilmedi.
