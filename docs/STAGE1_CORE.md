# Aşama 1 — Modelden bağımsız core tamamlandı

Bu belge Aşama 1 kabulünün tarihsel üç araç/215 test kapsamını korur. Güncel
core Aşama 3 ile notes.update/delete/initialize/replace de içerir; [not geçişi
ve güncel test sonucu](STAGE3_NOTES.md) ayrı kaydedilmiştir. Native host Aşama 2'de
eklendi; aşağıdaki başlangıç sınırları o aşamayı geriye dönük tarif etmez.

Bu belge ilk gerçek araçların kullanımını ve Aşama 1 kabul sonuçlarını açıklar.
Core model, mikrofon veya UI gerektirmeden not kaydeder/listeleyebilir ve salt
okunur sistem bilgisi alabilir. Henüz kullanıcıya açılan native uygulama değildir.

## Çalışan akış

`create_core()` → tek registry + yerel policy + TaskManager → `submit(ToolRequest)`
→ parametre doğrulama → sıra → yeniden doğrulama/izin/iptal → gerçek araç → sonuç.

`v1/app/bootstrap.py` bu bileşenleri birleştirir. Dönen manager `with` ile
kullanılmalıdır; çıkışta worker kapatılır. Host varsayılan principal olarak
`local-user` seçer ve üç yerel araç için açık izin verir. Kaynak `desktop`
olmalıdır. Bu etiketleri doğrulamak kullanıcı kimlik doğrulaması değildir;
gelecekteki native adaptör alanları güvenilir biçimde kendisi oluşturmalıdır.

## Araç sözleşmeleri

| Araç | arguments | Başarılı result.data |
|---|---|---|
| notes.add | {text: boş olmayan metin} | {note: {id, text, done}} |
| notes.list | {} | {notes: [{id, text, done}, ...]} |
| system.status | {} | {os, os_release, architecture, logical_cpu_count, cpu_percent, memory_percent} |

Not metni en fazla 10.000 karakterdir; yalnız boşluk kabul edilmez. Metin
kırpılmaz, ek parametreler reddedilir. Kimlik her yeni notta UUID ile üretilir;
yeniden okurken değişmez. done başlangıçta false'tur; güncelleme/silme aracı bu
aşamanın kapsamında değildir. Aynı metin farklı request_id ile iki kez eklenebilir.

Not dosyası `get_data_home()/notes.json` konumundadır. `version: 1` zarfının data
alanı `{notes: [...]}` olur. Her kayıt yalnız id/text/done alanlarını taşır;
done boolean olmalı, kimlikler boş olmamalı ve tekrar etmemelidir. Geçersiz
kayıt veya tanınmayan alan `invalid_notes` hatasıdır; dosya boşaltılmaz/ezilmez.
Bozuk JSON için [kayıt katmanının açık kurtarma yolu](STORAGE.md) geçerlidir.

notes.add yazdıktan sonra dosyayı geri okuyup tam listeyi karşılaştırır. Başarı
kanıtı persisted/read_back ve note_id içerir. Yazma öncesi hata FAILED'dır;
yazma başarılı olup doğrulama başarısızsa UNKNOWN/commit_unverified döner.
Manager belirsiz görevden sonra yeni işleri durdurur; aynı istek tekrar çalışmaz.
İptal yazmadan önce gözlenirse kayıt yapılmaz; kaydedilmiş/doğrulanmış not geç
iptalle silinmiş sayılmaz. Fiziksel yazma başladıktan sonra thread zorla kesilmez.

system.status standart Python `platform` ve `os` sorgularını kullanır. Mantıksal
CPU sayısı bulunamazsa null'dır. CPU/RAM kullanım yüzdeleri henüz ölçülmediği
için daima null'dır; sıfır veya sahte ölçüm verilmez. Araç dosya yazmaz, cihaz
açmaz, hostname/kullanıcı adı/token döndürmez. Bu çıktı mevcut UI telemetri
payload'ı değildir; native adaptör bağlanırken alanlar ayrıca eşlenecektir.

## Çağırma örneği

Bu örnek gerçek veri dizinine yazar. İzole deneme için önce TASKVEX_HOME'u
boş bir geçici dizinin mutlak yoluna ayarla; otomatik testler bunu kendileri yapar.

```python
from app.bootstrap import create_core
from app.core.contracts import ToolRequest

with create_core() as core:
    task = core.submit(ToolRequest(
        request_id="ilk-not-1", source="desktop", principal="local-user",
        tool="notes.add", arguments={"text": "İlk core notum"},
    ))
    result = core.wait(task.task_id, timeout=5)
    print(result.to_dict())  # Terminal durum ve gerçek doğrulama kanıtı.
```

request_id tekrar önleme yalnız mevcut manager oturumundadır. Uygulama yeniden
açıldığında aynı istek kimliğini tekrar göndermek yeniden eklemeye yol açabilir;
çökme sonrası exactly-once veya kalıcı görev günlüğü uygulanmadı. wait timeout'u
görevi iptal etmez ve 'not kaydedilmedi' anlamına gelmez.

## Kabul sonuçları — 21 Ekim 2026

`v1` içinde `.\.venv\Scripts\python.exe -m pytest -q -W error`:
**215 geçti**. `.\.venv\Scripts\python.exe -m pip check`: bağımlılık sorunu yok.
Yeni bağımlılık eklenmedi. Dağılım: 45 sözleşme, 30 registry, 36 manager,
29 policy, 44 kayıt/yol ve 31 gerçek yerel araç testi.

| Kabul ölçütü | Sonuç ve test kanıtı |
|---|---|
| Ortak istek/sonuç biçimleri | Geçti — test_contracts.py |
| Hatalı parametre handler'a ulaşmaz | Geçti — test_tool_registry.py ve test_local_tools.py |
| Aynı araç adı sessiz ezilmez | Geçti — test_tool_registry.py |
| Tek istek tek gerçek not mutasyonu | Geçti — 12 eşzamanlı replay tek görev/not, test_local_tools.py |
| Sıra, durum ve iptal | Geçti — test_task_manager.py; gerçek kuyruk notu ve yazma öncesi iptal de test edildi |
| Policy reddinde dosya yazılmaz | Geçti — test_policy.py ve gerçek yanlış kullanıcı/kaynak testleri |
| Not kaydı/listeleme/yeniden açma | Geçti — gerçek geçici JSON dosyasında kimlik ve içerik korundu |
| Yazma hatası başarı değildir | Geçti — replace hatasında FAILED/write_failed, eski dosya değişmedi |
| Bozuk JSON aslı korunarak kurtarılır | Geçti — ayrı .corrupt dosyası, ardından gerçek not ekleme |
| Belirsiz kayıt otomatik yinelenmez | Geçti — kayıt sonrası read hatası/uyuşmazlık UNKNOWN; yeni görevler durdu |
| Sistem aracı gerçek ve salt okunur | Geçti — gerçek platform/CPU sorgusu; ölçülmeyen alanlar null |
| Kayıt sırasında süreç kapanması | Geçti — önceki kayıt korundu; ayrıntılar STORAGE.md içinde |

Sonuçlar izole test dizinlerinde alındı. Kaynak/referans kodu import edilmedi;
gerçek kullanıcı notları taşınmadı. Ayrı olay framework'ü/abonelik sistemi
eklenmedi; mevcut submit/get/wait/cancel akışı bu aşama için yeterli.

## Sonraki sınır

Aşama 2: mevcut UI'ı PyWebView ile native açmak ve ilk ayar/salt okunur durum
akışını bağlamak. UI notlarının yazma sahipliği ve eski {t,d} biçiminin aktarımı
otomatik devralınmış değildir; Aşama 0 kararı korunur. Not CRUD geçişi ayrı açık
sözleşme gerektirir. Model/ses, uygulama pluginleri ve GUI katmanları sonraki
aşamalardır. Native pencere, gerçek donanım, hesaplar ve çok süreçli yazma bu
kabulün parçası değildir.
