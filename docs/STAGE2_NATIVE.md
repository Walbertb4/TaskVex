# Aşama 2 — Plan, ilk native dilim ve elle test

Bu belge hazır HTML arayüzünü Windows uygulaması olarak çalıştırma adımlarını
açıklar. Aşama 2'nin işlevsel native adımları ve otomatik kabulü hazırdır.
Görünür pencere ve gerçek dosya diyaloğu kabulü de sonradan Computer Use ile
tamamlandı: [görünür kabul](STAGE3_VISIBLE_ACCEPTANCE.md). İnsan UX/ses testi değildir.
Core not araçlarının UI'a devri Aşama 3'te uygulandı; bu belgedeki ilk native
kabul tarihsel Aşama 2 sınırıdır. Güncel sahiplik, sekiz süreçli native kabul
sonucu [STAGE3_NOTES.md](STAGE3_NOTES.md), güncel 332 test ve katalog adımı
[STAGE4_APPS.md](STAGE4_APPS.md) içindedir.

## Uygulama sırası ve durum

| Sıra | İş | Durum / kabul ölçütü |
|---|---|---|
| 1 | Native host ve ES modüllerinin açılması | Hazır; app.main mevcut index.html'i PyWebView/EdgeChromium ile açıyor |
| 2 | ui_ready ve güvenli UI bildirimi | Hazır; gerçek native iki yönlü teslimat, idempotent hazır bildirimi, initApp dönüşü doğrulandı |
| 3 | Ayar dosyası ve başlangıç snapshot'ı | Tamamlandı; kayıt/yeniden yükleme, bozuk kayıt/onaylı onarım ve sürüm reddi doğrulandı |
| 4 | Salt okunur durum ve dürüst offline | Hazır; system.status ortak core hattından geçiyor; model yokken MODEL OFFLINE |
| 5 | Yaşam döngüsü ve hata deneyimi | X/Shutdown, F11, Restart app, arayüz reset ve always-on-top bağlı. Başlangıç uyarısı, Retry ve onaylı ayar onarımı hazır |
| 6 | Son kabul | Otomatik kabul geçti. Görünür pencere, gerçek export/import diyalogları, iptal ve restart sonradan Computer Use ile tamamlandı; görsel görünüm gözlendi, piksel eşitliği testi yapılmadı |

Yeni framework veya dinamik plugin sistemi eklenmedi. PyWebView 6.2.1 ve onun
taşıma/.NET bağımlılıkları kuruldu; pyproject ve geliştirme kilidi güncellendi.
Başlangıç kodu app/main.py, köprü app/bridge/webview_bridge.py içindedir.

## Hemen çalıştır

PowerShell aç ve şunları çalıştır:

```powershell
cd C:\Users\batue\OneDrive\Desktop\TaskVex\v1
.\.venv\Scripts\python.exe -m app.main
```

Bir TaskVex penceresi açılmalıdır. Venv'i Activate.ps1 ile etkinleştirmek gerekmez.
İlk kurulum başka bir bilgisayarda yapılıyorsa önce bu Python ortamına
`python -m pip install -r requirements-dev.lock.txt` uygulanmalıdır. Native motor
Windows Edge/WebView2 Runtime gerektirir; eski Internet Explorer motoruna düşülmez.

Gerçek ayarlarından ayrı test etmek istersen aynı PowerShell'de önce:

```powershell
$env:TASKVEX_HOME = Join-Path $env:TEMP 'TaskVex-manual-test'
.\.venv\Scripts\python.exe -m app.main
```

Bu dizin yeniden açma testinde aynı kalmalıdır. Normal veri dizinine dönmek için
uygulamayı kapattıktan sonra `Remove-Item Env:TASKVEX_HOME` çalıştır. Bu yalnız
ortam değişkenini kaldırır; test dosyalarını silmez.

## Elle kabul kontrolü

1. Pencere açılınca görünümün yerinde olduğunu, System altında işletim sisteminin
   göründüğünü ve Skill Log'da "Native bridge ready" yazdığını kontrol et.
2. MODEL OFFLINE beklenen durumdur. CPU/GPU/RAM yüzdelerinin `—` olması da
   beklenir; henüz kullanım yüzdesi ölçülmüyor. Boş model/ses listesi doğrudur.
3. Settings içinden tema rengini değiştir ve Save düğmesine bas. Profile içinden
   bir tercih metni yazıp Save profile'a bas. Açık Save düğmeleri Python kayıt
   onayını bekler; reddedilen kayıtta modal açık kalır ve log'da hata görünür.
4. Pencereyi sağ üst X ile kapat. Aynı komutla yeniden aç; tema ve profil geri
   gelmelidir. Terminalde uygulama sürecinin kapanması da bu kontrolün parçasıdır.
5. Yerel UI notu ekle ve yeniden aç; native profilin localStorage'ında korunmalı.
   Bu Aşama 1 notes.json'a aktarım değildir. Genel ayar kaydı not ekleme yapmaz.
6. Chat, kamera veya Google gibi desteklenmeyen backend işlemlerinde başarı
   bekleme; log'da not_implemented görünür. Skill/rutin tanımı yerel kalır;
   bunları native çalıştırma henüz bağlı değildir.

Normal kapanış için X veya Shutdown kullan; native Shutdown Restart ekranına
geçmez, uygulamayı kapatır. F11 tam ekrana geçer, tekrar F11 geri döner.
Settings > System içindeki Restart app worker/pencere kapanışından sonra yeni
uygulama süreci ister; aynı veri dizini ve debug tercihi korunur. Always on top
gerçek pencereye anlık uygulanır; Save ile kalıcı olur. Reset interface preferences
onay sonrası yalnız arayüz tercihlerini sıfırlar; not/skill/rutin, profil, cihaz
ve bağlantı tercihleri korunur. Reset sırasında hata varsa önceki veri silinmez.

Yeni/temiz profilde varsayılan tema mordur (#a78bfa); kayıtlı tema korunur.
Reactor boşta da 60 FPS hedefler. Native WebView2 autoplay ayarı açılış sesinin
tıklama beklemesini kaldırır; SFX tercihi kapalıysa ses çalmaz. Fiziksel hoparlör
çıkışı ayrıca dinlenerek doğrulanmadı.

Geliştirici araçları için `python -m app.main --debug` kullanılabilir. Açılan
console'da `await window.pywebview.api.event('system_status')` gerçek salt okunur
sonucu verir. Kaynak HTML'yi çift tıklamak native uygulamayı başlatmaz.

## Kayıt ve güven sınırları

Varsayılan veri dizini `%LOCALAPPDATA%\TaskVex`, açık TASKVEX_HOME varsa o dizindir:

- settings.json: tema, renkler, profil, layout, SFX, ses/cihaz/model tercihleri.
- webview/: bu uygulamaya ait native tarayıcı profili ve localStorage.
- notes.json: Aşama 1 core not aracı verisi; UI henüz bu dosyayı kullanmaz.

save içindeki notes/skills/routines ve top-level API anahtarı alanları backend
ayar kaydına alınmaz. İç alanlar da beyaz listelidir; ör. conn.apikey reddedilir.
Bu dosya credential kasası değildir; profilin serbest metnine sır yazılmamalı.
Bozuk ayar dosyası otomatik silinmez veya boş varsayılanla ezilmez; başlangıç
uyarısı görünür ve backend save reddedilir. Retry dosyayı değiştirmeden tekrar
dener. Back up and repair settings açık onay ister, asıl baytları benzersiz
settings.json.<kimlik>.corrupt dosyasına taşır ve geçerli alanları koruyarak
ayarları onarır. Bozuk JSON okunamıyorsa tercihler varsayılana döner; yerel UI
not/skill/rutin/profil ve core notes.json silinmez. Yedek silinmez.

Desteklenmeyen sürümde uyumlu uygulama kullanılması, erişim hatasında izinlerin
kontrolü istenir; bu iki durumda onarım düğmesi gizlidir ve dosya korunur.
Yedekleme/yazma hatası başarı sayılmaz. Onarım sonrası yeni dosya yazılamasa
bile oluşturulmuş asıl yedek tutulur. Pencere hiç açılamazsa terminal ve Windows
hata kutusu kurulum/WebView2/veri yolu için yönlendirir; otomatik reset yapılmaz.

ui_ready yalnız {version:'1.0'} kabul eder. Snapshot koleksiyonları içermez;
eksik alanları koruyan mevcut UI sözleşmesi yerel not/skill/rutinleri korur.
initApp/loadStore artık uygulama sonucunu boolean olarak geri döndürür.
Sabit izinli UI metotlarına yalnız JSON-serileştirilmiş argüman gönderilir.
Tek public Python metodu event'tir; ham eval veya doğrudan dosya API'si açılmaz.

Başarılı save yanıtı `{ok:true,completed:true,saved:true}` olur; dosya geri
okunarak doğrulanır. Hata/eksik onay başarı sayılmaz. Otomatik ayar kayıtları
bağımsız kopyalarla tek sıradan gönderilir; Save, Export ve Import onayı bekler.
Ayar/profil panellerinde kayıt durumu görünür. 12 saniyelik bekleme sınırı gerçek
isteği iptal etmez veya yeniden göndermez; geç yanıt daha yeni kaydı ezemez.
Import native ayar onayı gelmeden koleksiyonları değiştirmez. Yerel yazma daha
sonra başarısız olursa önceki UI/localStorage korunur, native ayarlar yeni olabilir;
bu kısmi durum log ve kayıt durumunda açık gösterilir. Depolar arası atomiklik
iddiası yoktur. Kaynak yedek dosyası silinmez.
onTop artık fiziksel pencereye de uygulanır; cihaz tercihini kaydetmek gerçek
mikrofon/kamera oturumu açmaz.

Şimdilik tek uygulama örneği çalıştır. Kalıcı localStorage için native HTTP
origin sabit tutulur (PyWebView'in varsayılan 42001 portu); port çakışması/çok
uygulama örneği desteği ayrıca ele alınacaktır. Yerel sunucu yalnız UI dizinini
sunar. Harici Google Fonts yüklenemezse mevcut sistem fontu fallback'i geçerlidir.

## Otomatik doğrulama

```powershell
.\.venv\Scripts\python.exe -m pytest -q -W error
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe tests/native_smoke.py
```

267 pytest kontrolü geçti; bağımlılık kontrolü temiz. Fake-window köprü testleri
gerçek native testin yerine sayılmadı. native_smoke.py gerçek EdgeChromium motorunu
üretim main() üzerinden yedi ayrı süreçte çalıştırdı: kaydet, yeniden aç,
kayıt/import/export, export iptali, bozuk JSON, geçersiz alan ve desteklenmeyen
sürüm. Pencereler testte hidden'dır;
kullanıcının profilini/verisini kullanmaz.

Kanıtlar: [gerçek native sonuçları](stage2-native-smoke.json),
[tarayıcı not/ayar regresyonu](stage2-browser-regression.json). Native testte
modüller, tek exposed event, offline durumu, gerçek OS bilgisi, snapshot no-echo,
Save düğmesi, yeniden açma, yerel not korunması, bozuk save reddi ve kayıt
hatasında modalın açık kalması geçti. Tarayıcı regresyonu fallback ve simüle
native taşıma için not ekleme/tamamlama/silme, no-echo ve açık Save'i doğruladı.

Son pencere güncellemesi: [gerçek mor tema/ses politikası/F11/Shutdown testi](stage2-window-controls.json).
F11, input odaklıyken ve basılı tuş tekrarında da kontrol edildi; Shutdown gerçek
pencere closed olayına ve worker kapanışına ulaştı. [Reactor zamanlama testi](reactor-60fps-check.json)
60/90/120/144 Hz saatlerinde saniyede 60 çizim ve boot sentezinde dört osilatör
üretildiğini doğruladı. Bu son test fiziksel FPS veya hoparlör ölçümü değildir.

[Yaşam döngüsü native testi](stage2-lifecycle-smoke.json): gerçek WinForms
TopMost değişimi ve yeniden açılışta yüklenmesi, reset'in not/skill/rutin/profil
ve bağlantıları koruması, reset yazma hatası ve native Restart kapanışı doğrulandı.
Restart süreç açma çağrısı testte yakalandı; ardıl gerçek native süreci test
çalıştırıcısı başlattı. Kullanıcının masaüstünde görünür otomatik respawn bu
testin parçası değildir. İlk native deneme GUI thread'i dışında TopMost setter'ına
takıldı; Invoke düzeltmesi sonrası tekrar geçti. Test timeout'u Windows venv
launcher'ı dahil kendi süreç ağacını temizleyecek şekilde düzeltildi.

[Başlangıç/kurtarma native kanıtı](stage2-startup-recovery.json): uyarı görünümü,
onarım iptalinde asıl dosyanın korunması, onayla birebir yedek, geçerli alanların
korunması ve no-echo hazır duruma dönüş geçti. Üç hata senaryosunda yerel notlar
korundu; onarımda skill/rutin/profil de karşılaştırıldı. Yeni sürümde onarım
gizlendi ve dosya değişmedi. Windows fatal başlangıç hata kutusu birim testinde
taklit edildi; gerçek kutu ile elle etkileşim denenmedi. İlk test çalıştırmasının
eksik test import'u düzeltildikten sonra tüm pytest kontrolleri geçti.

[Son kayıt/import/export native kabulü](stage2-persistence-smoke.json) ve
[tarayıcı yedek kontrolü](stage2-persistence-browser.json): kuyruk sırası ve
veri kopyaları, observer'ın gönderimi değiştirememesi, gerçek FileReader import,
native ret öncesi UI koruma, localStorage quota hatasında UI geri alma, kısmi
başarının bildirilmesi, 12 saniyelik timeout'ta tek gönderim ve gerçek WebView2
Blob export dosyası doğrulandı. Native dosya seçim sonucu testte taklit edilerek
yalnız geçici test dosyasına yazıldı; fiziksel diyalog elle kullanılmadı. Export
iptalinde eski dosya değişmedi. Aynı sayfada ikinci sentetik indirme denemesi
beklediği için iptal testi ayrı native açılışa ayrıldı; bu, fiziksel art arda
tıklamaların elle doğrulandığı anlamına gelmez.

Tekrar deneme tarifi (görünür tur artık tamam): Settings > System > Export ile dosya seçip kaydet; aynı dosyayı
Import ile seç. Kayıt durumu başarıyı doğrulamalı ve not/skill/rutin içeriği geri
gelmelidir. Export'ta Cancel seçerek dosya üretilmediğini de kontrol et. Testi
izole TASKVEX_HOME ile yapmak gerçek verinin üstüne yedek uygulamayı önler.

Bu tarihsel hidden turda görünür pencere ve diyalog denenmedi; sonradan görünür
kabul ayrıca tamamlandı. Piksel karşılaştırması, gerçek kamera/ses, Google,
model ve donanım kontrolü denenmedi. Native test çalıştırıcısında Windows console kodlaması
nedeniyle ilk rapor yazdırma hatası düzeltildi; tekrar çalıştırma başarıyla bitti.

Teknik başvuru: [PyWebView API](https://pywebview.flowrl.com/api/) ve
[Windows motoru](https://pywebview.flowrl.com/guide/web_engine). Yerel HTTP,
storage_path/private_mode ve Edge Runtime seçimleri bu API'lere dayanır.
Ses için süreç içi autoplay argümanı: [WebView2 browser flags](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/webview-features-flags).
