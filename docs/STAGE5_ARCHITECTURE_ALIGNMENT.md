# Aşama 5 — ortak mimari uyum kontrolü

23 Ekim 2026. Kapsam: kaynak kodda model → araç → core akışı, UI olayları ve
mevcut veri/kaynak sahipliği. Tüm donanım ve gelecek entegrasyonların çalıştığı
iddia edilmez. Bu adım uyku geçişini taşır; diğer bulguların uygulamasını açmaz.

| Durum | Bulgu ve kaynak | Gerekli işlem |
|---|---|---|
| Bu adımda taşındı | Uyku kararı `sleep_intent.py` cümle kalıplarındaydı | Dosya kaldırıldı. `assistant.request_sleep_mode` artık ModelTools → registry/policy/TaskManager yolunda. Model yanıtı/çalma sonrası mevcut host geçişi korunur. |
| Açık — sonraki hedefli mimari işi | `model_tools.py::_check_note_target` içindeki son not ve içerik filtresi seçimleri kısmen TR/EN cümle kalıplarına bağlı | Modelden yapılandırılmış seçici al; kayıt kimliği, taze liste, tek eşleşme, tarih ve belirsizlik denetimini backend'de koru. Bugün çalışan silme güvenliğini kaldırarak çözme. |
| Açık — rutin/skill yürütme entegrasyonu | `ui/js/routines.js::runRoutine` ve `skills.js::runSkill` desteklenmeyen `run_routine/run_skill` olaylarını gönderiyor; bridge bunları not_implemented olarak reddediyor | Registry/policy/TaskManager yürütücüsü eklenmeden çalışır özellik sayma. Timeline'daki “Routine started” / “Skill run” kayıtları gerçek kabulden önce üretiliyor; kabul ile başlama ayrılmalı. |
| Açık — rutin sahiplik devri | `routines.js::initRoutines` içinde UI'a ait 15 s aralıklı zaman denetimi ve app/Wi-Fi tetikleme girişi var | Backend scheduler eklendiğinde aynı anda iki tetikleyici bırakma; UI scheduler'ı kapat ve tek yürütme sahibine geçir. Şu an ikinci backend scheduler yok. |
| Planlı eksik kapsam | Rutin/skill tanımları UI store/localStorage'da saklanıyor; native `validate_settings` bunları settings.json'a yazmıyor. Sayaç/kronometre UI'da çalışıyor; bunlar henüz model araç kataloğunda yok | Modele açıldıklarında yapılandırılmış araç/tek veri sahibi kullan. Generic save'e ikinci mutasyon bağlama. Yerel UI işlevini bugün bozma. |
| Planlı eksik bağlantılar | `settings.py` profil pMem/pSys/pGreet/pBr ve conn.voice alanlarını saklayabiliyor; `model_instruction.py` yalnız pLang/pIns'i model talimatına bağlıyor. pWake yerel motorda, pSc UI kısayollarında kullanılıyor. Live setup ses seçimi geçmiyor; REST TTS Kore kullanıyor | Kaydedilebilir alanı çalışır özellik sayma. Kullanıcı hafızası ve ses/persona tercihleri aşamaları geldiğinde mevcut sahiplerine bağlanmalı; gizli veya bütün profil alanları kendiliğinden modele aktarılmamalı. |
| Planlı eksik kapsam | Hava durumu, Google, Telegram, Discord vb. için çalışan core aracı henüz yok | Bunlar dil değiştirerek çalışmaz. Aşamaları geldiğinde sağlayıcı adaptörü ve ortak araç/izin hattı eklenmeli. |

## Korunan doğru sınırlar

- Not CRUD'u ve uygulama araçları bootstrap'ta kayıtlı, policy denetimli ve
  TaskManager üzerinden yürütülüyor. Native not UI olayları da bu core'a gider.
- Modelin not aktarım onayı olmadan not yetkisi yok; yeni uyku aracı not
  yetkisini genişletmez. Desktop dışındaki kaynaklara yeni yetki verilmedi.
- Mikrofon, wake-word, Live socket, ses oynatma ve pencere/ayar/anahtar yaşam
  döngüleri mevcut sahiplerinde kalır. Bunların doğrudan host kontrolü olması
  tek başına mimari ihlal değildir; doğal dil komutu çözümleyicisi değildirler.
- Uyku aracı kabulü yalnız bekleyen istek üretir (`applied=false`). Başarılı
  konuşma/çalma ve gerçek `sleep_start` sonucu ayrı; eski araç replay'i yeni
  geçiş üretmez. Stop/unknown/başarısız turda istek uygulanmaz.

## Doğrulama sınırı

Sentetik SDK/HTTP/WebSocket testleri, core ve native WebView2 kontrolleri
kullanılır. Gerçek hesap, kullanıcı notları veya ücretli API kullanılmaz.
Sentetik sağlayıcının doğru aracı seçmesi, gerçek modelin bütün doğal dil
varyasyonlarını doğru seçeceğinin kanıtı değildir. Kullanıcı kabulü ayrıca gerekir.

Son kanıt: 873 tam pytest + son ek Stop testi dahil 17 hedefli araç testi,
7 JS süiti, Pyright 0 hata/uyarı ve [10/10 native](stage5-sleep-tool-native.json).
İlk native koşuda chat başlangıcı hazır olma zaman aşımı verdi; sonraki izole
chat ve tam koşu geçti. İlk hatanın nedeni kesinleşmedi. Dört eski katalog
beklentisi yeni aracı içerecek şekilde güncellendi; not izinleri dar kalıyor.
