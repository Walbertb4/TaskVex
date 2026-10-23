# Küçük TaskManager — Aşama 1 / sıra 4

Uygulama: v1/app/tasks/manager.py. Yeni üretim bağımlılığı eklenmedi. Registry ve ortak sözleşmeler kullanılır; gerçek UI/model/hesap bağlantısı yok.

## Ne yapar?

Başvuru → registry doğrulama → kuyruk → tek worker → yeniden doğrulama → açık izin callback'i → iptal kontrolü → handler → tipli sonuç.

Worker ayrı Python thread'idir; handler'ları birer birer çalıştırır. Handler beklerken bile başka handler başlamaz. Bu ilk sürümde desktop dahil bütün işler bu yüzden seri çalışır; kaynak bazında paralellik veya ayrı kilit yöneticisi henüz yok.

## API

| Metot | Davranış |
|---|---|
| TaskManager(registry, authorize=None, capacity=256) | Worker'ı oluşturur. Callback yoksa yürütme izni reddedilir. |
| describe_tools() | Registry'den bağımsız name/description/parameters bildirimleri verir; handler/yetki nesnesi döndürmez ve yürütme izni vermez. Model adaptörü görünür alt kümeyi ayrıca seçer. |
| submit(request) | Parametreleri doğrular; queued Task kopyası veya aynı isteğin mevcut durumunu verir. Tamamlanmış sayılmaz. |
| get(task_id) | Bağımsız güncel Task kopyası |
| wait(task_id, timeout=None) | Terminal sonucu bekler; bekleme süresi dolarsa TimeoutError |
| cancel(task_id) | Kuyruktaysa cancelled; çalışıyorsa cancel_requested ve Event sinyali |
| close(timeout=5.0) | Yeni kabulü kapatır, bekleyenleri iptal eder, çalışana iptal ister; worker bittiyse True, hâlâ çalışıyorsa False |
| with TaskManager(...) | Blok çıkışında close; worker bitmezse açık shutdown_timeout hatası |

TaskManagerError.code: closed, request_conflict, uncertain_state, capacity_exceeded, unknown_task, invalid_timeout, worker_wait ve constructor doğrulama kodları. Geçersiz başvuru RegistryError da üretebilir. Bu API güvenilir uygulama içi API'dir; bir bot kullanıcısının başka kullanıcıya ait görevi get/cancel etmesini engelleyecek kimlik denetimi daha sonra giriş adaptöründe yapılmalıdır.

## Aynı isteği iki kez çalıştırmama

- Anahtar (principal, request_id). Farklı kullanıcılar aynı request_id kullanabilir.
- İçerik karşılaştırması source, principal, araç ve arguments dahil istek verisini kapsar. Nesne anahtar sırası karşılaştırmayı değiştirmez; JSON sayı gösterimi gibi diğer farklar konservatif olarak farklı içerik sayılabilir.
- Aynı anahtar ve içerik mevcut görev kimliğini/durumunu verir; queued, running, cancelled veya succeeded için yeniden handler çağrılmaz.
- Aynı anahtar farklı içerik request_conflict verir. Önceki görev değiştirilmez.
- Eşzamanlı başvurularda kontrol ve kayıt aynı Condition kilidi altında yapılır.
- capacity terminal kayıtları da sayar. Kayıt silerek tekrar önlemeyi zayıflatmak yerine yeni kimlikler reddedilir; mevcut kayıtların sorgusu/tekrarı korunur.
- Kayıt yalnız bu manager örneğinin belleğindedir. Yeniden başlatma, ikinci manager veya süreç çökmesi arasında exactly-once garantisi yok. Gerçek yan etkiler eklenirken kalıcı günlük/sağlayıcı anahtarı/gözlem ihtiyacı ayrıca değerlendirilecek.

## İptal ve bekleme süreleri

Kuyruktaki görev henüz handler'a gitmediğinden hemen cancelled olabilir. Çalışan görevde Event.set yalnız talep gönderir. Handler sinyali kontrol edip kendi kaynaklarını güvenle bırakmalı, sonra CANCELLED ToolResult döndürmelidir.

Geç iptal geldiğinde handler doğrulanmış SUCCEEDED sonucu döndürürse başarı korunur. "İptal ettim" diyerek gerçekleşmiş işlemi yok saymayız. Handler'a teslim sınırından sonra gelen iptal, henüz hiçbir yan etki olmadığını garanti etmez.

wait(timeout) çağıranın bekleme süresidir; görevin yürütme süresi değildir. TimeoutError görevi iptal etmez, unknown yapmaz veya thread'i öldürmez. Bu sürüm yürütme deadline/watchdog sunmaz; ToolContext.deadline None kalır. Otomatik süre sınırı eklenecekse fiziksel kaynak sahipliği korunarak ayrıca tasarlanmalı.

close metodunun False dönmesi kapanışın tamamlanmadığını söyler. Worker daemon değildir; takılı kalan handler normal süreç çıkışında sessizce terk edilmez. Handler'ın kapanış işbirliği gerekir; zorunlu süreç sonlandırmasının güvenliği garanti edilmez. Worker kendi kuyruğunu wait veya close ile senkron bekleyemez.

## Sonuçların güvenilirliği ve belirsizlikte durma

Handler yalnız ToolResult döndürür. None, metin, {ok:true}, yanlış görev kimliği veya bozuk sonuç başarıya çevrilmez; UNKNOWN olur. Handler başladıktan sonra atılan exception da işlemin hiç uygulanmadığını kanıtlamadığı için UNKNOWN olur. Ham exception metni sonuca/loga eklenmez.

UNKNOWN olduğunda sonraki handler'lar otomatik başlamaz: bekleyen görevler cancelled yapılır ve yeni istekler uncertain_state ile reddedilir. Mevcut belirsiz görevin durumu sorgulanabilir ve aynı kimlikle replay edilebilir; tekrar çalıştırılmaz. Bu sürümde otomatik recovery/resume API'si yok. Dış durum anlaşılmadan yeni manager açıp işlemi tekrarlamak güvenli toparlanma sayılmaz.

Handler FAILED ile işlemin uygulanmadığına ilişkin açık sonucu veya SUCCEEDED ile doğrulanmış sonucu döndürürse sıra devam edebilir. Bu beyanın doğruluğu yine aracı yazanın gözlemine bağlıdır; manager dış dünyayı kendisi ölçmez.

Yalnız senkron handler desteklenir. async def doğrudan kaydedilmişse çalışmadan FAILED/unsupported_handler olur. Sync fonksiyon coroutine döndürürse coroutine başlatılmadan kapatılır ve geçersiz sonuç UNKNOWN sayılır. Handler alt thread/süreç başlatıyorsa bunların yaşam döngüsünü de sahiplenmeli; başarılı döndükten sonra sahipsiz bir arka plan yan etkisi bırakmamalı.

## Policy bağlantısı

authorize(request_copy, tool_copy) açık True döndürmeli; None, 1 veya "allow" izin sayılmaz. Kopya verilmesi callback'in iç kaydı veya handler parametresini yanlışlıkla değiştirmesini önler. Callback exception üretirse handler çalışmaz ve görev FAILED olur.

TaskManager bir policy motoru/approval sistemi değildir; [ilk policy](POLICY.md) bu noktaya `authorize=policy.authorize` ile bağlanabilir ve bu birleşim test edilmiştir. Testlerdeki allow fonksiyonu yalnız test araçlarına izin verir; üretimde bütün araçlara True veren varsayılan oluşturulmadı.

## Doğrulama

`.\.venv\Scripts\python.exe -m pytest -q -W error`: 45 sözleşme + 30 registry + 36 manager testi; toplam 111 geçti. pip check temiz.

Önemli senaryolar: 16 eşzamanlı replay'in tek görev/tek çağrıya dönüşmesi; FIFO ve kuyruk iptali; çalışma ve preflight iptali; geç iptalde doğrulanmış başarı; kapanışta gerçekten bitmeyen worker'ın False ile bildirilmesi; belirsizlikte sıranın durması; kopyaların ayrılığı; kapasite/kimlik kapsamı; async/boş/yanlış sonuç; exception verisinin sonuca sızmaması.

Testler gerçek Python thread'leri ve Event kapıları kullanır; rastgele sleep gerekmez. Manager birim testlerindeki handler'lar test fonksiyonlarıdır. Gerçek not araçları ve system.status ile bütünleşme de test edildi; güncel **215 test** ve kabul sonuçları [STAGE1_CORE.md](STAGE1_CORE.md) içindedir. Native UI veya model testi yapılmadı.
