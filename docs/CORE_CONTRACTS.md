# Core sözleşmeleri — Aşama 1 / sıra 2

21 Ekim 2026. Uygulama: v1/app/core/contracts.py. Bu modül yalnız veri sözleşmeleridir; registry, TaskManager, policy, kayıt, UI köprüsü veya model oturumu çalıştırmaz. Üretim bağımlılığı eklenmedi.

## Tipler

| Tip | Alanlar | Anlamı |
|---|---|---|
| ToolRequest | request_id, source, principal, tool, arguments | Tek araç isteği. Görev kimliği ve oturum içi tekrar önleme TaskManager'ın sorumluluğu. |
| ToolSpec | name, description, input_schema, handler, required_capabilities, exclusive_resources | Bir aracın iç kaydı. UI veya model SDK'sı içermez. |
| ToolContext | task_id, request, cancel_event, deadline | Çalıştırıcıdan handler'a giden görev bağlamı. Python Event sinyali işbirlikçi iptal içindir. |
| ToolError | code, message, details | Yapılandırılmış hata veya belirsizlik gerekçesi. Gizli bilgi koyulmaz; log maskeleme sonraki katmanda. |
| ToolResult | task_id, status, verified, data, error, evidence | Yalnız terminal araç sonucu. Kabul/pending bu tipin başarı sonucu değildir. |
| Task | task_id, request, status, result | Görevin bir andaki kaydı. Durum geçişlerini uygulayacak nesne değildir. |

request_id giriş isteğinin kimliği; task_id core'un yürütme kimliğidir. Aynı kimlik oldukları varsayılmaz. source/principal boş olamaz fakat bu biçim kontrolü kimliği doğrulamaz. Kimlik güvenilir giriş adaptöründen gelecek; modelin yazdığı principal yetki vermez.

Araç adları küçük harfli ad alanı taşır: notes.add, system.status, apps.open. İç araç adını sağlayıcının function-name biçimine çevirmek gelecekteki model adaptörünün işidir.

## Durumlar

| TaskStatus | Terminal? | Kullanımı |
|---|---|---|
| queued | Hayır | Sırada |
| running | Hayır | Çalışıyor |
| awaiting_approval | Hayır | Kullanıcı onayı bekliyor; henüz uygulanmış sayılmaz |
| cancel_requested | Hayır | İptal talebi alındı; fiziksel işlemin durduğunun kanıtı değil |
| succeeded | Evet | Handler işlemin tamamlandığını doğruladığını açıkça bildiriyor |
| failed | Evet | Hata nedeni biliniyor; ToolError zorunlu |
| cancelled | Evet | Çalıştırıcı/handler durmayı doğrulamış; iptal talebinin kabulüyle karıştırılmaz |
| unknown | Evet | Bu yürütmenin sonucu doğrulanamadı; belirsizlik nedeni ToolError içinde zorunlu |

succeeded için verified=True ve error=None zorunlu. Diğer durumlarda verified=False olmalı; bu alan yalnız başarılı tamamlanmanın doğrulamasını ifade eder, hatanın gözlenip gözlenmediğini değil. Evidence farklı durumlarda gözlenen veriyi taşıyabilir.

verified=True tek başına dünyada bir işlem gerçekleştiğini kanıtlamaz; handler kanıtı gerçekten gözlemlemeli. Modül yanlış durum birleşimlerini önler, doğrulama motoru değildir. Boş handler dönüşünü veya {ok:true} cevabını ToolResult'a otomatik dönüştüren bir yol yok. TaskManager yürütücüsü gerçek dönüş tipini kontrol eder; hatalı sonucu UNKNOWN sayar.

Bir terminal Task'ın sonucu bulunmalı; sonuçtaki task_id ve status görevle eşleşmeli. Bitmemiş Task terminal sonuç taşıyamaz. Çalışma durumları için sırayla geçiş, kaynak kilidi ve tekrar yürütme kuralları TaskManager aşamasında uygulanacak. unknown otomatik yeniden deneme izni değildir.

## JSON ve veri sınırı

- arguments/input_schema/details/evidence kökte JSON nesnesidir. data herhangi bir geçerli JSON değeri olabilir.
- Nesne anahtarları metin; sayılar sonlu; tuple, özel nesne ve döngüsel yapı reddedilir. Null, False ve gerçek sıfır korunur.
- Constructor ve to_dict sınırlarında JSON verisi kopyalanır; çağıranın özgün listesi veya serileştirilmiş dönüş üzerinde yaptığı değişiklik kaydı değiştirmez.
- frozen dataclass alan atamasını engeller; iç sözlük/listeler derin immutable yapılmamıştır. Bunlara yerinde mutasyon yapmak yerine yeni kayıt oluşturulmalı. Registry/TaskManager kabul ve yürütme sınırında kendi doğrulamasını/kopyasını yapacak.
- ToolSpec yalnız şemanın JSON nesnesi ve kök type=object olduğunu kontrol eder. Tam JSON Schema geçerliliği ve arguments'ın araç şemasına uyması Registry aşamasında doğrulanacak; burada ayrı bir şema motoru yazılmadı.
- Request, error, result ve task to_dict() ile JSON uyumlu kopya verir. ToolSpec handler'ı ve ToolContext Event'i wire payload değildir; bunlar dışarı serileştirilmez.
- deadline varsa time.monotonic() ile aynı saat tabanında son süre olmalıdır; Unix zaman damgası değildir. Sürenin dolup dolmadığını bu tipler denetlemez.
- handler imzası (arguments, context) -> ToolResult olarak tanımlıdır. Bu adım callable varlığını kontrol eder; fonksiyonu çağırmaz ve imza/return annotation'ını yürütme kanıtı saymaz.

## Örnek

```python
from app.core.contracts import ToolRequest, ToolResult, Task, TaskStatus

request = ToolRequest(
    request_id="request-1", source="desktop", principal="local-user",
    tool="notes.add", arguments={"text": "Ders notu"},
)
queued = Task(task_id="task-1", request=request)

# Bir handler ancak gerçek kaydı doğruladıktan sonra başarı üretmelidir:
result = ToolResult(
    task_id="task-1", status=TaskStatus.SUCCEEDED, verified=True,
    data={"note_id": "note-1"}, evidence={"persisted": True},
)
finished = Task(
    task_id="task-1", request=request, status=TaskStatus.SUCCEEDED, result=result,
)
wire = finished.to_dict()
```

Örnek bir not kaydetmez; yalnız ortak tiplerin kullanılışını gösterir. Gerçek notes aracı ve çıktı biçimi artık [Aşama 1 sözleşmesinde](STAGE1_CORE.md) açıklanır. Mevcut UI emit payload'ları bu internal sözleşmeye sessizce değiştirilmedi.

## Doğrulama

v1 içinden `.\.venv\Scripts\python.exe -m pytest -q`: 45 test geçti. İstek/sonuç JSON sınırları, döngüler, sıfır/null/boolean ayrımı, dış mutasyondan kopya ayrımı, görev/sonuç kimlik ve durum tutarlılığı, iptal sinyalinin görevler arası ayrılması ve hatalı araç bildirimleri test edildi.

Registry, tek worker'lı handler dispatch/durum/iptal, ilk yerel izin kuralları ve disk kayıt katmanı artık hazır: [ToolRegistry](TOOL_REGISTRY.md), [TaskManager](TASK_MANAGER.md), [Policy](POLICY.md), [Kayıt](STORAGE.md). Kayıt katmanı ortak JSON doğrulamasını public copy_json(value) yardımcısıyla kullanır; veri sözleşmelerinin alanları değişmedi. Geçici dosyalarda kayıt testi yapıldı; native veya model testi henüz yok. Manager varsayılan olarak yürütmeyi reddeder; policy callback'iyle bütünleşmesi test edildi.

Gerçek notes.add/list ve system.status ile Aşama 1 de tamamlandı; **215 testin**
güncel kabul sonuçları [STAGE1_CORE.md](STAGE1_CORE.md) içindedir.
