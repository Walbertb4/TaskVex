# Aşama 4 — İlk uygulama plugini

Bu belge TaskVex'in not araçlarından gerçek bir Windows uygulamasına nasıl
genişleyeceğini anlatır. İlk hedef yalnız Not Defteri'dir. Plugin ayrı bir
görev sistemi değildir; açık kayıtlı araçlar aynı registry/policy/TaskManager
hattından çalışır. Henüz model veya yeni bir UI paneli gerekmiyor.

## Adım adım plan ve kabul

| Adım | Yapılacak iş | Bittiğini nasıl anlayacağız? | Durum |
|---|---|---|---|
| 1 — Katalog ve kimlik | Parametresiz apps.catalog; sabit notepad kimliği ve açık apps.read izni | Gerçek core hattı yalnız izinli katalog bilgisini döndürür; komut/yol almaz; dosya yazmaz | Tamamlandı |
| 2 — Windows durum gözlemi | apps.status({app_id:"notepad"}); güvenilir Windows adaptörüyle süreç ve pencere durumunu gözle | Kapalı/açık/gözlemlenemeyen durumlar ayrılır; pencere başlığı tek başına kimlik sayılmaz | Tamamlandı; gerçek Windows kapalı/açık gözlemi geçti |
| 3 — Doğrulanmış açma | apps.open({app_id:"notepad"}); host'un seçtiği desteklenen başlatma yöntemi | Başlatma sonrası hedef yeniden gözlenir; başlatma kabulü tek başına başarı değildir | Tamamlandı; gerçek kapalıdan açma geçti |
| 4 — Hata, tekrar ve iptal | Registry/policy, mevcut açık uygulama, başlatma hatası, gecikme, iptal, timeout ve replay senaryoları | Belirsizlikte ikinci süreç otomatik açılmaz; desteklenmeyen hedefe fallback yoktur | Kontrollü testlerle tamamlandı |
| 5 — Gerçek Windows kabulü | İzole denemede core üzerinden Not Defteri aç/status; kapat/aç ve tekrar çağır | Kanıtlanan süreç/pencere seviyesi raporlanır; test yalnız sahip olduğu boş pencereyi temizler | Tamamlandı; kullanıcı tüm pencereleri kapatarak iki gerçek açma turunu doğruladı; iki rapor kontrol edildi |

İkinci adımın açmadan önce gelmesi bilinçlidir: hedefin nasıl gözleneceğini
bilmeden "açıldı" dememeliyiz. Modern Not Defteri'nin başlatıcı süreci ile
gerçek pencere sahibi farklı olabilir; Windows adaptörü uygulandığında kurulu
sürüm gerçek makinede incelendi; modern Microsoft.WindowsNotepad paketinin
başlatıcı ve pencere sahibi süreçleri farklı olabildi. Gözlem bunları ayırır.

## İlk adımın çalışan sözleşmesi

`app/tools/local/apps.py` yerleşik izinli kataloğu tutar. Bugünkü kayıt:
`notepad -> Notepad`. `create_core()` parametresiz apps.catalog aracını kaydeder.
İstek, diğer araçlar gibi source=desktop ve güvenilir host'un principal'ını
taşır. Araç `apps.read` ister; yeni yetki not okuma/yazma veya uygulama açma
yetkisi değildir. apps.status da aynı apps.read yetkisiyle kaydedildi;
apps.open ayrıca apps.launch yetkisi ister; yalnız apps.read açmaya yetmez.

```python
from app.bootstrap import create_core
from app.core.contracts import ToolRequest

with create_core() as core:
    task = core.submit(ToolRequest(
        request_id="apps-catalog-1", source="desktop", principal="local-user",
        tool="apps.catalog", arguments={},
    ))
    result = core.wait(task.task_id, timeout=3)
    print(result.result.to_dict())
```

Başarılı data: `{"apps":[{"id":"notepad","name":"Notepad"}]}`.
Kanıt: `{"source":"builtin_allowlist"}`. verified=True yalnız bu katalog
okumasının doğrulandığı anlamındadır. "Not Defteri kurulu", "çalışıyor" veya
"pencere hazır" anlamına gelmez. Liste her çağrıda yenidir; dışarıdaki sonuç
değişikliği kataloğu değiştiremez. Açılışta uygulama taraması/başlatma yapılmaz.

## İkinci adım — Durum gözlemi sözleşmesi

`apps.status` yalnız `{"app_id":"notepad"}` alır. Registry parametreleri,
policy kullanıcı/kaynak/apps.read iznini kontrol eder. apps.py ortak araç
sonucunu, windows_apps.py dar Win32 gözlemini yönetir. Yeni bağımlılık yoktur;
ctypes standart kütüphanesi kullanılır. Core kurulurken Windows DLL'si yüklenmez.

Sonuç data alanları:

| Alan | Anlamı |
|---|---|
| app_id | Sabit notepad kimliği |
| running | Doğrulanmış süreç varsa true; tam gözlemde yoksa false; eksik negatif gözlemde null |
| visible_window | Doğrulanmış süreçte WS_VISIBLE üst seviye pencere varsa true; tam gözlemde yoksa false; eksik negatif gözlemde null |
| processes | pid, identity ve created (Win32 oluşum zamanı metni) içeren doğrulanmış süreçler |
| windows | hwnd, pid, minimized içeren gözlenen pencereler |
| complete | Gözlem tamamlandı mı? |
| observed_at | UTC anlık gözlem zamanı |

Tam kapalı gözlem de SUCCEEDED/verified=True'dır: sorgunun başarıyla
tamamlandığı anlamına gelir; uygulama açık demek değildir. Kısmi tarama
FAILED/observation_incomplete döndürür, data içindeki pozitif bulgular kalabilir.
Salt okunur hata UNKNOWN ile manager'ı durdurmaz. Native API/platform
kullanılamazsa data uydurulmaz; FAILED/observation_unavailable veya
platform_unsupported gelir. İptal süreç/pencere taraması arasında gözlenir.

Kimlik denetimi: yalnız geçerli Windows oturumundaki notepad.exe adaylarına
PROCESS_QUERY_LIMITED_INFORMATION ve sıfır süreli yaşam kontrolü için SYNCHRONIZE erişimi istenir. İşletim sisteminin paket
ailesi Microsoft.WindowsNotepad_8wekyb3d8bbwe ve image adı Notepad.exe olmalı;
klasik sürüm ise Windows'un bildirdiği dizindeki izinli sistem yollarından
birinde olmalıdır. Kullanıcı dizinindeki aynı adlı EXE kabul edilmez. Başlık,
belge içeriği veya executable yolu sonuç/log payload'ına konmaz. Süreç başlık
eşleşmesi değil OS kimliğiyle değerlendirilir; antivirüs/signature audit'i değildir.

Pencereler EnumWindows ve PID eşlemesiyle okunur. Sonrasında süreç kimliği ve
oluşum zamanı tekrar karşılaştırılır; WaitForSingleObject(handle,0) ile süreç sonlanmışsa canlı sayılmaz; PID yeniden kullanılmışsa eski HWND
sonuçtan çıkar ve gözlem eksik olur. created sayısı JS tam sayı sınırını
aşabileceği için metin taşınır. Bütün açılan process/snapshot handle'ları
finally ile kapatılır. Callback istisnası C sınırından dışarı kaçırılmaz.

WS_VISIBLE gerçek ön planda/etkileşime hazır garantisi değildir; küçültülmüş
veya başka sanal masaüstündeki pencere bu bayrağı taşıyabilir. Başka Windows
oturumları dışlanır, pencereler geçerli desktop'ta gözlenir. Bu sonuç bir anlık
görüntüdür; sonraki açma/GUI eylemi öncesinde yeniden kontrol edilmelidir.

## Sonraki adımların sınırları

- app_id yalnız yerleşik katalogdan seçilecek; kullanıcı/model executable,
  shell, komut satırı veya keyfi argüman veremeyecek. Belge açma bu ilk dilimde yok.
- Süreç gözlemi ile görünür pencere gözlemi ayrı kanıtlar olacak. Başlık
  eşleşmesi başka bir uygulamayı Not Defteri saymaya yetmeyecek. PID/HWND gibi
  kimlikler gözlem anına aittir; eski sonucu kalıcı canlı durum diye kullanmayız.
- Zaten doğrulanmış pencere varsa yeni başlatma yapılmaz. Süreç var/pencere
  yoksa mevcut açılış beklenir. Başlatma sonrası timeout, "hiç açılmadı"
  değildir; otomatik ikinci açma yapılmaz.
- Yeni bağımlılık veya plugin tarama framework'ü ilk adıma eklenmedi. Önce
  standart Windows/Python imkânlarıyla gereken dar adaptör uygulanacak.
- İlk plugin kabulü test/komut çağrısı üzerinden yapılabilir. UI/model bağlama
  bu araçların üstündeki ayrı giriş işidir; bugünkü native bridge genel araç
  yürütme API'sine genişletilmedi.

## Test sonucu — 21 Ekim 2026

`.\.venv\Scripts\python.exe -m pytest -q -W error`: **396 test geçti**.
Önceki durum gözlemi dilimindeki apps/Win32/policy süiti 77 testti.
test_apps.py ortak core, izin,
parametre, hata ve iptali; test_windows_apps.py paket/sistem yolu kimliğini,
handle kapatmayı, erişim reddini, başka oturumu, PID yeniden kullanımını ve
C callback hata/iptalini doğrular. Düşük seviye ABI testleri Windows dışı
platformda atlanır; diğer platformlar gerçekten test edildi denmez.

[Gerçek Windows sonucu](stage4-status-windows.json): uygulama açılmadan ilk
core sorgusu running=false/visible_window=false döndürdü. Kontrol için boş
TaskVex-Status-Test.txt dosyasıyla Not Defteri dışarıdan açıldı; apps.status
Microsoft paket kimliğiyle süreçleri ve pencere sahibini doğru eşledi. Üründe
Bu tarihsel status kabulünde başlatma yalnız test kurulumuydu; aşağıdaki yeni
apps.open kabulü ise gerçekten ürün aracı üzerinden çalıştırıldı.
İlk kapalı çağrının terminal çıktısı da raporda saklandı.

Not Defteri eski oturum sekmelerini geri getirdi. İçerik değiştirilmedi; yalnız
test dosyası sekmesi kapatıldı, geri gelen kullanıcı sekmelerine dokunulmadı.
Test sonrası pencereyi kapatmaya yönelik girişim, Computer Use kullanıcı girdisi
algıladığı için uygulanmadı; rapordaki after_test_tab_close hâlâ açık durumu
gösterir. Bu sonuç kapalı test gibi sayılmadı. Gerçek minimize/başka oturum ve
klasik Windows Notepad testi yapılmadı; bunlar kontrollü API testleriyle sınırlı.
Katalog desteği bilgisayardaki kurulum tespiti değildir; apps.status da kurulu
ama kapalı uygulamayı kurulu olmayan uygulamadan ayırt etmeyi garanti etmez.

Teknik kaynaklar: Microsoft'un [süreç snapshot'ı](https://learn.microsoft.com/en-us/windows/win32/api/tlhelp32/nf-tlhelp32-createtoolhelp32snapshot),
[image sorgusu](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-queryfullprocessimagenamew),
[paket ailesi](https://learn.microsoft.com/en-us/windows/win32/api/appmodel/nf-appmodel-getpackagefamilyname),
[pencere gözlemi](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-enumwindows)
ve [oluşum zamanı](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getprocesstimes)
ve [yaşam kontrolü](https://learn.microsoft.com/en-us/windows/win32/api/synchapi/nf-synchapi-waitforsingleobject) sözleşmeleri uygulama sırasında kontrol edildi.

## Üçüncü adım — Doğrulanmış açma

apps.open yalnız `{app_id:"notepad"}` alır; status ile aynı dar giriş şeması
kullanılır. ToolSpec apps.read + apps.launch ve apps.notepad kaynağını bildirir.
Policy ikisini de ister, güvenilir yerel host açıkça verir. Yeni dispatcher,
plugin taraması, UI paneli veya bağımlılık eklenmedi.

Önce apps.status iş mantığıyla tam gözlem alınır. Eksik/hatalı gözlemde açma
denenmez. Doğrulanmış pencere varsa success/already_open=true ve
launch_requested=false gelir. Yalnız süreç varsa 5 saniyeye kadar pencere
beklenir; ikinci başlatma yapılmaz. Başlangıçta hiç süreç olmadığı doğrulanırsa
GetSystemDirectoryW ile sabit notepad.exe yolu çözülür; PATH/env/cwd'den hedef
aranmaz, kullanıcı/model dosya/komut/argüman gönderemez.

Windows'a başlatma os.startfile ile bir kez iletilir. Bu ShellExecute temelli
standart kütüphane yöntemidir; cmd/PowerShell komutu çalıştırılmaz. startfile
dönüşü tamamlanma kanıtı değildir. Uygulamanın çıkışını bekleyen/öldüren bir
Popen sahibi yaratılmaz; harici uygulama TaskVex'ten uzun yaşayabilir. Ardından
aynı OS paket/sistem yolu kimliği ve pencere gözlemiyle hedef doğrulanır.

Başarı data'sı durum snapshot'ına ek olarak launch_requested ve already_open
taşır. Kanıtta window_observed=true bulunur. Garanti yalnız doğrulanmış süreçte
WS_VISIBLE pencere bulunmasıdır; öne getirme, küçültmeyi kaldırma, boş belge
veya etkileşime hazır olma garantisi değildir. Başka bir kullanıcının aynı anda
uygulama başlatmasını atomik kilitleyen bir OS mekanizması kurulmadı.

Başlatıcı bulunamaması/başlangıç gözlemi hatası, henüz yan etki yokken FAILED'dır.
Başlatma çağrısına girildikten sonra istisna, timeout veya iptal UNKNOWN'dır;
uygulama gerçekten açılmış olabilir. Manager yeni işleri durdurur ve aynı
request_id eski sonucu döndürür. Otomatik ikinci başlatma veya kill yapılmaz.
Önceden çalışan süreçte pencere beklerken timeout FAILED/window_not_observed,
iptal CANCELLED'dır çünkü bu görev başlatma yapmamıştır. Yerel bekleme sınırı
5 saniyedir; Windows başlatıcısının kendi çağrı süresini zorla kesmez.

Testler: test_app_open.py; zaten açık hedef, geciken pencere, süreç var/pencere
yok, ilk gözlem hatası, başlatıcı hatası, çağrı sonrası hata, iptal sınırları,
12 eşzamanlı aynı istek/replay ve UNKNOWN sonrasında yeni işin durmasını denedi.
test_windows_apps.py ayrıca sistem yolu çözümü ve kullanıcı komut/argümanı
olmayan native start çağrısını denetledi. Bu kontrollü sınır testleri fiziksel
Windows izin hatasının yaratıldığı anlamına gelmez.

## Gerçek apps.open kabulü

`v1` içinde isteyerek çalıştırılır; Not Defteri açabilir ve eski oturumu geri
getirebilir. Kullanıcı sekmelerini otomatik kapatmaz:

```powershell
.\.venv\Scripts\python.exe tests/apps_open_smoke.py --report ../docs/stage4-open-windows.json
```

[Gerçek sonuç](stage4-open-windows.json): geçici TASKVEX_HOME ile ilk gözlem
kapalıydı. Ürün apps.open aracı yalnız **1 gerçek start çağrısı** yaptı; süreç
ve pencere kimliği doğrulandı. Aynı request_id tekrarında aynı görev döndü;
yeni request_id ile ikinci apps.open mevcut pencereyi kullandı ve ikinci start
çağrısı olmadı. Başlatma/gözlem taklit edilmedi; yalnız çağrı sayısı sarılarak
ölçüldü. Test sonrasında uygulama açık bırakıldı, kullanıcı sekmelerine dokunulmadı.

Son gerçek kabul aşağıdaki kullanıcı testiyle tamamlandı. UI/model girişinin araçlara
bağlanması bu aşamanın kabulü değildir; native bridge genel araç çalıştırma
API'sine açılmadı. Çökme/yeniden başlama sonrası kalıcı istek günlüğü yoktur.

### 21 Ekim — Tip denetimi ve sonraki kabul kontrolü

Ekran görüntülerindeki üç Pylance sorununun kaynağı giderildi: bridge penceresi
`Window | None` olarak tanımlandı; olmayan pencereye erişim ve pencere oluşturma
başarısızlığı açık hata verir. Save payload'ı ayar doğrulamasından önce nesne
olmalıdır. `System` pythonnet tarafından çalışma anında oluşturulan bir .NET ad
alanıdır; `import_module` ile yüklenir ve WinForms GUI thread'ine Invoke korunur.
Uyarı bastırma veya yeni üretim bağımlılığı eklenmedi.

`app/main.py` ve `app/bridge/webview_bridge.py` için venv Python'u kullanan
Pyright sonucu: 0 hata, 0 uyarı. Pytest: **397 geçti**. Pencere oluşturulamazsa
GUI başlamadığını ve worker'ın kapandığını doğrulayan test eklendi.
[Gerçek WebView2 raporunda](stage4-typefix-native-smoke.json) sekiz senaryo geçti;
on_top, F11, kayıt/yeniden yükleme, shutdown ve hata halinde veri koruma dahil.
Bu testin pencereleri gizlidir; export dosya seçimi test tarafından sağlanır.

Computer Use ile mevcut kişisel pencereye dokunmadan File → New window üzerinden
ayrı bir Untitled penceresi oluşturuldu. Tek sekmesi değişmemiş ve 0 karakterdi.
İlk Alt+F4 sonrasında kapanış doğrulanamadı; pencere yeniden gözlenip Close
düğmesi kullanıldı. Sonraki pencere listesinde test penceresi yoktu, kişisel
pencere duruyordu. Ardından gerçek core apps.open/replay denemesi
[başarıyla geçti](stage4-after-blank-close-windows.json): mevcut hedef kullanıldı,
yeni başlatma sayısı 0 oldu. Bu, tüm Not Defteri süreçleri kapanıp yeni süreç
açılması testi değildir. Önceki kapalıdan gerçek açma kanıtı ayrı rapordadır;
bu deneme sırasında tümü kapalı → yeniden açma kabulü henüz açıktı; aşağıdaki
kullanıcı testi bu maddeyi kapattı.

### Kullanıcıyla kapatma ve yeniden açma kabulü — tamamlandı

Kullanıcı açık çalışmalarını koruyarak bütün Not Defteri pencerelerini kapatıp
smoke betiğini çalıştırdı; sonra yeniden kapatıp ikinci kez çalıştırdı ve iki
testin geçtiğini bildirdi. [İlk açma](stage4-manual-first.json) ve
[yeniden açma](stage4-manual-reopen.json) raporları ayrıca okundu ve denetlendi:
iki başlangıçta da running=false/visible_window=false, launch_count=1,
fresh_launch_checked=true, replay_same_task=true ve second_request_reused_window=true.
Açılan hedef iki turda da verified=true ve görünür pencereyle doğrulandı.
Kapatma kullanıcı tarafından yapıldı; betik kapatma/kill uygulamadı. İki tur ayrı
core süreçleridir; süreçler arası kalıcı replay garantisi test edilmiş sayılmaz.

Aşama 4'ün beş planlı adımı tamamlandı. Model bağlantısı Aşama 5 kapsamındadır.

Ek başvuru: Python'un [os.startfile](https://docs.python.org/3/library/os.html#os.startfile)
ve Microsoft'un [GetSystemDirectoryW](https://learn.microsoft.com/en-us/windows/win32/api/sysinfoapi/nf-sysinfoapi-getsystemdirectoryw)
sözleşmeleri başlatma yöntemi seçilirken kontrol edildi.
