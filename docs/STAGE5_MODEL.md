# Aşama 5 — Model, araç çağrıları ve ses


23 Ekim 2026: kullanıcı çoklu timer/stopwatch testlerini başarılı bildirdi.
Bu onay önceki sayaç kapsamına aittir; sonraki görsel/ses tweak’lerini kapsamaz.

## Güncel 5.R8.1 — sayaç seçici tema ve seçim sesi

5.R7.2 kullanıcı tarafından kabul edildi; af834ff commit’inde (push yok).
Bu dilimde yerel select korunarak tema/odak/ok stilleri eklendi; kullanıcı
change olayında mevcut sfx.blip çalar. Poll/model odağı ses üretmez; kayıt ID,
New, backend sahipliği ve Stop/unknown sözleşmesi değişmedi.

Doğrulama: 9 JS süiti geçti; sayaç testinde seçim gerçek ID’yi korudu, tek ses
üretti ve backend mutasyonu üretmedi. [Native chat](stage5-clock-selector-native-chat.json)
exit=0, ok=true: gerçek WebView2’de iki farklı tema rengi ve genişlik; mevcut
REST/Live çoklu sayaç/sekme, notlar, Stop, mikrofon ve uyku senaryoları geçti.
Native stderr içinde mevcut testin 30 saniyelik faulthandler durum dökümü var;
sonrasında test tamamlandı (exit=0). Döküm raporda korundu; bu temiz stderr iddiası değildir.
Bu tur tam pytest/10 süreç native tekrarlanmadı; Python üretim kodu değişmedi.
Gerçek hesap/API veya fiziksel kullanıcı verisi kullanılmadı. Fiziksel ses,
açık dropdown görünümü ve klavye kabulü kullanıcıda; yeni commit henüz yok.

Timer bitişindeki sabit say('Timer finished, boss.') ses üretmiyor ve kişisel
hitabı izlemiyor; bu açık 5.R8.2’de mevcut model/ses yaşam döngüsüyle ele alınacak.
5.R8.3–5 planı aşamalar.md’de; Aşama 5 kapanmıyor.

## Güncel 5.R7.2 — çoklu timer/stopwatch ve otomatik sekme

Önceki wake/shutdown dilimi kullanıcı onayıyla `20c755c` commit'ine alındı.
Bu dilimde native sayaç otoritesi tek RAM Clocks nesnesine devredildi. main aynı
nesneyi bootstrap ve NativeBridge'e enjekte eder. UI ve model create/control
mutasyonları aynı registry/policy/TaskManager hattına girer. Yeni framework,
worker/scheduler, disk dosyası veya bağımlılık eklenmedi.

Kayıtlı araçlar clocks.create/list/control'dür; ayrı clocks.read/write izinleri
vardır. Gerçek UUID, kind, etiket, ayarlı süre, durum ve generation korunur.
Birden çok timer ve stopwatch birbirini ezmez. Pause zamanı tutar; start devam
ettirir; reset durdurur ve timer ayarlı süreye, stopwatch sıfıra döner. Model
mevcut kontrol için bu turdaki yeni list/create sonucunun ID'sini kullanır;
eski okuma/replay yeni hedef kanıtı üretmez. Hedef belirsizse modelden açıklama
istenmesi talimatı vardır; kullanıcı cümlesini eşleyen özel niyet kodu yoktur.

Monoton saat tek sahibi tarafından hesaplanır. Native UI 500 ms salt snapshot
sorgular; her tik TaskManager kaydı açmaz, mevcut 256 kayıt kapasitesini poll ile
doldurmaz. UI sonucu sampled_at ile sıralar; eski sonuç daha yeni zamanı ezmez.
Modelin doğrulanmış create/control sonucu gerçek ID'ye ve ilgili sekmeye odaklar.
Timer açıkken stopwatch açtırma ve tersi, REST/Live native testinde doğrulandı.
Dropdown/New ve mevcut düğmeler aynı kayıtlara gider. Native başladıktan sonra
bridge kaybı ikinci yerel motor açmaz; hiç native başlamamış browser-only modun
eski tekli motoru korunur. Bu nedenle eski timers.js fallback'i bu tur silinmedi.

Başarı RAM durumundan geri okunur. Stop öncesi iptal, geç Stop'ta gerçek sonucun
korunması, çağrı tekrarı, eksik ID ve unknown kuralları korunur. UI'da unknown
mutasyonlar yeniden açılışa kadar kilitlidir; salt okuma mutasyon yetkisi değildir. Model turu ve belirsizlik boyunca mevcut sohbet kilidi UI
sayaç mutasyonlarını da engeller; süreler/okuma doğal olarak devam eder.
SFX tick/alarm ve bitme bildirimi id/generation ile tekrar etmez; ilk açılışta eski
finished kayda alarm yoktur. Alarmlar UI çalışmasına bağlıdır; OS alarmı değildir.
Set düğmesi reset ile opsiyonel duration_seconds kullanarak seçili timer’ın
süresini değiştirir; ID ve diğer kayıtlar korunur. New ise yeni kayıt oluşturur.
Kayıtlar uygulama kapanınca biter. Kalıcılık ve sayaç silme bu dilimde yoktur.

Doğrulama:

- Son tam regresyon **980 pytest** geçti; pause/deadline yarışı, Set ile aynı
  ID’de süre ayarı ve 20 sayaç testi buna dahildir. Son **40 sayaç/profil testi**
  ayrıca doğrulandı. Sahiplik, bağımsız kayıtlar,
  monoton süre, reset/resume, replay/Stop ve UI unknown sınırları denetlendi.
- **9 JS süiti** geçti; yeni clocks testi otomatik sekme/ID, geç snapshot, gerçek
  UI komut payload'ı, alarm, unknown, native latch ve ayrı browser fallback içerir.
- app, yeni saat testleri ve native runner için **Pyright 0 hata/uyarı**.
- [Tam native kontrol](stage5-clocks-native.json) **10/10 geçti**. Her REST/Live
  modunda iki timer + bir stopwatch, diğer sekmeden otomatik doğru ID/sekme,
  model pause/reset, UI start/pause/resume/reset, Set ile aynı timer ID’sinde
  süre ayarı ve toplam altı kaydın korunması
  doğrulandı; outbound settings save yankısı yoktu. Önceki shutdown, uyku,
  mikrofon, not, bilinmeyen sonuç ve kaynak temizliği regresyonları da geçti.
- İlk tam koşuda maksimum 16000 karakter kişisel talimatla toplam sistem metni
  20000 sınırını aştı (4 profil kontrolü). Yeni tekrar eden saat açıklaması
  kısaltıldı; sınır yükseltilmedi veya kullanıcı metni kırpılmadı. Tekrar tam koşu
  geçti. İlk yeni tip kontrolünde duration daraltması ve testte isim çakışması;
  JS fake DOM'da log stub'ı eksikti; bunlar düzeltilip tekrar doğrulandı.

Gerçek hesap, ücretli API, kullanıcı notu veya fiziksel mikrofon kullanılmadı.
Gerçek modelin yeni şemayı ve kullanıcı ifadelerini seçmesi USER_ACCEPTANCE.md
kısa testini bekler. Yeni commit manuel onaydan sonra; Aşama 5 kapanmadı.
Son 1–2 kullanıcı tweak'i ve kapsamlı olmayan hedefli debloat/kapanış bakımı
önümüzdeki adımlar. Kalıcı kullanıcı hafızası/dış entegrasyon başlatılmadı.

## Önceki 5.R7.1 — modelden TaskVex kapatma

Kullanıcının verdiği kapsam iki dilime ayrıldı: bu tur shutdown, sonraki 5.R7.2
çoklu timer/stopwatch. Mevcut timer UI'ı yalnız birer yerel örnek tuttuğu için,
çoklu kullanım aynı anda ikinci yürütme yolu eklenerek çözülmeyecek; ayrı ID'li
tek backend sahipliği ve UI görünümü birlikte ele alınacak. Bu tur sayaçlar
modele açılmadı. 5.F4 wake manuel kabulü bildirilmedi; commit yapılmadı.

Model assistant.request_shutdown({}) aracını ModelTools/registry/policy/TaskManager
üzerinden çağırır; scope=taskvex, applied=false kabulüdür. Uyku ile aynı
assistant_control_request çıkarımı, yalnız başarılı yeni turda shutdown_requested
üretir. Eski call replay'i, başarısız araç, Stop, unknown veya sleep+shutdown
çelişkisi kapanışı başlatmaz. Yanıt/çalma sonrası UI request_id ve connectionRevision
kontrol eder; mevcut Shutdown düğmesiyle ortak shutdownApplication fonksiyonu
aynı native shutdown olayını kullanır. Windows kapanışı, restart veya serbest
shell yürütmesi eklenmedi. Yeni executor/zamanlayıcı/model bağlantısı yoktur.

Host chat/model/kaynak/core temizliği yapmadan pencereyi kapatmaz. Pencere
destroy doğrulanamazsa unknown döner; UI otomatik tekrar etmez ve belirsizlik
kilidini korur. Model cevabındaki başarı metni gerçek kapanış kanıtı değildir.

Personalization wake-word karşılığı: prof.pWake settings.json'a doğrulanarak
kaydedilir. Bridge sleep_start sırasında bu değeri WakeWord'a verir; profil
adı değişirse cache yeni isim için yeniden kurulur. Live wake-only sınıflaması
aynı profile bağlıdır. Vex değeri backend'de gerçek davranışı etkiler.

Otomatik kontroller: 957 pytest; 8 JS süiti (yeni shutdown dahil); app, assistant
araç testleri ve native runner'da Pyright 0 hata/uyarı. İlk tam pytest'te iki eski
not-onayı katalog beklentisi yeni shutdown aracını içermedi; beklentiler güncellendi,
not araçlarının onaya kadar gizliliği korundu ve tam koşu 957/957 geçti.

Native kontrolün ilk tam koşusu chat için 60 s test sınırında durdu. Ayrı chat
kontrolü altı REST/Live shutdown testini geçti fakat sonraki mikrofon aşaması
başarısızdı: sentetik anahtar değişimi model kataloğunu doğru biçimde temizlemiş,
test cleanup'ı kataloğu geri yüklememişti. [Başarısız kayıt](stage5-shutdown-native-chat-failure.json)
korundu; üretim güvenlik kontrolü gevşetilmeden fixture kataloğu geri yükleyecek
şekilde düzeltildi. İlk native komut da yanlış kök cwd nedeniyle dosyayı bulamadı;
v1 cwd ile tekrar başlatıldı. Son [tam native kontrol](stage5-shutdown-native.json) **10/10 geçti**; altı REST/Live
shutdown çalma/Stop/bağlantı kontrolü, gerçek pencere/core kapanışı ve önceki
uyku/mikrofon/not regresyonları başarılı. [Ek teşhis kaydı](stage5-shutdown-native-chat-diagnostic.json)
model listesinin boş ve JS rejection listesinin boş olduğunu gösterir.
Gerçek kullanıcı notu/sesi, hesap veya ücretli API kullanılmadı. Gerçek dil ve
fiziksel kapanış kabulü USER_ACCEPTANCE.md'deki kısa kullanıcı testini bekler.

## Önceki 5.F4 — tek yerel wake tanımında Vex/Veks/Rex

5.R6 kullanıcı kabulü sonrası `cf9179c` commit'ine alındı. Kullanıcının isteğiyle
birleşik uzun kullanım ayrı adımı plandan çıkarıldı. Aşama 5 kapanmıyor; sonraki
5.R7, kapatma gibi mevcut UI kontrollerini yapılandırılmış Vex araçlarına bağlar.
Bu tur o kontroller uygulanmadı.

Yerel KWS ve Live yalnız-hitap kontrolü aynı wake_spellings tanımını kullanır.
Vex/Veks aynı VEX fonem dizisine, Rex ayrı REX dizisine çevrilir; tekrar eden
fonemler tek satıra iner. Özel Computer gibi isimler Vex ailesini açmaz. X/ex/eks
tek başına eklenmedi. Bu, AGENTS.md'de izin verilen yerel akustik hitap kontrolüdür;
doğal dil eylem yönlendiricisi değildir. İkinci mikrofon/model/executor yoktur.

Mevcut sleep_start → yerel PCM → KWS hit/sınır doğrulaması → aynı request_id
ile host wake kabulü → sınırlı Live devri korunur. Yalnız hitap bitince boş görev
üretilmez; hitapla gelen gerçek istek normal model araç hattında kalır. Eski
wake_feed, Mic Off, profil/cache değişimi ve unknown sınırları değişmedi.

Doğrulama:

- **947 pytest**, **7 JS süiti**, app + wake/ses testleri ve yeni smoke betiğinde
  **Pyright 0 hata/uyarı**.
- [Yerel motor testi](stage5-wake-variants-local.json): gerçek hash doğrulamalı
  sherpa-onnx 1.13.8, yapay Windows SAPI sesleri; Vex/Rex olumlu, ex/next/normal
  konuşma olumsuz örnekleri üç restart döngüsünde **15/15** geçti. Olumlu hitlerde
  yerel ses sınırı da doğrulandı. Veks ayrı akustik iddia değildir; Vex fonemlerini
  paylaşır. Sınırlı örnekler bütün aksan/gürültülerde doğruluk kanıtı değildir.
- [Native chat kontrolü](stage5-wake-variants-native-chat.json): gerçek WebView2,
  worklet, host/core; sentetik sağlayıcı ve ayrıca gerçek KWS + mevcut SAPI WAV
  Web Audio'dan geçirildi. Uyku/uyanma devri, Stop/Mic Off ve not regresyonu geçti.
- Yeni `tests/wake_variants_smoke.py` yalnız test aracıdır; uygulamaya TTS veya
  sesli onay eklemez. İlk doğrudan çalıştırma app import yolu eksikliğiyle durdu;
  mevcut native test düzenindeki repo yolu eklenince tekrar geçti.
- Ajan kullanıcı sesi/notu, gerçek hesap veya ücretli API kullanmadı. Fiziksel
  mikrofon kabulü açık; otomatik commit yok. Kullanıcı kısa testi USER_ACCEPTANCE.md.

KWS çoklu fonem satırları mevcut resmi keyword dosyası sözleşmesine uygundur:
[sherpa-onnx keyword spotting](https://k2-fsa.github.io/sherpa/onnx/kws/index.html).

## Önceki 5.R6 — toplu not tamamlama

5.R5 kullanıcı tarafından başarılı doğrulandı, `2120113` commit'ine alındı.
Bu ek adım notes.complete_many(ids, expected_snapshot, done) aracını mevcut
not onayı sonrası REST/Live kataloğuna açar. Aynı notes.select grubu, gerçek
ID'ler, snapshot ve ortak core/policy/TaskManager/_commit hattı kullanılır.
Yalnız done değişir; metin/ID/tarih/sıra/aktarım metadata'sı korunur. Son N,
tümü, contains veya açık ID grupları tamamlanabilir/yeniden açılabilir.
Kapsam genişletme, tekli belirsizliği gruba çevirme ve veri değişiminden sonra
otomatik yeniden seçim yoktur. Yeni NLP parser, executor veya UI save yolu yoktur.

Doğrulama: **929 pytest**, **7 JS süiti**, üretim app ve not hattı testlerinde
**Pyright 0 hata/uyarı**, [native 10/10](stage5-note-completion-native.json).
Native REST/Live son iki/tümü tamamlama, tümünü yeniden açma, ID/metin/tarih
koruma ve panel kutularını gerçek WebView2'de doğruladı; save/note_done yankısı
sıfır kaldı. Toplu silme, ses/Stop/uyku regresyonları da geçti.

İlk geniş Pyright komutuna test_policy.py de dahil edildiğinde **6 mevcut tip
hatası** görüldü: bilerek set verme/read-only alanı değiştirme ve iki eski
optional sonuç daraltması. Yeni araç katalog satırı dışındaki bu kodlar önceki
commit'te aynıdır; bu adımda değiştirilmedi. Son 0 sonucu yalnız yukarıdaki
açık kapsam içindir, tüm test ağacı için temiz tip kontrolü iddiası değildir.
Ajan gerçek hesap/ücretli API veya kullanıcı notları kullanmadı. Kullanıcı
5.R6 testlerini tamamen başarılı bildirdi; manuel kabul ve commit onayı alındı.

## Önceki uygulama — 5.R5 yapılandırılmış not seçimi / toplu silme

Uyku 5.R4 kullanıcı tarafından onaylandı ve `5fb30d3` commit'ine alındı; push
yok. Yeni not adımı henüz kullanıcı kabulü/commit almadı.

Not cümlesi/kelime sırası regex'leri ModelTools'tan kaldırıldı. Model kayıtlı
`notes.select` aracına kind=ids/text/contains/latest/all ve cardinality=one/many
gönderir; core gerçek adayları, selection_ready ve snapshot döndürür. Tekli
update/delete ve yeni delete_many, taze seçimin tam ID kümesine bağlıdır.
Model snapshot'ı expected_snapshot olarak geri verir; worker arada değişen
veriye mutasyon yapmaz. Snapshot yetki anahtarı değildir; taze seçim ve oturum
sahipliği ayrıca ModelTools'ta denetlenir. Ambiguous/başarısız seçimin ardından
aynı turda tahmini ID veya genişletilmiş kapsam kabul edilmez. Yeni kullanıcı
açıklaması yeni tur açar; eski seçim replay'i veya ara transkript açmaz.

Toplu silme tek `_commit` atomik yazısı ve geri okuma kullanır; deleted_ids ve
deleted_count yalnız doğrulanmış sonuçta döner. Başlamamış yazı Stop ile korunur,
geç Stop tamamlanan silmeyi geri almaz; readback kaybı UNKNOWN. ui_migrated,
not ID'leri ve kalan kayıt metadata'sı korunur. Native tekli UI CRUD'u aynı
protokolle sürer; modelin daha dar şemasında snapshot zorunludur. Panel mevcut
tek backend yenilemesinden gelir; yeni save/silme yankısı yoktur.

Son tam pytest 885 geçti; ilk tam koşuda yalnız eski liste→mutasyon planını
kullanan bir ses testi başarısızdı, açık select/snapshot sözleşmesine taşındı.
Eski doğal dil varyasyon testleri yerine yapılandırılmış hedef/izin/tarih/
snapshot/replay testleri vardır; modelin bütün ifadeleri anladığı iddia edilmez.
Pyright testlerdeki None daraltmaları düzeltildikten ve uzun native not
senaryoları fonksiyonlara ayrıldıktan sonra 0 hata/uyarı verdi; bastırma yoktur.
7 JS süiti ve geçici notlarla REST/Live toplu panel kontrolü geçti:
[batch chat raporu](stage5-note-batch-native-chat.json). Gerçek hesap ve kullanıcı
notları kullanılmadı. Manuel kabul USER_ACCEPTANCE.md başındadır.
Son ayrılmış not senaryolarıyla tekrar [tam native kontrol](stage5-note-selection-batch-native.json)
10/10 geçti; REST/Live son iki ve tüm notlar silindi, panel güncellendi,
outbound save/note_del yankısı sıfır kaldı. Son üyelik filtresi küme kullanacak
şekilde sadeleştirildi; ardından 62 seçim/batch testi yeniden geçti.

## Önceki uygulama — 5.R4 ortak uyku aracı

`sleep_intent.py` ve doğal dil regex kararları kaldırıldı. Kayıtlı
`assistant.request_sleep_mode(mode=once|persistent|off)` aracı, desktop REST
ve Live kataloglarına eklendi. Aynı ModelTools → registry/policy/TaskManager
hattı kullanılır; not aktarım onayı/izinleri değişmedi. Araç yalnız doğrulanmış
istek üretir (`applied=false`, `apply_after=reply_playback`). Yalnız başarılı
yanıt sonrasında rapora alınır; UI mevcut ses bitişinden sonra aynı host
geçişini ister. Önceki turun task_id'si, Stop, hata, unknown, başarısız araç
ve çelişkili kip yeni geçiş oluşturmaz. Başarı cümlesi tek başına etkisizdir.

Sabit yerel onay sesi geri eklenmedi; uyku/wake/mikrofon sahipleri korunur.
Diğer mimari sapmalar ve eksik bağlantılar
[uyum raporunda](STAGE5_ARCHITECTURE_ALIGNMENT.md). Gerçek sağlayıcı/doğal dil
kabulü henüz yapılmadı; sentetik sağlayıcının seçimini gerçek model başarısı
diye sunmuyoruz. Yeni manuel test USER_ACCEPTANCE.md başındadır.

İlk tam testte dört katalog beklentisi eski araç listesini beklediği için
başarısızdı; yeni aracı açıkça içerecek şekilde güncellendi, not araçlarını
onay öncesi kapalı tutma kontrolü korundu. Son tam pytest 873 geçti; eski regex
eşleşme testleri kaldırıldı, yerlerine ortak araç/izin/sonuç testleri geldi.
Son ek gerçek Stop testi dahil 17 araç testi, 7 JS süiti ve Pyright 0 geçti.
İlk native çoklu koşusu chat başlangıcında hazır olma zaman aşımı verdi;
sonraki izole [chat kontrolü](stage5-sleep-tool-chat.json) geçti. İlk native
başlangıç hatasının nedeni kesinleştirilmedi; testte süre sınırı uzatılmadı.
Son yeniden çalıştırılan [tam native kontrol](stage5-sleep-tool-native.json)
10/10 geçti; Stop, model yanıtı/ses bitişi, kalıcı mod ve gerçek host geçişi
mevcut WebView2 hattında doğrulandı. Sağlayıcı ve mikrofon yine sentetiktir.

## Önceki uygulama — 5.R3 yerel sesli onayı kaldır

Varyant takibi: kullanıcı “kalıcı uyku moduna geç” ifadesini bildirdi. Parser'da
“kalıcı olarak” zorunluluğu vardı; “olarak” isteğe bağlı yapıldı. TR aç/etkinleştir,
EN stay/remain asleep, keep sleeping, permanent/persistent sleep mode ve
disable/turn off/exit eşdeğerleri aynı tam-cümle kontrolüne eklendi. Soru,
olumsuzluk, alıntı ve birleşik iş reddi korunur; modelin doğal yanıtı/çalması
sonrasında geçiş değişmedi. 955 pytest ve
[native chat](stage5-sleep-phrases-native-chat.json) geçti; bildirilen Türkçe
açma + İngilizce kapatma UI hattından doğrulandı. Gerçek API/mikrofon kullanılmadı.
İngilizce model talepleri ve yerel sınırlı uyku dilbilgisi aynı kapsam değildir;
her serbest ifade veya henüz bağlanmamış özellik çalışıyor sayılmaz.

Kullanıcı 5.R2 testlerini başarılı bildirdi ve ayrı sentetik sesli onayları
istemediğini belirtti. Altı WAV, bu kliplerin fetch/decode/oynatma metodu,
yerel onay metinleri ve model yanıtını kesip local_sleep üreten yollar kaldırıldı.
Mevcut model talimatı kısa doğal onayı ister; ifade kodda ezberlenmez.
Host parser yalnız başarılı model yanıtı sonunda istenen modu bildirir.
UI aynı PCM kuyruğunun bitmesini bekler, ardından gerçek host uyku kabulünü
ister. Stop/yeni giriş/hata/unknown değişikliği onaylamaz. off da yanıt sonrası
uygulanır. Düğme/timer/görev sonrası dönüş ek yanıt gerektirmez.

Önceki 5.R2 commit'i: ae384cb. Kullanıcı bu düzeltmenin commit'ine de açık izin
verdi. Gerçek API çağrısı veya kullanıcı notları kullanılmadı; yeni davranışın
fiziksel kabulü ayrıca yapılacak. 923 pytest, 7 JS süiti ve Pyright 0 hata/uyarı
geçti. [10/10 native raporu](stage5-natural-sleep-reply-native.json), gerçek
WebView2/çalma hattında yanıt bitmeden uyumamayı doğrular; sağlayıcı ve mikrofon
sentetiktir. Kanıt ve sonuçlar [aşamalar.md](../aşamalar.md).

Ek Stop/çalma testi ilk denemede ikinci komutu mikrofon yeniden hazırlanırken
gönderdiği için beklenen ikinci yanıt oluşmadı; Stop'un uykuyu engellediği
kontrol zaten geçmişti. Başarısız kanıt silinmedi:
[zamanlama raporu](stage5-natural-sleep-stop-timing-failure.json).
Test, yeni komuttan önce mevcut waitingForSpeech durumunu bekleyecek şekilde
düzeltildi; bunun için üretim koduna bekleme veya yeniden gönderme eklenmedi.
[Son chat kontrolü](stage5-natural-sleep-stop-chat.json) geçti: bekletilen
çalma sırasında uyanık kalma, Stop'ta uyumama ve sonraki komutun normal
yanıt/çalma ardından uyutması doğrulandı. Son Pyright yine 0 hata/uyarı.

## Önceki uygulama — 5.R2 sesli girişin 25 s beklemesi

23 Ekim: kullanıcı `PCM sent 14 / events 2 / before input final` bildirdi;
yazılı mesaj yanıtlanıyor, sesli mesaj Thinking'de bekleyip idle timeout alıyor.
Bu ölçüler tek başına iki olayın ne olduğunu veya ses içeriğini kanıtlamaz.
Önceki hibrit VAD'nin bu gerçek hataya kesin neden olduğu iddia edilmedi.

Sesli setup şimdi otomatik VAD kapalıyken açık activityStart/PCM/activityEnd
kullanır. Yerel 700 ms sessizlik ve tampon korunur; kesin transkript/gerçek
çıktıyla erken kapanan girişin de eksik activityEnd'i tamamlanır. Stop sonrası
yeni gönderim/retry/komut tekrarı yoktur. Süre sınırını kısaltarak hata gizlenmedi.
Timeout tanısı input end: sent/missing ve speech chars ekler.

14 paket, iki ara transkript ve final bayrağı olmadan yalnız activityEnd'de
yanıtlayan sentetik SDK/socket testi geçti; gerçek kullanıcı arızasının birebir
yeniden üretimi değildir. Hedefli 165, tam pytest **921**, yedi JS süiti,
Pyright **0 hata/uyarı** ve native **10/10** geçti. Native kanıt:
[stage5-manual-activity-native.json](stage5-manual-activity-native.json).
Native WebView2 gerçektir; mikrofon/sağlayıcı sentetiktir.

Resmi [Live yetenek rehberi](https://ai.google.dev/gemini-api/docs/live-api/capabilities)
bu manual activity protokolünde audioStreamEnd kullanılmamasını belirtir.
Ücretli API/gerçek hesap/gerçek mikrofon kullanılmadı. Fiziksel kabul ve
25 saniyelik beklemenin gerçek hesapta giderildiği doğrulaması **açık**.
Yeni özellik ve commit yok; güncel sıra [aşamalar.md](../aşamalar.md).

## Önceki uygulama — 5.R1 uyku/algılama stabilizasyonu

Kullanıcı sessiz İngilizce onay, gecikme ve Stopped sonrasında Idle'da giriş
almama bildirdiği için F4 önüne inceleme alındı. Tam sonuç, kaynaklar, test
öncesi başarısız yeniden üretimler ve kalan sınırlar:
[STAGE5_SLEEP_STABILITY_REVIEW.md](STAGE5_SLEEP_STABILITY_REVIEW.md).

- Final transkriptte giriş kapatılırken eksik EOS aynı socket sahibinden
  gönderilir. Backend hazır onayından sonra yerel 700 ms sessizlik de EOS
  üretir; sıradaki PCM tesliminden önce EOS veya araç/model replay yoktur.
- Yanıt → normal dinlemede yalnız gürültü tabanı sıfırlanır; yarım aday ve
  ön tampon korunur. Wake devri sonrası kaynak hatası normal Stop/gerçek
  bitiş hattına gider; geçici hatada sınırlı yeni boş capture hazırlanabilir.
- Uyku onayları gerçek host durumundan sonra seçili TR/EN metin + paketlenmiş
  WAV'dır. Aynı LiveAudio sahibi/cihaz/Mute/Stop kullanılır; Gemini TTS veya
  ikinci model çağrısı eklenmedi. Sabit ses, Gemini konuşma sesinden farklıdır.
- Wake ağırlıkları RAM'de; her giriş yeni decoder/ID/boş PCM alır. Aynı
  yapay WAV ile gerçek KWS üç kez uyandırıldı; yeni motor 1036.93 ms,
  restart .19–.21 ms (yerel tek ölçüm; toplam latency değildir).

920 pytest, yedi JS süiti, app/hedefli Pyright 0 hata/uyarı. Native 10/10
ve son hybrid/cache sürümünde ek chat geçti. Raporlar inceleme belgesinde.
İlk ek chat'in zaman varsayımına dayalı Thinking testi başarısızdı; açık
sunucu bariyeriyle düzeltildi ve kayıt saklandı. Fiziksel mikrofon/gerçek
hesap kullanılmadı. Kullanıcının bütün gecikme örnekleri kapanmış sayılmaz.
Yeni özellik yerine birleşik fiziksel kabul sırada; commit/push yok.

## Güncel dilim — 5.F3 uyku niyetinin ortak ayrıştırılması

sleep_intent içindeki ortak tam cümle dilbilgisi değişti; TextChat metni ve
Live'ın kesin ses transkripti aynı once/persistent/off sonucunu kullanır.
“uyku moduna gir”, “kalıcı olarak uyku moduna gir”, “bundan sonra uyku
moduna geç”, “artık uyku modunda kal”, “kalıcı uyku modunu kapat” ve
switch to sleep mode / return to sleep after every task gibi karşılıklar
desteklenir. Hitap zorunlu değildir; lütfen/please başta/sonda, ek boşluk
ve büyük harf normalleştirilir. Kalıcı tercih yine yalnız bu sohbetin RAM'idir.

Eski normalleştirme `?` işaretini atıyordu: `sleep?` komut olabiliyordu.
Artık soru işareti korunarak reddedilir; tırnak/olumsuzluk silinmez. Tam
cümle dışında eşleşme yoktur; alıntı, açıklama, ek iş ve olumsuz talep
yerel uyku kontrolü üretmez. Bu sınırlı TR/EN dilbilgisidir, tüm doğal dili
anlayan yeni sınıflandırıcı değildir. Yerel wake motoru/telaffuzu değişmedi.

Ses transkriptindeki tam aday henüz kesin değilken mevcut çıktı bekletme
hattı korunur. Sonraki parça `girme`, soru veya ek işe dönüşürse model
çıktısı sırayla gösterilir; uyku kontrolü yapılmaz. Kesin niyetin yerel
raporu modelin onay metni değildir; gerçek SLEEPING mevcut sleep_start
host kabulünden sonra gösterilir. Araç yetkisi/core iş mantığı değişmedi.

Kanıt: yeni parser testleri önce 24 başarısız/24 başarılı verdi, düzeltme
sonrası tüm 916 pytest ve yedi JS süiti geçti. App/hedefli Pyright 0 hata/
uyarı. Typed ve ses yolunda once/persistent/off, araçsız sonuç, ret sesinin
bastırılması ve değişen adayın güvenli geri bırakılması test edildi. Native
10/10 geçti: stage5-f3-native.json; mevcut WebView2 senaryosunda yeni hitapsız
tek seferlik ifade ve kalıcı gir ifadesinin gerçek host durumuna bağlanması doğrulandı.

Kullanıcı devam izni verdi, yeni manuel başarı bildirmedi; runtime commit/
push yok. Fiziksel mikrofon/sağlayıcı denenmedi; F2 uyanış/25 s bildirimi
açık tutuldu. Sıradaki F4 yerel wake telaffuzu ve yanlış uyanma deneyleridir.

## Güncel dilim — 5.F2 mikrofon canlılığı / 25 s tanısı

F1 sonrasında kullanıcı uyanınca komut alınmadığını yeniden bildirdi;
önceki runtime kodu tam kabul edilmiş sayılmadı, commit/push yapılmadı.
Bu tur yalnız F2'nin kaynak toparlanması ve ölçüm kapsamı uygulandı.

live_mic tek AudioContext'in sonradan suspended/interrupted olmasını izler.
Aynı context'e bir resume denemesi, 1 s sınır; ret/takılma/closed durumunda
audio_context_unavailable ve kaynak temizliği. Kullanıcının On/Off tercihi
korunur, aynı cihaz yeniden açılmaz; açık Off/On yeniden hazırlayabilir.
release handler/timer'ı kaldırır; geç resolve/ret eski kaynağı yeni kaynağa
karıştıramaz. Mevcut aktif tur hata/Stop/unknown kuralları korunur.

LiveInput yalnız tamamlanmış SDK send'lerinin paket sayısı ve ilk ses/EOS
zamanını tutar; sunucunun sesi işlediğinin kanıtı değildir. Tur raporunda
input_sent_packets, input_first_sent_ms, input_end_sent_ms, received_events,
last_received_ms ve input_final_ms vardır. Zamanlar turun başlangıcından
itibaren ms, gerçekleşmemiş olay null'dır. received_events probe'a ulaşan
olay sayısıdır; taşıma katmanının tüm kontrol paketleri değildir. İptalde
gönderici bitirildikten sonra ölçümler alınır; ses/metin içeriği eklenmez.

live_idle_timeout durumunda wait_phase: before_input_final / after_input_final
(stream), provider_reply (diğer girişler). UI hata satırı PCM sent/events ve
aşamayı gösterir. Bunlar kesin tanı değildir: sıfır PCM yerel gönderim tarafını,
ses gidip final gelmemesi transkripsiyon/taşıma yolunu araştırmaya yarar.
Mevcut 25 s olay / 120 s toplam sınır ve tekrar etmeme davranışı değişmedi.

Kanıt: 853 pytest, yedi JS süiti, app/hedefli Pyright 0 hata/uyarı. Üç
sentetik timeout yolu, başarılı/ret/asılı resume, eski callback izolasyonu
ve EOS zamanı testlidir. Native 10/10 geçti: docs/stage5-f2-native.json; gerçek
WebView2 ile aynı kaynak suspend/resume, ret sonrası On tercihi ve açık
Off/On toparlanması kontrol edilir. Gerçek mikrofon/API kabulü yoktur.

İlk native çalıştırması yanlışlıkla depo kökünden yapıldı; credentials
senaryosunun ayrı `python -c` süreci `app` paketini bulamadığı için durdu.
Kökte find_spec('app') sonucu False ile doğrulandı. Belgelenen `v1` çalışma
dizininden yeniden çalıştırıldı ve 10/10 geçti; bu ilk deneme başarılı sayılmadı.

**Açık:** kullanıcının gerçek 25 s örneği ve uyanış sorununun tamamı henüz
bu ölçümlerle gözlenmedi; tamamen düzeldi denmez. F3 uyku niyeti ve F4
telaffuz değiştirilmedi. Kısa manuel test docs/USER_ACCEPTANCE.md içindedir.

## Güncel dilim — 5.F1 giriş bitişi / host onaylı uyku

Denetim ve aşama kaydı kullanıcı devam talebiyle `06d8e8f` commit'ine alındı;
önceki kabul edilmemiş runtime değişiklikleri commit'e eklenmedi, push yok.
Bu tur yalnız 5.F1 uygulandı; manuel kabul bekler. Aşama 5 kapanmadı.

U01: LiveInput artık finished=true kullanıcı transkriptinde, boş son transkript
paketi dahil, yeni PCM kabulünü kapatır ve gönderici task'ı bırakır. Bu model
veya core aracı için Stop değildir; gerçek yanıt/araç çalışması aynı receive
hattında devam eder. Düşünce parçası tek başına bitiş sayılmaz. Yeni, ayrı
barge-in girişi ancak normal modun mevcut kontrollü devrinde açılır.

U02: sleepPending ve mevcut createPendingOperation mekanizması ile uyku
hazırlığı gerçek uyku kabulünden ayrıldı. sleep_start bütün kesin sonuçlarda
completed ve sleeping döndürür. UI host sleeping=true demeden SLEEPING/Wake
göstermez; ret halinde uyanık kaldığını açıklar. Motor hazırlanamasa bile
host sleeping=true ise gerçek uyku korunur ve Wake düğmesi kullanılabilir.
Mic Off sırasında geç kabul tercihi On yapmaz. Sonuç yoksa veya 15 s kontrol
süresi aşılırsa Sleep state unknown/genel unknown kilidi kullanılır; eski
cevap yeni kaynak açamaz. Bekleyen uyku sırasında Stop/bağlantı değişimi
sonucu bilinmiyor diye korunur, isteğin geri alındığı varsayılmaz. Mic Off
her durumda kullanılabilir. Bilinmeyen durumda uygulamayı yeniden açmak gerekir.

U05: wake devrindeki 700 ms yerel sessizlik artık işçiyi kapatmaz; yerel
aktivite görünümü ile kesin giriş sonu ayrıdır. 15 s/150 paket ve kuyruk
sınırları korunur. Ayarlı wake sözcüğüyle tam eşleşen kesin ses transkripti
wake_only raporuyla, araç yürütmeden ve yanıt beklemeden kapanır. UI bunu
kalıcı modun tamamlanmış görevi saymaz; asıl isteği dinlemeye döner. Yeni
socket'te eski komut/PCM otomatik tekrar edilmez. Wake-only tanımı yalnız
ayarlı sözcüktür; Rex/X/fonetik tolerans bu tur eklenmedi.

Sınır: Wake kabulünden sonra Live transkripsiyon için açılabilir; wake_only
bir sıfır API çağrısı garantisi değildir. Sağlayıcı kesin transkript/bitiş
olayı hiç göndermezse eski olay süre sınırları kalır. Kullanıcının 25 s
Thinking ve askıya alınmış AudioContext problemi 5.F2'de incelenecek;
bu tur bütün gecikme/Idle sorunları giderildi denmez. Uyku niyeti hâlâ dar
listedendir; “uyku moduna gir” ve esnek TR/EN 5.F3'tür.

Kanıt: 850 pytest, yedi JS süiti; app ve hedefli Python/native dosyalarında
Pyright 0 hata/uyarı. Kesin transkript sonrası yeni PCM reddi ve gerçek
cevabın devam etmesi, wake-only araçsız bitiş, duraklamadan sonraki PCM'in
korunması, ret/unknown ayrımı, Off/timeout/geç cevap ve kalıcı mod görev
ayrımı hedefli testlerde geçti. Gerçek WebView2'nin 10 senaryosu geçti:
stage5-f1-native.json. Son ek chat kontrolü de host reddi ve 600 ms geciken
uyku kabulü ile geçti: stage5-f1-native-chat.json. İkinci JSON yalnız ek chat
kanıtıdır; ilk JSON tüm native senaryoları içerir. 30 s faulthandler tanılama
dökümü süreçten hata çıkışı değildir; son ok:true ayrıca doğrulandı. Gerçek
kullanıcı notu/sesi, üretim hesabı veya ücretli API kullanılmadı.

## Güncel denetim — uyku/ses açıkları yeniden üretildi

Güncel aşama ve adımlar: [aşamalar.md](../aşamalar.md). 843 pytest, 7 JS
süiti, app Pyright 0 hata/uyarı ve 10 native senaryo geçti; ayrıca yapılan
deneylerde beş runtime açık doğrulandı. Bunlar kapanmadı. Rapor:
[STAGE5_SLEEP_AUDIT.md](STAGE5_SLEEP_AUDIT.md); ham sonuçlar:
stage5-general-audit.json ve stage5-general-audit-native.json. Gerçek
sağlayıcı/mikrofon kabulü yoktur. İlk düzeltme paketi giriş/uyku protokolüdür;
niyet/telaffuz ve birleşik kabul bunun ardından gelir. Bu tur uygulama kodu
ve mevcut bekleyen düzeltmeler değiştirilmedi; commit/push yapılmadı.

## Uyku düzeltme planı — kullanıcı anlam düzeltmesi / adım 1

Kullanıcı önceki dilimin işlediğini fakat iki uyku davranışının yanlış
birleştirildiğini bildirdi; tam kabul/commit sayılmadı. Önceki değişiklikler
korundu. Bu tur yalnız aşağıdaki birinci adım uygulanmıştır; sonraki adımlar
kapanmadı ve Aşama 5 tamamlandı denmez.

1. **Uygulandı, manuel kabul bekler:** Stay asleep ile normal idle timer'ını
   ayır. Kalıcı modda çağrılan iş/yanıt/oynatma kesin bitince hemen uyu;
   yanıt boyunca ayrı barge-in mikrofonu açma. Normal konuşmada sleepDelay
   dolunca tek seferlik uyu. Eski timer/unknown/aktif görev engellerini koru.
2. **Açık:** Uyanış sonrası bazen 25 s Thinking ve Idle'da giriş yakalanmaması.
   Hazırlık, PCM/EOS, socket olayları ve yeniden dinlemeye devri ayrı ölçerek
   yeniden üret. 25 s mevcut olay sessizliği sınırıyla aynı olsa da kök neden
   henüz kanıtlanmadı; timeout'u kısaltmak düzeltme sayılmaz.
3. **Açık:** Uyku niyetini farklı Türkçe/İngilizce ifadelerden doğrulanmış
   host kontrolüne dönüştür; sözlü onay gerçek sonuçla uyuşsun. Bugün dar
   tam-ifade listesi vardır. Vex hitabı şart değildir; liste dışı ifade için
   genel model onayı host geçişini garanti etmez. Not araçları bu parser değildir.
4. **Açık:** Rex/X/Vex benzeri telaffuzları yerel KWS'de değerlendirmek;
   yanlış uyanma/arka plan konuşması kontrolleriyle kalibre etmek. Bu tur
   alternatif wake sözcükleri eklenmedi; ASR metni ile yerel algı ayrıdır.
5. **Açık:** Tekrarlı uyku/uyanma, Stop, Mic Off, disconnect, stale/unknown
   ve birleşik kabul. Sonra Aşama 5 kapanış açık sınırları/debloat.

Birinci adımın davranışı: automaticSleep RAM tercihi yalnız Stay asleep'i
ifade eder. Bu modda yanıt dinleyicisi/barge-in açılmaz; rapor completed:true,
unknown:false ve güncel bağlantı ise mevcut enterSleep hattına hemen dönülür.
Çalışan araç/oynatma tamamlanmadan veya yalnız Stop kabulüyle uyutulmaz.
Normal modda bağımsız sleepDelay (default 10, 0–300 tam saniye) kullanılır;
0 timer'ı kapatır. Timer kalıcı modu açmaz, uyandırılınca normal konuşma
sürer. Konuşma/aktif iş/unknown/cihaz engeli ve eski revision kontrolleri kalır.
Kalıcı moddan açık çıkış yalnız o tercihi kapatır; normal idle timer ayarını
silmez. Bu nedenle durum metni artık "Stay asleep mode disabled." der.
Mikrofon On/Off tercihi aynı kalır. Yerel KWS arka planda çalışırken ses Live'a
gitmez; fakat yanlış wake veya adresli görevle aynı anda konuşan başka birini
ayıran konuşmacı tanıma yoktur. Gizlilik fiziksel kabulü ve wake kalibrasyonu açık.

Kanıt: 843 pytest, yedi JS süiti; değişen Python/native dosyalarında Pyright
0 hata/uyarı. Gerçek uygulama fonksiyonlarıyla normal idle uyku/tek-seferlik
tercih, 0 ile kapatma, kalıcı modda timer kullanmama ve kesin bitişte hemen
uyuma, yanıt dinleyicisi açmama ve unknown/stale engelleri doğrulandı.
Native rapor `stage5-sleep-modes-native.json`, geçici profil ve sentetik
sağlayıcıyla gerçek WebView2 kontrolüdür. Uzun regresyonda idle timer test
profili için 0 yapıldı; hedefli bölümde 2 s ile normal uyku doğrulandı.
İlk native denemede fixture henüz yazılmamış settings.json'dan None alıp
.get çağırdığı için başarısızdı; bekleme boş kaydı da ele alacak şekilde
onarıldı. Son turda ok:true ve persistent_task_returns_immediately_and_normal_idle_timer_sleeps_once:true ayrıca doğrulandı. 30 s faulthandler dökümü süreç
başarısızlığı değildir; native final ok bayrağına bakılır. Gerçek hesap,
kullanıcı notu/sesi veya ücretli API kullanılmadı. İlk adım öteki hataları
çözdüğünü iddia etmez. Alttaki açıklamalar eski davranışın tarihsel kayıtlarıdır.

## Güncel dilim — sohbet boyunca otomatik geri uyuma ve mikrofon efekti

Önceki uyku/giriş düzeltmeleri kullanıcı tarafından başarılı bildirildi;
yeni işe başlamadan `701f33f` commit'ine alındı. Gizli anahtar kalıpları
kontrol edildi; push yapılmadı. Bu yeni dilim manuel kabul bekler.

Mikrofon On/Off native yolunda erken return nedeniyle atlanan sfx.blip,
kamerayla aynı click handler başlangıcına taşındı. Her tıklama tek efekt
üretir; global Sound effects/Effects volume tercihi geçerlidir. On/Off'un
giriş, oynatma ve kullanıcı tercihi sözleşmesi değişmedi.

Tam "Vex bundan sonra uyku modunda kal" / "stay in sleep mode" isteği
sleep_mode=persistent olarak host tarafından karşılanır ve uykuya geçer.
Wake sözcüğü/düğmesi veya yazılı mesaj uyandırır; yanıt, oynatma ve varsa
araçların kesin bitişinden sonra boşta süre başlar. Süre dolunca mevcut
enterSleep/sleep_start hattı yeniden kullanılır; yeni model/tool/worker yoktur.
"Vex uyku modundan kalıcı olarak çık" / "disable automatic sleep" off sonucu
verir: awake kalınır ve geri uyuma kapanır. Tek seferlik uyku once olarak
kalır, daha önce açılmış kalıcı tercihi kendiliğinden iptal etmez. Soru,
alıntı ve birleşik istekler kontrol komutu sayılmaz; gerçek yan etkili araç
başlamış ses turu uyku kontrolüne çevrilmez.

Tercih sohbetin UI RAM'inde tutulur; New Chat, uygulamayı kapatma veya açık
off komutu temizler. Disconnect/model/anahtar değişimi/Stop/pagehide/eski
revision zamanlayıcıyı iptal eder; aktif/unknown/cihaz engeli veya konuşma
varken otomatik uyku açılmaz. Yeni sağlıklı idle dinleme/etkileşim sonrası
kalıcı tercih devam edebilir. Mikrofon Off yalnız kullanıcı girişini kapatır;
kalıcı tercihi silmez ve otomatik uyku yerel mikrofonu kendiliğinden On yapmaz.

Ayarlar → Audio içinde sleepDelay, 1–300 tam saniye (default 10) olarak
settings.json'a yazılır; snapshot/import/export/yerel başlangıç/arayüz reset'i
aynı alanı taşır. Profil/wake sözcüğü yerinden taşınmadı. Süre değişince
uygun idle durumda sayaç yeniden kurulur. Geçersiz disk/UI save şeması
reddedilir; bozuk snapshot alanı diğer mevcut toleranslı alanlar gibi atılır.

Kanıt: 842 pytest, yedi JS süiti, değişen Python/native dosyalarında Pyright
0 hata/uyarı. Tam komut ayrımı, typed+voice host sonuçları, kayıt/read-back,
snapshot alanı ve süre/konuşma/active/unknown/stale guard'ları doğrulandı.
Gerçek WebView2, geçici profil ve sentetik sağlayıcı ile iki saniye ayarı,
Wake sonrası yeniden uyuma, açık off ile uyanık kalma ve Mic Off'un korunması
geçti; bu kontrol ek Live isteği açmadı. Mikrofon On/Off'un her birinde tek
kamera blip çağrısı da doğrulandı. `stage5-auto-sleep-native.json` bu native
kontrolün raporudur; gerçek kullanıcı verisi/sesi/hesabı içermez. İlk hedefli
komutta var olmayan test_settings.py yolu kullanıldığından test çalışmadı;
doğru testler ve son tam regresyon geçti. Fiziksel mikrofon/efekt duyumu ve
ücretli API bu tur denenmedi. Snapshot whitelist'i son kaynak incelemesinde
sleepDelay ile tamamlandı ve ilgili JS/native kontroller tekrar çalıştırıldı.
Son native turda 30 s faulthandler tanılama dökümü oluştu; süreç hata ile
çıkmadı, ok:true ve iki yeni kabul bayrağı doğrulandı. Döküm test başarısızlığı
veya gerçek API zaman aşımı olarak sunulmadı.

Source: Mic göstergesi mic_only/system_audio/app_audio UI sözleşmesidir;
mevcut native backend yalnız mikrofonu kullanır, PC/uygulama ses yakalaması
uygulanmadı. Bu dilimde yeni ses kaynağı entegrasyonu yapılmadı. Sonraki iş,
uyku kabulünün ardından Aşama 5 kapanışındaki açık sınırlar/genel kabul ve
ölçülü debloat kontrolüdür; bu tur Aşama 5 tamamlandı denmez.

## Güncel düzeltme — wake yanıtı, uyku çıktısı ve iki durumlu mikrofon

Kullanıcı wake sözcüğüyle uyanmanın çalıştığını, bazen Thinking sonrası yanıt
alamadığını ve uykuya geçerken modelin ana bilgisayar erişimi istediğini
bildirdi. Önceki dilimin tam kabulü sayılmadı; mevcut değişiklikler commit
edilmedi. Bu dilim aynı hataları tamamlar, yeni özellik aşaması açmaz.

R5: thought-only model_turn giriş sonu değildir. Gerçek kullanıcıya açık
metin/ses, araç çağrısı veya tur bitişi eski girişi kapatır. R4: wake devrinde
700 ms yerel sessizlik açık EOS üretir; kısa tek wake sözcüğü sunucu VAD'sinde
kaçırılsa da giriş sonsuz beklemez. 15 s/150 paket sınırı Stop/micBlocked
üretmez; yalnız girişi bitirir ve model yanıtını bekler. Wake ön tamponu da
150 pakete dahildir. EOS tüm önceki PCM onaylandıktan sonra gider; eski
kaynak callback'i yeni mikrofonu kapatamaz. Bu enerji eşiği gerçek konuşma
sınıflandırıcısı değildir; fiziksel kabul hâlâ gerekir.

Tam uyku transkripti adayı kesinleşene kadar gelen çıktı RAM'de bekler;
bitince host uyku sonucu verir, ret sesi oynatılmaz. Aday soru/başka isteğe
dönüşürse bekleyen olaylar sırayla işlenir; araçlar iki kez çalıştırılmaz.
Tampon en fazla 64 olay/2 MB, mevcut 25 s sessizlik/120 s tur sınırlarına tabidir.
Kişisel talimat yetki vermez; ortak model talimatı uyku isteğine ana bilgisayar
izni istemek yerine kısa onay vermesini söyler. ASR doğru ifade üretmeden
önce oynatılmış sesi geri alma garantisi yoktur; model talimatı tek başına
uyku yetkisi değildir. Uykuya yalnız host karar verir.

Kullanıcı isteğiyle micB yalnız Microphone On/Off, ışık ve aria-pressed ile
kullanıcı giriş tercihini gösterir. Retry/Blocked/Thinking/bağlantı/kurulum
ışığı etkilemez ve düğmeye yeni mod eklemez. On gerçek donanım garantisi
değildir; hatalar ayrı durum satırı ve log'dadır. On/Off yanıt oynatımını
kesmez; cihaz/izin/unknown güvenlik kapıları arka planda korunur.

Kanıt: 825 pytest, yedi JS süiti ve Pyright 0 hata/uyarı. Yeni kontroller:
thought sırasında giriş açık; kısa wake sessizliği EOS; yavaş PCM ön tamponu
atlamadan EOS; toplam 150 paket; uyku adayında ret sesini tutma ve soru olursa
sırayla bırakma. Gerçek WebView2 chat regresyonu sentetik sağlayıcı/geçici
profille geçti: stage5-wake-response-native.json. İlk native tur hata halinde
On ışığının sönmesini bekleyen eski assertion nedeniyle başarısızdı; yeni
On/Off sözleşmesine göre düzeltildi, son tur geçti. Bu JSON dosyası native
kontrol kanıtıdır, kullanıcı verisi veya gerçek hesap sonucu değildir.
Fiziksel kullanıcı mikrofonu ve gerçek/ücretli sağlayıcı bu tur kullanılmadı.

R4–R5 için kod ve sentetik kanıt tamamlandı, fiziksel tekrar kabulü bekler.
Bunlar onaylanmadan otomatik geri uyuma/saniye ayarı veya Aşama 5 kapanışına
geçilmez. Önceki alt başlıklar tarihsel kayıttır; güncel micB davranışı budur.

## Güncel kabul — R2–R3 toparlanma ve küçük R1 düzeltmesi

Önceki R0 adımı kullanıcı tarafından başarılı bildirildi ve yeni işe başlamadan
`616125d` commit'ine alındı; push yapılmadı. Aşağıdaki yeni dilim manuel kabul
bekler; alttaki eski adım kayıtları tarihsel doğrulama kapsamını gösterir.

Yerel wake kuyruğu dolduğunda, ön tampon eskidiğinde, zaman sınırı
kanıtlanamadığında veya yerel paket teslimi onaylanmadığında eski kaynak ve
PCM bırakılır. Uyku/On/idle durumunda en fazla iki yeni kaynak hazırlanır;
her deneme 250 ms sonra güncel mikrofon ve bağlantı revision'ını denetler.
Bütçe açık Sleep veya Mic On ile sıfırlanır; başarılı kaynak hazırlığı bütçeyi
sıfırlamaz. Eski ses, model isteği ve araç işlemi yeniden yürütülmez.
Off, Wake, Stop, Disconnect, sayfanın kapanması ve unknown kilidi bekleyen
tekrarı iptal eder. İzin, cihaz, kurulum, bozuk paket ve Live'a devir hataları
otomatik tekrar edilmez; nedeni görünür ve açık kullanıcı işlemi gerekir.
Açık Sleep önceki yerel mikrofon engelini yeniden deneyebilir; Off tercihi,
Disconnect ve unknown engeli korunur. On ışığı kullanıcı tercihini korur;
Retrying/Blocked etiketi ve açıklaması gerçek kaynak durumunu ayırır.

R1: ASR'nin `Veks, uykuya dal` yazımı yalnız tam uyku ifadesinin hitabı olarak
kabul edilir. Soru, alıntı ve birleşik istekler uyutmaz; genel komutlarda veya
not hedeflerinde bulanık eşleşme eklenmedi.

Kanıt: 821 pytest, yedi JS süiti geçti; değişen Python/native dosyalarında
Pyright 0 hata/uyarı. `stage5-wake-recovery-native.json`, geçici profil ve
sentetik sağlayıcıyla gerçek WebView2/AudioWorklet kontrolünün raporudur:
ilk yerel paket onayı 1400 ms geciktirilip kuyruk taşması oluşturuldu; yeni
yerel kaynak açıldı, On korundu, Live açılmadı. Cihaz capture bitişi açıklaması
ve açık Sleep ile yeniden hazırlık da geçti. İlk native tur eski genel hata
metni beklentisiyle, ikinci tur host uyanınca henüz etkinleşmemiş Sleep'e
tıklayan fixture nedeniyle başarısızdı. Fixture gerçek UI hazırlığını bekleyecek
şekilde düzeltildi; son tur geçti. Başarısız denemeler başarı diye sayılmadı.
Gerçek kullanıcı verisi, fiziksel mikrofon ve ücretli API kullanılmadı.

Sıradaki açık işler R4–R5: wake-only sessizliğinin 15 s giriş sınırına etkisi
ve işitilmeyen thought parçasıyla girişin erken kapanması. Otomatik geri uyuma,
saniye ayarı ve Aşama 5 kapanış/debloat/kabulü bunlardan sonra gelir.

### İnceleme düzeltmesi 1 — R0 zaman hizalaması ve wake kabulü

23 Ekim 2026: Kullanıcı incelemede belirlenen sırayla düzeltmeyi istedi.
Bu tur yalnız R0: sessizlik sonrası eski segment zamanını global paket sırası
sayma ve backend/UI uyanma devri düzeltildi. Önceki bekleyen değişiklikler
korundu; manuel kabul/commit yok, sonraki özellik aşaması açılmadı.

Sherpa 1.13.8 Python sonucu decoder'ın sessizlikte sıfırlanan timestamp'ını
verir. Eksik global ofset tahmin edilmiyor: hit anında sözcük süresi + 0.8 s,
en çok 3 s yerel PCM, başlangıcı bilinen yeni stream'de aynı modelle doğrulanır.
Doğrulanan token aralığının dışındaki toplam süre, yapay 0.3 s ileri-bakış
sessizliği dahil, motorun 1.5 s iç reset eşiğinden kısa olmalıdır. Bu koşul
ve token zamanları doğrulanmazsa hit ile ses gönderilmez. Sıfır dolgu Live'a
gitmez. Sürekli geçmiş yeniden çözülmez; yeni model/araç/API çağrısı yoktur.
Yalnız 30 yerel PCM paketi ek RAM'de tutulur; kütüphane sürümü pin'i korunur.

Host wake_feed hit'i artık yalnız pending kabulüdür; sleeping=True kalır.
UI mevcut ön tampon sınırını kontrol ettikten sonra wake({request_id}) ile
aynı hit'i kabul eder. Eski ID, iptal edilen kaynak ve onaysız hit Live açamaz.
Mic Off sırasında gelen geç kabul On tercihini değiştirmez veya eski sesi
göndermez. Yeni uyku/bağlantı revision'ı eski callback'i geçersiz kılar.
Geçersiz ön tamponda wake_close host'u uykuda bırakır; durum ayrışması giderilir.

Doğrulama: 816 pytest, altı JS süiti; değişen Python/native dosyalarında
Pyright 0 hata/uyarı. Gerçek yerel model ve sentetik SAPI sesinde 0/5/61/65 s
sessizlik sonrası başlangıçlar doğru, negatif kontrol hit üretmedi. Hit anı
işlemi 22–33 ms ölçüldü; donanım performans garantisi değildir. Raporlar:
stage5-wake-alignment-local.json ve stage5-wake-alignment-native.json (5 s
beklemeli gerçek WebView2, sentetik sağlayıcı). İlk 65 s native denemesi
uykuda kalıp zaman aşımına girdi; bu başarısızlık gizlenmedi. Aynı uzun testin
son tekrarı geçti: stage5-wake-alignment-long-native.json. Böylece önceki R0
eski-sınır hatası düzeltilmiş olsa da tek sentetik örnekle fiziksel algı
kararlılığı garanti edilmez. Fiziksel kullanıcı mikrofonu ve ücretli API kullanılmadı.
Son ek native kontrol: her birinde 5 s beklenen üç ardışık gerçek KWS/AudioWorklet
uyku-uyanma turu da geçti (stage5-wake-alignment-cycles-native.json). İlk uzun
denemedeki başarısızlık silinmedi; kullanıcı mikrofonuyla kabul hâlâ gereklidir.

Açık kalan inceleme işleri: R2–R3 yerel hata/kuyruk/toparlanma ve açıklayıcı
mikrofon durumu; R4–R5 wake-only sessizliği/giriş bitişi/erken düşünce kapısı;
R1 Veks uyku eşleştirmesi. Bu tur bu hatalar düzeldi denmez. Sonraki adım
yerel hata sonrası toparlanmadır; otomatik geri uyuma/UI temizliği bekler.

### Uyku kabul hatası düzeltmesi — 23 Ekim 2026

Kullanıcı fiziksel kabulde sesli uyku/wake ve Wake düğmesi sorunları bildirdi;
önceki sentetik başarı fiziksel kabul sayılmaz. Bu tur sonraki adıma geçilmedi.
Ekrandaki Rex/Max + tam uyku cümlesi ve "uykuya dal" host eşleştirmesine
eklendi; alıntı/soru/ek işlem reddi korunur. Ayarlı wake sözcüğüyle hitap da
desteklenir. Bu isim toleransı yerel KWS'ye veya not hedeflerine uygulanmaz.

Somut UI hatası: yerel KWS/kurulum hatasından kalan micBlocked, açık Wake
sonrasında temizlenmediğinden normal dinleme açılmıyordu. Wake artık bu engeli
temizleyip izin/cihazı yeniden doğrular; Mic Off tercihi ve unknown kilidi kalır.
Yeni SLEEPING reactor durumu yavaş/düşük renkli ayrı gösterilir ve Ayarlar →
Tema renklerinde özelleştirilir; wake sözcüğü önceki tercihle profilde kalır.

810 pytest ve altı JS süiti geçti. Gerçek WebView2'de eksik yerel motor sonrası
Wake ile normal dinlemeye dönüş doğrulandı. Ek fixture kontrolünde gerçek
sherpa KWS, SAPI İngilizce WAV'ını gerçek WebAudio/AudioWorklet/bridge hattında
algılayıp aynı Live hattına devretti; sağlayıcı sentetikti. Rapor:
stage5-wake-fix-native.json. Yerel motor bu makinedeki gerçek cache'den de
başlatılıp sessizlik paketiyle kontrol edildi. Kullanıcının mikrofonu/telaffuzu
ve ücretli/gerçek sağlayıcı denenmedi; fiziksel wake başarısızlığının tüm
sebeplerinin giderildiği iddia edilmez. Değişiklikler manuel kabul bekler.
Değişen Python dosyaları ve native testte Pyright: 0 hata/uyarı (typeshed yolu
açık verilerek). İlk tip kontrolü araç cache'inin stdlib yolunu bulamaması
nedeniyle geçersizdi; proje tipi hatası diye gizlenmedi veya kodla bastırılmadı.
Native tekrarında bir tur, fixture backend wake hit'ini yeni yanıtın bitişi
sanıp mikrofonu erken kapattığı için Disconnect beklemesinde başarısız oldu.
Fixture artık yeni yanıt metnini ve kontrollerin açılmasını bekler.
Düzeltme sonrası son native turu başarılı: SLEEPING renk kaydı, hata sonrası
manuel Wake, gerçek KWS/sentetik WAV devri ve sonraki Disconnect dahil geçti.

### Güncel uygulama adımı — yerel wake-word ve tek seferlik uyku

Önceki Stop gösterge düzeltmesi kullanıcı kabulüyle `515a531` commit'ine
alındı; push yok. Uyku uygulaması daha sonra `8f65541` commit'ine alındı;
fiziksel mikrofonla kullanıcı kabulü hâlâ beklenir.
Otomatik geri uyuma, saniye ayarı ve kalıcı kullanıcı hafızası eklenmedi.

**Davranış:** Live açıkken Sleep düğmesi veya tam "Vex uyku moduna geç" /
"Vex, go to sleep" isteği tek seferlik uyku açar. Uyurken mikrofon yalnız
local sherpa-onnx KWS'ye 16 kHz/mono/PCM16LE 100 ms paketler verir; Live
socket kapatılır, yerel algıdan önce bu yol Live'a kullanıcı sesi göndermez.
Microphone Off yerel dinlemeyi de kapatır, uyku tercihini kaldırmaz. On
tekrar yerel uyandırmayı hazırlar. Wake düğmesi veya açık yazılı mesaj da
uyandırabilir. Uyandıktan sonra normal sürekli konuşma sürer; iş sonunda
kendiliğinden tekrar uyumaz. New Chat uyku durumunu temizler; Stop/unknown
kuralları ve tamamlanmış not sonuçları korunur.

Typed uyku isteği host'ta, model/API çağrısı yapmadan karşılanır. Seste
transkript finished:true veya gerçek tur bitişi beklenir; yarım transkriptte
"uyku moduna geç ne demek?" sorusunun başı komut sanılmaz. Yalnız tam ve dar
TR/EN ifadeler kabul edilir; alıntı/ek iş/persistent istek tahmin edilmez.
Uyku/wake modelin keyfi iddiasıyla değil host kontrolüyle gerçekleşir.

**Yerel motor:** sherpa-onnx ve sherpa-onnx-core 1.13.8 kuruldu/pinlendi.
Upstream zh-en 3M 2025-12-20, chunk8 int8 encoder/joiner ve fp32 decoder
kullanılır. Vex İngilizce V EH1 K S fonemleriyle aranır. Kişiselleştirme'de
pWake alanı 1–3 İngilizce sözlük sözcüğü seçer (Vex/Hey Vex/Computer örnekleri);
her serbest Türkçe/özel ad desteklenmez. Ayar diskte saklanır, sonraki uykuya
uygulanır. Eski Wake sensitivity alanı henüz KWS eşiğine bağlanmadı; kullanılan
eşik 0.25/tek trailing blank'tir. Türkçe konuşma yanıtı pLang ile aynı kalır.

**Kaynak ve sınırlar:** mevcut tek mikrofon/AudioWorklet kullanılır. KWS
bridge'in kısa kilidinde seri CPU işlemi yapar; yeni tool executor/TaskManager
worker yoktur. Yerel IPC kuyruğu en çok 1 s; wake ön tamponu en çok 3 s'dir.
Algılanan sözcüğün fonem zamanından önceki tampon paketleri Live'a aktarılmaz;
sınır 100 ms PCM paketine yuvarlanır. Aynı cümlenin hit'ten sonraki kısmı aynı
mikrofondan mevcut Live girişine devredilir. Hit tamponun dışına düşmüşse
kırpılmış komut yürütmek yerine kaynak hatasıyla kapatılır; kullanıcı Wake ile
çıkıp isteği tekrarlar. Yerel stream en çok 60 s'de yenilenir; tam sınırdaki
sözcük kaçabilir. Ses diske yazılmaz. Eski request_id/sequence kapanmış kaynağa
veya yeni oturuma yazamaz. Gerçek donanımda yanlış uyanma/kaçırma henüz ölçülmedi.

Model dosyaları kod deposunda değil get_data_home()/models/wake altındadır.
Bu makinede kuruldu. Başka kurulumda: v1 içinden
`python -m app.session.wake_word --setup`. İndirme uygulama açılışında otomatik
yapılmaz. Sabit upstream arşiv SHA256'sı ve tek tek dosya hash'leri doğrulanır;
serbest archive extract yoktur. Model/keyword kullanılamazsa uyku açık kalır,
Live fallback yapılmaz; kullanıcı Wake ile çıkar. Üçüncü taraf ağırlıklar
TaskVex MIT lisansı altında yeniden etiketlenmez; THIRD_PARTY_NOTES.md'ye bak.
Kaynak: [resmi KWS rehberi](https://k2-fsa.github.io/sherpa/onnx/kws/pretrained_models/index.html).

**Doğrulama:** gerçek yerel motor + Windows SAPI sentetik 16 kHz konuşması
"Vex, tell me the time" örneğinde 0.7 s noktasında hit verdi; negatif kontrol
cümlesi hit vermedi. Bu tek sentetik çift fiziksel başarı oranı değildir.
Native kabulde yalnız algılayıcı sınırı taklit edildi; gerçek AudioWorklet,
bridge, core ve Live socket hattında uyurken sıfır Live trafiği, Mic Off,
aynı-kaynak handoff ve kaydedilmiş Computer seçimi doğrulandı. Gerçek hesap ve
ücretli API kullanılmadı. Kanıtlar: stage5-wake-local-engine.json,
stage5-wake-native.json, stage5-wake-full-native.json. Gerçek kullanıcı
mikrofonu/Türkçe telaffuz ve canlı sağlayıcı kabulü açık kalır.

23 Ekim 2026 tekrar kontrolü: 804 pytest testi ve altı JavaScript süiti geçti.
Gerçek WebView2 chat kontrolü tekrar geçti; mikrofon kapalıyken Sleep'in
backend Live bağlantısını kapatması ve capture açmaması da doğrulandı.
Bağımlılık tutarlılığı kontrolü başarılı. Bu tekrar kontrolde gerçek hesap,
ücretli sağlayıcı çağrısı ve fiziksel kullanıcı sesi kullanılmadı.

Sıradaki ayrı adım her işten sonra geri uyuma tercihi ve uygun boşta süre
ayarının uygulanmasıdır. UI temizliği/debloat Aşama 5 kapanışında kalır.

### Güncel küçük düzeltme — Stop ve kesilme göstergeleri

Geçici hafıza kullanıcı tarafından manuel kabul edildi; `dc79318` ile commit
edildi, push yok. Bu tur yalnız istenen iki gösterim düzeltmesi uygulanır;
yerel wake-word/uyku ayrı sonraki uygulama adımıdır. Yeni dilim manuel kabul
bekler; henüz commit edilmedi.

Header mikrofon ışığı artık fiziksel kaynağın kısa ömrünü değil, hazır ve
engelsiz Microphone On tercihini gösterir. Stop sırasında eski kayıt/PCM
atılıp kaynak yeniden hazırlanırken ışık sönmez. Bu değişiklik capture'ın
kesintisiz sürdüğü iddiası değildir; tooltip gerçek kaynağı ayırır. Off,
Disconnect, izin/cihaz hatası veya unknown engeli ışığı söndürür. Gerçek giriş,
Stop/araç iptali ve otomatik yeniden dinleme protokolü değiştirilmedi.

Normal, completed:true ve unknown olmayan Stop/Live interrupted sonunda
bağlantı rozeti nötr LIVE READY olur. Açık socket/online iddia edilmez;
sonraki mesaj yeni oturum açabilir. Gerçek ağ/model/izin hatası kırmızı kalır,
unknown komut kilidi korunur. Eski bağlantıdan gelen Stop sonucu yeni bağlantı
rozetini ezmez. İptal tanısı ve kesilmiş transkript korunur; başarıya çevrilmez.
Eşleşen istek kimliği olmayan veya unknown kesme hataları logdan gizlenmez.
LIVE READY rozetine tıklamak gereksiz reconnect başlatmaz.

Hedefli Node kontrolü normal kesme ile unknown/eski kimlik ayrımını ve nötr
rozet sınıfını doğrular. Native MutationObserver, Stop/kaynak devri boyunca
mikrofon on sınıfının sönmediğini izler; hata/Off testleri aynı süitte kalır.
Son doğrulama: 6 Node süiti, 10/10 tam WebView2 fazı ve son hedefli chat
fazı geçti; native betikte Pyright 0 hata. Kanıtlar:
stage5-stop-indicators-full-native.json ve stage5-stop-indicators-native.json.
Gerçek API/donanım denenmedi.

### Önceki uygulama adımı — sınırlı geçici sohbet hafızası

Önceki komut rehberi/ayar yerleşimi planını kullanıcı onayladı; `d4ffb16`
commit'i kaydedildi, push yok. Bu yeni uygulama adımı manuel kabul bekler;
henüz commit edilmedi. Kalıcı kullanıcı hafızası, wake-word veya uyku eklenmedi.

ConversationMemory, TextChat'in mevcut tek sohbet kilidinde yaşayan RAM
kaydıdır. Son 12 tur / en çok 16.000 JSON karakteri, her kullanıcı ve yanıt
metni en çok 2.000 karakter tutulur. Sınırda eski turlar çıkarılır, uzun metin
kesildi etiketi alır. Semantik özet/model eğitimi/vektör DB ve ek özet API
isteği yoktur. Bu ilk sürüm sınırlı yakın geçmişi tutar; eski bilginin sonsuza
kadar hatırlanması veya sağlayıcının kendi bağlam penceresi garanti edilmez.

Yazılı mesaj veya doğrulanmış giriş transkripti ve alınmış yanıt metni saklanır.
Başarılı/başarısız/kesilmiş/belirsiz sonuç ayrıdır. Araçlardan yalnız isim,
status ve verified özeti kalır; tool arguments/result.data, PCM, provider
resume handle, credential deposu veya disk geçmişi tutulmaz. Konuşmada
kullanıcının yazdığı/söylediği kişisel bilgi RAM metninin parçası olabilir;
anahtar güncellemesi bu geçmişi yeni anahtara aktarmadan temizler.

Stop, sıradan Disconnect, model/kişisel talimat ve ses/metin setup değişimi
aynı sohbetin RAM'ini korur. Fresh bağlantı kurulursa geçmiş model rolünde
etiketli JSON veri olarak `send_client_content(..., turn_complete=False)` ile
güncel istekten önce bir kez aktarılır. Reused veya resumed oturumda tekrar
aktarılmaz. Güncel kullanıcı isteği eski komuttan ayrı realtime yolundadır;
tool call/response mesajı, ID veya handler tekrar oynatılmaz. Güncel not verisi
halen gerçek araçtan okunur; RAM'deki geçmiş yazma izni veya hedef kanıtı
olmaz. memory_restored yalnız taşıma/bağlam aktarımı kanıtıdır; gerçek modelin
anlama/hatırlama başarısı değildir. Sağlayıcı sözleşmesi:
[Live capabilities](https://ai.google.dev/gemini-api/docs/live-api/capabilities).
Bağlam tokenları sağlayıcı tüketimine dahildir; ek özet çağrısı yapılmaması
bağlam aktarımının maliyetsiz olduğu anlamına gelmez.

**New Chat** düğmesi kullanıcı onayından sonra `new_chat` event'ini gönderir.
Host idle ve hazır olmalı; socket/core kapanışı doğrulanmadan RAM silinmiş
sayılmaz. Başarıda yalnız konuşma/RAM temizlenir; not, skill, rutin, profil,
ayar ve anahtar silinmez. Aktif veya unknown UI isteğinde düğme yürütülmez;
yeni sohbet unresolved işlemi iptal etmez/geri almaz, unknown kilidini açmaz.
Taşıma onayı kaybolursa UI güvenli unknown durumunda kalır. Düğme sesli
"unut" komutu değildir; kalıcı kullanıcı hafızası yönetimi sonraki aşamadadır.
Pencere kapanışı ve API anahtarı güncellemesinde RAM bırakılır. REST hattına
geçmiş/hafıza eklenmedi. Ek worker/yürütücü veya yeni bağımlılık yoktur.

Doğrulama: gerçek SDK ile sentetik socket, gerçek core/geçici notlar; sınırlar,
ses transkripti, reused/resumed tekrarsızlığı, fresh fallback, Stop sonrası
kesilmiş durumun korunması, tek not yazımı ve New Chat/anahtar temizliği
kontrol edildi. Son kontrol: 787 pytest, 6 Node süiti, 10/10 WebView2 fazı;
incelenen Python dosyalarında Pyright 0 hata. Gerçek hesap/ücretli API
kullanılmadı. Native kanıt:
[hedefli faz](stage5-conversation-memory-native.json) ve
[tam fazlar](stage5-conversation-memory-full-native.json). Gerçek sağlayıcı
hatırlama kabulü kullanıcı testinde açık bırakıldı.

Sonraki ayrı uygulama adımı yerel wake-word ve tek seferlik uyku; ardından
her işten sonra uykuya dönüş, bütünleşik kabul, UI/debloat ve son kapanış gelir.

## 22 Ekim 2026 — Ana ürün, hafıza ve uyku için güncel kapsam kararı

Son REST ses/Mic Off dilimi kullanıcı tarafından manuel kabul edildi ve
`ba47710` olarak commit edildi; push yapılmadı. Ana masaüstü ürünü Live'dır.
REST hattı gelecekte farklı araç/kanal adaptörleri için korunacak; ana ürünün
kullanıcı akışı veya otomatik Live→REST fallback'i olmayacak. Mevcut REST
test seçeneği bu plan güncellemesinde koddan kaldırılmadı; ana UI'dan ayırma
hedefli UI temizliği adımına alınmıştır. REST/TTS'ye yeni ürün özelliği ekleme.

### Kullanıcı tercihi — planlanan ayarların yerleşimi

- **Kişiselleştirme:** kullanıcı hafızasını görme/düzeltme/silme ve hafıza
  tercihleri burada yönetilecek. Wake-word seçimi de burada yer alacak;
  başlangıç sözcüğü Vex. Farklı sözcük desteği seçilen yerel motorla gerçekten
  doğrulanmadan her serbest metin çalışır diye sunulmayacak.
- **Ayarlar:** otomatik uykuya dönüşün kaç saniye sonra gerçekleşeceği burada
  yönetilecek. Süre kullanıcı konuşurken, Vex yanıt verirken, görev sürerken
  veya açıklama beklenirken işlemeyecek; uygun boşta durumda başlayacak.
  Bu süre kendi başına uyku modunu etkinleştirmez: tek seferlik uykudan uyanıp
  normal konuşmaya dönme ile her işten sonra tekrar uyuma davranışı korunur.
  Başlangıç değeri/aralığı uygulama adımında belirlenecek.

Bu tur yalnız plan/belge değişikliğidir; yeni kontrol, kalıcı ayar şeması,
hafıza veya wake-word işlevi eklenmedi. Çalışan yeteneklerin İngilizce özeti
kök dizindeki [commands.md](../commands.md) içindedir; her yeni komutta aynı
adımda güncellenmesi AGENTS.md gereğidir.

### Mevcut olan ile henüz yapılmayanın ayrımı

- Geçici sohbet bağlamı kısmen var: aynı Live oturumu yeniden kullanılır.
  Güvenli idle resumption desteklidir; Stop/Disconnect, kapsam değişimi veya
  güvenli resume yapılamaması yeni bağlam açabilir. Uygulamanın yönettiği,
  reset sonrasında da aynı sohbeti hatırlatan sınırlı geçici hafıza henüz yoktur.
- pLang/pIns ortak model talimatına aktarılır. pMem ve wake hassasiyet alanı
  ayar olarak saklanabilir; bu, çalışan hafıza çıkarımı veya wake-word motoru
  olduğu anlamına gelmez. Kalıcı kullanıcı bilgisi çıkarımı uygulanmadı.
- Microphone On/Off, Stop ve yerel ses aktivitesi mevcut. Yerel wake-word ve
  aşağıdaki iki uyku davranışı uygulanmadı. idle yalnız görsel durumdur;
  kullanıcı sesine cevap vermeyi engelleyen uyku modu değildir.

### Aşama 5 kapanmadan eklenecek ayrı adımlar — önerilen yürütme sırası

1. **Uygulama sahipliğinde geçici sohbet hafızası:** son konuşmalar ve sınırlı
   özet aynı mantıksal sohbet için RAM'de tutulur. Live resetinden sonra yalnız
   bilgi bağlamı aktarılır; eski kullanıcı komutu/tool call tekrar gönderilmez.
   Sohbeti temizleme/yeni sohbet hafızayı bırakır. Boyut sınırı ve özetleme
   açık olmalı; sınırsız geçmiş, tam hatırlama ve yeniden açılışta kalıcılık
   varsayılmaz. Özetleme ek API isteği gerektirirse maliyeti ayrıca belirtilir.
2. **Yerel wake-word ve tek seferlik uyku:** uyurken yalnız yerel anahtar
   sözcük algılayıcı çalışır; sıradan ortam sesi Live'a gönderilmez. Mikrofon
   Off ise wake-word de çalışmaz. "Uyku moduna geç" yalnız mevcut uykuyu açar;
   wake-word sonrasında normal sürekli konuşmaya dönülür. Uyku, uygulamayı/
   TaskManager'ı veya bilgisayarı kapatmaz; tamamlanmış işleri geri almaz.
   Kullanılan motor, cihaz ölçümü ve Türkçe telaffuz kabulü bu adımda seçilip
   doğrulanır; yalnız modele "cevap verme" talimatı vermek yeterli değildir.
3. **Her işten sonra uykuya dönme tercihi:** "bundan sonra uyku modunda kal"
   tercihi mevcut sohbet boyunca sürer. Wake-word geçici olarak konuşmayı açar;
   istek/iş gerçek terminal sonucuna ulaştığında tekrar uyur. Modelin ilk
   turn_complete olayı tek başına çok adımlı görevin bitişi sayılmaz. Açıklama
   bekleniyorsa konuşma kapanmaz; unknown sonuç güvenli komut kilidini aşmaz.
   "Uyku modundan kalıcı olarak çık" bu sohbetin tekrar uyuma tercihini
   kapatır. Buradaki kalıcı çıkış uygulama yeniden açılışına taşınan yeni bir
   disk ayarı anlamına gelmez. Wake-word + aynı cümledeki istek kaybolmamalı.
4. **Bütünleşik kabul:** geçici hafıza, iki uyku davranışı, Stop/Disconnect,
   sessizlik, model/anahtar değişimi, yan etkili araç ve fiziksel ses birlikte
   kontrol edilir; gerçek sağlayıcı/donanım ile sentetik sonuç ayrı raporlanır.
5. **Hedefli UI/debloat:** REST test kontrolünü ana masaüstü akışından ayır;
   kullanıcının bildirdiği görüntü kirliliğini ve ölçülen tekrarları temizle.
   Sırf satır sayısı için mekanik bölme/iş mantığı silme yapma.
6. **Son regresyon ve belge kapanışı:** uygulanan kapsam, açık sınırlar ve
   gerçek kullanıcı kabulüyle Aşama 5'in kapatılıp kapatılamadığı belirtilir.

Her prompt yalnız bir uygulama adımını kapsar. Bu liste plan güncellemesidir;
bu turda hafıza/wake-word/uyku kodu eklenmedi. Kalan fiziksel/maliyet kabulü
atlanarak Aşama 5 tamamlandı denmez.

### Aşama 6'nın başına — kalıcı kullanıcı hafızası

Entegrasyonlardan önce küçük, yerel kullanıcı bilgisi dilimi önerilir:
okul/iş/tercih gibi kullanıcının açıkça söylediği bilgiler kaynağı ve zamanıyla
saklanır; kişilik çıkarımı kesin gerçek gibi kaydedilmez. Modelin çıkardığı
aday bilgi ile kullanıcının doğruladığı bilgi ayrılır. Kullanıcı bilgileri
görebilmeli, düzeltebilmeli ve sildirebilmelidir. Her konuşmanın bütünü otomatik
profil kaydı olmaz. Bu hafıza notlardan, görev/audit günlüğünden ve L1 locator
hafızasından ayrıdır; aynı kayıt/policy/TaskManager ilkeleri yeniden kullanılır.
İlk sürüm için vektör veritabanı, model eğitimi veya yeni bir yürütücü gerekmez.
Ardından CORE_START_PLAN.md'deki işlem bazlı L0/entegrasyon sırası devam eder.

### Güncel: adım 6 — REST ses çıkışı ve Mic Off

Önceki mikrofon düzeltmesi kullanıcı kabulünden sonra `f35a13e` ile commit
edildi; push yok. Bu dilim kullanıcı tarafından 22 Ekim 2026 tarihinde
manuel testleri başarılı bildirilerek kabul edildi.

REST'in doğrulanmış nihai metni önce UI'a gösterilir; araç sonuçları korunur.
`read_reply({request_id})` yalnız host'un RAM'deki son başarılı REST metnini
bir kez okutur. UI serbest metin veya model seçemez; yanlış/eski ID geçerli
bekleyen cevabı tüketmez. Yeni sohbet, Stop, Disconnect veya kapanış cache'i
bırakır. TextChat'in aynı kilidi kullanılır; ikinci worker/core/CRUD yolu yoktur.

[Resmi speech-generation sözleşmesi](https://ai.google.dev/gemini-api/docs/speech-generation)
ve kurulu google-genai 2.32 ile doğrulanan
araçsız Interactions TTS kullanıldı: `gemini-3.8-flash-lite-tts`, Kore sesi,
`store:false`, 24 kHz mono PCM. Metin TTS'ye aynen okunacak içeriktir; araç
bildirimi/çağrısı yoktur. Canlı model seçimi listesi değiştirilmedi. TTS tek
ayrı API isteğidir; Mute gönderim öncesinde açıksa istek yapılmaz. CLI/bot
kendiliğinden ses üretmez. UI'daki Live ses seçimi bu REST Kore varsayılanını
henüz değiştirmez. REST mikrofon/STT bu dilimde eklenmedi.

Metin en çok 20.000 karakter, ham PCM en çok 60 saniye/2.880.000 byte'tır.
Sentez unary HTTP yanıtıdır: ses metin yanıtından sonra hazırlanır, Live kadar
erken başlayacağı iddia edilmez. HTTP 20 s sınırına tabidir; PCM mevcut 20 s
Web Audio kuyruğuna en çok 1 s'lik parçalarla gerçek zaman hızında verilir.
Ses aşamasının UI bekleme sınırı 110 s'dir. Stop HTTP'yi anında kesmez; kabul
`completed:false, waiting_for:speech_response|speech_completion` olur. Gerçek
bitiş gelene kadar kontroller kapalıdır, sonraki PCM reddedilir. Tamamlanmış
metin ve notlar geri alınmış sayılmaz. Ses hatası ayrı `audio_error` ile
gösterilir; metin/model/araç veya TTS otomatik yeniden denenmez. SDK 2.32'nin
0 retry'yi 1'e dönüştürmesi Interactions resource kurulmadan düzeltilmiştir;
503'te tek HTTP ve sıfır tekrar testi vardır. SDK yükseltmesinde bu kontrol korunmalı.

Microphone Off yalnız track'leri kapatır. Mevcut giriş akışına PCM ile aynı
sıradan, bir kez null/EOS gönderir; setup bekliyorsa hazır olduğunda gönderir.
Off nedeniyle Stop yoktur; modelin yanıtı/transkripti/çalması devam eder.
Daha önce yakalanmış/gönderilmiş ses geri alınmaz. Stop hâlâ açık iptaldir.

Hedefli gerçek SDK/sentetik HTTP testleri ve WebView2 kontrolleri; metnin önce
görünmesi, tek not mutasyonu, ses hatasında metnin korunması, Mute'ta sıfır
TTS, HTTP Stop bitişi, eski ID/tekrar reddi, Mic Off giriş sonu ve aktif çıktının
korunmasını kapsar. Kanıt: stage5-rest-audio-native.json ve
stage5-rest-audio-full-native.json. Gerçek hesap/kota, fiziksel hoparlör ve
sağlayıcının TTS erişimi test edilmedi; gerçek kabul açık. Yeni bağımlılık,
sesli REST giriş yolu, UI temizliği veya başka entegrasyon yapılmadı.

Son doğrulama: 780 pytest, 6 Node süiti, 10/10 gerçek WebView2 fazı ve
incelenen Python dosyalarında Pyright 0 hata. WebView2; setup öncesi Off,
aktif girişte EOS ve aktif çıktıda Off sonrası açık Stop ayrımını doğruladı.

Sonraki adımlar: gerçek bütünleşik kabul, hedefli UI temizliği/debloat,
son regresyon/belge kapanışı. Aşama 5 henüz kapanmadı.

Bu belge modelin mevcut core'u nasıl kullanacağını ve bugün hangi parçanın
gerçekten hazır olduğunu anlatır. Model yeni yürütücü/worker değildir; araç
handler'ına doğrudan erişmez. İlk ModelTools diliminde bağımlılık eklenmedi;
5.2'de resmi google-genai SDK'sı ve HTTP hata türleri için httpx bildirildi.

## Sıra ve güncel durum

### Önceki ara düzeltme — mikrofon tercihi model sonucundan bağımsız

Kullanıcı kabulü: 22 Ekim 2026 tarihinde On/Off ve hata sonrası dinleme
testleri başarılı bildirildi. Aktif girişte Off'un yanıtı kesmemesi sonraki
küçük düzeltme olarak istendi.

Kullanıcı adım 5 testlerini onayladı; `78c292a` ile commit edildi. Yeni isteği
ayrı dilim olarak uygulandı; REST ses adımına geçilmedi. Bu dilim manuel kabul
bekliyor ve henüz commit edilmedi; push yok.

Header düğmesi Microphone On / Off oldu. microphoneEnabled yalnız kullanıcının
tercihidir; model reddi, hedef bulunamaması veya Stop bu tercihi değiştirmez.
Stop eski ses/ön tamponu bırakır; gerçek host bitişi doğrulanınca On ise yerelde
yeni konuşma beklenir. Tamamlanmış hata yanıtı da aynı şekilde yeniden dinler.
Eski model mesajı/araç veya yakalanmış başarısız ses tekrar gönderilmez. Sessiz
beklemede yeni sağlayıcı isteği yoktur; hata/Stop tanısı durum satırında korunur.
Kullanıcının Off seçimi aktif yanıtın bitişi, Stop veya model-ready bildirimiyle
kaldırılmaz. Off, kaynakları hemen bırakır; etkin giriş sürüyorsa mevcut tur
iptali de istenir. Yanıt çalarken Off yalnız mikrofonu kapatır.

micBlocked ayrı bir kaynak engelidir: izin reddi/cihaz hatası, giriş sınırı,
Disconnect/anahtar değişimi ve unknown durumunda capture kapanır. Otomatik izin
veya bağlantı tekrar döngüsü yoktur. Model hazır bildirimi veya açık Off→On
kaynak engelini kaldırabilir; textOperation.uncertain kilidi yine aşılamaz.
Unknown'da düğme Off yapılabilir, tekrar On yapmak komut veya capture başlatmaz.
On/aria-pressed tercih durumunu; renkli on sınıfı gerçek capture durumunu gösterir.
Engel tooltip/durum satırındadır. Bu tercih mevcut oturum RAM'indedir; yeni
kalıcı mikrofon ayarı eklenmedi. Otomatik capture hâlâ Live modu ve yüklenmiş
bir Live model ister; REST'e yeni mikrofon/STT yolu eklenmedi.

Hedefli [gerçek WebView2/sentetik sağlayıcı](stage5-mic-toggle-native.json)
kontrolü reddedilen not silmede sıfır mutasyon/tekrar, Stop sonrası On/idle ve
sonraki gerçek AudioWorklet konuşmasının gönderimi, aktif yanıtta Off seçiminin
Stop/model-ready sonrasında korunması, izin reddi ve unknown'da Off→On ile
kilidin aşılamamasını doğruladı. Native testlerin başlangıç/temizleme adımları
artık Stop'un Off yapmasına güvenmez; düğmeden açıkça On/Off seçer.
Yeni backend olayı, CRUD mantığı, worker veya bağımlılık yoktur. Kullanıcı notu,
gerçek mikrofon/hesap veya ücretli API kullanılmadı. Gerçek donanım kabulü açık.
Tam kontrol: 765 pytest, 6 Node süiti, JS syntax ve native betiğinde 0
Pyright hatası. [10/10 tam WebView2 fazı geçti](stage5-mic-toggle-full-native.json);
son ek kontrolde Off aktif yanıt sırasında seçilip ardından Stop ile doğrulandı.
Sonraki ayrı iş REST ses çıkışı; Aşama 5 henüz kapanmadı.

### Önceki: adım 5 — durum, log ve süre sınırları

Kullanıcı kabulü: 22 Ekim 2026 tarihinde durum/log/süre ve idle/listening
testleri kullanıcı tarafından başarılı bildirildi; adım 5 manuel kabulü tamamlandı.

Dil/kişiselleştirme adımını kullanıcı onayladı; `73a87df` ile commit edildi.
Bu yeni adım manuel kabul bekler, commit/push yapılmadı. Kullanıcının küçük
idle/listening isteği aynı durum akışı içinde bu adıma dahil edildi.

Mikrofon açık ama sessizce aday bekliyorsa reactor idle kalır. Yerel aday
algılandığında listening, konuşmada yaklaşık 700 ms enerji sessizliği olduğunda
model turu hâlâ aktifse thinking görünür. Kullanıcı yeniden konuşursa listening'e
döner. Çıktı PCM'i speaking, başarılı yanıt sonrası aynı bekleyen mikrofon idle
olur. AudioWorklet yalnız aktivite değişimini bildirir; sunucu VAD'sinin
konuşmayı bitirmesi veya bir aracın tamamlanması yerine geçmez. Stop/hata/cihaz
kapanışında eski aktivite yeni mikrofonu etkileyemez. Unknown'da ses kaynakları
kapanır ve mevcut komut kilidi korunur; idle rengi kilidin açıldığı anlamına gelmez.

Normal, kimliği eşleşen completed/stopped/code:stopped ve unknown olmayan
sohbet dönüşü emit tarafında hâlâ ok:false'dur; taşıma hatası logu üretilmez.
UI normal bir durdurma kaydı ve gerçek araç sonuçlarını gösterir. Mikrofon feed
sonucu failed:false/closed:true ise normal geç paket kapanışı olarak ele alınır;
bozuk sıra, taşma ve failed:true gizlenmez veya başarıya çevrilmez. Backend
PersistentLive.input bu failed alanını ayrıca döndürür. Stop kabulü hâlâ bitiş
kanıtı değildir; eski kimlikli Stop/geç metin/ses ve unknown kuralları korunur.

Engine log tek addLog kaynağında son 200 DOM kaydı, kayıt başına 2.000 karakter
ile sınırlıdır. Şema uyarıları da aynı boyut/adet sınırında tutulur. addLog güvenli
textContent kullanır; mevcut sır maskelemesine AQ biçimi de eklendi. Log dosyası,
sınırsız geçmiş veya ikinci logger eklenmedi; transkriptler loga taşınmadı.

Live'ın eski 25 saniyelik toplam tur sınırı ikiye ayrıldı: sağlayıcıdan olay
beklemesi en çok 25 s, bütün tur en çok 120 s. Parça gelmeye devam ediyorsa ilk
25 s'de kesilmez; kontrol olayı sonsuz döngüsü de 120 s üst sınırını aşamaz.
Hatalar live_idle_timeout/live_timeout ve timeout_seconds ile ayrılır. Timeout
otomatik retry/resume/fallback değildir; kısmi metin ve tamamlanmış araç sonucu
korunur, çözülemeyen araç unknown bırakılır. UI bekleme sınırı Live 210 s,
REST 240 s'dir; bu süre aşımı gerçek iptal sayılmaz ve geç yanıt kilidi açmaz.
Mikrofon 15 s, setup tamponu 3 s, çalma kuyruğu 20 s, PCM çıkış toplamı 60 s,
metin/parça/araç sınırları korunur; 120 s sınırsız ses üretimi vaadi değildir.

Kanıt: 765 pytest, 6 Node süiti, değişen Python/native/test modüllerinde 0
Pyright hatası ve JS syntax kontrolü geçti. Üç yeni Python testi idle timeout'ta
tek kalıcı notun korunmasını, ilerleyen olayların idle süresini aşabilmesini,
toplam timeout'un yine işlemesini ve normal/bozuk feed ayrımını doğrular.
Yeni Node süiti normal Stop/unknown/kimlik farkı/gerçek hata log ayrımını,
maskeleme/adet/boyut sınırını ve eski/unknown deadline davranışını sınar.
Mevcut mikrofon süiti 700 ms aktivite geçişini ve kaynak sahipliğini de kapsar.
[Hedefli gerçek WebView2](stage5-status-native.json) gerçek AudioWorklet ile
idle/listening/thinking/speaking/idle sırası, normal Stop logu, log sınırı ve
önceki not/Stop/resume/unknown/ses regresyonlarını doğruladı. Sağlayıcı ve ses
sentetik, kayıt geçicidir; kullanıcı notu veya ücretli/gerçek API kullanılmadı.

Tam native regresyon: [10/10 faz geçti](stage5-status-full-native.json);
ayar/not/import/export/kimlik deposu ve kurtarma kontrolleri korundu. Son
unknown log ayrımı da hedefli Node testinden geçti.

Sonraki ayrı adım REST ses çıkışı açığıdır. Ardından gerçek entegre kabul,
hedefli UI temizliği/debloat ve son kapanış belgeleri kalır. Not şüphesi incelemesi
kullanıcının isteğiyle erteli; aynı socket tam çift yönlü interruption ve
fiziksel yankı kalibrasyonu bu adımda eklenmedi. Aşama 5 kapanmadı.

### Önceki: adım 4 — seçilen dil ve temel kişiselleştirme

Kullanıcı kabulü: 22 Ekim 2026 tarihinde dil/kişiselleştirme adımının
testleri kullanıcı tarafından başarılı bildirildi; adım 4 manuel kabulü tamamlandı.

Adım 3 kullanıcı testinden geçti ve `85648b9` commit'iyle kaydedildi. Yeni
adım 4 manuel kabulden önce commit edilmez; push yapılmadı.

`app/session/model_instruction.py` tek ortak talimat kaynağıdır. NativeBridge
her mesaj başında doğrulanmış disk ayarından bağımsız bir profil snapshot'ı
okur; UI zarfına yeni profil/talimat alanı açılmaz. TextChat bu snapshot'ı
REST ve Live adaptörlerine taşır. REST metni, Live yazısı, eski ses klibi ve
canlı mikrofon aynı pLang/pIns tercihlerinden yararlanır. Profil okunamazsa
model başlatılmaz (`profile_unavailable`); kayıtsız UI değişikliği gönderilmez.

pLang tr/en: Türkçe veya İngilizce yanıt/ses dili seçer. Eksik/eski desteklenmeyen
dil, mevcut UI varsayılanı Türkçeye düşer. pIns en çok 16.000 karakter kişisel
talimat taşır; modelin ton/uzunluk/davranış tercihlerini yönlendirir. Prompt
sıralamasında seçilen dil ve araç/sonuç/Stop kuralları bu tercihten üstündür;
modelin dil/stile her zaman uyması kodla garanti edilmez.
Gerçek yetki denetimi prompta bırakılmadı; aynı ModelTools/registry/policy/
TaskManager hattı ve ilk not aktarımı kapısı korunur. pMem/pSys/pGreet ve diğer
profil alanları bu dilimde modele gönderilmez; yeni bellek motoru eklenmedi.
Profilin pLang/pIns alanları sağlayıcıya iletilir; UI bu aktarımı açıklar.

REST retry/fallback aynı değişmez talimatı korur. Live oturum kimliği artık
etkili ortak talimatın SHA-256 özetini de içerir. Dil veya kişisel talimat
sonraki turda değiştiyse eski socket/resume/çağrı kapsamı bırakılır ve yeni
mantıksal bağlam açılır (`scope_changed`); eski mesaj/araç tekrarlanmaz.
Aynı etkili talimat, yalnız dış boşluk veya bağlanmamış profil alanı değişimi
bağlantıyı gereksiz sıfırlamaz. Profil kaydı aktif yanıta müdahale etmez;
sonraki mesajda uygulanır. Stop/Disconnect/kaynak temizliği değiştirilmedi.

Sağlayıcının [Change voice and language açıklaması](https://ai.google.dev/gemini-api/docs/live-api/capabilities#change-voice-and-language)
kontrol edildi: native audio açık language_code ayarını desteklemiyor, dili
otomatik seçiyor. Bu nedenle desteklenmeyen SDK alanı eklenmedi. Ortak talimat
seçilen dilde konuş/yaz ve belirsiz sözde tekrar iste der; bu, gerçek STT
kilidi veya hatasız dil tanıma garantisi değildir. Gerçek hesap kabulü açık.
REST ses çıkışı bu adımda eklenmedi; mevcut REST metin sınırı sürüyor.

Kanıt: 762 pytest (20 yeni profil testi), 5 Node süiti, değişen Python/test
modüllerinde 0 Pyright hatası. İlk hedefli regresyonda eski köprü testinin
kwargs beklentisi yeni profile alanını içermiyordu; sözleşmeye göre güncellendi.
Yeni bozuk-dosya testinin ilk koşusunda test dizini oluşmamıştı; fixture
hazırlandı. Üretim doğrulaması gevşetilmedi; son testler tamamen geçti.
[Hedefli gerçek WebView2](stage5-profile-native.json) gerçek Save profile formu,
diske yazma, REST/Live SDK'de aynı talimat, değişen profilde yeni bağlam ve
resume handle temizliğini doğrular. Sağlayıcı/ses sentetiktir; modelin gerçekten
istenen dil/stilde cevap verdiğinin kanıtı sayılmaz. Kullanıcı notu, gerçek
hesap veya ücretli API kullanılmadı.

Tam regresyon: [10/10 hidden WebView2 fazı geçti](stage5-profile-full-native.json);
ayar/not/kimlik deposu/import/export/kurtarma kontrolleri de korundu.

Sonraki ayrı adım durum/log/zaman sınırı yönetimidir. Manuel kabul ve Aşama 5
kapanışındaki açık koşullar bekleniyor; ses, yeni entegrasyon veya debloat'a
geçilmedi.

### Önceki: adım 3 — yerel VAD ve yanıt sonu mikrofon devri

Kullanıcı kabulü: 22 Ekim 2026 tarihinde VAD/mikrofon adımı testlerinin
başarılı olduğu kullanıcı tarafından bildirildi; adım 3 manuel kabulü tamamlandı.

Adım 2 anlık transkriptleri kullanıcı tarafından kabul edildi ve `3daf152`
commit'iyle kaydedildi. AGENTS.md uyarınca bu yeni adım manuel kabulden önce
commit edilmez; push yapılmadı.

İki somut sorun düzeltildi. Aynı 200 ms enerji eşiği hem boşta başlangıç hem
çalan yanıtı kesme için kullanılıyordu. Artık boşta 200 ms/0.015, yanıt sırasında
300 ms/0.025 taban RMS gerekir. DC/düşük frekans filtresi yalnız algı enerjisine
uygulanır; sağlayıcıya giden PCM değiştirilmez. Eşik, aday olmayan arka planın
hareketli ortalamasının üç katından düşük olamaz. 500 ms ön tampon korunur.
Browser'a echoCancellation/noiseSuppression açık, autoGainControl kapalı istenir;
cihazın bu tercihleri gerçekten uyguladığı fiziksel testle belirlenir.

Başarılı yanıt bitince bekleyen mikrofon artık kapatılıp yeniden açılmaz.
Aynı track, ön tampon ve yarım konuşma adayı boşta dinlemeye devrolur. Callback
eski closure kimliği yerine güncel dinleme hedefini kullanır. Not yenilemesi
beklenirken eski kimlik korunur; son kimlik/mod/kilit geçişi await içermeden
birlikte yapılır. Yakalanmış yeni ses yeniden kurulmaz. Stop/Pause/Disconnect,
model/anahtar değişimi, unknown ve ses hatasında bu koruma uygulanmaz;
kaynak kapatma ve belirsizlik kilidi sürer.

Bu değişiklik gerçek konuşma/yankı sınıflandırıcısı değildir. Uzun ve yeterince
yüksek bir gürültü hâlâ aday olabilir; kısık ses donanıma göre kaçabilir. Barge-in
mevcut Stop → gerçek sonuç → yeni tur sırasıdır; aktif Stop hâlâ bağlamı
sıfırlayabilir. Aynı socket'te tam çift yönlü interruption eklenmedi. Eski turun
kapanışında 3 saniyelik tampon taşarsa söz sessizce kırpılıp yürütülmez.
Dil/base instruction adım 4'tür; not incelemesi kullanıcının isteğiyle ertelidir.

Kontrollü kanıt: 742 pytest, 5 Node süiti, native betiğinde 0 Pyright hatası.
Node, sabit ofseti, kısa darbeyi, 200/300 ms ayrımını, arka plan uyumunu,
mod değişiminde ön tamponu ve yakalanmış sesi tekrar kurmama kuralını doğrular.
[Hedefli gerçek WebView2](stage5-vad-native.json), 100 ms darbenin hem aktif
hem yalnız çalan yanıtı kesmediğini; aynı mikrofonla yanıt sonu devamı,
ikinci otomatik konuşma, gerçek kesme, tek kalıcı not, Disconnect/unknown ve
REST/Live Stop regresyonlarını doğruladı. Ses/sağlayıcı sentetiktir; gerçek
hesap, ücretli API veya kullanıcı notları kullanılmadı. Fiziksel kabul açık.
Sağlayıcının [VAD sözleşmesi](https://ai.google.dev/gemini-api/docs/live-api/capabilities)
tekrar kontrol edildi; sunucunun 700 ms konuşma sonu ayarı değiştirilmedi.
Tam regresyon: [10/10 hidden WebView2 fazı geçti](stage5-vad-full-native.json);
ayar/not/kimlik deposu/import/export/kurtarma kontrolleri de korundu.
Sonraki ayrı adım seçilen dil ve temel kişiselleştirmedir; Aşama 5 kapanmadı.

### Önceki: adım 2 — anlık kullanıcı/model transkriptleri

Kullanıcı kabulü: 22 Ekim 2026 tarihinde kullanıcı anlık transkript
testlerinin başarılı olduğunu bildirdi; adım 2 manuel kabulü tamamlandı.

Kullanıcı önceki ekranın araya girilen başka sözler içerdiğini açıkladı;
"hikâye → not ekleme" sonucu doğrulanmış hata sayılmadı. İsteğiyle adım 1
not incelemesi ertelendi, not CRUD/niyet/izin mantığı değiştirilmedi.

Live giriş ve çıkış transkriptleri artık tur bitişini beklemeden aynı iki
mesajda görünür. Mevcut tek Live sahibi backend'den birikimli snapshot yollar:
host request_id, rol, artan sıra ve metin. live_transcript.js yalnız güncel
isteği kabul eder, tekrar/sırasız/eski bildirimleri reddeder, textContent ile
yazar. Giriş transkripti geç gelirse kendi model yanıtının önüne yerleşir.
Yazılı kullanıcı mesajı tekrar oluşturulmaz; normal bitiş ikinci model balonu
eklemez. Son rapor, bildirim teslim edilemediyse yedek metin kaynağıdır.

Stop/araya girme o ana kadar görünen model metnini dondurur. Kesilen yanıt
Interrupted, hata Incomplete, belirsizlik Result unknown ile işaretlenir;
tamamlanmış araç sonucu ile metin durumu birbirine karıştırılmaz. Başarısız
backend raporunda da alınmış kısmi metin korunur; başarıya çevrilmez. Geç
metin eski mesajı büyütemez veya yeni tura yazılamaz. Disconnect/model/anahtar
değişimi ve belirsizlik aktif transkript alıcısını kapatır. Gösterim hatası
model/araç retry'ı veya ikinci mutasyon üretmez.

Bu sağlayıcının verdiği metin parçalarını gösterir; yerel STT veya sözcük
zamanlaması eklenmedi. Henüz API'ye gönderilmemiş barge-in tamponunun metni
üretilemez; metin ancak sağlayıcının giriş transkripti gelince görünür.
Ses ve transkript olayları eşzamanlı gelmek zorunda değildir. Resmi Live
capabilities transkript sözleşmesi tekrar kontrol edildi. Dil/kişiselleştirme,
VAD/barge-in yeniden tasarımı, log bakımı ve debloat bu adıma dahil edilmedi.

Kontrollü kanıt: 742 pytest geçti; yeni 5 test tur bitmeden teslim, giriş/çıkış
snapshot kimliği, Stop'ta metin korunması, interrupted olayının metni, bildirim
hatasında final yedek ve köprü JSON serileştirmesini kapsar. Node transkript
süiti tek balon, sıra/kimlik sınırı, güvenli metin, kesilme/belirsizlik, yedek
ve geç giriş sırasını doğrular; diğer 4 Node süiti de geçti. Değişen Python
dosyaları ve native test betiği Pyright'ta 0 hata verdi.
[Hedefli gerçek WebView2](stage5-transcript-native.json) tur hâlâ aktifken
görünen yanıtı ve araya girme sonrası aynı balonda korunan Interrupted metni
doğruladı. Gerçek hesap/ücretli API/kullanıcı notu kullanılmadı; fiziksel kabul
açık. Önceki gerçek barge-in kabulü kullanıcının bildirdiği sorunlarla açıktır.

Son tam native kontrol [10/10 faz geçti](stage5-transcript-full-native.json).
Chat fazında tur bitmeden transkript, kesilen tek balon, barge-in, Disconnect
tampon iptali ve unknown kilidi; diğer fazlarda ayar/not/import/export/kurtarma
regresyonu doğrulandı. Toplam 742 pytest, 5 Node süiti ve 0 Pyright hatası;
son metin sınırı/geç giriş sırası düzeltmeleri ayrıca hedefli testlerden geçti.
Sonraki ayrı adım, kullanıcının belirlediği adım 3 VAD/barge-in düzeltmesidir.

### Önceki: konuşarak yanıtı kesme / güvenli tur devri — 22 Ekim 2026

Kullanıcı otomatik dinleme testlerini başarılı bildirdi. Bu tek adımda Live
yanıtının ilk kabul edilen ses parçasından itibaren aynı mikrofon adaptörü
yerelde konuşma adayı bekler. Kullanıcı konuşunca eski ses kuyruğu hemen
kesilir; yeni PCM mevcut 500 ms ön tampon ve en çok 3 saniyelik sınırlı RAM
kuyruğunda bekler. Model hâlâ çalışıyorsa eski request_id ile mevcut Stop
istenir. Yalnız ses çalması kaldıysa sağlayıcıya gereksiz Stop gönderilmez.

İptal kabulü tur bitişi sayılmaz. Eski host raporu completed:true ve ok:true
veya stopped:true vermeden yeni live_audio_start başlatılmaz. unknown/pending
araç sonucu mevcut kilidi kapatır ve yeni ses atılır. Tamamlanan not/araç
sonuçları korunur, backend'den yenilenir; geri alma, yeniden mutasyon veya
save geri beslemesi yoktur. Yeni tur da aynı ModelTools/registry/policy/
TaskManager ve transkript/ilk not aktarımı kapısından geçer.

Bu uygulama mevcut Stop hattıyla **sıralı tur devridir**; ikinci Live sahibi
veya aynı anda iki model turu açmaz. Sağlayıcının aynı socket üzerinde tam
çift yönlü interruption protokolü uygulanmış gibi sunulmaz. Aktif Stop Live
oturumunu sıfırlayabildiğinden yeni tur yeni mantıksal oturum/context açabilir;
mevcut UI context_reset_reason bilgisini gösterir. Sağlayıcı VAD sözleşmesi
resmi capabilities belgesinden yeniden kontrol edildi; yeni SDK protokolü eklenmedi.

Mikrofon/callback, eski istek kimliği, bağlantı revizyonu ve dinleme revizyonuna
bağlıdır. Eski PCM kesmeden sonra yeniden çalınmaz. Stop/Pause/Disconnect,
anahtar/model değişimi, cihaz hatası veya kuyruk taşması bekleyen sesi geçersiz
kılar. Eski turun güvenli kapanışı 3 saniyeden uzun sürerse ses kırpılıp
yürütülmez; dinleme durur ve kullanıcı yeniden konuşmalıdır.

Kontrollü geliştirme hesabı/kullanıcı notu/ücretli API kullanılmadı. İlk native
denemede test sunucusunun tek PCM paketi üretim boyut sınırını aşıyordu;
sentetik paket küçültüldü, üretim doğrulaması gevşetilmedi. Hedefli gerçek
WebView2/sentetik ses kontrolünde aktif yanıt ve kalan ses kesmesi, korunmuş
tek not yazısı, otomatik yeni tur ve Disconnect ile bekleyen sesin silinmesi
geçti. Son kanıtlar aşağıdaki kapanış kaydındadır. Gerçek yankı/gürültü ve
hesap kabulü açık; kulaklıkla manuel test önerilir. Debloat ve diğer özelliklere
geçilmedi; kullanıcı kabulünden sonra Aşama 5 kapanış kontrolleri ve planlı
hedefli bakım/debloat ele alınacak.

Kapanış kanıtı: [10/10 gerçek hidden WebView2 fazı geçti](stage5-barge-in-full-native.json).
Native chat raporu aktif yanıtta korunmuş not, yalnız çalma sırasında yeni tura
geçiş, geciktirilmiş gerçek iptal sırasında sıfır yeni tur, Disconnect ile
tamponun silinmesi ve unknown sonucunda sıfır yeni tur/kilitli kontrolleri içerir.
737 pytest, 4 Node süiti, JS syntax ve native test betiğinde 0 Pyright hatası.
UI'da üretim değişikliği app.js'teki mevcut koordinasyondadır; backend/core
iş mantığı veya yeni bağımlılık eklenmedi. Kalan sıra gerçek kullanıcı barge-in
kabulü, Aşama 5'in açık entegre kabul koşulları ve hedefli bakım/debloat'tır.

### Önceki: düğmesiz konuşma ve yanıttan sonra otomatik dinleme — 22 Ekim 2026

Kullanıcının isteğiyle native Mic artık her konuşmayı başlatma düğmesi değildir.
Uygulama ve API'den yüklenen Live model hazırsa otomatik yerel dinleme açılır;
katalog yüklemek hâlâ mevcut Load Live Models düğmesindedir. Katalogda/model
onayında bulunmayan bir model veya sabit fallback listesi kullanılmaz.
Üst düğme yalnız Pause listening / Resume listening olarak dinlemeyi duraklatır.
Her başarılı yanıtın sesi bittikten sonra yeniden dinlemeye geçilir; kullanıcı
her mesaj için düğmeye basmaz. Yazılı mesaj yerel beklemeyi durdurup aynı sohbet
kilidinden geçer, başarılı Live yanıtı ardından dinleme geri gelir.

Sessizlik API'ye gönderilmez. Mevcut AudioWorklet yerelde 200 ms ardışık RMS
>=0.015 ses adayını bekler; en çok 500 ms ön tampon tutar. Bu eşik yalnız
gönderime aday başlatır, söz/anlam/işlem yetkisi belirlemez. Konuşma bitişi
sağlayıcı VAD'sinde, araç niyeti transkript ve aynı ModelTools/core hattındadır.
Setup beklerken en çok 3 saniye PCM tutulur; fazlasında sessiz kırpma yerine
dinleme durur. Gönderim kuyruğu yine 1 saniye, backend 2 saniye, bir konuşma
giriş bütçesi 15 saniyedir. Yerel bekleme sessizlikte süresizdir ve sağlayıcı
turunu/kotasını zamanlayıcıyla tekrar tekrar başlatmaz.

Yanıt sırasında mikrofon kapanır; ses bittikten sonra otomatik yeniden açılır.
Bu yarı çift yönlü (dinle → yanıtla → dinle) kullanımdır. Yanıtı konuşarak
kesme/barge-in henüz uygulanmadı ve ayrı sonraki adımdır; sürekli açık socket
üzerinde aynı anda giriş/çıkış varmış gibi raporlanmaz. Stop/Pause/Disconnect,
anahtar değişimi, cihaz/izin hatası, taşma, model hatası veya belirsizlikte
otomatik dinleme durur. Hata/Stop sonrasında otomatik retry/replay yoktur;
kullanıcı Resume listening ile açıkça devam eder. Model değişimi yalnız backend
seçimi onayladıktan sonra yeniden dinlemeyi açabilir; manuel duraklatmayı kaldırmaz.

Kontrol: 737 pytest, dört Node süiti, JS syntax ve native test betiğinde 0
Pyright hatası. Node testi bir dakikalık sentetik sessizlikte paket üretilmemesi,
ses adayında ön tampon, 15 saniye sınırı, geç izin/Stop ve kuyrukları doğrular.
[Hedefli gerçek WebView2](stage5-auto-listen-native.json): düğmesiz katalog sonrası
başlangıç, boşta sağlayıcı çağrısı olmaması, düğmeye ikinci kez basmadan iki
konuşma, yanıt sonrası yeniden dinleme, izin reddi, Stop/cihaz çıkarılması ve
önceki REST/Live araç/iptal/yeniden bağlantı senaryoları geçti. İlk test geçişinde
test sırası önceki Stop ile otomatik modu zaten duraklatmıştı; başlangıç kabulü
Stop öncesine taşındı. İzin reddindeki "hazırlanıyor" yazısının kalması gerçek
bir UI hatasıydı; düzeltildi ve native kabul tekrar geçti. Gerçek hesap, ücretli
API, kullanıcı notları veya fiziksel mikrofon kullanılmadı. Ortam gürültüsü,
kısık ses ve izin kalıcılığı gerçek kullanımda ayrıca doğrulanmalıdır.

Son tam kontrol: [10/10 hidden native faz geçti](stage5-auto-listen-full-native.json).
Mevcut ayar/not/kimlik deposu/import/export/kurtarma senaryolarıyla birlikte
otomatik başlangıç ve iki konuşma kontrolü geçti. Son ön tampon düzeltmesi,
setup kuyruğu boşalmadan sınırın daraltılıp yanlış taşma üretmesini önler;
Node testinde 2 saniyelik bekleyen sesle ayrıca doğrulandı. Gerçek hesap ve
donanım kabulü açık bırakıldı; sonraki aşamaya geçilmedi.

### Önceki: tek konuşmada canlı PCM ve otomatik VAD — 22 Ekim 2026

Kullanıcı otomatik cihaz listesini onayladı. Mic artık WebM kaydını bitişte
göndermek yerine AudioWorklet ile konuşurken 100 ms / 3.200 bayt mono
16 kHz, little-endian PCM gönderir. Hazırlık/izin sırasında gönderim yoktur;
Live setup onayından sonra başlar. Konuşma bitişini sağlayıcının otomatik
VAD'si algılar; silence_duration_ms=700 seçildi. İlk model/araç yanıtında
giriş kapanır. Açık Mic ile tek konuşma akışıdır; sürekli açık çok turlu
dinleme, uyandırma ve yanıt sırasında araya girme yoktur. Sonraki ayrı adım
barge-in'dir. Aşama 5 kapanmadı.

Tek Live sahibi ve sohbet kilidi korunur. Kuyruklar backend'de 2 saniye,
UI'da 1 saniye; işçi toplam üretimi ve giriş bütçesi 15 saniyeyle sınırlıdır.
İstek kimliği/sıra/boyut doğrulanır; taşma veya hatada tur durur, otomatik
retry/fallback/replay yoktur. Stop gerçek bitişi bekler; tamamlanmış araçlar
geri alınmış sayılmaz. Transkript gelmeden araç başlamaz. Notlar aynı
ModelTools → registry/policy/TaskManager ve ilk aktarım kapısından geçer.
Metin/eski klip/VAD setup kapsamlarının resume kimliği ayrıdır. Eski
live_audio klip olayı uyumluluk için kalır; masaüstü Mic yeni akışı kullanır.

Sağlayıcı sözleşmesi resmi [Live capabilities](https://ai.google.dev/gemini-api/docs/live-api/capabilities)
sayfasından doğrulandı: send_realtime_input + otomatik VAD, duraklatılan
akışta audio_stream_end; manual activity_start/end ile karıştırılmaz.
Toplu not silme, diğer entegrasyonlar ve UI temizliğine geçilmedi.

Kontrollü sonuç: **737 pytest geçti**, değişen Python dosyaları ve native test
betiği Pyright'ta **0 hata** verdi. Node canlı akış, eski klip uyumluluğu, ses
çıkışı ve not tarihleri kontrolleri geçti; pip check temiz. İlk sentetik denemede
alıcı yeni pakette uyanmadığı için test başarısız oldu. Tam native denemede de
SDK'nin URL-safe base64 verisini standart decoder ile okuyan test sunucusu
hatası görüldü. İki taşıma taklidi düzeltildi; üretim PCM sözleşmesi gevşetilmedi.
[Hedefli native chat](stage5-stream-vad-native.json) gerçek hidden WebView2,
AudioWorklet, sentetik oscillator, transkript, Stop/cihaz çıkarılması, çıkış
yönlendirmesi ve mevcut REST/Live araç kontrollerini geçti. Tam native süitin
son sonucu kapanış notunda ayrıca belirtilir. Gerçek hesap/API, kullanıcı
notları ve fiziksel mikrofon kullanılmadı. Sentetik sunucunun ilk ses parçasında
yanıt üretmesi, gerçek sağlayıcının VAD kalitesini kanıtlamaz.

İzinler: native profil private_mode=False ve aynı origin/storage_path ile
korunur. WebView2'nin izin kararı ile seçilen cihaz tercihi ayrıdır. Gerçek
izin penceresinin yeniden açılış kalıcılığı bu dilimde denenmedi. Hava durumu,
konum ve kamera native entegrasyonu henüz yok; konum mevcut settings şemasında
bulunmuyor. Bağlandıklarında kayıtlı tercih ve geçerli izin yeniden kullanılmalı;
Windows/OS iptali veya profili temizleme ayrıca ele alınmalı.

#### Canlı akış dilimi kapanış kanıtı

[Tam native raporu](stage5-stream-vad-full-native.json): **10/10 native faz
geçti** (save, reopen, notes, persistence, export_cancel, credentials, chat,
corrupt, schema_invalid, future). Chat fazında gerçek WebView2/AudioWorklet,
sentetik PCM/transkript, Stop, cihaz çıkarılması, not CRUD, araç tekrarına karşı
tek yazı, REST/Live Stop, GoAway/resume ve kaynak kapanışı doğrulandı.
URL-safe base64 test sunucusu düzeltmesinden sonra tam tur yeniden geçti.
Son ek SDK wire kontrolü de geçti: 8 canlı giriş testi, 737 toplam pytest,
4 Node süiti, 0 Pyright hatası, temiz pip check. Gerçek hesap/fiziksel mikrofon,
sağlayıcı VAD hassasiyeti ve izinlerin gerçek yeniden açılış kabulü açık.
Kullanıcı kısa deneme listesi docs/USER_ACCEPTANCE.md'nin başındadır.

### Önceki: otomatik cihaz listesi — 22 Ekim 2026

Kullanıcı cihaz testlerini başarılı bildirdi; ilgili kullanıcı kabulü kaydedildi.
İsteğiyle Scan Devices / Grant Permission düğmesi kaldırıldı. Native hazır
bildiriminde, Audio ayarları açıldığında ve devicechange'de liste otomatik
yenilenir. Tarama yalnız enumerateDevices kullanır; getUserMedia çağırmaz,
izin istemez, kayıt başlatmaz ve hiçbir stream'i kapatmaz. İlk mikrofon izni
Mic düğmesindedir; izin sonrası liste bir kez daha yenilenir. İzin öncesinde
platform bazı cihazları/adları gizleyebilir; bu eksiklik için izin döngüsü yoktur.
Kayıtlı cihaz tercihi ve native save akışı korunur; listeleme tercih yazmaz.

Tek prompt/tek adım sınırı gereği bu dilim cihaz işinin son iyileştirmesidir;
sürekli dinleme/VAD bu promptta uygulanmadı. Sonraki tek adım, sınırlı PCM
akışını aynı Live sahibine taşımak ve konuşma bitişi/VAD davranışını açıkça
doğrulamaktır. Stop/Disconnect, araç kimlikleri ve belirsiz sonuç kuralları
korunacak; ardından konuşarak araya girme ve son entegre kabul ele alınır.

[Otomatik listeleme native chat kanıtı](stage5-auto-devices-chat-native.json):
Scan düğmesi olmadan açılış listesi, ayar açılışında sentetik cihaz listesi,
tarama sırasında getUserMedia çağrılmaması, exact giriş, cihaz çıkarılması,
seçim kaydı ve çıkış hazırlığında Stop doğrulandı. Gerçek hesap/ücretli API
ve kullanıcı verisi kullanılmadı. Önceki tam Python/native sonuçlar aşağıda
tarihçedir; bu UI diliminde tam süitler yeniden koşulmadı.

Son hedefli kontrol: native chat ve [save/reopen](stage5-auto-devices-reopen-native.json)
ile **3 native senaryo** geçti; başlangıç listesi, taramada kayıt açılmaması,
seçim/ayar/reset koruması ve yeniden açılış doğrulandı. Üç Node modül süiti
(mikrofon, ses çıkışı, not tarihleri) ve app/settings/panels syntax kontrolleri
geçti. Üretim Python/core veya sağlayıcı sözleşmesi değiştirilmedi.

### Açılış önbelleği düzeltmesi — 22 Ekim 2026

Kullanıcı cihaz diliminden sonra --debug ile boş pencere bildirdi; sonraki
açılışın çalıştığını onayladı. Eski konsol hatası alınamadığından belirli bir
import hatası kesin neden diye işaretlenmedi. Doğrulanan açık: PyWebView 6.2.1
statik dosya handler'ı no-store'u global response'a koyuyor, sonra farklı
static_file yanıtı döndürüyor; gerçek dosya yanıtında bu başlık bulunmuyor.
Non-private native başlangıç sabit DEFAULT_HTTP_PORT=42001 kullanıyor; eski
modüllerin aynı origin'de yeniden kullanılabilmesi gerçek bir güncelleme riski.

main._ui_app mevcut Bottle/SDK sunucusunu kullanır. Her açılışta yalnız asset
yoluna yeni bir önek verilir; HTML, CSS ve bütün göreli ES import'ları aynı
önekten yüklenir. no-store/no-cache gerçek statik yanıta eklenir. Origin,
WebView storage_path, settings/notes ve Windows kimlik deposu korunur; cache
ve kullanıcı profili silinmedi. WSGI app'in SDK sunucusu sabit önceki portu
kullanır; ikinci global HTTP sunucusu açılmaz. Zaten lock'ta kurulu Bottle
0.13.4 kullanıldı, yeni paket kurulmadı; doğrudan kullanım pyproject'e yazıldı.

Hedefli Bottle/WSGI testleri gerçek no-store başlığı, her açılışta yeni import
kökü, güncel settings export'u, dosya değişikliği ve dizin dışına çıkma reddini
doğrular. --debug gerçek hidden WebView2 chat/mikrofon/cihaz senaryosu geçti;
kullanıcı da yeniden açılışı onayladı. Gerçek hesap/API isteği yapılmadı.

Son kontroller: **74/74** hedefli pytest, Pyright **0 hata/0 uyarı**, pip check
temiz; [tam native açılış raporu](stage5-ui-startup-native.json) **10/10**.
Yeniden açılış, not/ayar koruması, import/export, Windows kimlik deposu,
REST/Live Stop ve mikrofon/cihaz yolu gerçek WebView2/sentetik taşıma ile geçti.
Tam Python süiti yeniden koşulmadı; önceki tam sonuç 727/727'dir.

İlk tam native tur credentials aşamasında hazır olma timeout'u verdi. Testlerin
kullanıcı uygulamasıyla aynı sabit porta bağlanabilmesi giderildi: her geçici
test profili ayrı boş port seçer, aynı testin reopen süreçleri bu portu korur.
Credentials tek başına ve ardından tam 10/10 geçti. İlk timeout'un kesin
nedeninin port çakışması olduğu kanıtlanmadı; başarısız sonuç kaydedildi,
assertion veya hazır olma şartı zayıflatılmadı.

### Önceki dilim — cihaz seçimi ve mikrofon kullanıcı kabulü

Son doğrulama: ilgili Python regresyonu **92/92**; üç Node modül süiti ve
değişen dört JS dosyasının syntax kontrolü geçti. Tam Python süiti bu JS
diliminde tekrar koşulmadı; önceki tam sonuç 727/727'dir. [Cihaz native raporu](stage5-audio-devices-native.json)
gerçek hidden WebView2'de **10/10** geçti. Sentetik cihaz listesiyle Scan'in
yalnız kendi stream'ini bırakması, sayısal string ID'li exact giriş, cihaz
çıkarılınca kaydı atma, eksik sink'te metni koruma, tercihlerin native JSON'da
doğrulanması ve çıkış hazırlığında Stop'un modele istek göndermemesi test edildi.
Bu makinenin WebView2'sinde setSinkId API'si mevcut ve varsayılan sink çağrısı
başarılıdır; gerçek birden fazla hoparlör arasında geçiş kabulü yapılmadı.

İlk tam native tur eski reset koruma kontrolünde başarısız oldu. Ayrıntılı
karşılaştırmada otomatik ayar-paneli taramasının varsayılan dOut seçeneğinin
saveAll tarafından store'a eklenmesi saptandı; bu aralıklı test hatası değildi.
Native dIn/dOut tercihinin sahibi onchange/store olarak düzeltildi: listeleme
ve reset yeni cihaz tercihi üretmez. Aynı koruma kontrolüyle son tam native
10/10 geçti. Başarısız sonuç gizlenmedi, assertion zayıflatılmadı.
Bağımsız audit-fixes.mjs bu turda çalıştırılmadı; playwright-core mevcut proje
ortamında yoktu, yeni test bağımlılığı kurulmadı. Gerçek hesap/ücretli API veya
kullanıcı notları/anahtarı kullanılmadı.

Kullanıcı başlat/bitir mikrofon testlerini başarılı bildirdi; temel fiziksel
mikrofon → transkript → Live ses kabulü tamamlandı. Bu bildirim sürekli
dinleme/VAD, bütün cihazlar veya konuşarak araya girme kabulü değildir.

Sıradaki tek dilim dIn/dOut cihaz seçimidir. Native UI'da açık Scan düğmesi
geçici mikrofon izni ister, enumerateDevices ile audioinput/audiooutput listesini
alır ve yalnız kendi izin stream'ini kapatır. Açılış veya devicechange izin
istemez. Kamera bu dilimde açılmaz. Browser-only onEvent/device yolu korunur.

Tercihler mevcut store.devs/Save Settings hattındadır; Python donanım indeksi
browser kimliği sayılmaz. Sayısal görünümlü string ID opak metin olarak korunur.
Varsayılan açık seçimdir. Özel giriş getUserMedia deviceId.exact ile, özel
Live çıkışı AudioContext.setSinkId ile uygulanır; başka cihaza sessiz fallback
yoktur. Seçim sonraki kayıt/yanıt içindir; çalışan kaydı yeniden açmaz.
Ses efekti oynatıcısı mevcut OS varsayılanında kalır.

Çıkış hazırlığı en çok 3 saniye sürer; bu sırada Stop/Disconnect/model/anahtar
değişimi model isteği gönderilmeden yerel hazırlığı bitirir. API desteklenmiyorsa,
izin reddedilirse veya cihaz yoksa output_device_unavailable gösterilir; metin
ve doğrulanmış araç sonucu korunur. devicechange sırasında seçili cihaz artık
listede yoksa yalnız sahip olunan kayıt/Live sesi bırakılır. Kayıp kayıtlı
tercih listede açıkça kullanılamaz görünür; ilk cihaza çevrilip üzerine yazılmaz.

Browser cihaz kimlikleri origin/izin kapsamına bağlıdır; yeni yerel origin veya
izin değişiminde yeniden Scan gerekebilir. Kalıcı UI tercihi fiziksel cihazın
her açılışta aynı kimlikle bulunacağını garanti etmez. Gerçek çoklu cihaz ve
çıkarma/takma kabulü kullanıcı testidir. Sonraki ayrı dilim sürekli akış/VAD'dır.

Başvurular: [Web Audio setSinkId](https://webaudio.github.io/web-audio-api/#dom-audiocontext-setsinkid),
[Media Capture enumerateDevices](https://www.w3.org/TR/mediacapture-streams/#dom-mediadevices-enumeratedevices).

### Kullanıcı önerisi — ayrı toplu not silme işi

“Son eklenen 2 notu sil” ve “tüm notlarımı sil” ayrı bir not iyileştirmesi
olarak kaydedildi; bu cihaz diliminde uygulanmadı. Güncel liste/gerçek ID'lerden
kesin hedef kümesi çıkarılmalı; bilinmeyen tarih veya sınırdaki tarih eşitliği
tahminle aşılmamalı. Toplu hedef/etki açıkça gösterilmeli, tümünü silme için
ürün onayı tasarlanmalı. Tek core işlemiyle atomik yazı/readback veya açık
ID bazlı gerçek sonuç kullanılmalı; modelin tekli delete döngüsüne güvenip
kısmi işlem tam başarı sayılmamalı. Replay/Stop/unknown kuralları korunmalı.
Bu öneri Aşama 5 kapanışına kendiliğinden yeni zorunlu kapsam eklemez.

Not, rutin ve skill aynı registry/policy/TaskManager/sonuç/kayıt temelini
kullanacaktır. Ayrı veri şeması ve alan araçları gerekir; genel CRUD framework'ü
veya her özellik için yeni mimari kurulmaz. Rutin scheduler'ı ve skill adım
doğrulama/yürütmesi ayrıca ele alınır. Bugün model/core entegrasyonunda notlar
ileridedir; rutin/skill'in model bağlantısı hazırmış gibi işaretlenmez.

### Önceki dilim — mikrofon kontrollerinin kanıtları

22 Ekim mikrofon doğrulaması: son tam pytest **727/727**, mikrofonun hedefli
SDK/core süiti **11/11**, seçili üretim dosyaları ve yeni testte Pyright
**0 hata/0 uyarı**. `live-mic.mjs`, `live-audio.mjs`, `note-timestamps.mjs`
ve JS syntax kontrolleri geçti. [Native rapor](stage5-microphone-native.json)
gerçek hidden WebView2'de **10/10** senaryodur: sentetik oscillator stream'i
gerçek MediaRecorder/WebM decoder üzerinden 16 kHz PCM'e çevrildi; aynı
Live hattında transkript/yanıt, track kapanışı, izin reddinde kontrollerin
açılması ve Stop'un kayıt göndermeden silmesi doğrulandı. Gerçek mikrofon,
üretim hesabı/anahtarı veya ücretli API çağrısı kullanılmadı.

İlk hedefli testte SDK'nin activityStart/activityEnd ve iç setup alanlarını
karışık camelCase/snake_case serileştirmesi test beklentisinde düzeltildi;
üretim SDK'sı yeniden yazılmadı. İlk native denemede önceki anahtar değişimi
testinin kataloğu bilerek boşaltması mikrofonun başlamasını doğru olarak
engelledi; fixture güncel katalogla yenilendi, chat senaryosu ve tam native
süit geçti. Tip kontrolündeki text daraltması açık boş metin atamasıyla
düzeltildi; kontrol projenin .venv Python'u ile tekrarlandı.

Bir tam regresyonda eski `test_quoted_literal_note_name_is_not_latest_instruction`
testi verified=false gördü (726 geçti/1 başarısız). İlgili modül ayrı çalışmada
53/53, ardından native süitiyle eşzamanlı olmayan tam çalışmada 727/727 geçti.
O hata için kök neden kanıtlanmadı; zamanlama/yük olduğu kesinleştirilmedi,
üretim not kodu veya test beklentisi değiştirilmedi. Yeniden oluşursa görev
sonucu/hata koduyla ayrıca incelenmelidir; başarısız ilk sonuç gizlenmedi.

Güncel tek dilim: açık başlat/bitir mikrofon girişi. Kullanıcı 22 Ekim'de
Live ses çıkışını gerçek kullanımda çalışıyor diye onayladı; eski “no playback”
arayüzü debug açılışı/yenileme sonrasında güncellendi. Bunun kesin önbellek
kök nedeni kanıtlanmadı; bu kabul her Mute/Stop/cihaz yarışını doğrulamaz.
REST metin hattı, araç/Stop ve tek Live oturumu sahibi korunur.

Mikrofon düğmesi yalnız açık kullanıcı hareketiyle izin ister. Kayıt RAM'de,
en çok 15 saniye/1 MiB'dir; süre dolarsa gönderilmeden silinir. Finish & Send
kaydı bitirir, track'leri kapatır ve tarayıcıda mono/16 kHz/16-bit PCM'e
çevirir (en çok 480.000 bayt). Bu ilk dilim canlı sürekli upload değildir:
kayıt bitince tek sınırlı konuşma gönderilir. Stop/Disconnect/model/anahtar
değişimi/sayfa kapanışı kaydı atar; geç izin verilirse track hemen bırakılır.
Kayıt/PCM dosya, log, localStorage veya yedeğe yazılmaz; transkript normal
konuşma görünümündedir. Çıkışla aynı anda mikrofon açılmaz.

`live_audio` aynı TextChat kilidi → PersistentLive → ModelTools/core yoludur.
Yeni araç yürütücüsü yoktur. Sağlayıcı manual activityStart/audio/activityEnd
ve input_audio_transcription kullanır; otomatik VAD bu ses setup'ında kapalıdır.
Metin ↔ mikrofon değişimi farklı setup olduğundan yeni mantıksal oturumdur;
eski checkpoint kullanılmaz. Kayıt veya kopan komut otomatik gönderilmez.
Transkript gelmeden hiçbir araç başlatılmaz; not hedef doğrulaması transkript
ve aynı turdaki verified liste üzerinden yürür. İlk not aktarımı kapısı korunur.
Gerçek mikrofon kabulü, sürekli akış/VAD, konuşarak araya girme ve cihaz seçimi
sonraki ayrı dilimlerdir; REST hâlâ yalnız metindir.

PCM yalnız güncel request_id ile host → izinli audioChunk bildirimi →
live_audio.js üzerinden Web Audio'ya gider. Yeni paket gerekmiyor. Kuyruk
20 saniye/512 source, paket 128 KiB ve tur toplamı 2.880.000 baytla sınırlı.
16-bit little-endian mono/24 kHz standart biçim kabul edilir. Format/cihaz/
autoplay/taşma hatasında kalan ses kesilir, uyarı gösterilir; doğrulanmış araç
sonucu/metin korunur. PCM log/history/localStorage/yedek/dosyaya yazılmaz.
CLI/alıcı olmayan denemede ses hâlâ atılır. Sayısal audio_bytes_forwarded ve
audio_bytes_discarded, null/güvenli kod audio_error raporlanır; teslim fiziksel
duyulabilirlik kanıtı değildir. Çıkış OS varsayılan cihazıdır; dOut seçiminin
cihaza uygulanması bu dilimde yoktur.

UI ses sürerken Stop'u tutar. Model bittiyse Stop yalnız yerel sesi keser;
model sürüyorsa native iptal sonucunu da bekler. Mute Live çıkış gain'idir,
mikrofon/SFX değildir. Hata/unknown, Disconnect, model/anahtar değişimi ve
pagehide kaynakları temizler. Geç ses yeni isteğe giremez; ayar/bağlantı
değişimi sırasında biten eski ses yanıtı yeni bağlantıyı online gösteremez.
Backend model bitişi ile UI çalma bitişi ayrı tutulur; en çok 22 saniye
çalma bitişi beklenir. Mevcut 25 saniyelik Live model turu sınırı değişmedi.

Kalıcı API anahtarı zaten Windows kimlik deposundadır. Salt okunur yerel
kontrolde mevcut profil configured=true ve süreç override=false görüldü;
anahtar gösterilmedi/değiştirilmedi. Yeniden açılış aynı profilin kaydını
kullanır. Parola alanı bilerek boş açılır. Farklı TASKVEX_HOME farklı kayıttır.
Testler yalnız geçici profillerin sentetik kayıtlarını oluşturup temizler.

22 Ekim kullanıcı kabulü: REST ve Live not CRUD, aynı metinli hedefte açıklama,
ID ile tek kayıt silme ve Stop sonrası yeni mesaj/önceki işlemi koruma geçti.
Önceki not CRUD “test edilemedi — API limiti” kaydı artık tarihçedir; bu
bildirim gerçek GoAway/resumption veya yeni zaman metadata'sını doğrulamaz.

Kullanıcının yeni isteğiyle önce tek bir ek dilim uygulandı: notlara UTC
`created_at` oluşturulma zamanı. Yeni native notu backend tarihler; düzenleme
ve done değişimi bu alanı korur. UI önbelleği, yedek/restore ve eski veri
aktarımı metadata'yı taşır. Eski tarihsiz kayıtlara tarih veya ID uydurulmaz;
eksik/null bilinmiyor demektir. Bozuk tarih tüm import/snapshot adayı için
yazı öncesi rettir. Yedekten gelen tarih ve makine saati mutlak sıralama kanıtı
değildir: eşit/bilinmeyen tarih ve saat sapması sonraki seçim adımında gözetilir.

Sonraki ayrı promptta “son not” ve “içinde 'merh' geçen not” seçimi uygulandı.
Kullanıcının mesajındaki tırnaklı literal parça güncel listenin tamamında
aranır; bir aday varsa ve model aynı gerçek ID'yi seçmişse yürütülür. TR/EN
açık kalıplar desteklenir; genel doğal dil/bulanık benzerlik çözülmez. Son
not en büyük oluşturulma zamanı demektir; liste konumu veya son edit değildir.
Bütün tarihler bilinmeli ve maksimum tarih tek olmalıdır. Tek açık ID diğer
belirsizlikleri giderebilir. Birden fazla filtre, latest + contains, sıfır/çoklu
aday, desteklenmeyen/olumsuz/tırnaksız filtrede açıklama istenir. Bu seçim
iyileştirmesi kullanıcı tarafından tamamen çalışıyor diye onaylandı. Sonraki
ses çıkışı dilimi yukarıda güncellendi; mikrofon henüz eklenmedi.

Güncel dilim: model üzerinden not düzenleme/tamamlama/silme uygulandı.
REST ve Live, mevcut CRUD'u aynı ModelTools/core hattından kullanır; ilk
not aktarımı onaylanmadan bütün not araçları kapalıdır. Aşağıdaki tarihsel
dört araç kapsamını bu bölüm ve UI/backend sözleşmesinin güncel bölümü yeniler.

Yeni mutasyondan önce o kullanıcı turunda verified notes.list gerekir.
Host kullanıcının mesajındaki tek gerçek ID, tek mevcut tam metin veya üstteki
tek içerik/zaman seçimini hedef sayar. Ayrılamayan aynı metinli notta ID istenir; diğer dolaylı tarif, sıra numarası,
birden fazla eşleşme veya bilinmeyen hedefte `note_target_required` ile açıklama
istenir. Eşleşme harf/boşluk farklarını tolere eder, kelime sınırını korur;
serbest doğal dil hedef çözümleme iddiası yoktur. Model ayrıca adayların gerçek
ID'lerini gösterip açıklama istemeye yönlendirilir. Core iş mantığı değiştirilmedi.

Mutasyon sonrası veya yeni başarısız okumada eski liste seçimi silinir. Her
kullanıcı turu seçimi yeniler; replay/Stop/GoAway kimlikleri korunur. Eski çağrı
aynı gerçek sonucu verir, tekrar yazmaz; değişmiş içerik manager çakışmasıdır.
UI mevcut backend okumasıyla yenilenir, ikinci mutasyon/save göndermez. Readback
belirsizse unknown kilidi korunur; tamamlanmış yazı Stop/kopma ile geri alınmış sayılmaz.

Önceki bağlantı adımında yerel ilerlemeyi engelleyen açık hata yoktur. Not
CRUD ve genel Stop akışının kullanıcı kabulü yukarıda güncellendi. Gerçek
GoAway/resumption ve senkron REST HTTP beklemesinin özel yarış senaryoları
ayrıca doğrulanmış sayılmaz; kontrollü taşıma gerçek sağlayıcı kabulü yerine geçmez.
Tek yazar/tek aktif mesaj sınırı sürer; ayrı bir süreçten eşzamanlı not yazımı
desteklenmez. Yeni hedef kontrolü bunu bir sürümlü çoklu yazar sistemine dönüştürmez.

| Adım | Kapsam | Durum |
|---|---|---|
| 1 | Host kontrollü araç kataloğu; model tool call → registry/policy/TaskManager → kimliği korunmuş sonuç; replay, bekleme ve iptal | Sağlayıcıdan bağımsız adaptör hazır, 22 test geçti |
| 2 | Anahtar/model ayarı ve güncel Gemini SDK adaptörüyle bir metin turu; çağrı/sonucu sağlayıcı biçimine çevirme, sınırlı araç turu ve ağ/kota hataları | SDK/CLI hazır; 3.5 Flash-Lite ile canlı katalog ve sentetik not kabulü geçti. Güvenli retry/fallback kontrollü testlerle doğrulandı; birleşik politikanın canlı kabulü açık |
| 3 | Native text/stop_task, güvenli anahtar girişi ve doğrulanmış bağlantı durumunu bağlama | Anahtar, UI, Live kataloğu, REST/Live Stop ve güvenli checkpoint ile Live devam ettirme hazır |
| 4 | Tek Live oturumu sahibi; mikrofon/hoparlör ve sınırlı ses kuyrukları | Live ses çıkışı kullanıcı tarafından onaylandı; sınırlı başlat/bitir mikrofon girişi eklendi, gerçek mikrofon/VAD/cihaz kabulü açık |
| 5 | Bağlantı kopması/yeniden bağlanma, çağrı kimliğinin korunması ve son gerçek cihaz kabulü | GoAway/idle resumption kontrollü testlerle hazır; gerçek hesap/cihaz kabulü açık |

SDK/model güncel resmi belgelerle doğrulandı: google-genai 2.32.0 ve metin için
gemini-3.8-flash. Anahtar açık GEMINI_API_KEY süreç ortamından, yoksa profilin
Windows kimlik deposundan gelir; genel ayar/yedeğe yazılmaz. 5.3'ün ilk diliminde
UI anahtar kaydı ve metin isteği bağlandı; son başarılı metin isteği gösterilir,
kalıcı Live, araç bağlantısı ve REST/Live Stop sonraki dilimlerde eklendi.

## Uygulama planı ve her adımın bitiş koşulu

Bu bölüm hedeftir; aşağıdaki açık işlerin uygulanmış olduğu anlamına gelmez.
Sıra 1 → 2 → 3 → 4 → 5'tir. Bir adımın çalışan akışı ve hata kontrolü
geçmeden sonraki katmanı bağlamayacağız. Her seferinde kapsamlı yeni bir denetim
döngüsü yerine değişen davranışa hedefli test ve mevcut regresyon süiti çalışır.

### 1 — Ortak araç çağrı hattı: tamamlandı

Mevcut ModelTools kullanılacak; ikinci dispatcher, izin sistemi veya görev
yöneticisi yazılmayacak. Host görünür araçları seçer; model kullanıcı kimliğini,
dosya yolunu veya yetkiyi payload ile değiştiremez. 22 testin kapsamı aşağıdadır.

### 2 — Gemini ile ilk metin ve araç turu: uygulandı, alternatif modelle canlı kabul geçti

Önce küçük Python denemesinde, UI ve mikrofon olmadan tek konuşma turu kurulur:
metin → Gemini → araç çağrısı → ModelTools → gerçek core sonucu → Gemini yanıtı.

- Güncel resmi Python SDK ve desteklenen model seçilir; sürüm mevcut pyproject
  ve lock düzeninde sabitlenir. Önce kullanılan araç şemalarının sağlayıcıyla
  uyumu kontrol edilir. Uymayan kurallar sessizce atılmaz; core doğrulaması korunur.
- İlk geliştirici denemesinde anahtar yalnız süreç ortamından alınır; kaynak,
  komut satırı argümanı, log, settings.json, localStorage veya yedeğe yazılmaz.
  Anahtar yoksa yerel core/UI çalışır, model açık ve anlaşılır hata verir.
- SDK'ya yürütülebilir Python handler'ları verilmez; otomatik araç çalıştırma
  TaskManager'ı atlayamaz. Araç bildirimleri ve sonuçları adaptörde dönüştürülür.
  Sağlayıcının çağrı kimliği/konuşma bağlamı korunur. Kimlik sağlanmayan biçimde
  kimlik bir kez host'ta atanır, yeniden denemede tekrar üretilmez.
- İlk canlı araç yalnız apps.catalog olur. Sonra geçici veri dizininde notes.add
  ve notes.list denenir; host izinli listeyi açıkça genişletir. Canlı not içeriği
  model hizmetine gönderilmeden kullanıcı kapsamı ve aktarılacak veri belli olur.
- Araç turlarının sayısı ve ağ beklemesi sınırlanır. Bozuk çağrı, boş yanıt,
  doğrulama reddi, 401/403, kota ve ağ timeout'u kontrollü sonuca dönüşür.
  Yan etkili çağrı ağ hatası nedeniyle otomatik yeniden yürütülmez.

Bitiş koşulu: gerçek model katalog isteğini araçla yanıtlar; geçici not denemesi
gerçekten tek kayıt üretir; hatalı çağrı diske yazmaz. Sağlayıcıya gönderilen
sonuç yalnız gerçekten terminal olmuş görevden alınır. Canlı kabul ile kontrollü
ağ/SDK testleri ayrı raporlanır. Bu adım sesli asistanı henüz çalıştırmaz.

### 3 — Metin, görev durumu ve ayarları mevcut UI'a bağlama

İlk bağımsız dilim olan anahtar kaydı uygulandı. 5.2'nin canlı katalog/not kabulü
503 nedeniyle açık kaldığı sırada yalnız bu yerel dilim ilerletildi; metin/stop_task
ve gerçek bağlantı durumu hazırmış gibi işaretlenmedi.

- Var olan text/reconnect/disconnect/model olayları mevcut sözleşme üzerinden
  yönlendirilir. Model iş mantığı bridge dosyasına yığılmaz; GUI thread'i ve
  modelin alıcı döngüsü uzun araç beklemesiyle bloke edilmez.
- Kalıcı anahtar girişi bağlanmadan önce Windows kimlik bilgisi deposu kullanılır.
  UI anahtarı geri okumaz; yalnız kayıtlı/eksik/hatalı durumunu öğrenir. Yedek
  export/import gizli anahtar taşımaz. Anahtar hata metinlerinde maskelenir.
- Metin ve model yanıtı mevcut konuşma görünümüne güvenli metin olarak gelir.
  Modelin değiştirdiği notlar backend otoritesinden UI'a yansır; UI setter'ı
  ikinci note_add/save komutu üretmez.
- stop_task konuşma turunu ve ilgili core görevini takip eder. İptal kabulü
  bitiş değildir; sonuç belirsizken idle/başarı gösterilmez. Model yanıtını
  durdurmak gerçekleşmiş araç işlemini geri almış sayılmaz.
- Metin API'sinde kalıcı bağlantı varsayılmaz: istemci oluşturmak online kanıtı
  değildir. Başarılı gerçek istekle erişim doğrulanır; son hata/kopma görünürdür.
  Uygulama açılışı kendi kendine ücretli istek veya mikrofon kaydı başlatmaz.

Bitiş koşulu: kullanıcı UI'dan isteği gönderir, araç sonucu ve tek doğru kayıt
görünür; stop, yanlış anahtar, yeniden bağlanma ve offline yerel not kullanımı
denenir. Güncel UI/backend sözleşmesi gerçek olay/yanıtlarla birlikte güncellenir.

### 4 — Tek Live oturumu ve gerçek ses

- Tek oturum sahibi bağlantı, mikrofon ve hoparlör kaynaklarını yönetir. Text
  ve Live aynı ModelTools/core hattını kullanır; iki ayrı araç yürütücü kurulmaz.
- Önce açık mikrofon aç/kapat kontrolüyle konuşma → model sesi çalıştırılır.
  Ses biçimi ve örnekleme hızı seçilen Live modelinin güncel şartlarına göre
  ayarlanır; cihazlar gerçekten açılmadan UI hazır göstermemelidir.
- Ses kuyrukları sınırlı tutulur; yavaş ağ sonsuz bellek birikmesine dönüşmez.
  Kullanıcı konuşarak araya girdiğinde eski ses çalımı temizlenir; başlamış
  araç işlemleri otomatik geri alınmış veya iptal olmuş kabul edilmez.
- Mic/mute, cihaz seçimi ve ses seviyesi mevcut UI'a bağlanır. Mute'un oynatmayı,
  mic kapatmanın kaydı etkilemesi açıkça ayrılır; uygulama kapanışında stream,
  bağlantı ve arka plan işleri gerçekten bırakılır.

Bitiş koşulu: gerçek mikrofon/hoparlörle konuşma ve izinli tek araç çağrısı
çalışır; cihaz yokluğu/ayrılması, sessize alma, araya girme ve normal kapanış
denenir. Sahte ses testi fiziksel cihaz testi diye raporlanmaz.

### 5 — Yeniden bağlanma ve Aşama 5'in son kabulü

- Live bağlantı kesilmesi, oturum devam ettirme ve varsa sunucu kapanış bildirimi
  ele alınır. Devam ettirme anahtarı ile ModelTools session_id/call_id farklı
  kimliklerdir; konuşma bağlamını sürdürmek tek başına araç tekrarını önlemez.
- Geciken eski oturum yanıtı yeni oturumu güncellemez. Bağlantı yenilendi diye
  yeni mikrofon/ikinci oturum veya ikinci araç yürütmesi başlamaz.
- Araç çalışırken ve araç bittikten hemen sonra bağlantı kesilmesi ayrı denenir.
  Sonuç bilinmiyorsa otomatik tekrar yoktur; bilinen sonuç yeniden okunur.
  Süreç çökmesi sonrası kalıcı replay günlüğü bu aşamada varmış gibi sunulmaz.
- Yerel notlar ve ayarlar model offline iken çalışır. TaskVex kapanıp yeniden
  açıldığında kayıt korunur; model/ses kaynakları sahipsiz kalmaz.

Son kabul: UI'dan hem yazılı hem sesli bir istek aynı core aracını çalıştırır;
iptal, kota/ağ hatası ve yeniden bağlantı doğru görünür. Hedefli testler ve tam
regresyon geçer; gerçek hesap/cihaz kabulü ayrıca kaydedilir. Bu koşullar
tamamlanınca Aşama 5 kapatılıp diğer L0 işlemlerine geçilir.

### Bu aşamanın dışında

Google Drive/Calendar/Mail, Telegram/Discord, yeni uygulama pluginleri, GUI
resolver, skill/rutin yürütücüsü, wake word, kamera/ekran paylaşımı ve model
eğitimi bu planın parçası değildir. Mevcut UI yeniden tasarlanmaz; gerekmeyen
framework, servis katmanı veya bütün gelecek klasörleri önceden oluşturulmaz.

Plan 21 Ekim 2026'da resmi [function calling](https://ai.google.dev/gemini-api/docs/function-calling),
[Live API](https://ai.google.dev/gemini-api/docs/live-api) ve
[oturum yönetimi](https://ai.google.dev/gemini-api/docs/live-api/session-management)
belgeleriyle karşılaştırıldı. Bunlar sağlayıcının yeteneklerini anlatır;
yukarıdaki sıra ve kabul ölçütleri TaskVex için seçtiğimiz uygulama planıdır.

## İlk dilimin kullanımı

`v1/app/session/model_tools.py` içindeki `ModelTools`, çalışan core'u ve güvenilir
host'un seçtiği principal/session_id/allowed_tools değerlerini alır. UI veya
model payload'ı kullanıcı/yetki seçmez. `allowed_tools` zorunlu, açık bir tuple'dır;
host tüm araçları kendiliğinden açmaz. Gerçek yürütme mevcut policy'den geçer.

```python
from app.bootstrap import create_core
from app.session.model_tools import ModelTools

with create_core() as core:
    tools = ModelTools(core, principal="local-user", session_id="host-session-1",
                       allowed_tools=("apps.catalog",))
    declarations = tools.declarations()
    task = tools.submit({"id": "provider-call-1", "name": "apps.catalog", "arguments": {}})
    response = tools.result(task.task_id, timeout=3)
```

Bu örnek yalnız yerel kataloğu okur; metni anlayan bir model bağlamaz. Bildirim
alanları name/description/parameters'tır; SDK biçimine çevirme sonraki adımın
sorumluluğudur. Gönderilen çağrıda yalnız id/name/arguments kabul edilir;
fazla kimlik/yetki alanı, bilinmeyen veya görünmeyen araç, şema dışı parametre ve
JSON dışı değer yürütülmeden reddedilir. Hatalar çağrı verisini mesajına koymaz.

ModelTools çağrı kimliği kendi yanıtında id olarak aynen korunur. session_id/call_id ikilisinin
JSON kodlamasının SHA-256 özeti manager request_id'sini oluşturur; source her zaman
güvenilir masaüstü kanalıdır. Aynı core ve mantıksal oturumda yeniden gönderim aynı
görevi döndürür; farklı içerik request_conflict verir. Yeniden bağlantı aynı
session_id'yi korumalıdır. Yeni bir oturumda yeni çağrı yapılabilir; farklı çağrı
kimliklerinin aynı kullanıcı niyetini anlattığını sistem kendiliğinden çıkarmaz.

Yanıt id/name/task_id/status/result içerir. result ortak ToolResult biçimidir;
verified, error ve evidence kaybolmaz. Ham request/principal ayrıca gönderilmez.
Bekleme timeout'u güncel görev durumunu verir, iptal veya FAILED uydurmaz.
Sağlayıcı yalnız terminal durumda function response göndermelidir. `cancel`
çalışan görevde yalnız cancel_requested olabilir; gerçek bitiş ayrıca izlenir.
UNKNOWN korunur ve manager yeni işleri durdurur; otomatik ikinci deneme yoktur.

Bir adaptör yalnız kendisinin submit ile ilişkilendirdiği görevleri okuyabilir
ve iptal edebilir. Core ve adaptör güvenilir süreç içi Python nesneleridir;
bu sınır bir Python sandbox'ı değildir. Core'un kapatılması host'a aittir.
Çağrı kaydı yalnız bellektedir; uygulama çökmesi/yeniden açılması arasında kalıcı
replay garantisi henüz yoktur.

## Test kanıtı ve sınır

`v1` içinde `python -m pytest -q tests/test_model_tools.py -W error`: **22 geçti**.
Gerçek geçici not dosyasına ekleme/listeleme, yeni adaptörde aynı oturumla replay,
değişmiş içerik çakışması, oturumlar arası kimlik ayrımı, yanlış payload ve şema,
policy reddi, bağımsız katalog kopyası, başka görevi okuma/iptal reddi, çalışan
işte bekleme/iptal ve UNKNOWN sonrası engelleme denendi. Ağ/sağlayıcı taklit
başarısı üretilmedi; sağlayıcı bu testlere dahil değildir.

5.1 diliminin tarihsel pytest sonucu **419 geçti**; model_tools.py ve manager.py için venv Python'u
kullanan Pyright sonucu **0 hata, 0 uyarı**. Mevcut UI/native bridge değiştirilmedi.
Canlı Gemini, metin yorumlama, API anahtarı, kota, ağ kesilmesi, Live ve fiziksel
ses cihazları bu turda denenmedi.

### 5.2 uygulaması ve doğrulama

`v1/app/session/gemini.py` gerçek google-genai 2.32.0 istemcisini kullanır.
Generate Content üzerinden tek metin isteğinin araç turları yürütülür. Bu,
SDK'nin desteklediği metin uç noktasıdır; yeni Interactions oturumu veya ikinci
sunucu tarafı konuşma deposu kurulmadı. Host gerektiğinde model adını seçebilir;
varsayılan gemini-3.8-flash yalnız metin içindir, Live modeli değildir.

Araçlar FunctionDeclaration.parameters_json_schema ile kuralları atılmadan
iletilir. SDK'nin belgelenmiş ad sınırı nokta içerdiğinden notes.add gibi core
adları değiştirilmez. Otomatik function calling kapalıdır. En çok 5 model/araç turu
ve 8 araç çağrısı yapılır; ilk turdaki retry/fallback ile en çok 7 HTTP isteği
olabilir. İstek başına HTTP timeout 30 saniyedir; SDK retry attempts=1 kalır,
tekrar politikasını adaptör yönetir. Tüm turun tek bir kesin süre sınırı yoktur.

Modelin özgün Content ve düşünme imzası sonraki turda korunur. Core'a giden çağrı
kimliği her bağımsız kullanıcı run'ının turn_id'siyle kapsamlandırılır; aynı
turun replay'i korunur, ayrı kullanıcı turu eski göreve karışmaz. Sağlayıcıya
dönen id özgün id'dir. Sağlayıcı id
vermezse bir defalık yerel parça kimliği kullanılır. Farklı kimlikle üretilmiş
aynı anlamdaki iki çağrının eşdeğerliğini sistem kendiliğinden çıkarmaz.
Paralel bildirilen çağrılar core'a sırayla verilir; bütün tur atomik değildir.
Önceki araç tamamlanıp sonraki ağ/çağrı hata verirse önceki sonuç tool_results
içinde korunur. UNKNOWN/cancelled veya halen çalışan görevde tur durur. Yeni
run çağrısı yeni kullanıcı isteğidir; hata sonrası otomatik run tekrarı yapılmaz.

İlk SDK diliminde `tests/test_gemini.py`: **41 test geçti**. SDK'nin gerçek HTTP serileştirmesi
MockTransport ile denendi: metin/araç turları, düşünme imzası ve çağrı kimliği,
tekrarlı/değişmiş çağrı, şema reddi, API 401/403/404/429/503, timeout/bağlantı
hatası, commit sonrası bağlantı kaybı, boş/kısmi yanıt, pending/iptal/belirsizlik,
tur/araç sınırları ve kabul betiğinin test verisi izolasyonu.

İlk koşumda Python 3.14'ün typing._UnionGenericAlias uyarısı SDK import'unu
uyarı=hata koşulunda durdurdu. Yalnız google.genai.types kaynaklı bu tam uyarı
pytest ayarında hariç tutuldu; diğer uyarılar hâlâ hatadır. İlk iki wire testi
ayrıca JSON alanının yalnız camelCase olacağını varsaydığı için başarısızdı;
SDK'nin ürettiği snake_case/camelCase gösterimi kabul edilerek test düzeltildi,
şemanın additionalProperties=false kuralının korunduğu ayrıca doğrulandı.
SDK dosyaları değiştirilmedi. Güncel komut `python -m pytest -q`'dur;
ek `-W error` bu dar pytest istisnasını da geçersiz kılar.

İlk SDK diliminde tam süit **460 geçti**; pip check temiz. SDK adaptörü, kabul betiği ve
test dosyasının Pyright denetimi: **0 hata, 0 uyarı**. UI/native bridge değişmedi.

Canlı kabul betiği `tests/gemini_smoke.py` hazır. Çalıştırılan
[gerçek deneme raporu](stage5-gemini-live.json) missing_api_key / live_request_made=false
döndürdü; bu bir canlı başarı kanıtı değildir. Anahtar olmadan dış istek yapılmadı.
Bu ilk denemede canlı katalog ve sentetik not kabulü açıktı; aşağıdaki güncel
canlı kabul bölümü daha sonra alınan başarılı sonuçları kaydeder.

Yerel anahtar hazır olan PowerShell oturumunda, v1 içinde:

```powershell
.\.venv\Scripts\python.exe tests/gemini_smoke.py --report ../docs/stage5-gemini-catalog-live.json
.\.venv\Scripts\python.exe tests/gemini_smoke.py --notes --report ../docs/stage5-gemini-notes-live.json
```

Anahtar `GEMINI_API_KEY` süreç ortamından alınır; komuta açık metin olarak
eklenmez ve sohbete gönderilmez. İkinci komut yalnız geçici dizine sentetik
TaskVex API acceptance notunu yazar, gerçek kullanıcı notlarına erişmez. Bunlar
isteyerek yapılan ücret/kota tüketebilen ağ testleridir; pytest'e dahil değildir.

SDK/API dayanakları: [resmi Python SDK](https://googleapis.github.io/python-genai/),
[sabitlenen sürüm](https://pypi.org/project/google-genai/2.32.0/),
[metin modeli](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash).
Kullanıcının bütün proje boyunca katılacağı denemeler [USER_ACCEPTANCE.md](USER_ACCEPTANCE.md)
içindedir; kod/sınır testleri kullanıcıya devredilmez.

### İlk kullanıcı canlı isteği — hata teşhisi

Kullanıcının [katalog raporu](stage5-gemini-catalog-live.json) live_request_made=true,
acceptance_verified=false, provider_error ve boş tool_results içeriyor. Araç
yürütülmeden API hatası dönmüş; eski rapor HTTP kodunu sakladığı için bunun
anahtar, istek/model veya servis kaynaklı olduğu henüz belirlenemez.

Hata raporu artık http_status ve yalnız izinli standart provider_status /
provider_reason alanlarını korur. HTTP 400 invalid_request, 402 billing_required
olarak ayrılır. Ham message/details/metadata, istek URL'si veya anahtar rapora
aktarılmaz. Bilinen ve bilinmeyen nedenler ile bozuk details dahil altı ek test
geçti. Yeni canlı deneme yapılmadı; katalog testinin güncellenmiş kodla tekrar
çalışması gerekiyor. Otomatik retry veya model/anahtar değişimi uygulanmadı.

PowerShell'de Read-Host ile yeni bir SecureString okumak daha önce atanmış
GEMINI_API_KEY ortamını değiştirmez. İkinci girişte farklı anahtar seçildiyse
NetworkCredential üzerinden ortam değişkenine yeniden atanmalıdır. Anahtar
sohbete veya komut argümanına yazılmaz.

### 5.3 ilk dilim — Windows kimlik deposu ve UI anahtar kaydı

`app/storage/credentials.py` standart ctypes ile CredReadW/CredWriteW kullanır;
yeni bağımlılık yoktur. Güvenilir host'un veri profilinden hesaplanan kayıt adı
TASKVEX_HOME profillerini ayırır. Kayıt CRED_TYPE_GENERIC ve aynı kullanıcı/makine
kalıcılığıyla tutulur. JSON/plaintext fallback yoktur. Anahtar boşluk/kontrol
karakteri olmadan 1–2048 ASCII karakter olmalıdır; bu biçim denetimi anahtarın
Google tarafından geçerli kabul edildiği anlamına gelmez.

UI Settings → Connection alanında Save API key veya Enter kullanılır. Blur
artık kayıt başlatmaz. Anahtar input'u beklemeden temizlenir; başarı ancak
Windows'a yazıp geri okuma doğrulamasından sonra bildirilir. API/model isteği
yapılmaz; model offline kalır. Key status yalnız kayıt varlığını gösterir.
Geç gelen eski status sorgusu yeni save sonucunu ezemez. Onay timeout'unda
otomatik retry yoktur; kontroller yeniden başlatılana kadar kilitli kalır.

`apikey` ve `query_apikey` mevcut tek native event köprüsündedir; yanıtlar sır
içermez. credentials.js ayrı UI sorumluluğunu taşır; settings.js'teki eski
otomatik API key gönderimi kaldırıldı. `apikey` browser fallback taşımasına
gitmez; native gözlemci `[REDACTED]` alır. Anahtar olayındaki native hata ve
gözlemci reddi ham içerikle loglanmaz. Generic save/yedek kapsamı değişmedi.

GeminiText açık api_key parametresini, yoksa GEMINI_API_KEY ortamını, ortam
tanımlı değilse profilin Windows kaydını kullanır. Kabul betiği anahtarı geçici
test profiline geçmeden önce host profilinden alır; gerçek notlara erişmez.
Ortam anahtarı açık bir override'dır: UI'da yeni kaydı test ederken eski ortam
değerini kaldırmak gerekir. Kimlik deposu okuma hatası eksik anahtar gibi gizlenmez;
CLI credential_unavailable ile ayrılır.

Çalıştırma ve anahtar kaydı (v1 dizininde):

```powershell
Remove-Item Env:GEMINI_API_KEY -ErrorAction SilentlyContinue
.\.venv\Scripts\python.exe -m app.main
```

UI'da Settings → Connection → API Key → Save API key; sonra uygulamayı normal
kapatıp aynı PowerShell'den yalnız katalog testini çalıştır:

```powershell
.\.venv\Scripts\python.exe tests/gemini_smoke.py --report ../docs/stage5-gemini-catalog-live.json
```

Kullanıcının API anahtarı bu geliştirme turunda okunmadı/kaydedilmedi. Testlerde
yalnız geçici profile ait sentetik anahtar kullanıldı ve o kimlik kaydı temizlendi.
Yeni yerel testler hata, bozuk kayıt, profil ayrımı, yazma sonrası doğrulama ve
bridge'den sır dönmemesi durumlarını kapsar. Güncel tam süit **481 geçti**.
Gerçek Windows/WebView2 kanıtı [native rapordadır](stage5-credentials-native.json).
Bu dilim sonunda metin UI, stop_task, Live, fiziksel ses ve canlı 503 kabulü açıktı.

Windows dayanakları: [CredWriteW](https://learn.microsoft.com/en-us/windows/win32/api/wincred/nf-wincred-credwritew),
[CredReadW](https://learn.microsoft.com/en-us/windows/win32/api/wincred/nf-wincred-credreadw),
[CREDENTIALW](https://learn.microsoft.com/en-us/windows/win32/api/wincred/ns-wincred-credentialw).
Bu depo aynı Windows kullanıcısıyla çalışan diğer güvenilir süreçlere karşı
bir sandbox değildir; UI'a credential read/ham anahtar API'si açılmadı.

### Güncel canlı kabul ve güvenli retry/fallback — 21 Ekim 2026

Kullanıcının gerçek hesapla çalıştırdığı iki rapor diskte kontrol edildi:
[katalog](stage5-gemini-flash-lite-live.json) ve
[sentetik not](stage5-gemini-flash-lite-notes-live.json).
İkisinde de model `gemini-3.5-flash-lite`, live_request_made=true ve
acceptance_verified=true. Not ekleme sonucu ile ardından okunan notun kimliği
aynıdır; gerçek kullanıcı notlarına erişilmedi. 3.8 Flash'ın önceki 503 raporu
korundu; bu sonuç hatanın kesin kaynağını kanıtlamaz.

Bu tek adımda metin adaptörünün retry/fallback politikası uygulandı:

- Her bağımsız run varsayılan `gemini-3.8-flash` ile başlar. İlk istekte 408,
  500/502/503/504 veya taşıma/timeout hatası gelirse yaklaşık 1 saniye bekleyip
  ana model tekrar denenir; yine geçici hata olursa yaklaşık 2 saniye sonra
  `gemini-3.5-flash-lite` bir kez denenir. Beklemelere 0–250 ms rastgele pay
  eklenir. SDK'nin kendi retry'ı kapalıdır; iç içe sınırsız deneme yoktur.
- Host `--model` ile açıkça başka model seçerse yalnız o modelde iki deneme
  yapılır. Hatalı anahtar, izin, istek, model bulunamaması ve 429 kota hataları
  tekrar edilmez veya başka modele yönlendirilmez. 429'un günlük kota mı anlık
  limit mi olduğu henüz ayrıştırılmadığından güvenli biçimde durulur.
- Herhangi bir araç sonucu alındıktan sonra retry/fallback yapılmaz. Başarı,
  başarısızlık, iptal, belirsizlik ve pending kayıtları korunur. Bu konservatif
  sınır okuma araçları için de geçerlidir; yeni bir modelle tur başlatılıp daha
  önce gerçekleşmiş eylem ikinci kez önerilip yürütülmez.
- Alternatif model cevap verdiyse aynı turun araç sonuçları yine o modele
  gönderilir; modeller arasında düşünme imzası aktarılmaz. Sonraki yeni run ana
  modelden başlar. Bu politika farklı kimlikle üretilmiş aynı anlamdaki iki araç
  çağrısını veya süreç çökmesi sonrası tekrarları kendiliğinden çözmez.
- Sonuçlarda `model` gerçek son denenen/kullanılan modeli, `model_attempts`
  sırayla bütün HTTP denemelerinin model adlarını taşır. Kabul betiğinde
  `requested_model` CLI seçimini ayrıca korur; fallback bilgisinin üzerini yazmaz.
  UI göstergesi sonraki metin bağlantısı adımında bağlanacak; bugün UI'da yoktur.

Doğrulama: SDK/HTTP sınırında **53 test**, tam süitte **493 test** geçti.
İlk tekrarın başarısı, alternatif modele geçiş, deneme sınırı, yeni run'da ana
modele dönüş, açık model seçimi, geçişten sonra tek not kaydı, araç sonrası
503/timeout'ta sıfır retry ve CLI raporundaki gerçek model kontrol edildi.
HTTP taşıması bu yeni hata senaryolarında taklittir; gerçek SDK ve core kullanılır.
Yeni politikanın canlı 503 → retry → fallback zinciri henüz denenmedi; önceki
iki başarılı kullanıcı raporu bu yeni zincirin testi olarak sunulmuyor.

Bu tur metin UI, stop_task veya ses adımına geçilmedi. Sıradaki tek adım mevcut
sohbet alanını native metin hattına bağlamaktır.

Politika dayanağı: Google'ın [retry rehberi](https://ai.google.dev/gemini-api/docs/troubleshooting)
ve [alternatif model yetenekleri](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite).

### 5.3 ikinci dilim — mevcut UI'dan tek metin turu

`app/session/text_chat.py` tek aktif isteği ve SDK istemcisinin ömrünü yönetir.
NativeBridge text olayını kısa doğrulamadan sonra genel köprü kilidi dışında
çalıştırır; böylece model beklerken ayarlar/pencere kontrolleri kilit arkasında
kalmaz. Ayrı worker, framework veya ikinci görev yürütücüsü kurulmadı.

Sabit host kataloğu apps.catalog, system.status, notes.add/list'tir. İlk backend
not aktarımı bitmeden model metni kabul edilmez. UI, metin turunda not/import
mutasyonlarını durdurur; normal bitişte notes_init ile gerçek listeyi yeniden
okur. Model yanıtı hata verse bile önceki not kaydı görünür olur. Genel save veya
setter ile ikinci not yazımı yapılmaz. Hata halinde metin girdisi korunur.

Başarıda kullanılan model ve istek sayısı, hatada güvenli hata mesajı görünür.
MODEL OFFLINE açılışı korunur. Yerel model kataloğu ağ testi değildir; model
seçim değişikliği de online sayılmaz. Başarılı metin isteği son erişim kanıtıdır,
sürekli bağlantı garantisi değildir. Fallback, seçili ana modeli kalıcı değiştirmez.

Henüz her mesaj bağımsızdır; önceki sohbet metinleri ve profil talimatları
aktarılmaz. Model not listesi istediğinde gerçek notlar sağlayıcıya gönderilir;
bu yüzden aşağıdaki manuel deneme ayrı boş profille yapılır. Silme, düzenleme,
uygulama açma, stop_task, reconnect/disconnect ve ses bu dilimde bağlanmadı.
Aktif metin turunda Stop kapalıdır; Shutdown/Restart/X isteği tur bitene kadar
reddedilir. 240 saniyede kesin yanıt yoksa UI unknown kilidine geçer ve otomatik
yeniden göndermez. Pending/belirsiz araç sonucu da aynı kilidi gerektirir.

Doğrulama: **503 pytest testi geçti**; Gemini/metin dosyasında **61 test** var.
Üretim metin/bridge/main ile Gemini ve native smoke testlerinin Pyright kontrolü
0 hata/0 uyarı. [Native rapor](stage5-text-native.json) gerçek hidden WebView2'de
**10 senaryonun** geçtiğini kaydeder. Yeni chat senaryosunda SDK ve core gerçek,
HTTP yanıtları kontrollüdür: iki 503 → alternatif → tek not → güvenli metin,
çift gönderim/kapanış reddi, ayar köprüsünün yanıt vermesi, hatada girdi/not
koruması, model seçiminin online olmaması ve unknown kilidi doğrulandı.
İlk native koşumda eski `keep-model` test tercihi yeni gerçek kataloğa uymadı;
fixture desteklenen modelle güncellendi. İkinci koşumda chat senaryosu kendi
kontrollerinden sonra eski reopen bölümüne düştü; testin faz sonu düzeltilerek
tüm 10 senaryo tekrar çalıştırılıp geçirildi. Başarısız koşumlar canlı API
hatası veya gizlenmiş ürün başarısı olarak sunulmadı.

#### Kullanıcının iki canlı denemesi

Yeni bir PowerShell'de v1 klasörüne geç ve anahtarı güvenli prompt ile tanımla:

```powershell
cd C:\Users\batue\OneDrive\Desktop\TaskVex\v1
$vexSecret = Read-Host "Gemini API key" -AsSecureString
$env:GEMINI_API_KEY = [System.Net.NetworkCredential]::new("", $vexSecret).Password
Remove-Variable vexSecret
```

Önceki retry/fallback adımı için varsayılan modeli açıkça değiştirmeden dene:

```powershell
.\.venv\Scripts\python.exe tests/gemini_smoke.py --report ../docs/stage5-retry-live.json
```

`ok`/`acceptance_verified` true beklenir; model_attempts gerçek denemeleri,
model yanıtlayan modeli gösterir. Ana model doğrudan yanıt verirse fallback'in
çağrılmaması doğrudur. 503'ü zorlamak için gerçek hesaba yük bindirilmez;
deterministik hata/geçiş kontrolleri pytest/native testlerinde zaten yapılır.

Bu UI adımı için ayrı geçici profil kullan; gerçek notlarını testte göndermesin:

```powershell
$env:TASKVEX_HOME = Join-Path $env:TEMP ("TaskVex-ui-test-" + [guid]::NewGuid().ToString("N"))
.\.venv\Scripts\python.exe -m app.main
```

Varsa Notes → Use backend notes onayını tamamla. Sırayla “Merhaba, tek cümleyle
yanıtla”, “Notlarıma Vex UI test notu ekle”, “Notlarımı listele” gönder. Tek not,
doğru yanıt, yanıtlayan model, tekrar açıldığında aynı test profilinde kalıcılık
beklenir. Aynı profili korumak için yeniden başlatırken yeni GUID üretme; yalnız
app.main komutunu tekrar çalıştır. 3.8 erişilemiyorsa Settings → Connection'dan
3.5 Flash-Lite seçilebilir; bu seçim erişim kanıtı değildir. Ağ kesik denemesinde
hata veya unknown beklenir; gerçekleşmiş işlem otomatik tekrarlanmamalı.

Testler bitince bu yeni terminalin ortamını temizle:

```powershell
Remove-Item Env:GEMINI_API_KEY
Remove-Item Env:TASKVEX_HOME
```

Canlı UI kabulü ve yeni politikanın gerçek 503 zinciri henüz denenmedi. Sıradaki
tek iş stop_task/iptal ve görev durumunu bu metin turuna bağlamaktır. O iş hazır
olunca aktif istekte Stop, ardından yeni istek ve tamamlanmış notun korunması
denenecek; bugün bu işlevin çalıştığı iddia edilmez.

### Güncel kullanıcı yönlendirmesi — Live kataloğu ve mesaj engeli

Bu bölüm önceki sabit UI metin kataloğu ve sonraki adım sırasını günceller.
Kullanıcı masaüstünde yalnız API'den gelen Live modellerini görmek, yazılı mesajı
sesli dinlemek istedi; bir turda tamamlanamayacak işleri bölmeye izin verdi.
Bu tur gönderim engeli ve katalog tamamlandı. Live WebSocket/ses çıkışı bugün
yok; tarayıcı TTS'si veya sahte ses yanıtı ile tamamlanmış gibi gösterilmedi.
Sıradaki öncelik metin girdisi → gerçek Live ses yanıtı ve güvenli kaynak ömrü;
Stop/iptal ve bağlantı yaşam döngüsü de açık kalır. Mikrofon girdisi ayrı dilimdir.

Gönderim engelinin somut nedeni, ilk not aktarımının normal sohbetin ön koşulu
olmasıydı. Artık aktarım beklerken model yalnız apps.catalog/system.status görür;
onaydan sonra not araçları eklenir. UI ve backend birlikte doğrulanır. Devam
eden/belirsiz not yazımı korunur; aktarım otomatik onaylanmaz. Browser-only açılış
gerçek Python köprüsüne sahip değilse sohbet altında native açılış komutu görünür.

`app/session/catalog.py` resmi SDK models.list üzerinden sayfaları okur ve yalnız
supported_actions içinde bidiGenerateContent olan modelleri verir. Ad eşlemesi,
sabit model listesi veya hatada eski listeden seçim yoktur. En çok beş sayfa ve
10 saniye/sayfa; kısmi liste başarı sayılmaz. API anahtarı değişirken eski hesaba
ait katalog kabul edilmemesi için kısa bridge kilidi ile sorgu başlatılır;
sorgu sürerken anahtar kaydı ve ikinci sorgu reddedilir. API hatası aktif
seçenekleri geçersiz kılar. Liste boşsa UI bunu açık gösterir.

UI Settings → Connection → Load Live models yalnız açık kullanıcı tıklamasıyla
listeyi yükler. Başlangıç veya anahtar kaydı otomatik API listelemez. Live model
seçimi gelecek ses oturumunun tercihidir; bugün REST metin modeline geçirilmez.
Mevcut 3.8 Flash → retry → 3.5 Flash-Lite metin yolu botlar için korunur.
Live seçilince veya katalog yüklenince online/ses hazır sinyali üretilmez.

Kanıt: **513 pytest testi geçti**, Gemini/metin/katalog test dosyasında **69 test**;
üretim katalog/metin/bridge ile Gemini/native testlerinin Pyright sonucu 0 hata,
0 uyarı. [10 senaryolu native rapor](stage5-live-catalog-native.json) gerçek hidden
WebView2 ve kontrollü HTTP kullanır. Chat senaryosu ayrı boş profil açar; not
aktarımı onaysızken genel yanıt alır, araç kapsamını denetler, sonra açık not
onayı ile tek kaydı ve fallback'i dener. API'den daha önce kodda bulunmayan
future-live modeli gelir; metin modeli listeden elenir. Live tercihi REST modelini
değiştirmez. Son katalog kilidi/metin düzeltmesi sonrası chat senaryosu ayrıca
yeniden geçti. Gerçek hesap listesi ve insanın kendi UI oturumundaki sonuç henüz
doğrulanmadı; kaynak kodu/test başarısı kullanıcının her olası gönderim hatasının
kesin teşhisi olarak sunulmaz.

Resmi dayanak: [models.list ve supported_actions](https://ai.google.dev/api/models),
[Live WebSocket API](https://ai.google.dev/api).

Kendi hesabınla yeni PowerShell oturumunda native açılış:

```powershell
cd C:\Users\batue\OneDrive\Desktop\TaskVex\v1
$vexSecret = Read-Host "Gemini API key" -AsSecureString
$env:GEMINI_API_KEY = [System.Net.NetworkCredential]::new("", $vexSecret).Password
Remove-Variable vexSecret
.\.venv\Scripts\python.exe -m app.main
```

Önce yalnız “Merhaba” gönder; not aktarımı onayı genel sohbet için gerekmez.
Sonra Settings → Connection → Load Live models ile listeyi dene. API'de uygun
yeteneğin bulunmaması boş sonuçtur, tahmini modeller eklenmez. Not testi
istenirse ilk not aktarımını açıkça onayla; hassas not listesi yerine önceki
ayrı test profili kullanılabilir. Bu tur sesli yanıt beklenmemeli.


### Not ekleme sonrası API hatası ve yaklaşık 30 saniye bekleme — teşhis

Kullanıcı ekleme/listeleme/kalıcılık/silme kabulünü geçti; yeniden eklemede
“Gemini request failed; tools were not retried” gördü. Bu metin APIError HTTP
hata yolundandır; not dosyasının bozulduğu kanıtı değildir. Ekran görüntüsünde
HTTP durumu olmadığı için 400/429/503 gibi nedenlerden hangisi olduğu bilinmiyor.
Gecikme yalnız 3.5 modele bağlanamaz: önceki ana model denemeleri ve araç sonrası
ikinci model isteği süreye dahildir. HTTP timeout 30 saniyedir; bu kasıtlı sabit
bekleme veya bütün turun 30 saniyede biteceği garantisi değildir.

Bu tur güvenli teşhis görünür yapıldı. Sonuç JSON'unda elapsed_ms tüm turu,
model_attempt_details içindeki elapsed_ms yalnız o HTTP denemesini ölçer.
Her denemede model, sınırlı outcome ve varsa sayısal HTTP kodu vardır; anahtar,
not içeriği, istek URL'si veya ham sağlayıcı hatası eklenmez. UI kota/izin/istek/
servis/ağ hatasını açıkça ayırır; HTTP kodu, uygulama kodu, son model ve süreyi
sohbet altında, denemeleri Engine Log'da gösterir. Girdi korunur, notlar yeniden
okunur; ağ hatası tamamlanmış araç işlemini otomatik tekrarlatmaz.

Kontrol: **515 pytest testi geçti**, Gemini/metin/katalog dosyasında **71 test**.
Ekle → son notu sil → aynı sağlayıcı çağrı kimliğiyle yeni bağımsız turda tekrar
not ekle testinde tek doğru yeni kayıt oluştu. Kontrollü saat ile HTTP/total süre
ayrımı ve ham hata redaksiyonu denendi. Gerçek hidden WebView2 chat senaryosunda
HTTP 400 + invalid_request ve güvenli deneme logunun gösterimi doğrulandı;
[rapor](stage5-text-diagnostic-native.json). HTTP yanıtları taklittir.
Üretim adaptörü ve değişen Gemini/native testleri Pyright: 0 hata, 0 uyarı.

Yeni gerçek hesap denemesi bu tur yapılmadı. Kullanıcı uygulamayı kapatıp aynı
PowerShell'den `.\.venv\Scripts\python.exe -m app.main` ile açabilir. Yeniden
hata alırsa sohbet altındaki yeni HTTP/kod/model/süre satırı ve ilgili Model
request log satırları teşhis için yeterlidir; anahtar paylaşılmaz. Tekrar
isteği göndermeden önce not paneli kontrol edilir. Gerçek gecikme kaynağı ve
kullanıcının gördüğü HTTP hatasının nedeni hâlâ açık; timeout/retry politikası
bu kanıt olmadan değiştirilmedi. Live metin → ses bağlantısı da henüz yoktur.


### Geçici Live gecikme testi — kullanıcı isteği

Kullanıcı yalnız gecikme karşılaştırması için Live bağlantısı istedi; ses
oynatımı bu dilimde kapsam dışıdır. `app/session/live_probe.py` her UI mesajında
tek yeni WebSocket açar. Sohbet altındaki Live latency test kutusu varsayılan
olarak açıktır; işaretliyken `live_text` seçili API Live modeline yönlenir.
Katalog yüklenmemişse açık ret verir; kullanıcı Settings → Connection → Load
Live models ile listeyi yükler ve konuşma modeli seçer. Yeni model adları
sabitlenmedi. Normal REST metin ve retry/fallback kodu kutu kapalıyken korunur.

Live yapılandırması AUDIO + output_audio_transcription kullanır. Resmi 3.8
Live belgesinde TEXT-only çıkış desteklenmediği için üretilen ses oynatılmadan,
biriktirilmeden atılır; yazısı gösterilir. Ses üretimi kota tüketebilir. Araçlar
bildirilmez; notları ekleme/listeleme dahil hiçbir araç çalışmaz. Bu yüzden
normal not kabulünün yerine geçmez. Otomatik model değişimi/retry yoktur.

Ölçümler: connect_ms, first_event_ms, first_text_ms, elapsed_ms. Hepsi istemcinin
soğuk başlangıcından itibaren ölçülür; ilk metin ve toplam süre UI'da görünür.
Her mesaj bağımsız yeni bağlantı olduğundan kalıcı bağlantının tekrar kullanım
gecikmesi ölçülmez. UI LAST LIVE TEST etiketi kapatılmış son başarılı istektir,
canlı sürekli bağlantı değildir. Ses entegrasyonu veya tam Live aşaması bitmiş
sayılmaz. Turn_complete ile IDLE farkı korunur; kesinti, boş/kısmi yanıt, araç
çağrısı, 2000 olay/32000 karakter sınırı ve 25 saniye timeout açık hataya döner.
SDK/socket kaynakları normal/hatalı/timeout çıkışlarında temizlenir. HTTP ve
WebSocket kodları farklı etiketlenir; serbest hata nedeni/anahtar sızdırılmaz.

Doğrulama: **526 pytest testi geçti**; bunların **10'u** yeni Live protokol ve
kaynak yaşam döngüsü testidir. Gerçek SDK ile yalnız WebSocket taşıması taklit
edildi; kurulum ve realtime_input JSON'u, çoklu ses parçaları + transkript,
IDLE bekleme, boş/araçlı/kesilmiş/uzun yanıt, timeout, hata redaksiyonu ve ortak
meşgul/kapanış kilidi denendi. Üretim Live/metin/bridge ve Live/native testleri
Pyright: 0 hata/0 uyarı. Gerçek hidden WebView2 chat senaryosu da geçti:
[Live probe native raporu](stage5-live-probe-native.json). Seçili Live modele
istek, UI transkripti/süreleri, not dosyasının değişmemesi ve REST fallback
olmaması doğrulandı. Dış API/WebSocket bu testlerde sentetiktir.

Host süreç ortamı ve Windows profilinde kullanılabilir anahtar olmadığı güvenli
boolean kontrolüyle görüldü; gerçek anahtar okunup loglanmadı. Gerçek hesapla
Live isteği veya gecikme iyileşmesi henüz doğrulanmadı. Kullanıcının açık
PowerShell'inde anahtar varsa uygulamayı kapatıp v1 içinde yeniden açması yeterli:

```powershell
.\.venv\Scripts\python.exe -m app.main
```

Settings → Connection → Load Live models → varsa gemini-3.8-live seç. Sohbet
altında Live latency test açık kalsın. “Merhaba, yalnızca hazır de.” gönder.
Yanıt altındaki first text ve toplam saniyeyi karşılaştırma için kaydet.
İstenirse aynı kısa metni kutu kapalıyken REST ile bir kez dene; orada retry
zinciri, ilk Live denemesinde ise yeni bağlantı maliyeti ölçüme dahildir.
Not testi için kutuyu kapat. Uzun cevaplar ses üretim süresini de etkiler;
“Live daha hızlıdır” sonucu hesapta gerçek ölçüm olmadan çıkarılmaz.

Resmi dayanak: [Gemini 3.8 Live response modalities](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-live),
[Live yetenekleri ve text input](https://ai.google.dev/gemini-api/docs/live-api/capabilities).


### Kalıcı Live sahibi — bu tur tamamlanan tek adım

Kullanıcı geçici Live testinde 4.5/5.2 saniye bildirdi; bunlar önceki REST
isteklerinden daha kısa görüldü. Bu gözlem tüm görevlerde sabit hızlanma
kanıtı değildir. Şimdiki dilim her mesajda bağlantı açma maliyetini kaldırır.
`app/session/live_session.py` içinde LiveConnection SDK/socket kaynaklarının,
PersistentLive ise tek I/O thread/event loop'un sahibidir. Thread ilk Live
mesajında açılır; TaskManager'ın mevcut worker'ı değişmez. Aynı model ve anahtar
kimliğinde takip eden mesaj aynı socket'e gider; sağlayıcı konuşma bağlamını
bu açık oturumda koruyabilir. Yerel sohbet kaydı veya ses dosyası oluşturulmaz.

Başarılı turdan sonra kaynak açık kalır. Model/anahtar değişimi ve açık
Disconnect idle kaynağı kapatır; socket/SDK/loop/thread kapanışı doğrulanır.
Aktif turda bu işlemler reddedilir, tamamlanmış iptal gibi gösterilmez. GUI
beklenmedik biçimde biterse finally temizliği aktif ağ işini de iptal eder.
Hata, timeout, GoAway veya yarım yanıt sonrası kaynak atılır; başarısız mesaj
otomatik replay veya REST fallback almaz. Yeni mesaj yeni oturum açabilir;
önceki bağlamın devam ettiği iddia edilmez. Uzak idle kopma sonraki I/O'da
anlaşılabilir; proaktif idle sağlık bildirimi, otomatik resumption/compression
bu dilimde yoktur. Sağlayıcının oturum/bağlantı ömür sınırları hâlâ geçerlidir.

Mevcut Live tur ayrıştırıcısı ortak kullanılır; ikinci araç/konuşma yürütücüsü
kopyalanmadı. Doğrudan bağımsız probe hâlâ soğuk oturumunu kapatır. Masaüstü
Live yolunda mode=live_session_test, session_reused=false/true gelir. UI ilk
yanıtta new session, ikincide session reused gösterir; first text ve toplam
süre her mesajın başlangıcına göredir. Ses oynatma ve Live araçları kapalıdır.

Doğrulama: **531 pytest testi geçti**, Live dosyasında **15 test** var. Aynı
socket'te iki tur, Disconnect sonrası yeni oturum, model/anahtar değişimi,
hata sonrası aynı isteğin tekrar yürütülmemesi, sonraki yeni mesajın yeni socket
alması, GoAway reddi ve thread kapanışı gerçek SDK + sentetik socket ile denendi.
Üretim Live/metin/bridge/main ve Live/native testleri Pyright: 0 hata, 0 uyarı.
Gerçek hidden WebView2'de iki mesajın aynı socket'i kullandığı, UI reused
etiketi, not dosyasının korunması ve Disconnect'in I/O thread'ini kapatması
[tekil native raporda](stage5-persistent-live-native.json) doğrulandı.
Gerçek hesabın kalıcı oturum gecikmesi henüz ölçülmedi.

Tam native regresyonun ilk denemesinde chat süreci WebView2 açılışında 60 saniye
timeout aldı; traceback'te Live I/O işi henüz başlamamıştı. Bu geçiş başarılı
sayılmadı. Aynı chat senaryosu yeni boş profilde tek başına tekrar geçti;
açılış timeout'unun kesin nedeni belirlenmedi. Tam native paket ikinci koşumda
10/10 geçti; [tam native rapor](stage5-persistent-live-full-native.json). İlk
başarısız açılış koşumu bu başarıdan ayrı olarak yukarıda korunmuştur.

### Live araç bağlantısı — 22 Ekim 2026

Önceki araçsız testin kapsamı bu dilimde genişletildi. Live `apps.catalog`,
`system.status` ve ilk aktarımı onaylanmışsa `notes.add/list` araçlarını görür.
SDK handler'ı doğrudan çalıştırmaz: ModelTools aynı registry/policy/TaskManager
hattını kullanır. Provider çağrı kimliği zorunludur, kimliksiz çağrı reddedilir.
Kaynak/kullanıcı host'tan gelir; model argümanları yetkiyi değiştiremez.

Standart Live modellerinde kısa yerel araçlar BLOCKING bildirilir; extended-thinking
modellerinde NON_BLOCKING gerekir ve bitiş için IDLE beklenir. Araç beklemesi
event loop'u bloklamaz; gerçek core sonucu FunctionResponse olarak gönderilir.
Tur 25 saniye, her araç beklemesi 5 saniye, en çok 8 çağrıyla sınırlıdır.
Bekleyen/belirsiz görev başarı sayılmaz; UI yeniden açılışa kadar kilitlenir.
Sunucu iptali tamamlanmış notu geri almaz. Ağ hatası sonrası doğrulanmış sonuçlar
korunur; mesaj otomatik tekrar gönderilmez. UI not çağrısı sonrası backend'den
okuyarak paneli yeniler, setter üzerinden ikinci mutasyon üretmez.

Aynı açık socket ModelTools nesnesini korur: aynı çağrı kimliği/argüman aynı
göreve gider; değiştirilmiş argüman çakışma verir. Model/anahtar/araç kapsamı
değişince kaynak yenilenir. Yeni socket veya yeni çağrı kimliği aynı doğal dil
niyetini otomatik birleştirmez; süreçler arası replay günlüğü yoktur. Çoklu araç
çağrısı tek atomik işlem değildir; önceki tamamlanmış yazı sonrakinin hatasıyla
geri alınmaz. Normal Stop, ses oynatma ve mikrofon bu adımda eklenmedi.

Doğrulama: **546 pytest testi geçti**; yeni `test_live_tools.py` içindeki 15
test gerçek SDK/core/JSON kaydı ve sentetik socket kullanır. Ekle/listele,
çağrı tekrarı/çakışması, yetki/parametre reddi, aktarım onayı, kayıt sonrası ağ
hatası, pending, sunucu iptali, extended-thinking IDLE ve kapsam değişimi
denendi. Değişen üretim dosyaları ve yeni test Pyright: 0 hata/uyarı.
Gerçek API hesabıyla bu yeni Live araç dilimi henüz denenmedi.

Native doğrulamanın ilk tam koşumu ve ayrı chat koşumu kapanışta zaman aşımı
verdi. Ayrı koşumun raporu araç kaydının/UI yenilemesinin geçtiğini, testin
socket kapandıktan hemen sonra thread'in None olmasını beklediğini gösterdi.
Socket kapanışı tüm host temizliğinin bitişi değildir. Test, thread kapanışını
da bekleyecek şekilde düzeltildi. Önceki koşumlar başarılı sayılmadı; yalnız
WinForms app.Run traceback'i açılışın takıldığını kanıtlamaz.

Düzeltme sonrası tam native paket **10/10 geçti**:
[WebView2 raporu](stage5-live-tools-native.json). Gerçek UI → Live SDK → gerçek
core → JSON kayıt → not paneli yenilemesi, aynı çağrının ikinci kayıt üretmemesi,
oturum yeniden kullanımı ve Disconnect sonrası thread kapanışı doğrulandı.
Yalnız HTTP/WebSocket taşıması sentetiktir; bu gerçek hesap/ses kabulü değildir.

Resmî sözleşme: [Live API araçları](https://ai.google.dev/gemini-api/docs/live-api/tools).

### Live Stop — 22 Ekim 2026

Native UI her Live mesajını `{text,request_id}` zarfıyla gönderir. Eski string
girişi korunur, fakat kimliksiz çağrı UI Stop hedefi değildir. Stop düğmesi
Live isteği sırasında açıktır; `stop_task:{request_id}` yalnız eşleşen aktif
tura sinyal verir. Yanıt `{ok:true,accepted:true,completed:false,request_id}`
iptalin kabulüdür; UI bu yanıtla idle olmaz. Eski kimlik, boş/bozuk payload ve
aktif olmayan tur reddedilir. Aynı Stop'un tekrarı temizliği yeniden kesmez.

Modelin ağ beklemesi kendi event loop'unda kesilir. Yalnız bu turda kabul edilen
araçlara mevcut TaskManager üzerinden iptal iletilir; kısa bir gerçek sonuç
beklemesi yapılır. Tamamlanmış/sonradan doğrulanmış başarı korunur; not geri
alınmaz. Sonuç hâlâ pending/unknown ise `stopped:false,unknown:true` gelir ve
UI kilitli kalır. Gerçek bitişte asıl live_text yanıtı `stopped:true,completed:true`
taşır; UI notları backend'den yeniler, kontrolleri açar. Bu yanıtın ok:false
olması normaldir: model yanıtı başarıyla tamamlanmış gibi gösterilmez.

Stop SDK/socket kaynağını bırakır; I/O thread'i sonraki mesaj için idle kalır.
Yeni mesaj yeni socket/bağlam açar; otomatik mesaj replay veya resumption yoktur.
Disconnect idle thread'i de kapatır. REST'in senkron HTTP isteği bu dilimde
iptal edilmiş gibi gösterilmez; onun turunda Stop kapalıdır. Ses eklenmedi.

Doğrulama: 560 pytest testi; değişen Python dosyaları ve Stop testinde Pyright
0 hata/uyarı; app.js sözdizimi kontrolü temiz. Stop testleri erken sinyal,
eski kimlik, bekleyen ağ, kayıt sonrası Stop, çalışan aracın gerçek bitişi,
geç iptale rağmen doğrulanmış başarı, yinelenen Stop ve belirsiz sonucu kapsar.
Gerçek hidden WebView2 paketi 10/10 geçti: düğmeyle durdurma, notları koruma
ve sonraki mesajda yeni oturum [raporda](stage5-live-stop-native.json) doğrulandı.
SDK/core/DOM gerçek, HTTP/WebSocket taşıması sentetiktir; gerçek hesap kabulü
kullanıcıdadır. Önceki Live araçları kullanıcı tarafından çalışıyor diye onaylandı.

### REST Stop — 22 Ekim 2026

REST metin hattı Live ile aynı UI istek zarfını ve Stop düğmesini kullanır.
TextChat yalnız o turun GeminiText istemcisini kimlikle tutar; Stop modelin
uzun süre tutulan meşgul kilidini beklemez. GeminiText'te Event iptal sinyali,
kısa kapı kilidi ise yeni HTTP/araç kabulü ile Stop'un sırasını belirler.
Yeni dispatcher/worker, bağımlılık veya başka aşama eklenmedi.

Devam eden senkron HTTP zorla kesilmez. Kabul yanıtı completed:false ve
waiting_for=http_response ise UI mevcut isteğin bitişini beklediğini gösterir.
HTTP yanıtı/hatası geldikten sonra araç, retry veya fallback başlamaz. Retry
beklemesi Event ile uyanır. HTTP'nin 30 saniyelik timeout ayarı korunur; bu
transport'un her koşulda tam o sürede döneceği garantisi değildir. UI bitişe
kadar giriş/notları kilitler. İşbirlikçi iptale rağmen tamamlanmış araç sonucu
başarı olarak korunur; veri geri alınmış sayılmaz. Pending/unknown görev veya
iptal sonucu okuma hatası UI'ı kilitli bırakır. Geç Stop yanıtı yeni mesajı
etkilemez; her REST turu ayrı istemci ve sinyal alır. Live Stop korunmuştur.

Doğrulama: **578 pytest testi geçti**; 17 yeni REST Stop senaryosu ve bir
köprü zarfı testi dahil. SDK gerçek, HTTP sentetik; ana modelin ilk/ikinci
denemesi ve alternatif model beklemesinde Stop, geç tool call, 503/timeout,
backoff, kayıt sonrası iptal, çalışan araç, belirsizlik ve sonraki tur
kimliği denendi. Üretim gemini/text_chat/webview_bridge ve yeni test_rest_stop
Pyright: 0 hata/uyarı. app.js sözdizimi temiz. Ek genişletilmiş Pyright kontrolü
test_native_bridge.py'nin mevcut FakeWindow sahte nesnelerinde 7 tip hatası
verdi (Window yerine test nesnesi ataması ve calls/on_top erişimi); bunlar yeni
testte değildir, bu görevde bastırılmadı veya kapsam dışı yeniden düzenlenmedi.
Tüm bu dosyanın çalışma zamanı testleri geçti. Gerçek hesap kullanılmadı.

Tam native paket **10/10 geçti**: [REST Stop WebView2 raporu](stage5-rest-stop-native.json).
REST HTTP kapısı açıkken Stop düğmesi, kabul/bitiş ayrımı, kontrollerin kilidi,
geç gelen notes.add çağrısının reddi ve not dosyasının değişmemesi doğrulandı.
Aynı paket Live Stop, yeni Live oturumu ve Disconnect kabulünü de geçti.
Gerçek SDK/core/DOM ile sentetik HTTP/WebSocket kullanıldı; ücretli API yoktu.

Takip düzeltmesi: yukarıdaki 7 FakeWindow tip hatası giderildi. Testler pencere
nesnesini pytest monkeypatch ile açıkça enjekte eder; sahte pencereye ait
calls/on_top kontrolleri yerel FakeWindow referansından yapılır. Üretimin
Window tipi gevşetilmedi, type-ignore/Any ile hata gizlenmedi. Köprü süiti
72/72 geçti; test_native_bridge ve REST Stop üretim/yeni test dosyalarının
birleşik Pyright kontrolü 0 hata/0 uyarı verdi. Üretim davranışı değişmedi;
native paket bu yalnız test düzenlemesi için tekrar çalıştırılmadı.

Gerçek hesap kabulü: kullanıcı API limitine ulaşıldığını bildirdi. Bu nedenle
yeni REST Stop'un gerçek API ile manuel kabulü **test edilemedi — API limiti**
olarak açık kalır. Bu, geçmişte geçen Live/metin kontrollerini geçersiz kılmaz;
sentetik HTTP/WebSocket testleri gerçek hesap kabulü yerine sayılmaz.

### Live GoAway ve session resumption — 22 Ekim 2026

Önceki “resumption yok” bölümleri tarihsel kapsamdır. Mevcut tek LiveConnection
sahibine setup onayı, idle kontrol okuması ve sınırlı resume eklendi; ikinci
alıcı thread/worker veya araç yürütücüsü kurulmadı. Resmî sözleşme ve kurulu
google-genai 2.32.0 alanları kontrol edildi. SessionResumptionConfig ile
sağlayıcıdan checkpoint istenir. SetupComplete olmadan kullanıcı metni gitmez.

GoAway ön bildirimdir: aktif tur tekrar gönderilmez, mevcut deadline içinde
tamamlanabilir. Koparsa doğrulanmış araç sonuçları korunur ve aktif turun eski
checkpoint'i kullanılmaz. Yeni metinden önce idle socket en çok 50 ms ve 32
kontrol mesajıyla yoklanır. Yalnız bitmiş turdan sonra idle'da görülen
resumable=true/dolu new_handle kabul edilir. Üretim/araç sırasında gelen
checkpoint'ler güvenli dönüş noktası sayılmaz; false/boş güncelleme eskisini siler.

Idle kopma/GoAway sonrası geçerli checkpoint ile resume aynı ModelTools'u,
çağrı görev eşlemesini ve host logical_session_id'sini korur. Aynı çağrı ID'si
aynı göreve gider; yeniden not yazmaz. Kullanıcı metni otomatik replay edilmez.
Resume setup reddi 400/404/1008 veya eksik onay ise metin gönderilmeden yalnız
bir fresh setup denenebilir. Yetki, kota, 503 veya ağ hatasında tekrar yoktur.
Checkpoint yoksa/eskimişse yeni bağlam açıldığı UI'da belirtilir. Başarılı
resume session resumed, aynı socket session reused, yeni bağlam new session
etiketi ve gerektiğinde context_reset_reason ile görünür.

Handle yalnız bellektedir, log/UI/yedeğe yazılmaz; yerel işlenişinden 2 saat
sonra kullanılmaz. Stop, Disconnect, model/anahtar/araç kapsamı değişimi ve
başarısız aktif tur handle ve eski mantıksal kapsamı temizler. Idle'daki
beklenmedik araç/içerik yürütülmez, temiz bağlama geçilir. Arka planda sürekli
idle dinleyici yoktur; kopma sonraki preflight'ta anlaşılır. Henüz gönderilmemiş
kontrol mesajını 50 ms içinde alamazsak devam noktası bulunamayabilir; bu
durumda bağlamı korunmuş gibi göstermeyiz. Kesintisiz aktif tur kurtarma,
süreçler arası resumption, context compression ve ses bu dilimde yoktur.

Doğrulama: **601 pytest testi geçti**; 23 lifecycle testi dahil. Gerçek SDK/core
ve sentetik socket ile GoAway sonrası tamamlanma, idle kopma, başarılı resume,
çağrı replay/tek yazı, setup reddi ve sınırı, auth/kota/503, false/boş/eskimiş
checkpoint, aktif tur hatası, Stop ve kapsam değişimi, beklenmedik idle araç,
eksik setup ve kontrol mesajı sınırı denendi. Değişen üretim kodu ve resume/
bridge testlerinin Pyright kontrolü 0 hata/uyarı; app.js sözdizimi temiz.
Gerçek hesap kabulü **test edilemedi — API limiti**; ücretli API kullanılmadı.

Tam native paket **10/10 geçti**: [Live resumption WebView2 raporu](stage5-live-resumption-native.json).
Gerçek WebView2/SDK/core ve sentetik HTTP/WebSocket ile GoAway sonrası resume
setup, UI session resumed etiketi, aynı mantıksal oturum, token'ın UI'a
sızmaması ve sonra Stop → yeni oturum → Disconnect doğrulandı. Aynı pakette
REST Stop, tek not yazımı, ayar/import/export ve başlangıç kurtarma geçti.

Kaynaklar: [Live session management](https://ai.google.dev/gemini-api/docs/live-api/session-management),
[resumption ve setup sözleşmesi](https://ai.google.dev/api/live#sessionresumptionupdate).

#### Not düzenleme/silmenin yeri

Core ve native UI CRUD Aşama 3'te tamamlandı. Model tarafındaki `notes.update`
ve `notes.delete` için önceki plan yalnız ilk dar kapsamı belirtiyor, açılacak
alt adımı açıkça adlandırmıyordu. Bu iş Aşama 5'te, iptal hattından sonra ve
ses bağlamadan önce ayrı bir dilimdir; yeni bir Aşama 6 entegrasyonu değildir.
Hedef: gerçek liste/ID ile seçim, aynı metinli notlarda belirsizliği açıklatma,
yanlış kaydı değiştirmeme, gerçek sonuç ve UI yenileme. Bu Stop diliminde
modelin araç listesi genişletilmedi.

#### Aşama 5 kapanış koşulları — 22 Ekim 2026

Her prompt yalnız bir adımı uygular. Live bağlantı yaşam döngüsünün bu dilimi
tamamlandı; model not düzenleme/silme de ayrı dilimde tamamlandı. Bu liste kalan
işlerin kapanış kontrolüdür; maddeler doğrulanmadan tamamlandı işaretlenmez.

- [x] GoAway/resumption ve kopmada belirsiz sonuç yönetiminin bu dilimi kontrollü
  testlerle tamam; aynı çağrının resume yüzünden ikinci yazı üretmediği doğrulandı.
  Gerçek hesap kabulü API limiti nedeniyle aşağıdaki maddede açık kalır.
- [x] Modelden notes.update/delete gerçek ID ile çalışıyor; belirsiz veya aynı
  metinli hedefte açıklama isteniyor, UI yenilemesi ikinci mutasyon üretmiyor.
- [x] Yazılı mesaja Live ses yanıtı, sınırlı PCM kuyruğu ve mute kontrollü
  testlerle hazır; Stop bekleyen sesi temizliyor. Temel gerçek ses çıkışı
  kullanıcı tarafından onaylandı; tüm cihaz/yarış senaryoları sayılmaz.
- [ ] Mikrofon/cihaz/VAD ve konuşarak araya girme tamam; gerçek mikrofon ve
  hoparlör/kulaklıkla kullanıcı kabulü yapılmış, denenmeyen cihazlar belirtilmiş.
- [ ] REST/Live Stop, gecikmiş yanıt, offline yerel kullanım, kopma,
  shutdown/restart ve daha uzun süreli kullanım senaryoları son entegre sürümde
  doğrulanmış; açık hatalar ve sınırlamalar kaydedilmiş.
- [ ] Eksik gerçek hesap testleri yapılmış: not CRUD ve genel Stop akışı
  kullanıcı tarafından onaylandı; gerçek GoAway/resumption, özel HTTP bekleme
  senaryoları ve entegre ses kabulü ayrıca açık; yeni not seçimi de kullanıcı
  tarafından onaylandı. Sentetik
  başarı bu kullanıcı/sağlayıcı kabulünün yerine geçmez.
- [ ] Değişen yolların regresyon/native/tip kontrolleri geçmiş; gerçek hesap,
  native motor ve sentetik taşıma sonuçları ayrı raporlanmış.
- [ ] Entegrasyon sonrası hedefli UI görüntü temizliği ve bakım yapılmış;
  belirgin tekrarlar giderilmiş, sırf satır sayısı için mekanik dosya bölünmemiş.
- [ ] Belgelerin güncel durum bölümleri kodla tutarlı; tarihsel sonuçlar açıkça
  ayrılmış. Yeniden başlatma sonrası çağrı tekrarı riski değerlendirilmiş,
  kalıcı çağrı günlüğü gerekiyorsa kapsamı ve zamanı kararlaştırılmış.

Kapanış kapsamı: bütün sistem için koşulsuz “exactly once” garantisi verilmez;
aynı doğal dil isteği kullanıcı tarafından bilerek tekrar edilebilir. Kalıcı
çağrı günlüğü gereksinimi, ileride dış mesaj gönderme veya dosya değiştirme gibi
işlemler açılmadan ele alınmalıdır. Çok süreçli yazma, çok kullanıcı/bot kimlik
doğrulaması, genel plugin sandbox'ı ve canlı telemetri mevcut Aşama 5'i kapatmak
için topluca uygulanmaz; ilgili sonraki aşamalarda ihtiyaçlarıyla planlanır.
Gerçek hesap/donanım kabulü açıkken Aşama 5 tamamen tamamlandı sayılmaz.

#### Aşama 5'in kalan sırası

Not hedefi iyileştirmesi kullanıcı tarafından onaylandı. PCM çıkışı yerel
testlerle hazır; önce kısa ses kullanıcı kabulü. Sonra kalan sıra şöyledir;
her prompt bir adım uygular:

1. Başlat/bitir mikrofon kullanıcı kabulü tamam; cihaz seçimi kontrollü testlerle
   hazır. Önce çoklu cihaz kullanıcı kontrolü, sonra sürekli akış/VAD ve
   konuşarak araya girme ayrı adımlarla tamamlanır.
2. Gerçek hesap ve mikrofon/hoparlörle son kabul: yerel offline kullanım,
   shutdown/restart, kopma, iptal, tek araç yürütme ve regresyon.

Mimari plana uygundur: sağlayıcı detayı adaptörde, yürütme ortak core'da,
Live kaynağının sahibi tek bileşende kalır. Kullanıcının gecikme isteğiyle
Live'ın ilk araçsız dilimi, 5.3'teki Stop tamamlanmadan öne alındı; bu iş
bitmiş veya Aşama 5 kapanmış sayılmaz. Live araç bağlantısı artık hazır;
REST/Live Stop, güvenli idle resumption ve modelden not CRUD hazırdır.
Live ses çıkışının kullanıcı kabulünden sonra sıradaki dilim mikrofon/cihaz/
VAD'dir. Bu görevde mikrofon eklenmedi; Aşama 5 kapanışı işaretlenmedi.

Manuel kontrol: app.main ile yeniden aç, API Live listesini yükle ve aynı
modelde bir kısa mesaj gönder. Aktarım bekliyorsa Use backend notes ile onayla.
“Notlarıma Live deneme 001 ekle” ve “Notlarımı listele” gönder; panelde tek kayıt
ve doğru liste bekle. “Desteklenen uygulamaları listele” / “Sistem bilgilerini
göster” ile diğer iki aracı dene. Logdaki araç durumu succeeded/verified olmalı.
Onay araç kapsamını değiştirirse yeni oturum normaldir; sonraki tur reused olur.
Sonra Disconnect'e bas, yeni mesajda new session bekle. Hata sonrası not kaydı
oluşmuşsa aynı ekleme komutunu körlemesine tekrar gönderme.
Resmi kaynak: [Live session management](https://ai.google.dev/gemini-api/docs/live-api/session-management).


#### Model not CRUD diliminin doğrulaması — 22 Ekim 2026

**639 pytest testi geçti**; yeni hedefli dosya 38 test içerir. Gerçek SDK/core,
sentetik HTTP/socket ve geçici not dosyaları kullanıldı. İki taşıma için metin
düzenleme, done işareti, silme, gerçek ID/diğer kaydı koruma, liste olmadan
ret, belirsiz/yanlış/aynı metinli hedef, ID ile ayrıştırma, aynı çağrının tek
mutasyonu, Stop sonrası gerçek sonucu koruma, bağlantı hatası sonrası doğrulanmış
sonuç ve readback unknown denendi. Ayrıca Live resume sonrası silme replay'i,
eski/başarısız listenin seçim izni vermemesi ve registry doğrulaması denendi.

Üretim adaptörleri, yeni test dosyası ve native bridge testlerinin Pyright
kontrolü 0 hata/uyarı verdi. Tam hidden WebView2 paketi **10/10 geçti**:
[Model not CRUD native raporu](stage5-model-notes-native.json). Gerçek gönder
düğmesinden REST ve Live done/edit/delete sonuçları panelde ve dosyada
kontrol edildi; aynı ID korundu, save/note_add/note_done/note_del echo sayısı
sıfırdı. Önceki Stop, GoAway/resume, kaynak temizliği ve kayıt testleri de geçti.
Ücretli API, üretim hesabı veya gerçek kullanıcı notu kullanılmadı.
Gerçek hesap kabulü **test edilemedi — API limiti**.


#### Not oluşturulma zamanı — doğrulama ve açık sınır

22 Ekim 2026: 654 pytest testi geçti; bunun 15’i yeni tarih davranışını kapsar.
Yeni tarih, replay, düzenleme/tamamlama ve yeniden açılışta korunur; tarihsiz/null
eski notlar okunur ve yalnız okuma dosyayı değiştirmez. Aktarım/restore bilinen
tarihi korur; geçersiz takvim tarihi/biçim ve normal mutasyonda sahte tarih
reddedilir. `node ui/tests/note-timestamps.mjs` tarih koruma ve bozuk importun
aday üretmeden reddini doğruladı. Değişen JS dosyalarının sözdizimi temiz;
notes.py, yeni Python testleri ve ModelTools için Pyright 0 hata/uyarı verdi.

İlk native koşumu yeni eklenen ikinci export diyaloğunu beklerken persistence
fazında başarısız oldu; o anda backend’de tarihli not doğru kaydedilmişti.
Tarihli yedek kontrolü mevcut tek export akışına birleştirilerek test düzeltildi.
Yeniden çalıştırılan tam hidden WebView2 paketi 10/10 geçti:
[Not zamanları native raporu](stage5-note-timestamps-native.json).
Gerçek UI/core/dosya ile UI cache, done/edit sonrası sabit tarih ve kimlik,
export/import tarih koruma, bozuk tarihli importta dosyayı koruma doğrulandı.
Önceki REST/Live Stop, resume, tek yazı ve kaynak temizliği kontrolleri de geçti.

Bu yeni metadata diliminde gerçek kullanıcı dosyası veya ücretli API
kullanılmadı. Kullanıcının önceki CRUD/Stop kabulü kaydedildi; yeni timestamp
alanının gerçek modelle manuel kabulü henüz yapılmadı. “Son not” ve kısmi
metin seçimi açık; eşit/bilinmeyen tarihte tahminle işlem yapılmayacak.


#### Not hedefi seçimi — doğrulama ve manuel kabul sınırı

22 Ekim 2026: 707 pytest testi geçti. Yeni `test_note_selection.py` 53 test
kapsar: REST/Live literal kısmi metin ve son not ile silme/edit/done, Türkçe
büyük İ ve tipografik tırnak, İngilizce açık kalıplar, liste sırasından bağımsız
tarih seçimi, eski/eksik/null/eşit tarih, yanlış ID ve sıfır/çoklu adayın yazı
üretmemesi, bileşik/olumsuz/tırnaksız/boş filtre reddi, açık ID ile ayrıştırma,
literal 'son notu' adlı not ve resume sonrası replay/yeniden liste zorunluluğu.
Önceki Stop, unknown, kayıt ve model regresyonları da tam süitte geçti.

ModelTools, yeni test ve REST/Live sağlayıcı adaptörlerinin Pyright kontrolü
0 hata/uyarı verdi. Tam hidden WebView2 paketi 10/10 geçti:
[Not hedefi seçimi native raporu](stage5-note-selection-native.json).
Gerçek gönder düğmesi, SDK/core ve sentetik HTTP/WebSocket ile her iki hatta
partial seçimle done, latest seçimle edit/delete denendi. Panel/metadata doğru
yenilendi, ikinci save/not mutasyonu yoktu. Stop/resume/kaynak temizliği de geçti.
CRUD, araç şeması ve UI görünümü değiştirilmedi; bağımlılık eklenmedi.

Gerçek kullanıcı notu veya ücretli API kullanılmadı. Kullanıcının önceki CRUD
ve genel Stop kabulü geçerlidir; yeni hedef seçiminin gerçek model kabulü
henüz bekleniyor. Bu dar çözümleyici TR/EN'deki tırnaklı pozitif içerik filtresi
ve açık latest ifadelerini tanır; serbest tarif, tüm diller, birleşik koşullar
ve anlamsal/negatif filtreler desteklenmez. 'Son' kayıtlı oluşturulma zamanına
göredir; saat sapması veya kullanıcı yedeğindeki tarihin doğruluğu kanıtlanmaz.
Tarihsiz eski notlar varken otomatik latest işlemi yerine ID istenir. Bu bir
hata veya eski veriye tarih ekleme gerekçesi değildir.

Bu prompt yalnız not hedefi adımını tamamladı. Önce kısa kullanıcı kabulü;
sonra Live ses çıkışı, mikrofon/VAD ve kapanış listesindeki gerçek hesap/
donanım, uzun kullanım, Stop/kopma/resumption, hedefli UI bakım/debloat ve
belge/çağrı tekrarı sınırı incelemeleri ayrı adımlarda tamamlanacak. Aşama 5
henüz tamamen kapanmadı, Aşama 6'ya geçilmedi.


#### Live PCM çıkışı — test kanıtı ve sınırlar

22 Ekim 2026: 716 pytest testi geçti. Yeni test_live_audio.py içindeki 9 test
PCM/transkriptin birlikte işlenmesini, format/paket/tur boyutu sınırını, başarısız
ses alıcısında doğrulanmış notun korunmasını, istek ID kapsamını ve Stop sırasında
ses tesliminin tekrar edilmemesini doğruladı. Yeni testin ilk koşumunda eski
fixture'ın üç baytlık (16-bit hizasız) sesi ve aşırı uzun otomatik parametrik
test adı sorun oldu; geçerli PCM ve kısa test kimlikleriyle düzeltildi. Seçili
üretim adaptörleri, yeni test ve native bridge testleri için Pyright 0 hata/uyarı.

`node ui/tests/live-audio.mjs` PCM little-endian dönüşümü, gerçek bitişi bekleme,
eski ID reddi, Stop/Mute, süre/parça kuyruk sınırı, bozuk PCM, autoplay reddi ve
pagehide temizliğini cihaz açmadan doğruladı. Tarih JS kontrolü ve değişen JS
sözdizimi kontrolleri de geçti. İlk native koşumu eklediğim Mute bağlantısının
mikrofon düğmesine yanlış yerleşmesini yakaladı; bağlantı doğru Mute düğmesine
taşındı, mikrofon davranışı korundu. Düzeltilmiş ve son bağlantı değişimi
kontrolü eklenmiş tam native paket 10/10 geçti:
[Live ses native raporu](stage5-live-audio-native.json).

Gerçek WebView2/SDK/core ile sessiz sentetik PCM render edildi: geçerli paket
onayı, metin/araç sonucunun korunması, ses bitene kadar UI kilidi, Mute/Unmute,
model bittikten sonra kalan sesi Stop, geç paket reddi, anahtar değişimi olayı
sırasında eski yanıtın online yazmaması, Disconnect/IO kapanışı doğrulandı.
Önceki kayıt/restore, REST/Live Stop ve GoAway/resumption kontrolleri korundu.

Mevcut gerçek API kaydının varlığı yalnız boolean olarak kontrol edildi;
anahtar gösterilmedi, yeniden yazılmadı ve hiçbir ücretli API çağrısında
kullanılmadı. Native kimlik deposu testleri yalnız ayrı geçici profil ve sentetik
anahtar kullandı; ayrı süreçten yeniden okuma da geçti. Kayıtlı anahtar aynı
Windows kullanıcısı/makine ve veri profilinde yeniden açılışta kalır.

Fiziksel hoparlör/kulaklıktan gerçek modelin duyulması henüz denenmedi;
kullanıcının kısa kabulü açık. Duyulabilirlik, hoparlör seviyesi, seçili dOut
cihazı, gerçek mikrofon/VAD/barging-in ve uzun süreli bütünleşik kabul bu
adımın kanıtı değildir. Taşan/bozuk seste otomatik model tekrarı veya ikinci
araç yürütmesi yoktur; metin ve bilinen sonuç korunup ses uyarısı verilir.
Varsayılan 25 saniye Live model turu ve sınırlı ses kuyruğu devam eder.

Kaynaklar: [Live API ses biçimi ve interruption](https://ai.google.dev/gemini-api/docs/live-api/capabilities),
[resmî SDK başlangıcı](https://ai.google.dev/gemini-api/docs/live-api/get-started-sdk).
