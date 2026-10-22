# Gemini bağlantı incelemesi — 21 Ekim 2026

Kapsam: kullanıcı tarafından seçilen gemini-live-api-dev skill'i ve migration
referansı ile mevcut GeminiText, ModelTools ve canlı kabul betiğinin karşılaştırılması.
Skill kaynakları kullanıcının .agents/skills/gemini-live-api-dev dizinindedir.
Bu bir Live uygulaması geliştirme turu değildir; mevcut metin adaptörü incelendi.

## Doğru olanlar

- SDK google-genai 2.32.0; eski google-generativeai kullanılmıyor.
- Mevcut yol Generate Content metin/araç turudur. gemini-3.8-flash metin modeli
  ile bu yol uyumludur; gemini-3.8-live ayrı WebSocket/ses protokolüdür.
  Live için yalnız model adını değiştirmek yeterli değildir. CLI yardımına
  --model alanının Live modeli için olmadığı açıkça eklendi.
- SDK'nin otomatik function calling özelliği kapalı; handler'a doğrudan geçiş
  yok. Host'un izinli kataloğu, registry, policy ve TaskManager korunuyor.
- Araç şemaları kural atılmadan aktarılıyor; model Content'i ve düşünme imzası
  sonraki isteğe aynen ekleniyor. FunctionResponse sağlayıcının id/name bilgisini
  koruyor. Tek yanıtta gelen araçlar mevcut worker'da sırayla yürütülüyor.
- Anahtar yalnız süreç/host girişinden alınıyor; genel ayar, log veya yedekte
  saklanmıyor. HTTP retry kapalı; tur/araç sınırları mevcut. Kısmi tamamlanmış
  iş ağ hatasında saklanıyor; pending/UNKNOWN başarıya çevrilmiyor.
- Bu sync istemci açıkça kapatılıyor. UI, mikrofon veya Live alıcı döngüsü henüz
  buna bağlı olmadığı için burada Live receive döngüsünü bloke etme iddiası yok.

## Yeniden oluşturulan ve düzeltilen iki sorun

### 1 — Bağımsız kullanıcı turlarında araç çağrı kimliği karışması

GeminiText.run her çağrıda yeni bir kullanıcı isteği tanımlıyor; ancak sağlayıcı
id'si yalnız ModelTools oturumuna bağlıydı. İki bağımsız run aynı id'yi kullanırsa
ikinci istek eski görevin replay'i sanılabiliyordu. Test iki ayrı not isteğinde
iki not beklerken yalnız bir not gözledi ve düzeltmeden önce başarısız oldu.

Core'a iletilen çağrı kimliği artık kullanıcı turunun bir kez üretilen turn_id'si
ile kapsamlandırılıyor. Aynı run içindeki replay aynı göreve gider; ayrı run
farklı görev oluşturur. Gemini'ye dönen id ve özgün Content değiştirilmez.
Boş sağlayıcı id'si bu kapsama eklenmeden önce yine reddedilir. Kalıcı çökme
günlüğü veya anlamsal olarak aynı yeni çağrıları kendiliğinden birleştirme eklenmedi.

### 2 — Not kabul testinde geri okuma için yanlış başarı

Betik notes.add ve notes.list araçlarının görünmesini, son dosyada tek not
bulunmasını yeterli sayıyordu. Model önce boş listeyi okuyup sonra not eklediğinde
not geri okunmamış olsa bile acceptance_verified=true çıkabiliyordu. Yeni test
bu sırayı oluşturarak düzeltmeden önce yanlış başarıyı doğruladı.

Kabul artık başarılı notes.list sonucundaki kayıtların, dosyaya yazılmış tek
sentetik notla kimliği dahil eşleşmesini ister. Eklemeden önceki boş liste
kabulü geçiremez. Test, kullanıcının gerçek notlarına yine erişmez.

## Kanıt ve kalan sınır

Düzeltmeden önce hedefli koşum: iki yeni sınır durumu başarısız, mevcut üç kabul
durumu başarılı. Düzeltmeden sonra tam pytest: **460 geçti**. Gemini testleri:
**41 geçti**. GeminiText, ModelTools, kabul betiği ve testleri için Pyright:
**0 hata, 0 uyarı**. pip check temiz. Yeni bağımlılık veya otomatik retry eklenmedi.

Kullanıcının son canlı katalog raporu HTTP 503 / UNAVAILABLE ve boş tool_results
içeriyor. Bu incelemede yeni canlı istek yapılmadı; yerel düzeltmelerin 503'ü
giderdiği iddia edilmiyor. Anahtar/kota/model hesabı ve Live ses bağlantısı
bu kontrollü testlerin kanıtı değildir. 5.2 canlı kabulü açık kalır.

Live aşamasında skill'in send_realtime_input, tüm event parçalarını işleme,
ses kuyruklarını interruption'da temizleme ve oturum devam ettirme kuralları
uygulanacak. Extended Thinking seçilirse NON_BLOCKING ve interaction_status
gereksinimleri ayrıca ele alınacak. Skill ana metnindeki minimal düşünme düzeyi
ifadesi migration referansıyla çelişiyor; bu değer mevcut koda eklenmedi ve
Live uygulama turunda modelin resmi kartı esas alınacak.

## Kontrol edilen resmi kaynaklar

Skill'in llms.txt dizini okunup ilgili sayfalar seçildi. Gemini dokümantasyon
MCP aracı bulunmadığından resmi web kaynakları kullanıldı:

- [Doküman dizini](https://ai.google.dev/gemini-api/docs/llms.txt)
- [Generate Content araç çağrıları](https://ai.google.dev/gemini-api/docs/generate-content/function-calling.md.txt)
- [Gemini 3.8 Flash](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash)
- [Gemini 3.8 Live ve geçiş kuralları](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-live)
