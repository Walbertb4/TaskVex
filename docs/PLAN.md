# TaskVex — Güncel plan

## Şimdi: 6.1.1 — elle yönetilen kalıcı kullanıcı hafızası

Önceki 5.R8.6 kullanıcı kabulü başarılı, 526bfed commit’inde.
5.F6 bakımı kullanıcı tarafından kabul edildi; ea8aa15 commit’inde.
5.F7.1 tek-instance dilimi uygulandı ve otomatik doğrulandı. Kullanıcı devam ve
GitHub’a push onayı verdi; 5c338e8 ile yayımlandı. Ayrı fiziksel test sonucu bildirilmedi.
5.F7.2/3 uygulandı: 1017 pytest, 17 hedefli günlük testi, Pyright 0 ve 10 native
aşama geçti. Kullanıcı devam/commit onayı verdi; 5c21156 commit'inde, push yok.
5.F8.1 yalnız yanıt ses seviyesini mevcut tercihlere ve oynatıcıya bağlar. Ses
karakteri 5.F8.2'de bağlanıyor; diğer profil alanları 5.F8.3 olarak ayrı kapsamda.

- [x] İlk envanter ve onaylanan önceki adımın commit’i.
- [x] Tarihsel belgeleri docs/eski altına özgün yollarıyla taşı.
- [x] Ölü yolları kaldır; kullanılan/yakında planlı UI verilerini koru.
- [x] Büyüyen UI modüllerini sorumluluk sınırlarına göre ayır.
- [x] Kaynak/test/config/belge envanteri, mimari ve sabit ayar incelemesi: docs/AUDIT.md.
- [x] Güncel mimari/plan/changelog/sözleşme/README’ler; arşiv hash kaydı.
- [x] 996 pytest, 9 JS suite, 4 browser grubu, 10 native aşama ve hedefli Pyright 0.
- [x] Arşiv hash, güncel belge linkleri ve açık sınır raporu: docs/AUDIT.md.
- [x] Bakım kullanıcı kabulü → ea8aa15 commit. Aşama 5 kapanışı aşağıdaki açık işleri bekler.

Debloat güvenlik/doğrulama/Stop korumalarını kaldırmaz. REST ve bağımsız tarayıcı
UI modu korunur. Bekleyen skill/rutin tanımları silinmez. Gelecekteki özellikler
sanki bugün çalışıyormuş gibi gösterilmez.

## Yol haritası

| Aşama | Durum | Kapsam |
|---|---|---|
| 0 | Temel tamam | MIT, veri sahipliği ve referans/lisans sınırı |
| 1 | Temel tamam; kalıcı günlük/retention kabul edildi | Sözleşmeler, registry, policy, tek TaskManager, JSON kayıt |
| 2 | Temel tamam | PyWebView2 host, köprü, ayarlar/kimlik deposu, native yaşam döngüsü |
| 3 | Tamam/kabul edildi | Backend not CRUD/aktarımı/yedek ve gerçek ID’ler |
| 4 | İlk plugin tamam | Allowlist Notepad katalog/status/açma; genel GUI otomasyonu değil |
| 5 | İşlevsel temel kabul; kalan sınırlar kayıtlı, kullanıcı aşama 6'ya geçiş istedi | Gemini REST/Live, ses, Stop/interrupt, resume, geçici hafıza, uyku, not/sayaç/kapatma |
| 6 | 6.1.3 sor/sorma tercihi otomatik doğrulandı; kullanıcı testi bekliyor | Kalıcı kullanıcı hafızası, L0 yetenekleri, Google/Telegram/Discord ve profil alanları |
| 7 | Başlamadı | GUI resolver, L1 reçete, L2 DOM, L3 UIA, L4 vision ve skill yürütme |
| 8 | Başlamadı | Tek backend rutin/scheduler, servisler, dağıtım/paketleme |

Güncel mimari ARCHITECTURE.md, değişiklikler CHANGELOG.md. Eski ayrıntılı kabul ve
adım numaraları docs/eski/aşamalar.md içinde tarihsel olarak korunur.

## Aşama 5 kapanış sınırları

- İşlevsel dilimler (REST/Live Stop, resume sözleşmesi, not seçimi/CRUD/toplu
  işlem, ses/transkript, geçici hafıza, uyku/wake, kapanış ve sayaçlar) uygulandı;
  kullanıcı son dilimler için başarılı test bildirdi. Bu bakımın kabulü ayrıdır.
- Eski 5.F5 uzun/fiziksel testi kullanıcı isteğiyle ayrı adımdan çıkarıldı;
  genel regresyon korunur. Yeni bir zorunlu uzun kullanıcı testi icat edilmez.
- Gerçek hesap resume/GoAway ve sağlayıcı kaynaklı gecikme kabulü API limiti
  nedeniyle yeniden test edilemedi. Sentetik başarı gerçek sağlayıcı ispatı değildir.
- Kalıcı core'da 256 artık RAM/aktif iş sınırıdır; disk geçmişi korunur.
  Günlüksüz izole TaskManager eski güvenli toplam sınırını korur.
- Restart günlüğü tamamlananı tekrar yürütmez; başlamış yarım iş unknown, kuyruk
  iptal olur. Unknown uzlaştırma ekranı yok; kilit restart ile kalkmaz. Disk
  geçmişi büyür ve eski not içeriklerini tutabilir; otomatik temizlik yoktur.
- Native tek-instance kilidi 5.F7.1’de uygulandı; doğrudan script yazıcıları aynı
  host kilidi sözleşmesini kullanmalı. Üçüncü taraf/varlık paketleme lisansları dağıtım öncesi.
- 5.F7.2/3 için kısa kullanıcı kabulü → commit; bu koşullar çözülmüş sayılmadan
  Aşama 5 için sınırsız/üretime hazır iddiası yok. Açık sınırla geliştirmeye
  devam kararı ve sonraki tek adım kullanıcıyla belirlenir.

## Sonraki aşamaların alt adımları

Henüz uygulanmadılar; her promptta istenen tek dilim ayrıca daraltılır.

| Kimlik | Amaç ve kabul sınırı |
|---|---|
| 6.1 | 6.1.1 kabul edildi; 6.1.2 model mutasyonları uygulandı/otomatik doğrulandı; 6.1.3 onaylı öneriler uygulandı/otomatik doğrulandı |
| 6.2 | Telemetri/app/media araçları; her ölçüm/işlem gerçek kaynak ve doğrulama ile |
| 6.3 | Dosya okuma, sonra kontrollü değişiklik; hedef/izin ve readback |
| 6.4 | Hava/konum izni ve web arama; onay ve harici içerik sınırı |
| 6.5 | Google Drive/Calendar/mail; OAuth kapsam, yenileme, bağlantı ve işlem kanıtı |
| 6.6 | Telegram/Discord giriş-çıkış; principal/hedef yetkisi, belirsiz teslimde replay yok |
| 6.7 | Mevcut görev günlüğü üzerinde harici veri taint/risk onayı/kanal yetkisi ve unknown uzlaştırma; 6.5/6.6 yazma önkoşulu |
| 7.1 | Tek uygulamada L3 UIA hedef ve sonuç doğrulama |
| 7.2 | L1 doğrulanmış reçete; bağlam değişiminde eski hedef kullanılmaz |
| 7.3 | Tarayıcı L2 DOM, gerektiğinde bütçeli L4 vision/OCR |
| 7.4 | Skill JSON yürütme; aynı registry/policy/TaskManager, serbest eval yok |
| 7.5 | DPI/pencere/eski hedef/izin/unknown regresyonu |
| 8.1 | Tek backend scheduler; ikinci UI yürütücüsü yok |
| 8.2 | Rutin CRUD/tetik ID'si; çift çalışma ile bildirim ayrımı |
| 8.3 | Kullanıcının açtığı arka plan servisleri ve sınırlı/maskeli log |
| 8.4 | Şema geçişi, çökme kurtarma ve güvenli güncelleme |
| 8.5 | Paketleme, tek-instance entegrasyon kabulü, lisans/SBOM ve temiz kurulum |


## 5.F7 — İlk üç denetim bulgusunun kapatılması

Sıra bağımlılığa göre seçildi; kullanıcı onayıyla 5.F7.2 ve 5.F7.3 aynı turda birleştirildi.

| Adım | Kapsam | Durum |
|---|---|---|
| 5.F7.1 | Aynı veri kökü için OS tek-instance kilidi; crash/exception/restart/ayrı profil | Uygulandı: 1000 pytest, 10 native aşama, Pyright 0; [kanıt](reports/instance-checks.json). Kullanıcı devam/commit/push onayı verdi; ayrı fiziksel test raporu yok |
| 5.F7.2 | Kalıcı görev/istek günlüğü; restart sonrası eski tamamlanmış veya belirsiz işlem tekrar yürütülmez | Uygulandı/otomatik doğrulandı; [kanıt](reports/task-journal-checks.json). Kullanıcı devam/commit onayı; 5c21156 commit'inde, push yok |
| 5.F7.3 | Kalıcı dedup korunarak terminal kayıt retention; 256 sınırı ömür boyu toplam değil aktif işler için | Uygulandı/otomatik doğrulandı; 300 iş (kapasite 4/256), aktif kuyruk ve eski replay. Kullanıcı devam/commit onayı; 5c21156 commit'inde, push yok |
| 5.F8.1 | Settings Audio altında efektlerden ayrı Vex reply volume; aynı PCM gain, kayıt/snapshot/reset/Mute | Uygulandı: 1024 pytest, 9 JS, 5 browser, 10 native, Pyright 0; [kanıt](reports/reply-volume-checks.json). Kullanıcı çalıştığını doğruladı; commit onaylı |
| 5.F8.2 | Belgelenmiş hazır Live sesleri, [LIVE] etiketi, conn.voice → speech_config; anahtar input durum ibaresi | Uygulandı: 1025 genel pytest + 24 son hedefli test, 9 JS, 5 browser, 10 native, Pyright 0; [kanıt](reports/live-voices-checks.json). Kullanıcı devam onayı verdi; ayrı fiziksel ses testi bildirmedi |
| 5.F8.3 | Kalan profil/base instruction/greeting sabitlerinin gerekli kapsamını ayrıca belirle | Henüz uygulanmadı; kalıcı hafıza ve entegrasyonların aşama 6 sınırı korunur |

5.F7.1 kilidi native host içindir. 5.F7.2 create_core girişine ayrıca günlük/core
OS kilidi ekler; doğrudan JsonStore yazıcısı hâlâ bu sahipliği atlayamaz. Günlük
ve not/dış işlem tek transaction değildir; lock/günlük dosyalarını silerek
“temizleme” yapılmamalıdır.


### 5.F7.2/3 — uygulanan kapsam ve kabul

- **5.F7.2 — kalıcı görev günlüğü:** aynı veri kökünün tek sahipliği altında
  request kimliği/parmak izi ve yürütme durumunu kalıcı tut. Tamamlanan aynı
  istek tekrar çalışmasın; kimlik/içerik çakışması reddedilsin. Crash sırasında
  başlamış ama sonucu bilinmeyen iş unknown kalsın, otomatik tekrar yapılmasın.
  Günlük yazılamaz/bozulursa yan etkiyi güvenli biçimde engelle; geçici veriyle
  ayrı süreç/restart/crash testleri ve mevcut Stop regresyonları zorunlu.
- **5.F7.3 — kapasite/retention:** yalnız 5.F7.2 doğrulandıktan sonra. 256'yı
  süreç boyunca toplam iş sınırı olmaktan çıkar; RAM/aktif kuyruk yine sınırlı
  kalsın. Eski terminal kayıtları taşımak/saklamak replay bilgisini silmesin.
  256'dan fazla ardışık iş, dolu aktif kuyruk, eski isteğin tekrarı ve restart
  testleriyle doğrula. Sınırı sadece büyütmek çözüm sayılmaz.

İkisi uygulandı: **1017 pytest**, 17 hedefli günlük testi, hedefli Pyright **0** ve
**10/10 native** aşama geçti. [Test kanıtı](reports/task-journal-checks.json),
[native kanıt](reports/task-journal-native.json). Gerçek hesap/API ve fiziksel ses
yeniden denenmedi. Kullanıcı devam/commit onayı verdi; ayrı fiziksel test bildirmedi. 5.F8.1 yanıt ses seviyesi uygulandı/otomatik doğrulandı; ses karakteri 5.F8.2
olarak uygulanıyor; diğer profil boşlukları 5.F8.3 olarak bekliyor.


### 5.F8.1 — kabul kapsamı

- Aynı live_audio GainNode'u: anlık yüzde, Mute kaldırınca seçili seviye;
  Live/REST/timer sesleri ortak; mikrofon ve efekt seviyesi bağımsız.
- UI tercihi ve native şema: 0–1 doğrulama, eski kayıtta varsayılan 1,
  sıfırı koruma, snapshot/yerel kayıt/native süreçte yeniden açma ve reset 1.
- Yeni komut, sağlayıcı isteği, framework veya ikinci oynatıcı yok.
- Hedefli PCM testleri, browser/native ayar-kayıt-kapanış ve gerekli regresyon.
  Fiziksel hoparlör kabulü kullanıcıda; ücretli API testte kullanılmaz.


5.F8.1 son doğrulama: **1024 pytest**, **9 JS suite**, **5 browser grubu**,
**10/10 native aşama**, app Pyright **0**. [Özet](reports/reply-volume-checks.json),
[native kanıt](reports/reply-volume-native.json). Ücretli API ve fiziksel hoparlör
kabulü denenmedi. Kullanıcı çalıştığını doğruladı; commit onaylı, push yok.


### 5.F8.2 — bu turun sınırı

- Google belgelerindeki 30 hazır Live sesinden tek allowlist; [LIVE] UI etiketi.
  Ses keşfi API'den yapılmış gibi gösterilmez. conn.voice genel ayar deposunda.
- Seçim sonraki Live metin/mikrofon/timer turuna gider; aktif yanıt kesilmez.
  Ses değişimi eski resume handle'ını kullanmaz. REST TTS ve güvenlik hattı korunur.
- Anahtarın varlığı input placeholder'ında; gerçek value/sır DOM'da tutulmaz.
  Başarısız/belirsiz kayıt başarılı API bağlantısı gibi sunulmaz.
- 5.F8.1 kullanıcı tarafından çalışıyor olarak onaylandı; 9d67a1d commit'inde.
  Yeni dilimin kullanıcı kabulü/commit'i ayrı bekler; aşama 5 kapanmış sayılmaz.


5.F8.2 doğrulama: **1025 genel pytest**, ek son katalog kontrolü dahil **24 hedefli
profil/ses/belge testi**, **9 JS suite**, **5 browser grubu**, app Pyright **0**,
**10/10 native aşama**. [Özet](reports/live-voices-checks.json),
[native kanıt](reports/live-voices-native.json). Gerçek hesap ve fiziksel ses
kabulü yapılmadı; kullanıcı aşama 6'ya geçiş onayı verdi; ayrı fiziksel ses testi bildirmedi. Aşama 5'in açık sınırları korunur.


## 6.1 — kullanıcı hafızası dilimleri

Kullanıcı aşama 6'ya geçiş istedi; aşama 5'in sağlayıcı/fiziksel kabul,
unknown uzlaştırma, lisans ve kalan profil alanları kapanmış sayılmaz.
Önceki Live ses seçimi 2cebea8 commit'inde; push yok.

| Adım | Kapsam | Durum |
|---|---|---|
| 6.1.1 | Personalization'da açık gönderim tercihi; kaydet/gör/düzelt/temizle, REST/Live bağlamı, eski sohbet bağlamını bırakma; New Chat düğmesini kaldır | Uygulandı: 1035 pytest, 9 JS, 6 browser, 10 native, Pyright 0; [kanıt](reports/personal-memory-checks.json). Kullanıcı kabul etti; e7f3ce4 commit’inde |
| 6.1.2 | Model üzerinden hafıza gör/ekle/düzelt/unut; tek kayıt otoritesi ve snapshot doğrulamasıyla ModelTools → registry/policy/TaskManager | Uygulandı: 1050 pytest, 9 JS, 7 browser, 10 native, Pyright 0; [kanıt](reports/model-memory-checks.json). Kullanıcı kabul etti; 50421c3 commit’inde |
| 6.1.3 | Model çıkarımlarını öneri olarak sunma; kullanıcı onayı öncesinde gerçek/kalıcı kullanıcı bilgisi saymama | Uygulandı: 1065 pytest, 9 JS, 8 browser, 10 native, Pyright 0; [kanıt](reports/memory-suggestions-checks.json). Kullanıcı kabulü/commit bekliyor |

6.1.1 otomatik öğrenmez; eski legacy pMem metni varsayılan kapalıdır. Kalıcılık
mevcut settings.json profilidir; ek veritabanı yok. Unutma aktif yanıtı kesmez,
geçmiş sağlayıcı kayıtlarını/yedekleri silmez. Geçersiz kayıt/disk hatası başarı
sayılmaz. New Chat UI ve kullanılmayan handler kaldırıldı; internal reset
endpoint'i mevcut core test/gelecek kanal sözleşmesi için korunur.


6.1.1 son doğrulama: **1035 pytest**, **9 JS suite**, **6 browser grubu**,
**10/10 native aşama**, app + yeni hafıza testi Pyright **0**. İlk tarayıcı
checkbox hatası düzeltildi; native geçmiş-metin beklemesi ve profil kurtarma
beklentisi yeni sözleşmeye göre netleştirildi. [Rapor](reports/personal-memory-checks.json),
[native](reports/personal-memory-native.json). Gerçek hesap/ücretli API ve fiziksel
hatırlama/ses testi yok. Kullanıcı testleri başarılı bildirdi; commit onaylı.


### 6.1.2 — açık model hafıza işlemleri

- Önceki dilim kullanıcı test onayıyla e7f3ce4 commit'ine alındı; push yok.
- Tek settings.json/prof.pMem üzerinde memory.read/patch; açık pMemory tercihi,
  taze tur/snapshot, tekil metin hedefi ve doğrulanmış readback.
- UI save/reset ile paylaşılan kısa depo kilidi; eski formun hafızayı geri
  yazmasını engelleyen memoryBase karşılaştırması. Ortak şema storage'a taşındı.
- REST/Live aynı katalog/ModelTools hattında; timer bildirimleri araçsız.
  Sonuçta güncel profil UI'a döner, ikinci mutasyon yok. Sonraki tur eski
  socket/RAM bağlamını bırakır; geç Stop gerçekleşmiş kaydı geri almaz.
- Otomatik çıkarım/öneri 6.1.3 bekler. Gerçek hesap/ücretli API yok;
  otomatik doğrulama kullanıcı kabulünün yerine geçmez.

6.1.2 son doğrulama: **1050 pytest**, **9 JS suite**, **7 browser grubu**,
**10/10 native aşama**, app + yeni model hafıza testi Pyright **0**.
[Özet](reports/model-memory-checks.json), [native](reports/model-memory-native.json).
Başarısız ara denemeler raporda korunur; ücretli API/gerçek model ve fiziksel
ses kabulü yapılmadı. Açık form taslağı korunur; çakışmada uygulamayı yeniden
açmak gerekebilir. Kullanıcı testleri başarılı bildirdi; commit onaylı.


### 6.1.3 — konuşmadan kişisel bilgi önerme ve onaylı kayıt

- Önceki dilim kullanıcı test onayıyla 50421c3 commit'ine alındı; push yok.
- Varsayılan kapalı pLearn; pMemory ile birlikte aynı REST/Live konuşma
  modelinde memory.propose açar. Ek çıkarım API'si veya yeni depo yoktur.
- Kaynak alıntısı bu turun gerçek metni/Live transkriptine bağlanır;
  host kanıtı modelden alınmaz. Kaynak yoksa öneri atlanır, sohbet sürer.
- Tek RAM adayı; onay/ret yalnız UI memory.decide → registry/policy/TaskManager.
  Model öneriyi onaylayamaz; bu kipte yeni ekleme append yolunu da aşamaz.
- Onay mevcut append/readback ile tek profile yazılır. Eski ID, ret, değişmiş
  izin/snapshot ve restart aday bilgisini kendiliğinden gerçeğe dönüştürmez.
- Modelin üçüncü kişi/alıntı/şaka/hassas bilgi ayrımı gerçek sağlayıcıyla kabul
  edilmedi; insan incelemesi bu yüzden korunur. Sesle onay bu dilimde yoktur.

6.1.3 son doğrulama: **1065 pytest**, **15 hedefli öneri testi**, **9 JS suite**,
**8 browser grubu**, **10/10 native aşama**, app + yeni öneri testi Pyright **0**.
[Özet](reports/memory-suggestions-checks.json), [native](reports/memory-suggestions-native.json).
Ara test varsayımları ve açık sınırlar raporda; gerçek/ücretli API ve anlamsal
çıkarım kalitesi test edilmedi. Kullanıcı kabulü/commit bekliyor; yeni aşamaya geçilmedi.


### 6.1.3 düzeltmesi — gerçek konuşmada kaynak alıntısı reddi

- Kullanıcı manuel testte başarısızlık bildirdi; önceki sentetik başarı kullanıcı
  kabulü değildir. Adım yeniden açıldı, commit/sonraki aşama yok.
- Salt okunur tanı: gerçek memory.propose sonucu source_unavailable,
  source_verified=false. Özel konuşma metni çıktıya/rapora alınmadı.
- Modelin yeniden yazdığı kaynak cümlesini gerçek transkriptle birebir
  eşleştirmek yanlış bir sözleşmeydi. Kaynak artık mevcut tur sahibinden
  doğrudan bağlanır; model source_quote üretmez. Replay eski kaynağı korur.
- Kullanıcı onayı, taze snapshot, native karar ve eksik ASR koruması aynen
  kalır. Engine log yalnız güvenli hata kodunu da gösterir.
- Parafraz regresyon testi düzeltmeden önce failed verdi; aynı örnek sonra
  geçti. REST/Live/uzun kaynak ve gerçek native UI doğrulaması tamamlandı.

Kaynak düzeltmesi son kontrol: **1068 pytest**, **33 hedefli hafıza/öneri testi**,
**8 browser grubu**, **10 native aşama**, app + öneri testi Pyright **0** ve
live-status JS paketi geçti. [Rapor](reports/memory-source-checks.json),
[native](reports/memory-source-native.json). Gerçek hesap kullanılmadı; kullanıcı
uygulamayı yeniden açıp tekrar test edecek. Henüz commit/sonraki adım yok.


### 6.1.3 — görünür inceleme ve isteğe bağlı sormadan kayıt

- Kullanıcı ekranında memory.propose başarılı ve Review memory suggestion
  görünüyordu; kalıcı alanın boş olması onay bekleyen adayın beklenen durumuydu.
  Kullanıcı bu görünümü yetersiz buldu ve sor/sorma tercihi istedi.
- pMemoryConfirm varsayılan true: onay penceresi otomatik açılır. Kullanıcı
  false kaydederse aynı propose → _apply append/readback üzerinden doğrudan
  kaydedilir, editor backend'den yenilenir. Yeni depo/yürütücü yoktur.
- Tercih UI/native/yedek/snapshot'ta kalıcı; model seçemez. Eski profilde
  varsayılan sor'dur, onay tercihi değişimi eski snapshot'ı geçersiz kılar.
- Doğrudan kayıt capability'si memory.write, Stop/replay/readback korumaları
  aynıdır. Karar sonrası Save başarıya dönüşmeden disk kanıtı gerekir.
- Kullanıcı kabulü henüz yok; mevcut 6.1.3 commit edilmedi, sonraki adım yok.

Son sor/sorma doğrulaması: **1074 pytest**, **33 hedefli hafıza testi**, **9 JS
suite**, **9 browser grubu**, **10 native aşama**, app + öneri testi Pyright **0**.
[Rapor](reports/memory-review-checks.json), [native](reports/memory-review-native.json).
Gerçek API/çıkarım doğruluğu denenmedi; her iki kip için kullanıcı testi ve
commit beklenir. Yeni adıma geçilmedi.
