# Aşama 0 — Core başlangıç kararları

Tarih: 21 Ekim 2026. Durum: başlangıç kapsamı ve sözleşme sınırları kaydedildi; core uygulaması başlamadı.

## Kararlar

| Konu | Karar |
|---|---|
| Lisans | TaskVex'in özgün katkıları MIT. Telif satırı TaskVex contributors. Üçüncü taraf koşulları ayrı korunur. |
| Referans | Hermes yok. Mark LVI yalnız referans; otomatik kod aktarımı yok. |
| Platform | İlk hedef Windows masaüstü, tek yerel kullanıcı. Bot/çok kullanıcı kimliği sonraki aşama. |
| UI | v1/ui mevcut konumunda, vanilla ES modülleri korunur. Yeni framework yok. |
| İlk host | PyWebView; gerçek native açılış Aşama 2'de doğrulanacak. |
| Çalışma modeli | Küçük Python core, tek registry ve başlangıçta tek görev worker'ı. |
| İlk araçlar | Core testlerinde notes.add/list; UI köprüsünün ilk diliminde ayarlar ve salt okunur system.status. |
| İlk plugin | apps.open/apps.status; izinli katalogdaki Not Defteri ile gerçek Windows denemesi. |
| Veri | TASKVEX_HOME ile değiştirilebilir; Windows varsayılanı %LOCALAPPDATA%/TaskVex. Testler ayrı geçici kök. |
| Model/ses | İlk core için gerekmiyor; araç hattı doğrulandıktan sonra Gemini/Live. |
| Plugin yükleme | Başlangıçta açık kayıtlı güvenilir uygulama pluginleri. Dosya bırakınca otomatik Python import yok. |
| Yetki | Model/plugin yetki vermez. İlk policy yalnız tanımlı düşük riskli işlemlere izin verir; diğerleri açıkça reddedilir. Onay UI'ı olmayan aşamada riskli işlem çalışmaz. |
| Hata | Kabul, tamamlanma, başarısızlık ve belirsiz sonuç ayrı. Sahte başarı veya belirsiz işlemde otomatik tekrar yok. |

## UI durum ve yazma sahipliği

Güncel ek: Aşama 3'te native not sahipliği backend'e geçti; eski not aktarımı
açık kullanıcı onayı ve aynı dosyada tek seferlik işaretle uygulanır. Generic
save notları yazmaz; tarayıcı-only mod yerel kalır. Aşağıdaki ilk dilim tablosu
tarihsel başlangıç kararıdır; güncel sözleşme [STAGE3_NOTES.md](STAGE3_NOTES.md).

Bu tablo backend uygulanırken kullanılacak karardır; mevcut UI'ın davranışını bugün değiştirmez.

| Alan | Mevcut sahip | İlk native dilim | Sonraki geçiş |
|---|---|---|---|
| Tema, renkler, profil, layout, SFX, tercihler | settings.js + localStorage | save içinden izinli ayar alanlarını backend kalıcılaştırır; kayıt kesin sonucu gerekir | Sürüm/revizyonla güncelleme; sırlar bu alana dahil değil |
| Notlar | notes.js, save payload'ı ve note_* olayları | Native not yazımı henüz bağlanmaz; yerel mod korunur | Sabit note_id + request_id; tek backend CRUD sahibi; save notları tekrar yazmaz |
| Skill tanımları | skills.js + save/skill_* | Yalnız mevcut yerel tanım davranışı; backend çalıştırma desteklenmiyor | Tek yazma sahibi ve sürümlü tanım/komut ayrımı |
| Rutin tanımları | routines.js + save/routine_* | Mevcut yerel davranış | Tanım saklama ile tetikleme ayrı; backend devralırken UI scheduler durdurulur |
| Sayaç/kronometre | timers.js | UI yerel sahibi | Core araçları eklendiğinde kalan süre ve tetikleme otoritesi açıkça devredilir |
| Timeline | panels.js + taskvex_tl | UI görünüm günlüğü; görev yürütme kanıtı sayılmaz | Gerekirse backend görev günlüğü ayrı |
| Cihaz listeleri ve gerçek kamera/ses | Backend/donanım gerekli | Desteklenmiyor; açık unavailable/not_implemented | Gerçek envanter ve durum backend'den; seçim tercihi fiziksel işlem kanıtı değil |
| Model/voice katalog ve bağlantı | Backend gerekli | Offline; boş katalog/uygun unavailable | Model oturumu açılmadan online(true) gönderilmez |
| CPU/RAM vb. | connections.js görünümü | system.status ölçüm adaptörü üretir; UI yalnız görüntüler | Eksik/null/sıfır mevcut sözleşmeye göre ayrılır |
| Google, konum, takvim, mesajlaşma | Backend gerekli | Desteklenmiyor | Sağlayıcı adaptörü + policy; oturum/hesap kapsamı korunur |

### Notlarda çift yazma sınırı

21 Ekim baz testinde bir UI not ekleme eylemi hem save hem note_add üretti. Bu mevcut tarayıcı modu için gözlenen davranıştır; iki ayrı backend yazma handler'ı bağlamak için izin değildir. Native not protokolü değişirken api.js/app.js/notes.js/schema.js/settings.js birlikte ele alınacak. Aynı metinli iki not farklı kimlikle silinebilmeli. Eski yedek ve backend veri dosyası yokluğu açık veri aktarımıyla yönetilmeli; boş backend snapshot'ı yerel notları sessizce silmemeli.

## Olay yönlendirme grupları

| Olay grubu | Handler sahibi / ilk davranış |
|---|---|
| ui_ready | Bridge/bootstrap: doğrulanmış ilk snapshot, katalog/destek bilgisi; model online sinyali değildir |
| save | Ayar handler'ı: izinli ayar alanlarını doğrula ve kaydet; tüm gelen nesneyi doğrudan diske basma. notes/skills/routines sahipliğiyle çakışma yaratma |
| note_add, note_done, note_del | Not handler'ı: native CRUD protokolü tamamlanana kadar mutasyon bağlanmaz |
| skill_save/delete, routine_save/delete | Tanım kaydı; native sahiplik tasarlanana kadar uygulanmaz |
| run_skill, run_routine, text, stop_task | Ortak komut/görev hattı; model/skill yürütücüsü henüz yoksa not_implemented |
| device, query_devices, mic, mute, audio_listening, camera, screen_share, noise, wake_sens | Donanım/oturum handler'ı; UI tercihi ile fiziksel sonuç ayrı |
| query_camera, query_location | Salt okunur kesin durum sorgusu; gerçek sahip yoksa başarılı durum uydurulmaz |
| reconnect, disconnect, restart, shutdown, closed | Oturum/app yaşam döngüsü; restart/kapama gerçek kaynak sahibinden doğrulanır |
| google_connect, location, model, voice, media | İlgili entegrasyon/oturum handler'ı; hazır değilse açık ret |
| apikey | Credential handler'ı; henüz destek yok. Generic save, log veya sıradan JSON'a yazılmaz |
| layout, timeline, timeline_clear, drawer, inspect, shortcut, export, cal_soon | Görünüm/bildirim veya ilgili alana yönlendirme; isme bakıp iş yürütülmez. Gerçek payload ve UI davranışı kaynak sözleşmesiyle kontrol edilir |
| reset, ontop | Reset kapsamı yalnız açık kullanıcı ayarları; kimlik bilgileri/başka dosyalar topluca silinmez. ontop native pencere tercihi |
| Tanımsız olay | {ok:false,error:{code:"not_implemented",message:"..."}} önerilen native ham yanıt. emit bunu başarısız taşıma/istek sonucu olarak sarmalar; sahte completed üretilmez |

Kaynak olay envanteri baseline.json içindedir; regex yalnız literal emit adlarını çıkarır. Kamera/konum gibi koşullu/computed adlar ayrıca elle incelendi. Bu liste yürütme yetki listesi değildir.

## İlk core sözleşme sınırları

- request_id: aynı içerikle yinelenirse aynı görev; farklı içerikle aynı kimlik reddedilir. Başlangıçta tekrar önleme oturum kapsamındadır; çökme sonrası exactly-once iddiası yok.
- ToolSpec: ad, açıklama, giriş şeması, handler ve gerçekten gerekli yetki/kaynak bildirimi.
- Görev: queued/running; gerekirse awaiting_approval; succeeded/failed/cancelled/unknown sonucu. Cancel_requested kabulü iptal tamamlandı demek değildir.
- Araç sonucu boşsa veya sözleşmeye uymuyorsa succeeded sayılmaz. Süre dolması yan etkinin uygulanmadığını kanıtlamaz.
- Bridge ayar/read-only isteklerini yönlendirir; model/araç/skill yürütmesi ortak TaskManager'dan geçer. UI ile bot için ayrı yürütücü üretilmez.
- Bekleyen worker fiziksel işlemi sürdürebiliyorsa desktop kilidi güvenli bitiş gözlenmeden bırakılmaz. Thread timeout thread'i öldürmez.
- Beklenmeyen handler hatası UI'ı kapatmaz; log maskelenir. Log/olay abonesinin hatası tamamlanmış yan etkiyi yeniden yürütmez.

## Baz doğrulama

Kanıt: [baseline.json](stage0/baseline.json), [1280×800 başlangıç görüntüsü](stage0/ui-1280x800.png).

6 hedefli kontrol geçti: HTTP açılışı/bridge alias; save + note_add çakışmasının gözlenmesi; not yenileme kalıcılığı; backend snapshot'ın outbound üretmeden uygulanması; geçersiz snapshot'ın mevcut notu koruması; denenen akışta pageerror/unhandledrejection olmaması. HTML/CSS ve 13 JS modülünün SHA-256 değerleri kaydedildi, kontrol sırasında kaynak değişmedi.

Ortam: headless Edge, yeni izole tarayıcı profili, localhost HTTP, dış ağ engelli; native olmayan onEvent simülasyonu. Kullanıcının tarayıcı profili/notları kullanılmadı. Bu tam UI denetimi veya gerçek PyWebView/hardware testi değildir. Test betiği mevcut Codex çalışma alanındaki work/diagram-check/stage0-baseline.mjs dosyasında; taşınabilir proje testleri Aşama 1'de eklenecek.

## Kapanış ve kalanlar

21 Ekim güncellemesi: not add/done/del işlemlerinin yerel kaydı artık emitSave:false kullanıyor; kullanıcı eylemi yalnız ilgili note_* olayını üretir. Aşama 0'daki çift olay gözlemi tarihsel önce durumudur; güncel doğrulama [note-events-fix.json](note-events-fix.json) içindedir. İki taşıma senaryosunda (fallback ve simüle native) ekleme/tamamlama/silme, yenileme, no-echo ve açık ayar save davranışı doğrulandı. Sabit kimlik/native sahiplik işi sonraki aşamada kalıyor.

- Kullanıcı UI yedeğini aldığını bildirdi; yedeğin içeriği bu turda ayrıca doğrulanmadı.
- MIT LICENSE, referans dışlama kuralları ve THIRD_PARTY_NOTES.md eklendi.
- İlk core kapsamı, olay/veri sahipliği ve kabul sınırları kaydedildi.
- UI dosyaları değiştirilmedi; çalışan backend, plugin veya model oturumu oluşturulmadı.
- Tam varlık/telif geçmişi ve bağımlılık lisans envanteri yayın öncesi açık iş. MIT dosyası önceki her varlığın lisansının doğrulandığı anlamına gelmez.
- Git reposu/ilk commit bu görevde kurulmadı. Yeni core bağımlılık sürümleri Aşama 1 uygulamasında seçilip doğrulanacak.

Sonraki uygulama: Aşama 1. Önce istek/sonuç + registry + küçük TaskManager + policy + atomik kayıt ve izole core testleri. Gemini, GUI katmanları ve plugin mağazası bu pakette yok.
