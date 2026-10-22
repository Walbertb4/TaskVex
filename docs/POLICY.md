# İlk policy kuralları — Aşama 1, sıra 5

Bu belge `v1/app/policy/engine.py` içindeki izin denetimini açıklar. Policy,
"bu kullanıcı bu aracı çalıştırabilir mi?" sorusunu cevaplar; aracı çalıştırmaz.
İlk sürüm tek yerel kullanıcı ve `desktop` kaynağı içindir.

## İzin tablosu

| Araç | Gereken capability (yetki) | Şimdiki durum |
|---|---|---|
| notes.add | notes.write | Gerçek dosya aracı bağlı ve test edildi |
| notes.update | notes.write | Sabit kimlikle güncelleme; native UI bağlı |
| notes.delete | notes.write | Sabit kimlikle silme; native UI bağlı |
| notes.initialize | notes.write | İlk aktarımı okuma veya açık UI onayıyla bir kez uygulama |
| notes.replace | notes.write | Açık yedek yüklemesinde tam liste değiştirme |
| apps.catalog | apps.read | Salt okunur desteklenen uygulama kataloğu; kurulum/çalışma veya açma yetkisi değildir |
| apps.status | apps.read | İzinli uygulamanın salt okunur süreç/pencere gözlemi; açma/kapatma yetkisi değildir |
| apps.open | apps.read + apps.launch | İzinli Not Defteri başlatma ve pencereyi doğrulama; keyfi yol/argüman veya kapatma yoktur |
| notes.list | notes.read | Gerçek dosya aracı bağlı ve test edildi |
| system.status | system.read | Salt okunur gerçek sistem aracı bağlı ve test edildi |
| Diğer bütün araçlar | İzin yok | Reddedilir |

Host, kullanıcıya vereceği yetkileri başlangıçta açıkça seçer. Yetki verilmezse
bütün yürütmeler reddedilir. Okuma ve yazma ayrı izinlerdir; joker yetki yoktur.
Bilinmeyen yetki adı yapılandırma hatasıdır; sessizce kabul edilmez.

## Mevcut hatta kullanımı

```python
from app.policy.engine import PolicyEngine
from app.tasks.manager import TaskManager

# registry güvenilir host tarafından oluşturulur. Bu örnek uygulamayı başlatmaz;
# gerçek core kurulumu app.bootstrap.create_core içindedir; native pencere yoktur.
policy = PolicyEngine(
    principal="local-user",
    capabilities=frozenset({"notes.read", "notes.write", "system.read"}),
)
with TaskManager(registry, authorize=policy.authorize) as manager:
    pass  # Güvenilir adaptörden gelen ToolRequest burada submit edilecek.
```

Akış: registry parametreleri doğrular → manager kuyruğa alır → yürütmeden önce
registry yeniden doğrular → policy izin verir/reddeder → izin varsa handler çalışır.
Policy reddi `FAILED / permission_denied` sonucudur; handler çağrılmaz. TaskManager'a
callback verilmemesi de ret demektir. Bu adım yeni bir dispatcher eklemez.

İzin için istek kaynağı tam olarak `desktop`, principal yapılandırılan kullanıcı,
istek araç adı da verilen ToolSpec adı olmalıdır. Core tablosundaki yetkilerle
ToolSpec.required_capabilities tam eşleşmeli ve kullanıcıda bulunmalıdır. Plugin
boş yetki bildirerek veya başka yetki adı yazarak bu kontrolü aşamaz. İzinler
kopyalanır ve değişmez saklanır; başlangıçta verilen set'i değiştirmek izin eklemez.

## Güven sınırı ve kapsam

principal/source birer metindir; bunları eşlemek kimlik doğrulaması değildir.
İleride güvenilir native giriş adaptörü bu alanları kullanıcı/model payload'ından
kopyalamadan kendisi oluşturmalıdır. Telegram/Discord/model kaynakları şu an
reddedilir. Python pluginleri güvenilir uygulama kodudur; bu policy bir sandbox
değildir ve süreç içindeki kötü niyetli Python kodunu izole etmez.

Onay penceresi, dinamik yetki değiştirme, dosya kökü/hesap kapsamları ve riskli
işlemler bu aşamada yoktur. İleride yeni araç eklendiğinde core izin tablosu ve
gerekli hedef/parametre kısıtları birlikte incelenmelidir. Sırf registry'ye kayıt
olmak veya istek arguments alanına onay yazmak yetki vermez.

## Dolaylı Prompt Enjeksiyonu ve Taint Tracking (Güvenilmeyen Dış Veri)

L2 (DOM), L4 (ekran/OCR), Web, gelen e-posta veya harici dosyalardan okunan içerik model bağlamına girdiğinde oturum kirlenmiş (`tainted`) sayılır. Model bu veriyi talimat sanıp tehlikeli araçlar çağırsa bile, PolicyEngine tainted oturumda yan etkili/kritik araçları (`terminal.exec`, `gmail.send`, `notes.delete`, `files.delete` vb.) otomatik izin (`ALLOW`) vermez; mutlaka arayüzde kullanıcıdan fiziksel onay isteyen `CONFIRM` kararına yükseltir. Yetki kararı promptun iddiasına değil, RequestContext ve oturumun taint durumuna göre verilir.

## Doğrulama

`v1` dizininde `.\.venv\Scripts\python.exe -m pytest -q -W error`:
45 sözleşme + 30 registry + 36 TaskManager + 29 policy testi = **140 geçti**.
Policy testleri bilinmeyen araç/kaynak/kullanıcı, eksik/farklı yetki bildirimi,
bozuk yapılandırma ve değişmez izinleri kapsar. Gerçek TaskManager ile izin reddi,
sonraki işin devamı ve tekrar isteğinin tek yürütülmesi doğrulandı.

Gerçek not/disk aracı ve salt okunur sistem bilgisi de artık doğrulandı; güncel
215 testin kabul sonuçları [STAGE1_CORE.md](STAGE1_CORE.md) içindedir. Native UI,
donanım kontrolü ve hesaplar denenmedi; UI bağlantısı henüz yoktur.
