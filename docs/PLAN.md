# TaskVex — Güncel plan

## Şimdi: 6.2.3a yerel ağ trafiği/bağlantısı; ping ve Wi-Fi sinyali sonraki dilim

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
| 6 | 6.1 hafıza dilimleri kullanıcı tarafından kabul edildi; sıradaki 6.2 | Kalıcı kullanıcı hafızası, L0 yetenekleri, Google/Telegram/Discord ve profil alanları |
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
| 6.1 | Elle/modelden hafıza, öneri, sor/sorma ve düğme/konuşma kararı kullanıcı tarafından kabul edildi; son commit 6f52b4c |
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
| 6.1.3 | Model çıkarımı, sor/sorma tercihi, düğme veya sonraki kullanıcı yanıtıyla ortak karar | Son doğrulama: 1081 pytest, 9 JS, 9 browser, 10 native, Pyright 0; [kanıt](reports/memory-voice-review-checks.json). Kullanıcı kabul etti; 6f52b4c commit’inde |

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


### 6.1.3 — ayrı onay grubu ve doğal konuşmayla karar

Önceki sor/sorma dilimi kullanıcı tarafından başarılı bildirildi; c5d086c
commit'ine alındı, push yapılmadı. Bu tur yalnız onay sunumu/kararı değişir.

- Save/Dismiss, sohbet altındaki dört kontrolün sağında ayrı tema uyumlu grup;
  Personalization içinde aday/onay yok, otomatik modal açılmaz.
- Vex normal yanıt/ses hattında izin sorar; sonraki kullanıcı yanıtını
  memory.read → memory.decide → registry/policy/TaskManager hattına taşır.
- Aynı turda öneri ve kendi kendini onay engeli, taze gerçek ID, snapshot,
  eski UI/model kararı, replay ve Stop öncesi doğrulanmış sonuç korunur.
- Ayrı TTS, cümle listesi, ikinci kayıt sahibi veya API isteği eklenmedi.
- Kabul: düğme ve sesli evet/hayır aynı adayı bir kez kaydeder/reddeder;
  ilgisiz/kararsız yanıt onay olmamalı. Anlamsal karar gerçek modelle ayrıca
  kullanıcı testinde değerlendirilecek. Otomatik doğrulama sürüyor.
- Bu yeni değişiklik için kullanıcı kabulü/commit bekleniyor; sonraki aşamaya geçilmedi.


Bu onay sunumu dilimi doğrulaması: **1081 pytest** (106.65 s), **40 hedefli
hafıza testi**, **9 JS suite**, **9 browser grubu**, **10 native aşama**,
app + öneri testi Pyright **0**. [Rapor](reports/memory-voice-review-checks.json),
[native](reports/memory-voice-review-native.json). 1920px'de sağda ayrı grup,
1280px'de taşmayan görünüm doğrulandı. Gerçek API, fiziksel mikrofon ve modelin
anlamsal onay doğruluğu denenmedi. Kullanıcı kabulü ve bu dilimin commit'i bekler.


## 6.1 kabulü ve kalan UI bağlantılarının sırası

Kullanıcı düğme/konuşmayla karar testlerini başarılı bildirdi. İlgili uygulama
6f52b4c commit'ine alındı; push yapılmadı. Yukarıdaki önceki kabul bekleme
notları tarihsel doğrulama turlarını anlatır; güncel 6.1 durumu kabul edildi'dir.
Bu tur yeni özellik kodlanmadı; aşağıdaki dilimler henüz başlamadı.

| Sıra | Kapsam / kabul koşulu |
|---|---|
| 6.2.1 | CPU/RAM/disk/pil/aktif exe ortak sahibi ve periyodik UI/model bağlantısı uygulandı; bu turun otomatik/native ve kullanıcı kabulü aşağıda |
| 6.2.2 | Windows PDH GPU kullanım adaptörü uygulanıyor; CPU/GPU sıcaklığı ve VRAM kapasitesi destekli kaynak bekliyor |
| 6.2.3 | Network/Wi-Fi, anlık gönderme/alma hızı, bağlantı ve gecikme; transfer hızı ile internet hız testi ayrımı; offline yerel CPU ölçümünü silmez |
| 6.2.4 | Sağlayıcının gerçek kullanım verisinden token sayacı; tur/oturum ve context sınırı ayrı; bilinmeyen hesap kotası veya tahmini kullanım kesin değer gibi gösterilmez |
| 6.2.5 | Mevcut Windows medya oturumu: parça bilgisi, oynat/duraklat/önceki/sonraki; UI ve model aynı araç/alan sahibi |
| 6.3 | Dosya eki/dosya okuma ve ardından kontrollü değişiklik; hedef/izin/readback |
| 6.4 | Hava durumu, manuel/izinli otomatik konum ve web arama; önbellek/son güncelleme ve gerçek hata durumu |
| 6.5 | Google bağlantısı, Calendar/Drive/mail; önce 6.7'nin ilgili risk/kanal/yazma korumaları |
| 6.6 | Telegram/Discord; yine 6.7'nin ilgili korumaları önkoşul |
| 6.8 — kapsam önerisi | UI'daki kamera, Live ekran paylaşımı ve mikrofon dışı ses kaynakları için ayrı dilimler; izin, görsel/ses akışı ve kaynak temizliği; GUI tıklama otomasyonundan ayrı |
| 5.F8.3 kalan profil alanları | Başlangıç karşılama, tarayıcı/sekme/uygulama tercihleri ve shortcut alanları ilgili uygulama/dosya/tarayıcı dilimiyle bağlanır; kişisel talimat güvenlik sınırlarını aşan base override olmaz |
| 8.1 | Gerçek yerel hatırlatıcılar için mevcut planın tek backend scheduler'ı; skill/rutin yürütmesinden ayrı olsa da ikinci zamanlayıcı yazılmaz |

Timeline/log mevcut yerel görünüm olarak kalır; yeni veri üreticileri yalnız gerçek
olaylarını besler. Inspect/Create Skill, skill yürütmesi ve rutin kapsamı bu UI
önceliklendirme isteğinin dışındadır. 6.8 yeni bir uygulama onayı veya tamamlanma
iddiası değildir; mevcut plandaki eksik multimodal kapsamın önerilen yeridir.


### 6.2.4 ilk dilim — son sağlayıcı token bildirimi

Kullanıcı sınırlı tur bütçesiyle en hafif 6. aşama adımını ve doğrudan commit
istedi; 6.2.4 bu nedenle öne alındı. Live/REST usage metadata mevcut rapordan
UI'a bağlandı. Limit bilinmiyorsa sayı tek başına gösterilir; yeni tur/verisiz
yanıt eski değeri temizler, sıfır geçerlidir. Eski setter limit sözleşmesi korunur.
Oturum toplamı, ücret/kota ve model context limiti bu küçük dilimde uygulanmadı;
6.2.4 için bunlar yapılmış sayılmaz. Sonraki özellik adımı hâlâ 6.2.1'dir.
Gerçek/ücretli API çağrısı yapılmadı. Kullanıcı bu tur commit'e açık izin verdi;
fiziksel kullanıcı kabulü henüz yoktur. Otomatik sonuçlar raporda kaydedilecek.


Token dilimi: **1091 pytest** (86.85 s), **96 hedefli Python testi**,
**10 browser grubu**, **9 JS suite**, app Pyright **0**.
[Özet](reports/token-counter-checks.json). Fiziksel kullanıcı/API kabulü bekler;
kullanıcının bu tur verdiği açık commit izni manuel kabul olarak sunulmaz.

**10/10 native aşama** da geçti: [native regresyon](reports/token-counter-native.json).
Token sayısı için SDK sentetik taşıma + tarayıcı görünüm testi; gerçek hesap yok.


### 6.2.4 — Gemini içinde hesaplama ve uygulama oturumu toplamı

Kullanıcı bu tur son bildirim yerine tüm oturumu istedi. Python token
hesaplaması mevcut gemini.py içinde toplandı; Live ve speech adaptörleri
kendi metadata'larını iletir. TextChat ömründeki tek RAM toplamı Stop,
Disconnect/model/anahtar/bağlam değişiminde korunur; uygulama restart'ında sıfırlanır.
REST araç turları ve ayrı ses isteği dahil edilir. Live ara snapshot'ları aynı
üretimde bir kez sayılır; metadata eksikse bilinen toplam ≥/Incomplete gösterilir.
Bu değişiklik önceki son-bildirim diliminin yerini alır; kota/context/fatura
kesinliği iddiası yoktur. Idle'da geç gelen metadata ve sağlayıcının göndermediği
kullanım geri sorgulanmaz. Gerçek/ücretli API kullanılmaz.

Hedefli SDK ve uygulama testleri eklendi; genel/native doğrulama sürüyor.
Bu tur commit/push istenmedi: yeni dilim manuel kullanıcı kabulünü bekler.
Sıradaki özellik 6.2.1 olarak kalır; genel sağlayıcı framework'ü eklenmedi.


Oturum toplamı son doğrulama: **1101 pytest** (102.68 s), **138 hedefli SDK/
oturum testi**, **11 browser grubu**, **9 JS suite**, app Pyright **0**,
**10/10 native aşama**. Native UI iki yanıtta 10 → 20 toplamını doğruladı.
[Özet](reports/session-token-checks.json), [native](reports/session-token-native.json).
Gerçek API/fatura denetimi yapılmadı; uygulama yeniden açılarak kullanıcı testi
beklenir. Commit ve push yapılmadı. Önceki son-bildirim raporu tarihsel kanıttır.


### 6.2.1 — birlikte tamamlanan yerel ölçümler

Kullanıcı token oturum testini başarılı bildirdi; açık talimatıyla commit sonraya
bırakıldı. Kullanıcı 6.2'de beraber yapılabilenleri istedi. Bu tur CPU/RAM, disk,
pil ve aktif uygulama bağlantıları aynı Telemetry örneğinde birleştirildi.
Win32 + standart Python kullanıldı; bağımlılık kurulmadı. CPU iki örneğin farkı,
RAM/disk GiB, pil yok/bilinmiyor ve ilk/eksik/sıfır ölçüm ayrımı korunur.
UI sorgusu görev günlüğünü poll ile büyütmez; model mevcut ortak araç hattını
kullanır. Aktif uygulamanın yalnız exe adı alınır; belge başlığı ve tam yol yoktur.
Model offline olduğunda yerel metrik ve oturum token toplamının silinmesi de düzeltildi.

Kapsamı sonraya ayrılanlar: 6.2.2 GPU/sıcaklık için uygun donanım/sensör kaynağı;
6.2.3 Wi-Fi/ağ arabirimi ve trafik/gecikme; 6.2.5 Windows medya oturumu/denetimleri.
Bunlar bu dilimde çalışıyor sayılmaz. Sıradaki kapsam 6.2.2 kaynak seçimi ve
ilk destekli donanım adaptörüdür; gerekiyorsa okunamayan donanım açıkça raporlanır.
Hava/Google/skill/rutin kapsamına geçilmedi. Kullanıcı talimatıyla commit/push yok.


6.2.1 son otomatik doğrulama: **1109 pytest** (160.19 s), **96 hedefli test**,
**12 browser grubu**, **9 JS suite**, app + telemetri testi Pyright **0**.
İlk native tur chat aşamasında 60 s süre sınırına takıldı; eşzamanlı pytest
bitince aynı süre sınırıyla tek başına tekrar edilen bütün native süit
**10/10 geçti**. Kesin neden kanıtlanmadı, başarısız tur gizlenmedi.
[Özet](reports/local-telemetry-checks.json), [native](reports/local-telemetry-native.json),
[ilk süre aşımı](reports/local-telemetry-native-first-run.json).
Gerçek Windows CPU ikinci örnek/RAM/disk/pil salt okunur ölçüm kontrolü de geçti.
Gerçek API ve modelin bu yeni soruları yorumlaması kullanıcı kabulünü bekler.
Önceki token adımı kullanıcı kabul edildi; iki dilimin commit'i talimatla ertelendi.


### 6.2.2 — Windows GPU kullanımı ve sistem görünümü

Önceki token/yerel ölçüm adımları kullanıcı kabulüyle eba75a5 commit'inde;
push yapılmadı. İlk NVIDIA denemesi kullanıcı isteğiyle kaldırıldı. Eski
[nvidia özeti](reports/nvidia-telemetry-checks.json) ve [native raporu](reports/nvidia-telemetry-native.json)
yalnız terk edilen denemenin kanıtıdır; güncel uygulamanın kabulü değildir.

- windows_gpu.py: Windows PDH sayaçları, tek Telemetry sahibi, aynı
  registry/policy/TaskManager model hattı; ayrı worker/model/depo yoktur.
- Aynı motordaki süreçler toplanır; kartın en yoğun motoru, dashboard'da en
  yoğun kart gösterilir. Üretici executable'ı/driver API'si çağrılmaz.
- İlk örnek referans, gerçek sıfır geçerli, kayıp sayaç unavailable; hatada eski
  GPU verisi kalmaz ve CPU/RAM korunur. Native kapanış PDH kaynağını bırakır.
- Üst açıklama satırı kaldırıldı; GPU etiketi sabit. Barın yüzdeyle aynı
  genişliği 1280/1920'de ve 0/25/100 değerlerinde test edilir.
- Windows sayaç sağlayan adaptörler desteklenir; her eski kart için garanti
  yoktur. CPU/GPU sıcaklığı ve VRAM kapasitesi açık sınırdır. NVIDIA fallback yok.
- Gerçek Windows üzerinde doğrudan salt okunur sayaç sorgusu başarılı;
  sayaç kimlikleri ürün adı/Task Manager sıra numarası diye sunulmadı.
- Sonraki bağımsız özellik 6.2.3 ağ/Wi-Fi; bu tur yeni özellik aşamasına geçilmez.

Son doğrulama: **1120 pytest** (127.49 s), **19 hedefli test**, **13 browser
grubu** (1280/1920 ve GPU barı 0/25/100), **9 JS suite**, **10 native aşama**,
app + GPU testi Pyright **0**. [Özet](reports/windows-gpu-checks.json),
[native](reports/windows-gpu-native.json). İlk tip kontrolünde sahte PDH testinin
None-only alanı hata verdi; açık tür eklenince geçti. Gerçek ortak Windows
Telemetry ilk örnekte warming_up, ikinci örnekte GPU %8.4 ve geçerli RAM döndürdü;
okuma sonrası kaynak kapatıldı. Diğer üreticilerin fiziksel cihazları ve gerçek
model/ücretli API test edilmedi. Manuel kullanıcı kabulü, commit ve push yok.


6.2.2 kullanıcı testi başarılı bildirildi; Windows GPU/sistem görünümü dilimi kabul edildi.
AGENTS.md gereği sonraki adımdan önce commit alınır; push istenmedi.


### 6.2.3a — pasif fiziksel ağ ölçümleri

GPU/sistem görünümü kullanıcı tarafından kabul edildi ve 43c7f28 commit'ine
alındı; push yok. Bu tur yalnız ağ dilimi uygulanır.

- Tek Telemetry örneği IP Helper ile fiziksel arabirim link durumunu ve 64 bit
  RX/TX sayaç farkını örnekler; UI aynı query_system, model aynı system.status
  registry/policy/TaskManager hattını kullanır. Yeni worker/timer/depo yoktur.
- UI Receive/Send Mbps, yerel bağlantı ve Wi-Fi bağlı/bağlı değil bilgisi verir.
  Bu veri internet erişim testi veya azami bant genişliği değildir.
- İlk örnek, reset, cihaz kümesi değişimi ve kaynak hatası hız üretmez; sıfır
  gerçek ölçümdür. VPN/sanal arabirimler çift sayılmamak için dışarıda kalır.
- SSID/IP/MAC/profil adı modele veya rapora alınmaz; sistem tablosu finally'de bırakılır.
- 6.2.3b: hedefi belli ping/erişilebilirlik ve izin/kaynak sınırlarıyla Wi-Fi
  sinyal yüzdesi ayrıca yapılacak. API gecikmesi genel yanıt süresi sanılmayacak.
- Bu daraltma bir sonraki özelliği yarım kabul etmez: a diliminin kabulü
  yerel sayaç/UI/model/yeniden bağlantı testleridir; b açık kalır.

Son doğrulama: **1132 pytest** (142.83 s), **31 hedefli test**, **14 browser
grubu**, **9 JS suite**, **10 native aşama** ve app + ağ testi Pyright **0**.
[Özet](reports/network-local-checks.json), [native](reports/network-local-native.json).
İlk hedefli turda iki test yalıtım noktasından başarısız oldu; yalıtım DLL
yükleyicisine taşınınca geçti. Gerçek Windows pasif okuması ilk örnekte hız
üretmedi, ikinci örnekte RX/TX döndürdü; özel ağ kimliği kaydedilmedi.
Gerçek model/ücretli API ve fiziksel bağlantı kesip açma denenmedi.
Kullanıcı kabulü bekler; yeni dilim commit/push edilmedi. Sırada 6.2.3b var.


6.2.3a kullanıcı tarafından başarılı bildirildi; yerel ağ dilimi kabul edildi.
Sonraki adımdan önce commit alınır, push yapılmaz.
