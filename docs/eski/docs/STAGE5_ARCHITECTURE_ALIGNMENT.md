# Aşama 5 — ortak mimari uyum kontrolü

## Güncel 5.R8.2–5 bağlantı düzeltmeleri

Timer bitişindeki sabit boss/say yolu kaldırıldı. Host gerçek Clocks kaydını
onaylayıp mevcut TextChat/PersistentLive ile, boş araç kataloğunda bildirir.
Modelden doğal dil eylemleri aynı registry/policy/TaskManager hattında kaldı;
bildirim hiçbir eylem izni eklemez. UI poll görünümü ve boşta bildirim kuyruğunu
besler; ikinci worker, zamanlayıcı, mikrofon veya ses oynatıcı yoktur.
Katalog otomatikleşti; var olan credential/model ayarı depoları kullanıldı.
noise/wake sürgülerinin gösterilip uygulanmayan kısmı kendi sahiplerine bağlandı.
Diğer planlı eksik entegrasyonlar aşağıda açık kalır; debloat/kapanış yapılmadı.

23 Ekim 2026. Kapsam: kaynak kodda model → araç → core akışı, UI olayları ve
mevcut veri/kaynak sahipliği. Tüm donanım ve gelecek entegrasyonların çalıştığı
iddia edilmez. 5.R4 uyku geçişini, 5.R5 not hedeflerini ortak hatta taşıdı;
diğer bulguların uygulaması bu adımda açılmadı.

| Durum | Bulgu ve kaynak | Gerekli işlem |
|---|---|---|
| 5.R4'te taşındı — kullanıcı kabul etti | Uyku kararı `sleep_intent.py` cümle kalıplarındaydı | Dosya kaldırıldı. `assistant.request_sleep_mode` artık ModelTools → registry/policy/TaskManager yolunda. Kullanıcı test onayıyla 5fb30d3 commit'ine alındı. |
| 5.R5'te taşındı — kullanıcı kabul etti | `model_tools.py::_check_note_target` içindeki son not ve içerik filtresi cümle kalıpları kaldırıldı | Kayıtlı `notes.select` gerçek ID/cardinality/snapshot üretir; tekli mutasyon ve atomik `notes.delete_many` aynı core hattını kullanır. 5.R6 `notes.complete_many` ile aynı tam-grup tamamlamayı ekler; metin/ID/tarih korunur. Belirsizlik, taze seçim, tarih, Stop/unknown/replay koruması sürer. |
| Açık — rutin/skill yürütme entegrasyonu | `ui/js/routines.js::runRoutine` ve `skills.js::runSkill` desteklenmeyen `run_routine/run_skill` olaylarını gönderiyor; bridge bunları not_implemented olarak reddediyor | Registry/policy/TaskManager yürütücüsü eklenmeden çalışır özellik sayma. Timeline'daki “Routine started” / “Skill run” kayıtları gerçek kabulden önce üretiliyor; kabul ile başlama ayrılmalı. |
| Açık — rutin sahiplik devri | `routines.js::initRoutines` içinde UI'a ait 15 s aralıklı zaman denetimi ve app/Wi-Fi tetikleme girişi var | Backend scheduler eklendiğinde aynı anda iki tetikleyici bırakma; UI scheduler'ı kapat ve tek yürütme sahibine geçir. Şu an ikinci backend scheduler yok. |
| Planlı eksik kapsam | Rutin/skill tanımları UI store/localStorage'da saklanıyor; native `validate_settings` bunları settings.json'a yazmıyor. Sayaç/kronometre 5.R7.2’de tek backend Clocks sahibine ve clocks.create/list/control araçlarına taşındı; tarayıcı-only tekli görünüm ayrı ortamda korunur | Modele açıldıklarında yapılandırılmış araç/tek veri sahibi kullan. Generic save'e ikinci mutasyon bağlama. Yerel UI işlevini bugün bozma. |
| Planlı eksik bağlantılar | `settings.py` profil pMem/pSys/pGreet/pBr ve conn.voice alanlarını saklayabiliyor; `model_instruction.py` yalnız pLang/pIns'i model talimatına bağlıyor. pWake yerel motorda, pSc UI kısayollarında kullanılıyor. Live setup ses seçimi geçmiyor; REST TTS Kore kullanıyor | Kaydedilebilir alanı çalışır özellik sayma. Kullanıcı hafızası ve ses/persona tercihleri aşamaları geldiğinde mevcut sahiplerine bağlanmalı; gizli veya bütün profil alanları kendiliğinden modele aktarılmamalı. |
| Planlı eksik kapsam | Hava durumu, Google, Telegram, Discord vb. için çalışan core aracı henüz yok | Bunlar dil değiştirerek çalışmaz. Aşamaları geldiğinde sağlayıcı adaptörü ve ortak araç/izin hattı eklenmeli. |

## 5.R7.2 eklemesi — çoklu timer/stopwatch

Native tek Clocks örneği bootstrap ve bridge tarafından paylaşılır. Model ve
UI mutasyonları kayıtlı clocks araçları/policy/TaskManager hattındadır. Salt
host görünüm okuması bu nesnenin snapshot'ıdır; her UI tiki görev açmaz.
Yerel fallback motoru native başladığında durur; köprü kaybıyla tekrar açılmaz.
UI id ile kayıt seçer, model işlemi doğru sekmeye geçer. Yeni framework,
servis worker veya kalıcı veri otoritesi yoktur. Uygulama kapanışı saatleri bitirir.

## 5.R7.1 eklemesi — uygulama kapanışı

assistant.request_shutdown aynı ModelTools/registry/policy/TaskManager hattındadır.
Core pencere kapatmaz; yanıt/çalma sonrası uygulama mevcut Shutdown host sahibini
çağırır. Düğmeyle ikinci kapanış yolu kurulmadı. Stop/eski tur/unknown/replay
korunur; OS shutdown yetkisi yoktur. 5.R7.1 sırasında sayaçlar sonraki dilimdi; 5.R7.2’de yukarıda açıklanan
tek Clocks sahibine taşındı.

## Korunan doğru sınırlar

- Not CRUD'u ve uygulama araçları bootstrap'ta kayıtlı, policy denetimli ve
  TaskManager üzerinden yürütülüyor. Native not UI olayları da bu core'a gider.
- Modelin not aktarım onayı olmadan not yetkisi yok; yeni uyku aracı not
  yetkisini genişletmez. Desktop dışındaki kaynaklara yeni yetki verilmedi.
- 5.F4 wake varyasyonları tek yerel wake_spellings tanımında KWS/Live hitap
  kontrolünü paylaşır. Bu doğal dil eylem parser’ı veya yeni araç yürütücüsü değildir.
- Mikrofon, wake-word, Live socket, ses oynatma ve pencere/ayar/anahtar yaşam
  döngüleri mevcut sahiplerinde kalır. Bunların doğrudan host kontrolü olması
  tek başına mimari ihlal değildir; doğal dil komutu çözümleyicisi değildirler.
- Uyku aracı kabulü yalnız bekleyen istek üretir (`applied=false`). Başarılı
  konuşma/çalma ve gerçek `sleep_start` sonucu ayrı; eski araç replay'i yeni
  geçiş üretmez. Stop/unknown/başarısız turda istek uygulanmaz.

## Doğrulama sınırı

Güncel 5.R5 kanıtı: 885 tam pytest, son değişiklik sonrası 62 seçim/batch
regresyonu, 7 JS süiti, Pyright 0 hata/uyarı, REST/Live batch chat ve
[tam native 10/10](stage5-note-selection-batch-native.json). Seçim ile yazı
arasında veri değişiminde ret, tek yazı, geri okuma, Stop ve replay sınandı.
5.R5 gerçek kullanıcı kabulü başarılı; `2120113` commit’ine alındı. 5.R6 tamamlamanın kullanıcı kabulü de başarılı.

Sentetik SDK/HTTP/WebSocket testleri, core ve native WebView2 kontrolleri
kullanılır. Gerçek hesap, kullanıcı notları veya ücretli API kullanılmaz.
Sentetik sağlayıcının doğru aracı seçmesi, gerçek modelin bütün doğal dil
varyasyonlarını doğru seçeceğinin kanıtı değildir. Kullanıcı kabulü ayrıca gerekir.

Önceki 5.R4 kanıtı: 873 tam pytest + son ek Stop testi dahil 17 hedefli araç testi,
7 JS süiti, Pyright 0 hata/uyarı ve [10/10 native](stage5-sleep-tool-native.json).
İlk native koşuda chat başlangıcı hazır olma zaman aşımı verdi; sonraki izole
chat ve tam koşu geçti. İlk hatanın nedeni kesinleşmedi. Dört eski katalog
beklentisi yeni aracı içerecek şekilde güncellendi; not izinleri dar kalıyor.
