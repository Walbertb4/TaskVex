# ToolRegistry — Aşama 1 / sıra 3

Uygulama: v1/app/session/tool_registry.py. Ortak tipler: [CORE_CONTRACTS.md](CORE_CONTRACTS.md).

Registry araç rehberidir: ad, açıklama, parametre şeması ve handler kaydını tutar. Araç çalıştırmaz, izin vermez, dosyadan plugin yüklemez; görev yürütme TaskManager'dadır. Yerleşik araç ve plugin aynı ToolSpec ile kaydolur.

## Kullanım sırası

1. Bootstrap ToolSpec oluşturup register(spec) çağırır.
2. Registry bildirimin kopyasını alır; şemayı kontrol eder. Geçersizse kayıt eklenmez.
3. Aynı ad zaten varsa duplicate_tool verir; ilk kayıt değişmez.
4. İstek geldiğinde validate_request(request) geçerli ve kopyalanmış ToolRequest döndürür veya RegistryError verir.
5. [TaskManager](TASK_MANAGER.md) yeniden doğrulama, [policy callback'i](POLICY.md) ve iptal kontrolünden sonra senkron handler'ı çağırır. Parametre doğrulaması izin veya yürütme tamamlanması değildir.

## Metotlar

| Metot | Sonuç |
|---|---|
| register(tool) | Geçerli ToolSpec'i kaydeder; dönüş None; hata halinde mevcut kayıtlar korunur |
| get(name) | Bağımsız ToolSpec kopyası; bilinmeyen ad unknown_tool |
| list_tools() | Ada göre sıralı ToolSpec kopyaları; yetkiye göre filtrelenmiş katalog değildir |
| validate_request(request) | Parametreleri doğrulanmış, ayrı ToolRequest kopyası; handler çağrılmaz |

RegistryError, ContractError alt türüdür. code alanı duplicate_tool, invalid_tool, invalid_schema, unknown_tool, invalid_request veya invalid_arguments olabilir. Araç parametrelerinin ham değerleri doğrulama hata mesajına eklenmez; UI/log katmanlarının genel maskeleme yükümlülüğü devam eder.

## Şema kuralları

Yeni doğrudan üretim bağımlılığı jsonschema>=4.26,<5; kurulan sürüm 4.26.0. Kendi şema motorumuzu yazmadık. Belgeler: [doğrulama API'si](https://python-jsonschema.readthedocs.io/en/stable/validate/).

- Draft 2020-12 kullanılır. $schema varsa tam `https://json-schema.org/draft/2020-12/schema` olmalı; yoksa aynı draft kullanılır.
- Kök type=object şartı ToolSpec'ten gelir; şemanın ayrıntıları kayıt sırasında check_schema ile denetlenir.
- İlk profil, bütün şema belgesinde $ref/$dynamicRef/$recursiveRef anahtarlarını reddeder; yerel referanslar da dahil. Şemalar inline, yani dış referansa ihtiyaç duymadan kendi içinde tanımlı olmalı. Burada ağ/dosya çözümleyicisi yok.
- required, türler, enum, uzunluk/sayı sınırları, nesne ve dizi alt şemaları gibi kurallar kütüphane tarafından değerlendirilir.
- Ek parametreleri reddetmek için şemada additionalProperties:false yazılmalı. Registry bu kuralı şemaya gizlice eklemez.
- Değerler dönüştürülmez ve default otomatik uygulanmaz. Null yalnız şema izin veriyorsa geçer; sıfır korunur; boolean sayı yerine geçmez. JSON Schema gereği 1.0 gibi kesirsiz sayı integer kuralını sağlayabilir.
- format bu sürümde doğrulama iddiası değil, şema bilgisidir; FormatChecker etkin değil. E-posta/URL gibi alanlar gerçek entegrasyonda ayrıca ele alınmalı. JSON Schema'nın tanımadığı anahtarlar standart gereği genel olarak görmezden gelinebilir; check_schema bütün yazım hatalarını bulma garantisi değildir.

## Kopyalama ve sınırlar

Kayıt, get ve list_tools şemaları kopyalar. Çağıranın veya dönen bildirimin iç sözlüğünü değiştirmesi içerideki validator kurallarını değiştirmez. İstek de yeniden sözleşme doğrulamasından geçerek kopyalanır; oluşturulduktan sonra arguments'a eklenen NaN/özel nesne gibi veri reddedilir.

Startup sonrasında paralel kayıt/hot reload, enabled durumu, plugin taraması, sandbox, policy, timeout veya handler dispatch bu sürümde yok. Güvenilir uygulama kodu handler'a doğrudan erişebilir; registry bir güvenlik sandbox'ı değildir. Büyük/zararlı şemalar için kaynak kotası veya regex çalışma süresi sınırı da bu adımda uygulanmadı; şemalar uygulamayla gelen güvenilir bildirimler olacak, kullanıcı/model şema kaydedemeyecek.

## Test kanıtı

v1 içinde `.\.venv\Scripts\python.exe -m pytest -q`: 45 sözleşme + 30 registry testi, toplam 75 geçti. pip check temiz.

Yeni testler çift isim, bilinmeyen araç, bozuk/desteklenmeyen şema, iç içe parametre hataları, schema snapshot'ı, request kopyası, sıfır/null/boolean ayrımı, hata mesajında girdi sızdırmama ve handler çalıştırılmamasını kapsar. Gerçek araç, UI/native ve model entegrasyonu çalıştırılmadı.
