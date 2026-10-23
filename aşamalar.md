# TaskVex — Aşamalar ve güncel adımlar

Bu dosya projenin güncel ilerleme kaydıdır. Tarihsel geliştirme notlarını tekrar
okumadan neyin çalıştığını, neyin açık olduğunu ve sırada ne bulunduğunu gösterir.
Son güncelleme: 23 Ekim 2026. Mevcut aşama: **Aşama 5, uyku/ses kararlılığı**.
Aşama 5 kapanmadı; Aşama 6 uygulamasına geçilmedi.

## Nasıl güncellenir?

- Aşama yeni adımlara bölündüğünde, kapsam/sıra değiştiğinde ve her adım sonunda
  bu dosyayı güncelle. Mevcut kimlikleri koru; yeni alt adımlara yeni kimlik ver.
- **Temel kabul tamam:** önceki kapsam uygulanmış ve kabul kaydı var. Daha sonra
  bulunan bir sorun ilgili alt adımı yeniden açabilir; tüm ürün hatasız demek değildir.
- **Uygulandı, kabul bekliyor:** kod ve otomatik kanıt var; gerçek kullanıcı kabulü yok.
- **Açık / Engel / Planlandı:** tamamlandı değildir. Başarılı regresyon açık bir
  yeniden üretimi kapatmaz. Bulguyu, düzeltmesini ve kabulünü ayrı kaydet.
- Mimari kararlar ARCHITECTURE.md, çalışan komutlar commands.md, detaylı model
  kanıtları docs/STAGE5_MODEL.md içindedir. Bu dosya geçmişi silmez; güncel durumu
  gösterir. README yol haritası buradaki aşama numaralarıyla aynı kalmalıdır.
- Kullanıcı manuel kabul etmeden commit yok; kabulden sonra AGENTS.md akışı uygulanır.

## Genel yol haritası

| Aşama | Kapsam | Güncel durum |
|---|---|---|
| 0 | Baz çizgi, veri sahipliği, MIT ve referans/lisans sınırları | Başlangıç kararları kaydedildi |
| 1 | Modelden bağımsız core | Temel kabul tamam; uzun oturum kapasite sınırı ayrıca değerlendirilecek |
| 2 | Native host, UI köprüsü ve ayarlar | Temel kabul tamam; bugünkü 10 native regresyon senaryosu geçti |
| 3 | Backend otoriteli not CRUD ve aktarım/yedek | Temel kabul tamam; gerçek kullanıcı kabulü ve güncel regresyon kaydı var |
| 4 | İlk Windows uygulama plugini | Notepad katalog/status/açma kabulü tamam; tüm uygulamalar veya modele apps.open açılması değildir |
| 5 | Gemini, Live, araçlar, ses, geçici hafıza ve uyku | **Devam ediyor; aşağıdaki 5.F adımları açık** |
| 6 | Kalıcı kullanıcı hafızası, yeni L0 işlemleri ve dış entegrasyonlar | Planlandı; başlamadı |
| 7 | GUI resolver, L1 reçete, L2 DOM, L3 UIA, L4 vision ve skill yürütme | Planlandı; başlamadı |
| 8 | Rutin/scheduler, arka plan servisleri, dağıtım ve paketleme | Planlandı; başlamadı |

## Aşama 0 — Başlangıç

- 0.1 UI baz çizgisi/yedek ve sözleşme kararları kaydedildi.
- 0.2 TaskVex özgün katkıları MIT; üçüncü taraflar ayrı tutuldu.
- 0.3 Veri sahipliği ve desteklenmeyen işlemin açık reddi tanımlandı.
- Kaynak: docs/STAGE0_DECISIONS.md ve CORE_START_PLAN.md.

## Aşama 1 — Core

- 1.1 Python ortamı, pyproject ve geliştirme lock dosyası hazır.
- 1.2 İstek/görev/araç/sonuç sözleşmeleri ve JSON doğrulaması hazır.
- 1.3 ToolRegistry kayıt, parametre doğrulama ve isim çakışması reddi hazır.
- 1.4 Tek worker TaskManager, kuyruk, request_id tekrar koruması, durum/iptal hazır.
- 1.5 Açık yetki listesiyle policy ve atomik JSON saklama hazır.
- 1.6 Yerel notlar ve salt okunur sistem aracı core hattında doğrulandı.
- Sınır: TaskManager tüm görev kayıtları dahil 256 kayıt tutar; kapasite dolunca
  yeni istek reddeder. Restart sonrası kalıcı exactly-once veya çok süreçli
  yazma garantisi yoktur. Bunlar gizli sınırsız ölçek varsayımıyla sunulmaz.
- Kaynak: docs/STAGE1_CORE.md, docs/TASK_MANAGER.md, docs/POLICY.md, docs/STORAGE.md.

## Aşama 2 — Native UI

- 2.1 PyWebView/EdgeChromium gerçek açılış, ES modülleri ve ui_ready köprüsü hazır.
- 2.2 İzinli ayarlar snapshot/save/read-back/yeniden açılış ve kontrollü kurtarma hazır.
- 2.3 Shutdown/restart, F11, varsayılan mor tema ve efekt başlangıç yolları hazır.
- 2.4 Not/skill/rutin gibi koleksiyonların generic save ile yanlış backend yazımına
  dönüşmemesi ve desteklenmeyen olayın reddi doğrulandı.
- Kaynak: docs/STAGE2_NATIVE.md; bugünkü native rapor ayrı deney kanıtıdır.

## Aşama 3 — Notlar

- 3.1 Onaylı ilk aktarım, sabit ID ve backend tek otoritesi hazır.
- 3.2 Ekleme/listeleme/düzenleme/tamamlama/silme ve doğrulanmış UI yenileme hazır.
- 3.3 Yedek import/export, hata/iptal/geç yanıt ve yeniden açılış hazır.
- Modelden CRUD, tarihe/kısmi metne göre hedef seçimi Aşama 5'te eklenmiştir.
- Kaynak: docs/STAGE3_NOTES.md ve docs/STAGE3_VISIBLE_ACCEPTANCE.md.

## Aşama 4 — İlk uygulama plugini

- 4.1 apps.catalog, sabit Notepad kimliği ve yetki sınırı hazır.
- 4.2 apps.status ve gerçek süreç/pencere gözlemi hazır.
- 4.3 apps.open ve açma sonrası kanıt hazır.
- 4.4 Tekrar/iptal/başlatma hatası/belirsizlik kabulü hazır.
- 4.5 Gerçek Windows Notepad açma kabulü önceki raporlarda mevcut.
- Kaynak: docs/STAGE4_APPS.md. Bugünkü denetimde gerçek Notepad yeniden açılmadı.

## Aşama 5 — Uygulanan temel dilimler

| Kimlik | Dilim | Durum ve sınır |
|---|---|---|
| 5.1 | REST → ModelTools → registry/policy/TaskManager | Temel kabul tamam; REST ana masaüstü ürün yolu değil |
| 5.2 | API anahtarı ve Windows credential saklama | Temel kabul tamam; üretim anahtarı denetimde okunmadı |
| 5.3 | API Live kataloğu, tek Live sahibi, metin ve PCM çıkışı | Uygulandı; mevcut giriş/uyku bulguları ayrıca açık |
| 5.4 | REST/Live Stop, gerçek bitiş ve geç yanıt koruması | Temel kabul ve bugünkü regresyon geçti |
| 5.5 | GoAway ve session resumption | Sentetik/native kanıt var; gerçek sağlayıcı GoAway kabulü açık |
| 5.6 | Modelden not CRUD, tarih, tekil kısmi hedef ve ID doğrulama | Kullanıcı kabulü mevcut; toplu silme gibi henüz açılmamış kapsam eklenmiş sayılmaz |
| 5.7 | Mikrofon/cihaz/VAD, transkript, barge-in, dil/kişisel talimat | Temel dilimler çalışıyor; ses yaşam döngüsü yeniden açıldı |
| 5.8 | Sınırlı RAM sohbet hafızası ve New Chat | Uygulandı ve kabul kaydı var; kalıcı kullanıcı hafızası değildir |
| 5.9 | Tek seferlik uyku ve yerel wake | Uygulandı fakat **açık bulgular nedeniyle kararlı kabul edilmedi** |
| 5.10 | Stay asleep ile normal idle timer'ın ayrılması | Kod/sentetik kanıt var; normal timer kullanıcıda çalışıyor, birleşik uyku kabulü açık |
| 5.11 | 23 Ekim genel denetimi ve yeniden üretimler | Tamamlandı: docs/STAGE5_SLEEP_AUDIT.md; denetim düzeltme değildir |

## Aşama 5 — Şimdiki düzeltme sırası

Bu liste önceki parçalı uyku planlarının güncel karşılığıdır. Somut açıklar
[denetim raporunda](docs/STAGE5_SLEEP_AUDIT.md) numaralıdır.

| Kimlik | Yapılacak iş | Kabul koşulu | Durum |
|---|---|---|---|
| 5.F1 | Tek tur ses/giriş bitişi ve UI/host uyku durumunu tutarlı yap (U01, U02, U05) | Bitmiş transkript sonrası yeni ortam PCM'i eski tura gitmez; backend reddinde UI uyuyor demez; yalnız wake ile görev birbirine karışmaz; Stop/unknown korunur | **Sıradaki; açık** |
| 5.F2 | Idle mikrofon canlılığı ve 25 s Thinking'i ayrı teşhis et (U04) | AudioContext suspend/cihaz/uyku turu sonrası gerçek kaynak durumu anlaşılır; güvenli toparlanma ve eski kaynak koruması test edilir; 25 s için olay zamanlarıyla neden kanıtlanır | Açık |
| 5.F3 | Türkçe/İngilizce uyku niyetini gerçek host sonucuna bağla (U03) | “uyku moduna gir” ve “kalıcı olarak uyku moduna gir” gibi doğal varyantlar; soru/olumsuz/alıntı/ek işte yanlış geçiş yok; yalnız model onayı başarı sayılmaz | Açık |
| 5.F4 | Wake telaffuzu ve yanlış uyanma | Vex/Rex/X benzeri adaylar gerçek yerel motor ve negatif seslerle değerlendirilir; gelişigüzel X sesi kesin wake sayılmaz | Planlandı |
| 5.F5 | Birleşik uzun kullanım ve fiziksel kabul | Normal ve stay-asleep döngüleri, Mic Off, Stop, hata, yeni sohbet, disconnect/restart; farklı bekleme süreleri; gerçek hesap/donanım ayrımı | Açık |
| 5.F6 | Kapanış bakımı ve belgeler | UI temizliği/debloat ölçülü; eski planlar güncel gibi görünmez; 256 görev sınırı ve restart replay sınırı için karar; README kapsamı doğru | Başladı; kapanmadı |

5.F1–5.F4 tamamlanmadan yeni entegrasyon eklenmez. Hatalı sözleşmenin etrafına
bir if/kelime daha eklemek kalıcı çözüm sayılmaz. Her düzeltmenin eski hatayı
başarısız gösteren hedefli testi olmalıdır.

### Bugünkü kanıt — 23 Ekim

- 843 pytest geçti; 7 JavaScript süiti geçti; app genelinde Pyright 0 hata/uyarı.
- Native 10/10 senaryo geçti: docs/stage5-general-audit-native.json.
- Buna rağmen 5 bağımsız runtime açığı sentetik deneyde doğrulandı. Bu deneyler
  eski hatanın varlığını ispatlar; kabul testi geçişi değildir.
- Deney betikleri ve ayrıntılı sonuçlar docs/STAGE5_SLEEP_AUDIT.md içinde.
- Ücretli/gerçek API, fiziksel mikrofon ve kullanıcı notları kullanılmadı.
- Bu tur uygulama kodu değiştirilmedi; belgeler/AGENTS kuralı güncellendi.
  Kullanıcı bug bildirdiği için önceki bekleyen kodlar commit edilmedi.

## Aşama 6 — Kalıcı hafıza ve yeni L0 entegrasyonları

Tamamı planlıdır; alt adımlar uygulanırken yeniden daraltılacaktır.

- 6.1 Kullanıcının çıkardığı bilgileri görme/düzeltme/unutma ve açık hafıza
  tercihi, Personalization altında. Şu anki pMem alanı çalışan hafıza değildir.
- 6.2 Telemetri, sayaç, uygulama ve medya işlemlerini tek tek modele bağlama.
- 6.3 Dosya okuma; sonra kontrollü değiştirme ve doğrulama.
- 6.4 Hava durumu/konum izni ve web arama.
- 6.5 Google Drive, Calendar ve mail: OAuth, kapsam, yenileme ve tek işlemle kabul.
- 6.6 Telegram alma/gönderme ve Discord botu: kullanıcı/kanal/hedef yetkisi,
  teslim kanıtı ve belirsiz gönderimde tekrar etmeme.
- 6.7 Harici yan etkilerden önce kalıcı çağrı kaydı ve restart dedup kararını ver.

## Aşama 7 — GUI resolver ve skill yürütme

- 7.1 Tek uygulamada L3 UIA hedefleme ve yeniden doğrulama.
- 7.2 Doğrulanmış akışı L1 reçete/hafıza ile tekrar kullanma.
- 7.3 Tarayıcı L2 DOM; gerektiğinde L4 vision/OCR ve bütçe.
- 7.4 Skill JSON adımlarını aynı registry/policy/TaskManager hattından yürütme.
- 7.5 DPI/pencere değişimi, eski hedef, izin reddi ve belirsiz yan etki kabulü.

## Aşama 8 — Rutinler, servisler ve dağıtım

- 8.1 Tek backend scheduler sahibi; mevcut UI timer'ından açık sahiplik devri.
- 8.2 Rutin CRUD, tetikleme ID'si, çift çalıştırma ve bildirim/sonuç ayrımı.
- 8.3 Kullanıcının açtığı arka plan servisleri; log maskeleme/döndürme.
- 8.4 Veri şeması geçişi, çökme kurtarma, normal kapanış ve güncelleme.
- 8.5 Paketlenmiş native kurulum, model/üçüncü taraf lisansları ve temiz dağıtım.
