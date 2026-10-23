# TaskVex — 23 Ekim 2026 genel denetim ve uyku/ses bulguları

## Güncel yeniden açılış — 5.R1

Kullanıcı Stopped→Idle, gecikme ve sesli onay eksikliği bildirdi. Yeni
[inceleme](STAGE5_SLEEP_STABILITY_REVIEW.md) iki başarısız yeniden üretim
ile EOS ve yanıt-sonrası gürültü tabanı açıklarını doğruladı. Yerel onay,
sınırlı terminal sonrası capture toparlanması ve wake motoru cache'i eklendi.
920 pytest/7 JS/native ve yapay gerçek KWS kanıtı var; fiziksel/sağlayıcı
kabulü yoktur. F4 önüne R1 kabulü alındı, bütün gecikmeler kapatılmadı.

## Önceki denetim sonrası durum — 5.F3

U03 için ortak parser gir/kalıcı gir/nezaket/boşluk ve EN varyantlarıyla
düzeltildi; soruyu komuta dönüştüren soru işareti silme de kaldırıldı.
916 pytest/yedi JS ve tip kontrolü geçti; gerçek mikrofon/API kabulü açık.
F2 fiziksel uyanış/25 s bildirimi ve F4 telaffuz açık kalır. Son kanıt ve
native sonucu STAGE5_MODEL.md / ../aşamalar.md içindedir.

## Önceki güncel durum — 5.F2

U04'ün sonradan askıya alınmış AudioContext açığı aynı kaynakta sınırlı
resume/hata temizliğiyle düzeltildi. 853 pytest/yedi JS ve tip kontrolü geçti.
Fiziksel uyanış/komut alamama bildirimi hâlâ açık; 25 s için içeriksiz
gönderim/olay ölçümleri eklendi, gerçek örneğin nedeni henüz kanıtlanmadı.
Son kanıt ve native sonucu STAGE5_MODEL.md / ../aşamalar.md içindedir.

## Önceki güncel durum — 5.F1

Aşağıdaki deneyler denetim anındaki kodu gösterir; tarihsel kanıttır. U01,
U02 ve U05 için 5.F1 kod/test düzeltmesi uygulandı ve manuel kabul bekler.
850 pytest/7 JS/10 native + ek chat kontrolü geçti. Ayrıntı STAGE5_MODEL.md,
güncel durum ../aşamalar.md içindedir. U03 (niyet), U04 (ses canlılığı) ve
gerçek 25 s beklemenin neden zinciri açıktır. Eski deney betiklerindeki
"bug var" assert'leri güncel kabul testleri değildir.

TaskVex, tek yerel kullanıcının Windows masaüstünde UI/Live ses yoluyla
konuştuğu ve sınırlı araçları registry/policy/TaskManager üzerinden çalıştırdığı
bir uygulamadır. Beklenen yük bir masaüstü oturumu, tek aktif model turu ve tek
mikrofon kaynağıdır. İnceleme mevcut çalışma ağacını kapsar; Mark referans
reposu, yedek checkout'lar ve henüz uygulanmamış L1–L4 entegrasyonları ürün
kodu sayılmadı. Bugünkü işlem denetimdir; uygulama kodu değiştirilmedi.

## Sonuç

**Uyku/ses katmanı kararlı değil.** Aşağıdaki beş runtime bulgusu kaynak ve
sentetik deneyle doğrulandı. UI/host durum ayrışması, konuşma sınırı ve ses
kaynağı canlılığı çözülmeden kelime listesine bir ifade daha eklemek yeterli
olmaz. Kaynak/kuyruk/araç sahipliği temeli ve not veri hattı için bugünkü
regresyonlarda yeni bir başarısızlık bulunmadı; bu hatasızlık garantisi değildir.

## Önce düzeltilmesi gerekenler

### U01 — Bitmiş transkriptten sonra eski mikrofon turu PCM almaya devam ediyor [P1]

- **Nedir:** `input_transcription.finished=true` kullanıcının o konuşmasının
  transkript bitişidir; `live_probe.py:157` bunu metne ekliyor. Giriş kapatma
  kapısı `live_probe.py:204` gerçek model çıktısı/araç/tur bitişini bekliyor.
- **Problem / kanıt:** Sentetik socket tam ve bitmiş transkript gönderip
  bekletildi. Gerçek LiveInput hâlâ `closed=False`; sonraki 100 ms PCM'i kabul
  etti (`later_pcm_accepted=true`). Model düşünürken arkadaş konuşması eski
  tura karışabilir; ayrı barge-in'i kapatmak bu eski kaynağı kapatmıyor.
- **En küçük tamam düzeltme:** Kesin giriş sonunu, kullanıcıya cevap ve görev
  bitişinden ayır. Sağlayıcı transkript/EOS olaylarını tek giriş sahibiyle
  eşleştir; aktif aracı veya yanıtı Stop etmeden eski PCM kabulünü sonlandır.
- **Bırakırsak:** Stay-asleep'in arka plan konuşmasını izole etme amacı eksik
  kalır. Bu, gerçek hesaptaki 25 s beklemenin kanıtlanmış tek nedeni değildir.

### U02 — Backend uyku isteğini reddederken UI uyuyor görünebiliyor [P1]

- **Nedir:** `ui/js/app.js:461` enterSleep önce `sleeping=true`, SLEEPING ve Wake
  düğmesini ayarlıyor. `app/bridge/webview_bridge.py:243` ise reset_live kabul
  etmezse gerçek sleeping durumunu değiştirmeden ret döndürebiliyor.
- **Problem / kanıt:** Gerçek host'ta reset_live reddi → `ok=false`,
  `backend_sleeping=false`. Gerçek UI fonksiyonlarında aynı ret →
  `ui_sleeping=true`, düğme `Wake`. Ret ayrıca `app.js:408` tarafından her
  durumda motor eksikliği koduna indirgeniyor; asıl neden kayboluyor.
- **En küçük tamam düzeltme:** Hazırlık/bekleme durumunu gerçek uyku kabulünden
  ayır; ret ve belirsizliği koru. Host uyku kabulüyle yerel KWS hazırlığının
  ayrı sonuçları olsun; eski kabul yeni moda taşınmasın.
- **Bırakırsak:** Kullanıcı uyuduğunu düşünürken iki taraf farklı durumda
  kalır; sonraki Wake/Stop/yeniden dinleme belirtileri yanıltıcı olur.

### U03 — Uyku niyeti dar liste ve iç boşluklara duyarlı [P1]

- **Nedir:** `app/session/sleep_intent.py:10,20,30` tam metin eşleşmesi yapar.
  Başlangıç hitabı opsiyoneldir; Vex şartı yoktur. Fakat genel niyet algısı yoktur.
- **Problem / kanıt:** Kullanıcının `Vex uyku moduna gir` ve `Vex kalıcı olarak
  uyku moduna gir` örnekleri `None`. `uyku moduna geç` → once iken iki iç
  boşlukla `uyku moduna  geç` → None. `enter sleep mode` → once; yani İngilizce
  liste vardır ama sınırsız anlatım desteği değildir.
- **En küçük tamam düzeltme:** Yüzey normalizasyonu ve niyet/host sonucu
  sözleşmesini birlikte düzelt. Modelin niyeti anlaması geçiş yetkisi/success
  sayılmasın; soru, olumsuzluk, alıntı ve birleşik istekte yanlış uyuma olmasın.
- **Bırakırsak:** Model “anlaşıldı” diyebilir fakat host uyumaz. Sadece “gir”
  eklemek sonraki benzer varyantı çözmez. Bu tur parser değiştirilmedi.

### U04 — Askıya alınan AudioContext aktif mikrofon sanılabiliyor [P1]

- **Nedir:** `ui/js/live_mic.js:28–48` ses bağlamını başta doğruluyor, sonra
  track.onended/worklet hatasını dinliyor. AudioContext statechange ele alınmıyor.
- **Problem / kanıt:** Gerçek liveMic modülü sentetik bir çalışan bağlamla
  hazırlandı; bağlam suspended yapıldı. `mic_active=true`, hata sayısı 0 ve
  state handler yok. `listenAutomatically` mevcut active kaynağı görüp yeni
  hazırlık yapmaz. Askıda PCM akmadığı halde On/Idle bekleyebilir.
- **En küçük tamam düzeltme:** Ses bağlamı ve track canlılığını tek kaynak
  sahibinde gözle; iptal edilen kaynağı canlandırmadan güvenli durumu bildir
  ve sınırlı toparlanmayı uygula. Off/unknown/Disconnect atlanmamalı.
- **Bırakırsak:** Kaynak susması görünmez kalabilir. Kullanıcının her Idle
  kilitlenmesinin kesin nedeni bu değildir; fiziksel olay kaydı hâlâ gerekir.

### U05 — Wake-only ile görev girişi aynı akış sayılıyor [P2]

- **Nedir:** `pcm_worklet.js:9–12,74–81` wake devrinde konuşuluyor varsayarak
  700 ms sessizlikte EOS verip işçiyi pasifleştiriyor. `app.js` wake kabulü
  sonrası doğrudan `sendText('', {stream:true})` ile model turu açıyor.
- **Problem / kanıt:** Wake → 700 ms sessizlik → bir speechEnd; ardından
  konuşma örnekleri verildiğinde mesaj sayısı artmadı. “Vex” deyip kısa
  duraklayan kişi, görevini sonraki parçaya bırakabilir. Kalıcı modda wake'e
  verilen bir selamın bitişi, henüz söylenmeyen görev bitmiş gibi uyutabilir.
- **En küçük tamam düzeltme:** Uyanma kabulü, adresli görev başlangıcı, giriş
  sonu ve yanıt/görev bitişini ayır. İlk sözcüğü görevin kendisi sayma; kısa
  wake ile aynı cümledeki gerçek isteği ve sonradan gelen isteği ayrı test et.
- **Bırakırsak:** Kısa wake'in ardından sessiz model bekleme veya isteği
  kaçırma görülebilir. Gerçek sağlayıcının 25 s beklemesine ilişkin neden
  zinciri burada tamamlanmış değildir; sağlayıcı/cihaz testi yapılmadı.

## Dokümantasyonda düzeltilenler

### D01 — README uygulanmayan güvenlik ve yanlış aşama sırası söylüyordu [P2, belge düzeltildi]

PolicyEngine gerçekte bool allow/deny iken README otomatik tainted veri ve
CONFIRM yükseltmesini uygulanmış gibi anlatıyordu. Kodda bu mekanizma yok;
L1–L4 ve dış veri entegrasyonları da henüz yok. “Zero race conditions” gibi
koşulsuz ifade ve Stage 8'i yalnız L2/L4 sayan yol haritası düzeltildi.
Yeni kaynak `aşamalar.md`; Stage 7 GUI/skill, Stage 8 rutin/servis/paketlemedir.
Bu düzeltme güvenlik özelliği uygulamaz; mevcut sınırı doğru açıklar.

## Test kanıtı ve kapsama sınırı

- 843 pytest: PASS (bugünkü tekrar, önceki rapor sayısı kopyalanmadı).
- 7 JS süiti: PASS. Wake, kaynak, transkript, ses ve not tarihini kapsar.
- Native tüm 10 süreç/senaryo: PASS. Rapor: `stage5-general-audit-native.json`.
  Açılış/yeniden açılış, notlar, persist/import/export, export iptali,
  credential geçici profili, chat, bozuk/şeması bozuk/ileri sürüm dosya dahil.
- `pyright app`: 0 hata / 0 uyarı. Bu tip kontrolüdür, davranış garantisi değildir.
- Ayrı deneyler U01–U05'i doğruladı. Mevcut testlerin geçmesi bu açıkları
  kapatmıyor; bu sınır durumları düzeltme testlerine dönüştürülmelidir.
- Makinece okunur sonuç: `stage5-general-audit.json`. Bu dosya deney/test
  sonuçlarını içerir; ayar, kullanıcı verisi veya credential yedeği değildir.

Deney betikleri bu çalışmanın çıktılarındadır; uygulama koduna eklenmediler:

```powershell
cd C:\Users\batue\OneDrive\Desktop\TaskVex\v1
.\.venv\Scripts\python.exe C:\Users\batue\Documents\Codex\2026-10-20\mi\outputs\taskvex-audit-20261023.py
node C:\Users\batue\Documents\Codex\2026-10-20\mi\outputs\taskvex-audit-20261023.mjs
```

## İncelenen ve incelenmeyen kapsam

Entry point, kurulum/dependency manifest'i, native köprü, ayar/credential
sınırı, core kurulumu, registry/policy/TaskManager, not mutasyon/doğrulama ve
model hedef koruması; REST retry/Stop, Live sahibi/PCM/Stop/resume ve UI'ın
ses/uyku/ayar yolları incelendi. UI skills/routines ve kaydetme/HTML üretimi
bağlantıları da gözden geçirildi; yer tutucular çalışan backend sayılmadı.
Her dosyanın her satırının bağımsız güvenlik denetimi veya tüm donanım,
kurulum ve kullanıcı davranışlarının kabulü yapıldığı iddia edilmez.

Fiziksel mikrofon/telaffuz, gerçek API/GoAway, hoparlör duyumu, üretim
credential'ı/notu, gerçek Notepad açma, paketlenmiş kurulum ve referans repo
bu tur denenmedi. 60 s wake stream yenileme, 256 toplam TaskManager kaydı ve
restart sonrası kalıcı dedup eksikliği belgelenmiş sınırlar olarak kaldı;
yeni, gizli bulgu veya bu tur çözülmüş özellik gibi sunulmadı.

Öncelik: önce giriş/uyku protokolü ve canlılık, sonra esnek niyet ve wake
kalibrasyonu, ardından birleşik fiziksel kabul. Kesin izleme sırası
`aşamalar.md` içindeki 5.F1–5.F6'dır. Genel framework veya yeni dependency
önerilmiyor; sahiplik/bitiş kapıları mevcut kodda düzeltilmeli.
