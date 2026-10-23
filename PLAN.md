# TaskVex — Güncel plan

## Şimdi: 5.F6 bakım ve Aşama 5 kapanış incelemesi

Önceki 5.R8.6 kullanıcı kabulü başarılı, 526bfed commit’inde (push yok).
Bu dilim uygulandı ve otomatik doğrulandı; manuel kabul ve yeni commit henüz yok.

- [x] İlk envanter ve onaylanan önceki adımın commit’i.
- [x] Tarihsel belgeleri docs/eski altına özgün yollarıyla taşı.
- [x] Ölü yolları kaldır; kullanılan/yakında planlı UI verilerini koru.
- [x] Büyüyen UI modüllerini sorumluluk sınırlarına göre ayır.
- [x] Kaynak/test/config/belge envanteri, mimari ve sabit ayar incelemesi: docs/AUDIT.md.
- [x] Güncel mimari/plan/changelog/sözleşme/README’ler; arşiv hash kaydı.
- [x] 996 pytest, 9 JS suite, 4 browser grubu, 10 native aşama ve hedefli Pyright 0.
- [x] Arşiv hash, güncel belge linkleri ve açık sınır raporu: docs/AUDIT.md.
- [ ] Kullanıcı kabulü → commit; Aşama 5 kapanış kararı.

Debloat güvenlik/doğrulama/Stop korumalarını kaldırmaz. REST ve bağımsız tarayıcı
UI modu korunur. Bekleyen skill/rutin tanımları silinmez. Gelecekteki özellikler
sanki bugün çalışıyormuş gibi gösterilmez.

## Yol haritası

| Aşama | Durum | Kapsam |
|---|---|---|
| 0 | Temel tamam | MIT, veri sahipliği ve referans/lisans sınırı |
| 1 | Temel tamam; kapasite sınırı açık | Sözleşmeler, registry, policy, tek TaskManager, JSON kayıt |
| 2 | Temel tamam | PyWebView2 host, köprü, ayarlar/kimlik deposu, native yaşam döngüsü |
| 3 | Tamam/kabul edildi | Backend not CRUD/aktarımı/yedek ve gerçek ID’ler |
| 4 | İlk plugin tamam | Allowlist Notepad katalog/status/açma; genel GUI otomasyonu değil |
| 5 | İşlevsel dilimler kabul; 5.F6 devam | Gemini REST/Live, ses, Stop/interrupt, resume, geçici hafıza, uyku, not/sayaç/kapatma |
| 6 | Başlamadı | Kalıcı kullanıcı hafızası, L0 yetenekleri, Google/Telegram/Discord ve profil alanları |
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
- 256 kayıt kapasitesi: uzun oturum sınırı açık. Sonraki core işi terminal kayıt
  retention'ını replay garantisiyle birlikte tasarlamak; sessiz evict yasak.
- Restart sonrası idempotency/journal, dış yan etkili entegrasyonlardan önce
  zorunlu. Bugünkü süreç içi koruma kalıcı garanti olarak sunulamaz.
- Çoklu instance kilidi ve üçüncü taraf/varlık paketleme lisansları dağıtım öncesi.
- 5.F6 için kısa kullanıcı kabulü → commit; bu koşullar çözülmüş sayılmadan
  Aşama 5 için sınırsız/üretime hazır iddiası yok. Açık sınırla geliştirmeye
  devam kararı ve sonraki tek adım kullanıcıyla belirlenir.

## Sonraki aşamaların alt adımları

Henüz uygulanmadılar; her promptta istenen tek dilim ayrıca daraltılır.

| Kimlik | Amaç ve kabul sınırı |
|---|---|
| 6.1 | Kullanıcı hafızası: açık tercih, gör/düzelt/unut; çıkarım kullanıcı gerçeği sayılmaz |
| 6.2 | Telemetri/app/media araçları; her ölçüm/işlem gerçek kaynak ve doğrulama ile |
| 6.3 | Dosya okuma, sonra kontrollü değişiklik; hedef/izin ve readback |
| 6.4 | Hava/konum izni ve web arama; onay ve harici içerik sınırı |
| 6.5 | Google Drive/Calendar/mail; OAuth kapsam, yenileme, bağlantı ve işlem kanıtı |
| 6.6 | Telegram/Discord giriş-çıkış; principal/hedef yetkisi, belirsiz teslimde replay yok |
| 6.7 | Dış yan etkiler öncesi kalıcı çağrı günlüğü/taint/risk onayı; 6.5/6.6 yazma önkoşulu |
| 7.1 | Tek uygulamada L3 UIA hedef ve sonuç doğrulama |
| 7.2 | L1 doğrulanmış reçete; bağlam değişiminde eski hedef kullanılmaz |
| 7.3 | Tarayıcı L2 DOM, gerektiğinde bütçeli L4 vision/OCR |
| 7.4 | Skill JSON yürütme; aynı registry/policy/TaskManager, serbest eval yok |
| 7.5 | DPI/pencere/eski hedef/izin/unknown regresyonu |
| 8.1 | Tek backend scheduler; ikinci UI yürütücüsü yok |
| 8.2 | Rutin CRUD/tetik ID'si; çift çalışma ile bildirim ayrımı |
| 8.3 | Kullanıcının açtığı arka plan servisleri ve sınırlı/maskeli log |
| 8.4 | Şema geçişi, çökme kurtarma ve güvenli güncelleme |
| 8.5 | Paketleme, tek instance, lisans/SBOM ve temiz kurulum kabulü |
