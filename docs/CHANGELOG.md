# Changelog

Bu dosya TaskVex değişikliklerinin tek güncel kaydıdır. Mimari kararların mevcut
hali ARCHITECTURE.md, yapılacak işler PLAN.md içindedir. Henüz sürüm yayımlanmadı.

## Unreleased

### Ortak yerel telemetri — CPU/RAM/disk/pil/aktif uygulama

- Tek Telemetry örneği model ve UI için gerçek Win32 ölçümlerini sağlar.
  UI mevcut tick üzerinden snapshot okur; poll görev günlüğünü büyütmez.
- İlk CPU örneği/bozuk sayaç/kayıp ölçüm —; gerçek sıfır korunur.
  Aktif uygulama yalnız exe adıyla gösterilir; kullanıcı belge başlığı okunmaz.
- Bağlantı kesilince yerel ölçümler ve oturum token toplamı silinmez.
  Yeni bağımlılık/servis/thread yoktur. GPU/sıcaklık/ağ/media sonraki dilimlerdir.
- Kullanıcı token testini kabul etti ve commit'i erteledi; bu tur commit/push yok.
- 1109 pytest, 96 hedefli test, 12 browser, 9 JS ve Pyright 0. İlk native
  chat süre aşımından sonra izole tekrar 10/10 geçti; [kanıt](reports/local-telemetry-checks.json).

### Gemini oturum token toplamı

- Python token ayrıştırma/toplama mevcut gemini.py içinde tekleştirildi.
  UI artık son yanıt yerine uygulama ömründeki toplamı gösterir.
- REST araç turları, Live üretimleri ve ayrı TTS yanıtları sayılır;
  ara Live snapshot'ları gelişigüzel toplanmaz. Stop ve Disconnect toplamı korur.
- Eksik kullanım kesin sıfır sayılmaz; bilinen toplam ≥/Incomplete gösterilir.
  Yeni API çağrısı/depo/bağımlılık yoktur; restart sayacı sıfırlar.
- Gerçek API/fatura doğrulaması yapılmadı; bu dilimin kullanıcı kabulü bekleniyor.
- 1101 pytest, 138 hedefli test, 11 browser, 9 JS, 10 native ve Pyright 0;
  [kanıt](reports/session-token-checks.json).

- GitHub README güncel hafıza onayı/otomatik kayıt, son token bildirimi ve
  1091 testlik doğrulamaya göre düzeltildi. Telemetri/hava/ağ eksikleri ve
  görev günlüğünde öneri/kaynak verisi kalabilmesi açıkça belirtildi.

### Son sağlayıcı token göstergesi

- Live/REST gerçek usage metadata mevcut sohbet raporuna ve UI'a bağlandı.
  Eksik bilgi eski değeri korumaz; sıfır geçerlidir. Limit/kota uydurulmaz.
- Ayrı API çağrısı/depo/bağımlılık eklenmedi. Gösterilen son bildirimdir;
  oturum toplamı, hesap kotası veya tüm araç/ses isteklerinin toplamı değildir.
- Kullanıcı bu küçük adım için doğrudan commit istedi; gerçek API kabulü yapılmadı.
- 1091 pytest, 96 hedefli test, 9 JS, 10 browser, 10 native ve Pyright 0;
  [kanıt](reports/token-counter-checks.json).

- Kullanıcı hafıza önerisinin düğme/konuşma kararını başarılı bildirdi;
  uygulama 6f52b4c commit'inde, push yok. PLAN'da güncel kabul durumu ve
  telemetri/ağ/token/media ile kalan UI bağlantılarının sırası netleştirildi.
  Bu planlama turunda yeni uygulama özelliği eklenmedi.

### Hafıza önerisine sohbet yanında veya konuşarak karar

- Save/Dismiss kişiselleştirmeden sohbetin altındaki dört kontrolün sağına,
  ayrı ve temaya bağlı gruba taşındı; otomatik modal/Review ara düğmesi kaldırıldı.
- Vex mevcut normal ses/metin yanıtında izin ister. Sonraki açık kullanıcı
  kararı aynı memory.decide aracına gider; UI/model iki ayrı kayıt yolu değildir.
- Model kendi oluşturduğu adayı aynı turda onaylayamaz. Sonraki turda taze
  pending ID gerekir; eski ID ve geç karar yeni adaya uygulanmaz.
- Karar sonrası gerçek backend profili yenilenir; ikinci save yoktur.
  Önceki 6.1.3 kullanıcı kabulü c5d086c commit'inde, push yapılmadı.
- 1081 pytest, 40 hedefli hafıza testi, 9 JS, 9 browser, 10 native ve Pyright 0;
  [kanıt](reports/memory-voice-review-checks.json). Gerçek API/mikrofon denenmedi;
  bu değişikliğin kullanıcı kabulü ve commit'i beklenir.


### Hafıza için sor/sorma tercihi ve doğrudan inceleme

- Personalization'a Ask before saving learned information checkbox'ı eklendi;
  eski kayıtta true. Öğrenme ve hafıza tercihleriyle aynı profilde saklanır.
- Onay gerekiyorsa pencere otomatik açılır; Review düğmesinin bulunmasına
  bağımlı değildir. Zaten açık paneli toggle ile kapatmaz.
- Checkbox false ise memory.propose aynı alan sahibinin append/readback yoluyla
  doğrudan kaydeder; UI backend'den yenilenir. Model bu tercihi değiştiremez.
- memory.write yetkisi, taze snapshot, replay/Stop ve belirsizlik kuralları
  korunur. Yeni alan snapshot kimliğine dahil edilir.
- 1074 pytest, 9 JS, 9 browser, 10 native ve Pyright 0; [kanıt](reports/memory-review-checks.json),
  [native](reports/memory-review-native.json). Canlı API/çıkarım doğruluğu denenmedi;
  kullanıcı kabulü ve commit beklenir.


### Hafıza önerisi kaynak reddi düzeltmesi

- Kullanıcı manuel testte memory.propose başarısızlığı bildirdi. Günlükten
  source_unavailable doğrulandı; 6.1.3 yeniden açıldı, kabul edilmiş sayılmaz.
- Kaynak cümlesini modele yeniden yazdırıp birebir eşleştirme kaldırıldı.
  ModelTools gerçek kullanıcı metni/ASR'yi kendisi bağlar; alıntı varyasyonu
  geçerli öneriyi düşürmez. Öneri hâlâ onaydan önce profil gerçeği değildir.
- Engine log araç başarısızlığında güvenli hata kodunu gösterir; özel veri
  loglanmaz. Kaynaksız sesli işlem, snapshot, replay ve onay korumaları sürer.
- 1068 pytest, 33 hedefli hafıza/öneri testi, 8 browser grubu, 10 native aşama,
  Pyright 0 ve live-status JS geçti. [Kanıt](reports/memory-source-checks.json),
  [native](reports/memory-source-native.json). Gerçek hesapla denenmedi;
  kullanıcı tekrar testi ve commit beklenir.


### Konuşmadan hafıza önerileri ve kullanıcı onayı (6.1.3)

- Personalization pLearn tercihi varsayılan kapalı; pMemory ile birlikte aynı
  konuşma modelinden memory.propose önerileri alınır. Kaynak bu turun gerçek
  metni/Live transkriptine bağlanır; model host kanıtı üretemez.
- Öneri profil hafızasına yazılmaz; günlük aday metnini içerebilir. Tek RAM
  adayı ve Save/Dismiss UI kararı aynı core
  hattındadır. Öğrenme açıkken model yeni bilgiyi append ile onaysız ekleyemez.
- Onay tek profil/aynı append-readback; eski öneri/izin/snapshot/restart ret,
  unknown kilidi ve ikinci save üretmeden UI güncellemesi. Taslak korunur.
- 6.1.2 kullanıcı tarafından kabul edildi, 50421c3 commit'inde; push yok.
- 1065 pytest, 15 hedefli öneri testi, 9 JS suite, 8 browser grubu, 10/10 native
  aşama ve Pyright 0; [kanıt](reports/memory-suggestions-checks.json),
  [native](reports/memory-suggestions-native.json). Gerçek/ücretli API ve modelin
  anlamsal çıkarım doğruluğu denenmedi; kullanıcı kabulü/commit bekliyor.


### Açık model hafıza işlemleri (6.1.2)

- memory.read/patch, REST ve Live'da mevcut registry/policy/TaskManager hattına
  eklendi; yalnız etkin pMemory ile, açık kaydet/düzelt/unut isteği için.
- Taze tur/snapshot ve tekil hedef denetimi; readback, tekrar/iptal/unknown
  kuralları. Aynı profil dosyası kullanılır, yeni hafıza DB'si yoktur.
- Native core/bridge aynı JsonStore kilidini paylaşır. Ortak ayar şeması
  bridge/settings.py'den storage/settings.py'ye taşındı; tüm çağıranlar güncel.
- UI hafızayı backend'den yeniler; eski form overwrite ve geç kayıt ack'i
  korunur. Çakışmada otomatik merge/retry yoktur; gerekirse uygulama yeniden açılır.
- 6.1.1 kullanıcı tarafından kabul edildi, e7f3ce4 commit'inde; push yok.
- 1050 pytest, 9 JS suite, 7 browser grubu, 10/10 native aşama ve Pyright 0.
  [Kanıt ve başarısız ara denemeler](reports/model-memory-checks.json),
  [native](reports/model-memory-native.json). Açık form taslağı korunur;
  gerçek hesap/ücretli API yok. Kullanıcı kabul etti; 50421c3 commit’inde.


### Elle yönetilen kullanıcı hafızası ve New Chat kaldırılması (6.1.1)

- New Chat düğmesi ve kullanılmayan UI handler/kontrol referansları kaldırıldı.
  Internal reset API'si korunur; geçici hafıza Stop/Disconnect'te devam eder.
- Personalization pMem editörü ve açık pMemory tercihi mevcut profil deposuna
  bağlandı. Eski metin onaysız gönderilmez. Ortak instruction opt-in bilgiyi
  yalnız veri olarak alır; model çıkarımı otomatik kaydedilmez.
- Etkin kişisel hafıza değişince sonraki turda eski Live/RAM bağlamı bırakılır;
  belirsiz kapanışta yeni tur başlamaz. Aktif yanıt/geçmiş mesaj/yedekler silinmez.
- Ses seçimi adımı devam onayıyla 2cebea8 commit'ine alındı; push yok.
- 6.1.2 model mutasyon araçları ve 6.1.3 çıkarım önerileri ayrı dilimlerdir;
  bu turda eklenmedi. Yeni bağımlılık/veri otoritesi yok.
- 1035 pytest, 9 JS suite, 6 browser grubu, Pyright 0 ve 10/10 native aşama
  geçti. Checkbox restore hatası düzeltildi; iki native eski varsayım daha
  kesin kontrolle güncellendi. Başarısız ara turlar [raporda](reports/personal-memory-checks.json),
  son native kabul [burada](reports/personal-memory-native.json). Gerçek hesap/
  ücretli API ve fiziksel ses yok; kullanıcı kabul etti, e7f3ce4 commit’inde.


### Live ses seçimi ve anahtar durum ibaresi (5.F8.2)

- Connection altında belgelenmiş 30 hazır Live sesi [LIVE] etiketiyle listelenir.
  Tek conn.voice tercihi kalıcı ayarlardan aynı Live setup speech_config'una
  taşınır; metin/mikrofon/timer yanıtı ortaktır. Ses değişimi eski resume token'ını
  kullanmaz, aktif turu kesmez. REST TTS değişmedi; özel/TTS-only ses eklenmedi.
- API key input'u kayıtlı/eksik/belirsiz durumu placeholder'da gösterir; gerçek
  anahtar veya son karakterleri göstermez. Anahtar varlığı API erişim onayı değildir.
- gemini-live-api-dev skill'i ve Google Live sağlayıcı sözleşmesi doğrulandı.
  Ses listesi belge kaynaklıdır; model keşfi API'den kalır. Yeni bağımlılık yok.
- Önceki ses seviyesi adımı kullanıcı kabulüyle 9d67a1d commit'ine kaydedildi;
  push yok. Kullanıcı devam/commit onayı verdi; ayrı fiziksel ses testi bildirmedi.
- 1025 genel pytest + 24 son hedefli test, 9 JS suite, 5 browser grubu,
  app Pyright 0 ve 10/10 native aşama geçti. [Özet](reports/live-voices-checks.json),
  [native](reports/live-voices-native.json). SDK testinin alan adı varsayımı ve
  bir tip belirsizliği düzeltildi; başarısız denemeler raporda korunur.
  Gerçek hesap/ücretli API ve fiziksel ses denenmedi.


### Vex yanıt ses seviyesi (5.F8.1)

- Settings Audio altında tema ve klavye uyumlu Vex reply volume barı eklendi.
  Tek PCM oynatıcısının kazancını anlık değiştirir; Live/REST/timer bildiriminde
  ortaktır. Mute aç/kapat seçili seviyeyi korur; SFX ve mikrofon değişmez.
- replyVolume 0–1 arası doğrulanır; varsayılan/reset 1, sıfır korunur.
  Aynı save/snapshot/import-export yoluyla yerel ve native tercihe kaydolur.
  Yeni sağlayıcı çağrısı/oynatıcı eklenmedi. Voice/kişiselleştirme 5.F8.2 bekliyor.
- Önceki günlük/kapasite adımı kullanıcı devam onayıyla 5c21156 commit'ine
  kaydedildi; push yapılmadı. Kullanıcı bu dilimin çalıştığını doğruladı; commit onaylı.
- 1024 pytest, 9 JS suite, 5 browser grubu, app Pyright 0 ve 10/10 native
  aşama geçti. [Özet](reports/reply-volume-checks.json),
  [native kanıt](reports/reply-volume-native.json). Gerçek hesap/ücretli API ve
  fiziksel hoparlör testi yapılmadı.


### Kalıcı görev günlüğü ve kapasite (5.F7.2/3)

- Aynı TaskManager, standart kütüphane SQLite günlüğünü kullanır; kabul, handler
  öncesi ve terminal kayıtlar FULL transaction ile yazılır. İkinci core OS
  kilidiyle reddedilir; yeni bağımlılık/yürütücü/model yolu eklenmedi.
- Restart tamamlanan işi yeniden çalıştırmaz. Queued iptal, başlamış yarım iş
  unknown olur. Kimlik/içerik çakışması reddedilir; disk hatası yeni etkileri
  durdurur. Doğrulanmış araç sonucu geç kayıt hatasıyla geri alınmış sayılmaz.
- Native core'da 256 toplam ömür sınırı kaldırıldı; RAM kayıtları ve aktif işler
  sınırlıdır. Terminal RAM kopyaları çıkarılsa da eski get/wait/cancel/replay
  diskten aynı kimliği/sonucu verir. Günlüksüz test yöneticisi eski güvenli sınırı korur.
- Günlük düz yerel veri içerir, eski not metnini tutabilir, otomatik silinmez.
  Unknown uzlaştırma ekranı ve dış servis exactly-once garantisi eklenmedi.
- Eski açılış testleri artık yalnız tasks dizininin oluşmasını bekler; yeni
  gözlem restart'ta yeni request_id kullanır. İlk test turundaki eski varsayım
  hataları ve test bağlantısı ResourceWarning'i düzeltildi. İlk genel turdaki
  tek Live/asyncio uyarısı odaklı ve son genel turda tekrarlanmadı; filtre gevşetilmedi.
- 1017 pytest, 17 hedefli günlük testi, Pyright 0 ve 10/10 native aşama geçti.
  Ayrıntılar [test kanıtı](reports/task-journal-checks.json) ve
  [native raporda](reports/task-journal-native.json). Gerçek hesap/ücretli API yok;
  kullanıcı devam/commit onayı verdi; ayrı fiziksel test bildirilmedi.


### README ve oturum kapanışı

- GitHub README, uygulanan özellikler/planlı kapsam/veri akışı/açık sınırlar ve
  test kanıtını ayıracak şekilde İngilizce yeniden yazıldı. Ölçülmemiş hız/RAM,
  sınırsız otonomi veya üretime hazır güvenlik iddiası yok.
- 5.F7.2 kalıcı günlük ve 5.F7.3 güvenli kapasite/retention işleri kabul koşullarıyla
  PLAN.md'ye kaydedildi. Ses tercihleri ve ayrı yanıt seviyesi 5.F8'de bekliyor.
- Kullanıcı 5.F7.1 için devam, commit ve GitHub push onayı verdi; bu, ayrı bir
  fiziksel test sonucunun bildirildiği anlamına gelmez.


### Tek-instance güvenliği (5.F7.1)

- Aynı veri kökü için OS dosya kilidi worker/pencere açılmadan alınır; ikinci
  native instance açık hata ile reddedilir. Başka veri profili engellenmez.
- Kapanış/exception/crash kilidi bırakır; restart yeni süreci ancak bırakıldıktan
  sonra başlatır. PID/stale dosya silme, yeni bağımlılık veya ikinci state sahibi yok.
- Kullanıcının docs altına taşıdığı ana belgeler korundu; aktif linkler ve AGENTS
  yeni belge konumlarına uyarlandı. Tarihsel arşiv değiştirilmedi.
- 1000 pytest, hedefli Pyright 0 ve 10/10 sentetik native aşama geçti;
  gerçek alt süreç/crash ve native giriş/restart testleri de dahil.
  Sonuç: reports/instance-checks.json. Gerçek hesap/ücretli API kullanılmadı.
- 256 kayıt ve kalıcı replay günlüğü bu dilimde değişmedi. 5.F7.2/3 açık.


### Bakım ve belge düzeni

- 133 eski belge/kanıt dosyası özgün göreli yolları ve SHA256 manifestiyle
  docs/eski altına taşındı. Arşiv güncel yönerge değildir.
- Arşiv byte'ları .gitattributes ile Git satır sonu dönüşümünden korunur;
  manifest başka sistemde checkout yapıldığında da geçerlidir.
- ARCHITECTURE.md ve PLAN.md yeniden yazıldı; çalışan komutlar ve köprü sözleşmesi
  docs içinde tekilleştirildi. README'lerdeki çelişkili ilerleme günlükleri kaldırıldı.
- AGENTS.md yeni belge sahipliğini ve her değişiklikte bu kaydın bakımını zorunlu kılar.
- Kullanılmayan MediaRecorder/decode yolu ve yalnız onu sınayan test kaldırıldı;
  gerçek AudioWorklet akışı ve onun regresyonları korundu.
- Backend yürütücüsü olmayan UI rutin/takvim tarayıcıları ve skill/rutin sahte
  başlangıç bildirimleri kaldırıldı. Yerel tanımlar ve eski profil metinleri korundu;
  bağlı olmayan kontroller planlı olarak işaretlendi/devre dışı bırakıldı.
- Sohbet/mikrofon/uyku yaşam döngüsü assistant_session.js'e, görsel kabuk shell.js'e,
  cihazlar devices.js'e ve layout layout.js'e ayrıldı. preferences.js tek tercih
  nesnesidir; yeni framework, bağımlılık veya ikinci durum sahibi eklenmedi.
- Native kabul senaryoları runner'dan native_scenarios.py'ye taşındı.
- REST/Live araç katalogları ortak sabitlere alındı; eski politika testi tip
  uyarıları testin kasıtlı geçersiz girdileri açıkça belirtilerek düzeltildi.
- Denetim bulguları, özelleştirme boşlukları ve gerçek test kapsamı docs/AUDIT.md'dedir.

Doğrulama: 996 pytest, 9 JS suite, 4 browser grubu, 10 native aşama; hedefli
Pyright 0 hata/uyarı, pip check temiz. Runtime Python+JS net 706 satır azaldı.
İlk konum/link testi hataları ve çözümü cleanup-checks.json içinde açıkça kayıtlıdır.

Bakım kullanıcı tarafından kabul edildi, ea8aa15 commit’inde. Gerçek hesap/ücretli
API testi yapılmadı; otomatik kanıtlar docs/reports altında tutulur.

### Önceki kabul edilen temel

- `526bfed`: sayaç listesinde yalnız UI üzerinden silme; tema aksanlarını reactor
  durumundan ayırma. Bu adım kullanıcı tarafından kabul edildi.
- Önceki ayrıntılı değişiklik/kabul geçmişi Git ve docs/eski altında korunur;
  eski günlükler yeniden mimariye kopyalanmaz.
