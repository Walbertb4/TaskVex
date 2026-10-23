# UI/backend sözleşmesi

Uyku kabul düzeltmesi: colors.sleeping, diğer reactor durumları gibi saklanan
bir renktir; SLEEPING durumu IDLE'dan ayrıdır. Açık Wake, yerel uyandırıcı
hatasından kalan micBlocked engelini temizleyip cihaz/izin kontrolünü yeniden
yapar; Microphone Off ve belirsiz sonuç kilidi korunur. Host'un dar uyku
eşleştirmesi uykuya dal ve yalnız tam uyku cümlesi önünde Rex/Max hitaplarını
da kabul eder; bunlar genel komut/wake algısı için bulanık eşleşme değildir.

## Güncel: tek seferlik uyku ve yerel wake PCM

pWake, profilde 1–64 karakter/1–3 ASCII İngilizce sözcüktür; default Vex.
Kaydedilir, modele system instruction olarak verilmez; yerel motor sonraki
uykuda sözlük/fonem desteğini ayrıca doğrular. Uyku tercihi RAM'dedir.

- sleep_start(): hazır/idle host Live'ı kapatır, RAM sohbeti korur, yerel
  WakeWord oluşturur; {ok,completed,request_id,wake_word} döner. Başarısız
  motorda sleeping:true kalır, otomatik Live fallback olmaz.
- wake_feed({request_id,sequence,data}): tek base64 3200-byte PCM16LE/16kHz
  paketi. Sıra 0'dan artar. {ok,completed,detected,start_sequence} döner;
  start_sequence hit başlangıcının 100 ms paket indeksidir. Eski ID, yanlış
  sıra/encoding/taşma reddedilir; bozuk kaynak bırakılır, uyku korunur.
  detected:true yalnız bekleyen hit'tir; host sleeping=True kalır. UI kendi
  ön tamponunu doğrulamadan uyanma tamamlanmış sayılmaz.
- wake_close(request_id): yalnız eşleşen yerel kaynağı bırakır, uykuyu kaldırmaz.
- wake(): idle/hazır host manuel olarak uyandırır ve yerel kaynağı bırakır.
- wake({request_id}): yalnız mevcut, algılanmış hit'in UI kabulüdür. Tampon
  doğrulamasından sonra gönderilir; completed:true gelmeden Live istenmez.
  Eski/kapatılmış/onaysız ID reddedilir. wake_close pending hit'i iptal eder
  ve host'u uykuda tutar. Mic Off tercihine bu kabul müdahale etmez.

sleep_start kabulünden sonra Live audio start/clip host'ta sleeping koduyla
reddedilir. UI tarafından kabul edilmiş hit veya açık yazılı Live isteği bu engeli kaldırır.
UI da ayrı sleep kapısı tutar; sıradan enerji adayı uyandırma sayılmaz. Wake
butonu/typed istek açık kullanıcı eylemidir. New Chat uyku durumunu temizler.
Uyurken Mic Off kaynakları bırakır; On yeniden yerel dinleme açar.

Typed tam uyku ifadesi local_sleep/sleep_requested:true raporuyla modellenmeden
karşılanır. Sesli ifadede yalnız finished transkript veya gerçek tur sonundaki
tam ifade kabul edilir; yarım soru komut olmaz. Yan etkili araç başlamış tur
uykuya çevrilmez. UI gerçek bitişten sonra sleep_requested'ı uygular.
Bu yaşam döngüsü kontrolüdür; ikinci tool worker/CRUD/registry hattı eklenmedi.

Mevcut liveMic kaynağı waitForWake ile yalnız yerel paket yollar. 1 s bekleyen
IPC ve 3 s ön tampon sınırı vardır. Hit başlangıcından önceki PCM bırakılır;
sonrası aynı kaynaktan mevcut LiveInput hattına geçer. Yetersiz/eski tampon
kırpılarak komut çalıştırmaz; capture engeli gösterilir. Geç callback'ler
micRevision/session ID ile korunur. 60 s model stream yenileme sınırında
wake kaçabilir; fiziksel kabul açıktır. Otomatik tekrar uyuma/süre ayarı yoktur.

R0 düzeltmesi: timestamp doğrudan global sıra değildir. Hit'te en çok 3 s
yerel pencere aynı KWS ile başlangıcı bilinen stream'de doğrulanır; iç reset
olamayacağı token süresi/sessizlik marjından kontrol edilir. Yapay ileri-bakış
sessizliği yalnız yerel doğrulamadır, PCM çıkışına eklenmez. Doğrulanmış global
sınır yine UI'ın 3 s ön tamponunda bulunmalıdır; eski ses kırpılarak gönderilmez.

## Güncel küçük düzeltme — gösterim

Yeni host event/payload yok. paintMic on sınıfı artık native/Live modeli hazır,
On seçilmiş ve kaynak/unknown engeli olmayan kullanıcı tercihini gösterir;
fiziksel track'in Stop sırasında kısa devri ışığı söndürmez. Tooltip kaynak
hazırlığı ile gerçek capture'ı ayırır. Off/Disconnect/izin/cihaz/unknown engeli
söndürür. Fiziksel kayıt/Stop/yeniden dinleme protokolü değişmedi.

setConnectionStatus('idle', text) dahili UI durumudur: nötr pill net idle,
isConnected=false, reconnect timer temizlenir; açık socket iddia edilmez.
Eşleşen güncel bağlantıda completed:true ve unknown olmayan Stop veya
live_interrupted bu duruma geçebilir. Genel hatalar kırmızı off kalır.
Normal interrupted logda transport hatası olmaz; unknown, eski kimlik ve
başarısız iptal gizlenmez. idle rozet tıklaması reconnect başlatmaz.

## Güncel: geçici hafıza ve new_chat

Geçici sohbet RAM kaydı TextChat'e aittir; UI localStorage/settings/yedek içine
aktarılmaz. Live tur raporunda memory_restored:boolean, yeni socket'e sınırlı
geçmiş verisinin aktarıldığını bildirir. UI bunu "recent conversation restored"
olarak gösterebilir; tam hatırlama veya tool sonucu doğrulaması değildir.
Tarihçe yalnız fresh bağlantıda model rolünde JSON ve turn_complete:false
olarak gider; used/resumed socket'te yinelenmez. Güncel komutlar ayrı kalır.
Ham PCM/tool payload ve restore için yeni araç çalıştırma yoktur.

`new_chat` yalnız payload'sız hazır host/idle TextChat'te kabul edilir. Başarı:
`{ok:true, completed:true, memory_cleared:true}`. Etkin sohbet varsa veya
kapanış doğrulanmazsa ret verilir; meşgulken RAM silinmez. UI önce kullanıcı
onayı ister, sonra giriş/yeni sohbet kontrollerini sonuçlanana kadar kilitler.
15 s onay aşımı veya kayıp taşıma unknown olur; geç cevap yeni sohbete yazamaz.
Başarıda msgs ve stream kaydı temizlenir; notlar/ayarlar/anahtar korunur.
Unknown komut kilidini yeni sohbet düğmesi kaldıramaz. Eski PCM/transkript
alıcıları resetLiveAudio ile bırakılır. Mikrofon On tercihi yeni konuşmada
korunur; temizlik sırasında capture başlatılmaz.

RAM sınırı 12 tur/16.000 JSON karakteri, metin başına 2.000 karakterdir;
eski tur atılır, otomatik özet API isteği yoktur. Stop/Disconnect/model ve
profil değişimi yakın geçmişi korur. New Chat, uygulama kapanışı veya API
anahtarı güncellemesi temizler. Geçmişteki araç sonuçları eski veri olarak
etiketlenir; yeni notes.update/delete için güncel liste/hedef kontrolü aynıdır.
REST'e hafıza bağlanmadı. PMem alanı halen kalıcı hafıza motoru değildir.

## Güncel: REST read_reply ve Microphone Off

`text` başarılı metni/araç raporunu önce döndürür. Native UI bu metni hemen
gösterir; ardından `read_reply` event'ine yalnız `{request_id:string(1..128)}`
gönderir. Hazır host ve son başarılı REST cevabıyla eşleşme gerekir; ek alan
ve serbest metin reddedilir. Yanlış ID bekleyen cevabı tüketmez. Doğru cevap
bir kez tüketilir; yeni sohbet/Stop/Disconnect/kapanış eski metni bırakır.

Ses aynı TextChat kilidinde, aynı request_id ile mevcut audioChunk alıcısına
PCM16LE/24 kHz/mono gider. Sonuç `ok`, `completed:true`, `request_id`,
`speech_model`, `audio_bytes_forwarded`, `audio_error` taşır. Stop sonucunda
`code:stopped, stopped:true` eklenir. İlk metin/araç raporu ayrı kalır; TTS
hatası bunları başarısız veya geri alınmış saymaz. UI notları backend'den
okur; ikinci not mutasyonu/save yoktur. Mute açıkken yeni TTS çağrısı atlanır;
çalarken Mute mevcut sesi susturur. Özel hoparlör hatasında sessiz varsayılan
cihaz fallback'i yoktur. Metin/araç/TTS otomatik tekrarlanmaz.

Stop kabulü `completed:false, waiting_for:speech_response|speech_completion`
olabilir; senkron HTTP bitmeden UI kilidi açılmaz. Ses aşaması UI sınırı110 s;
geç PCM eski request_id ile yeni yanıta yazamaz. TextChat sahipliği ve bilinmeyen
sonuç kilidi korunur. TTS tek ayrı API isteğidir; araç/deklarasyon yok, store:false,
Kore, gemini-3.8-flash-lite-tts; model listesine TTS eklenmez. Limitler:
20.000 karakter, 20 s HTTP, 60 s PCM; bot/CLI read_reply çağırmadan sessizdir.

Mic Off, `live_audio_feed({request_id,sequence,data:null})` ile giriş sonunu
bildirir. PCM ve EOS seri gönderilir; EOS yalnız bir kez, setup onayından sonra
gider. Donanım hemen kapanır; Live yanıtı/transkript/output kesilmez. Stop ayrı
iptal yoludur. Off setup sırasında da Stop'a çevrilmez. Gönderilmiş ses geri
alınmaz; hiç ses ulaşmamışsa sağlayıcı yanıt vermeyebilir. REST mikrofon yolu yok.

## Güncel ara düzeltme — Microphone On/Off

Yeni event veya payload yok. microphoneEnabled UI oturum tercihi, micBlocked
kaynak engelidir. Stop/model hatası tercihi Off yapmaz. completed:true ve kesin
host bitişinden sonra, kapsam değişmediyse On tercihi yerelde yeni konuşma bekler.
Hata/Stop tanısı korunur. Eski ses/araç/model mesajı tekrar edilmez; sessizlik
API isteği oluşturmaz. Bekleyen yeni sesin eski görev sonuçlanmadan devredilmesi
ve unknown kilidi kuralları aynıdır. Off seçimi geç callback/model-ready ile açılmaz.

Mic düğmesi Microphone On/Off ve aria-pressed ile tercihi, on sınıfıyla gerçek
capture'ı gösterir. Unknown'da da Off yapılabilir; On komut kilidini aşmaz.
İzin/cihaz/giriş sınırı engelinde otomatik izin döngüsü yoktur. Disconnect veya
anahtar değişimi kaynağı bırakır; kullanıcı tercihini değiştirmez. Hazır model
bildirimi veya açık Off→On yeniden hazırlayabilir; uncertain yine engeldir.
Tercih RAM'dedir; kalıcı ayar, REST mikrofon yolu veya yeni izin eklenmedi.
Live model/mod hazır olma şartı sürer. Sessiz capture idle, konuşma listening'dir.

## Güncel: adım 5 — aktivite, kapanış ve süre tanısı

Yeni public event yok. AudioWorklet'in yerel activity:boolean mesajı yalnız
mevcut liveMic kaynağında işlenir. prepareStream(onError, deviceId, onActivity)
ve speaking getter gösterim içindir: hazır sessizlik idle, konuşma listening,
aktif turda 700 ms sessizlik thinking, çıktı PCM'i speaking'dir. Bu bildirim
sunucu turunu bitirmez, araç/komut başlatmaz. Eski kaynak callback'i yok sayılır.

PersistentLive.input feed dönüşüne failed:boolean ekler; kapalı/eski istekte
failed:false, bozuk sıra/taşmada true olur. emit normal failed:false/closed:true
reddini loglamaz, ok:false dönüşünü korur. Model çağrısında yalnız eşleşen
request_id + code:stopped + stopped:true + completed:true + unknown olmayan
sonuç normal durdurmadır; unknown veya gerçek hatalar bastırılmaz. İptal kabulü
kontrolleri açmaz. Normal feed kapanışında eski mikrofon bırakılır; çalan yanıtın
yeni mikrofonuna dokunulmaz. Yeni araç yolu/worker veya otomatik replay yoktur.

Ortak addLog son 200 kayıt/2.000 karakteri, textContent ve sır maskelemesini
uygular; schema uyarıları da boyut/adet sınırlıdır. Transkript loglanmaz.
Live backend 25 s olay sessizliği / 120 s toplam tur sınırı kullanır:
live_idle_timeout ve live_timeout kodları timeout_seconds tanısı taşır.
UI createPendingOperation.begin(deadline) Live 210 s / REST 240 s bekler.
UI süresinin dolması iptal/tamamlanma değildir; eski yanıt yeni isteği açamaz.
Önceki mikrofon, tampon, çalma ve araç boyut sınırları aynıdır.

## Güncel: adım 4 — kaydedilmiş model tercihleri

Yeni public event veya payload alanı yok. save/saved/completed doğrulaması
aynıdır; NativeBridge text/live_text/live_audio/live_audio_start başlangıcında
_load_settings ile disk profilinin bağımsız snapshot'ını alır. Profil okunamazsa
profile_unavailable/completed:true/ok:false döner; model/araç başlatılmaz.
Bu noktada completed reddedilen isteğin bittiğidir, kayıt veya model başarısı
değildir. TextChat ve adaptörlerin iç profile keyword'ü public UI alanı değildir.

model_instruction.py yalnız pLang/pIns alanlarını ortak system instruction'a
çevirir. tr/en sabit eşlemedir; eksik/desteklenmeyen eski değer tr varsayılır.
pIns ayar şemasındaki 16.000 karakter sınırında kalır. Seçilen yanıt dili ve
araç/sonuç/iptal kuralları kişisel stil talimatından üstündür. Profil metni
sonuç/teşhis/loglara eklenmez; SDK'ye gönderilir. Diğer profil alanları gönderilmez.
REST retry/fallback aynı talimatı kullanır. Live kapsamı talimatın hash'ini
kapsar; etkili değişiklik sonraki mesajda eski resume/çağrı kapsamını temizler,
context_reset_reason:scope_changed verir. Aktif yanıtın snapshot'ı değişmez;
otomatik replay veya ikinci worker yoktur. Önemsiz/bağlanmamış alan değişimi
mevcut bağlantıyı bozmaz. UI Save profile yalnız kayıt doğrulanınca kapanır.

UI Response language etiketi tanımanın otomatik kaldığını belirtir. Sağlayıcı
native audio'da language_code desteklemediği için böyle bir alan gönderilmez;
bu bir STT dili kilidi değildir. Başka profil alanlarının model entegrasyonu,
REST ses çıkışı veya yeni izin bu adımın parçası değildir.

## Güncel: adım 3 — yerel aday ve mikrofon devri

Backend event/payload değişmedi. waitForSpeech(callback, replyPlaying=false)
boşta 200 ms/0.015 veya yanıt sırasında 300 ms/0.025 taban filtreli RMS ister;
aday olmayan arka planın üç katı daha yüksekse o eşik geçerlidir. Orijinal PCM
ve 500 ms ön tampon değişmez. autoGainControl:false cihaz tercihidir.
continueListening() yalnız henüz tetiklenmemiş beklemeyi aynı track/tamponla
boşta moda alır; yakalanmış/aktif akışı sıfırlamaz. app.js hedef kimliğini ve
modu son await'ten sonra aynı senkron blokta bırakır. Ses hatası/Stop/unknown/
kapsam değişiminde bu devam uygulanmaz; kaynak kapanır. Yeni araç/yürütücü yok.
Barge-in hâlâ sıralı Stop ve gerçek bitişi bekler; bağlam sıfırlanabilir.
Bu enerji kapısı fiziksel yankı veya konuşma sınıflandırıcısı garantisi vermez.

## Güncel: istek kimlikli anlık Live transkript — adım 2

Yeni izinli bildirim: window.vex.liveTranscript({request_id,role,sequence,text});
jarvis alias aynı nesnedir. role u/j; sequence tur içinde artan pozitif tamsayı,
text birikimli snapshot'tır (delta değildir). Giriş en çok 20.000, çıkış 32.000
karakterdir. request_id güvenilir host'tan gelir; model yeni hedef seçemez.
UI boolean teslim onayı verir. Eski/finalize edilmiş istek veya tekrar/sırasız
paket reddedilir. Backend gösterim hatasını transcript_error ile raporlar,
araç veya model çağrısını tekrar etmez. Metin normal sohbet dışında dosya/loga
eklenmez; ses oynatma hattı ve araç yetkileri değişmedi.

live_transcript.js her rol için tek balon tutar; textContent ile snapshot'ı
yeniler. Geç gelen giriş aynı turun yanıtının önüne konur. Final rapor yedektir,
ikinci balon üretmez. Stop/barge-in çıkış balonunu dondurur; sonraki eski
snapshot tüketilip gösterilmez. Kesilme Interrupted, hata Incomplete, belirsizlik
Result unknown etiketidir; bunlar araç başarı durumu değildir. Scope değişimi
alıcıyı kapatır. Bilinmeyen sonuç mevcut komut kilidini açmaz.

Sağlayıcı parçaları geldikçe gösterim yapılır; yerel ses tanıma ve ses/metin
sözcük senkronizasyonu eklenmedi. API'ye henüz gönderilmemiş yerel ses tamponu
için sahte transkript yoktur. Eski streamMsg(c,t) uyumluluğu korunur; yeni Live
hattı kimliksiz streamMsg kullanmaz. REST görünümü ve not CRUD değişmedi.

Kanıt: ../../../docs/stage5-transcript-full-native.json — 10/10 hidden native
faz geçti. 742 pytest, 5 Node süiti ve değişen Python/native dosyalarında 0
Pyright hatası. Gerçek hesap ve fiziksel ses kabulü açık kalır.

## Önceki: konuşarak araya girme / sıralı tur devri — 22 Ekim 2026

Yanıtın ilk kabul edilen PCM parçasından itibaren mikrofon yerelde konuşma
adayı bekler. Yeni ses algılanınca liveAudio.stop(old_request_id) kuyruğu
boşaltır; aktif modele mevcut stop_task gönderilir. Yalnız kalan ses çalıyorsa
host zaten bitmiştir ve ikinci Stop gerekmez. Yeni ses en çok 3 saniye RAM'de
tutulur. Host completed ve ok/stopped sonucu kesinleşmeden yeni live_audio_start
gönderilmez. unknown veya bekleyen araçta giriş atılır, kontroller kilitli kalır.

Bu sıralı Stop → gerçek bitiş → yeni tur uygulamasıdır; aynı socket üzerinde
eşzamanlı çok turlu giriş/çıkış değildir. Aktif Stop context'i sıfırlayabilir;
UI normal context_reset_reason bilgisini gösterir. Yeni backend olayı yoktur.
Mevcut transkript/kimlik/policy/TaskManager/not aktarımı kapıları korunur.

Bekleyen ses eski request_id, micRevision ve connectionRevision ile bağlıdır.
Stop/Pause/Disconnect, kapsam değişimi, cihaz hatası, taşma ve belirsizlik
aktarımı geçersiz kılar. Kesilmiş eski PCM aynı aktif istekte teslim alınsa da
çalınmadan atılır; yeni istek başladıktan sonra eski kimlik normal şekilde
reddedilir. Eski istek tamamlanırken mikrofon temizliği yeni konuşmanın ön
tamponunu kapatamaz. Gerçekleşmiş araçlar backend okumasıyla korunur, yinelenmez.

Kontrollü kabul: 737 pytest, 4 Node süiti, 0 Pyright hatası ve 10/10 native faz.
Kanıt: ../../../docs/stage5-barge-in-full-native.json. Yeni native senaryolar
aktif/yalnız çalma devri, tamamlanmış notun korunması, Disconnect ile tamponun
atılması ve belirsiz sonuçta yeni tur açılmamasını doğrular. Gerçek hesap ve
fiziksel yankı/gürültü kabulü açık kalır.

## Önceki: otomatik yerel dinleme ve yanıt sonrası dönüş — 22 Ekim 2026

Native hazır ve API kataloğundan Live model seçilmişse mikrofon otomatik açılır.
Kullanıcı her konuşmada Mic'e basmaz; düğme Pause listening / Resume listening
işlevindedir. Katalog yüklemesi mevcut açık kullanıcı işlemidir; model seçimi
başarısı taskvex-live-model-ready yerel UI olayıyla bildirilir. Olay sağlayıcı
bağlantısının online veya araç işleminin başarılı olduğu anlamına gelmez.

AudioWorklet yerelde ses adayı bekler: RMS >=0.015 için 2 ardışık 100 ms blok,
en çok 5 blok ön tampon. Sessizlikte API mesajı veya yeni model turu üretilmez.
Ses adayında ön tampon kaybolmadan mevcut live_audio_start/feed hattı kullanılır.
Setup tamponu 3 saniye, gönderim kuyruğu 1 saniye, backend kuyruğu 2 saniye,
toplam giriş 15 saniyedir. Aşım sessiz kırpma/başarı değildir, dinleme durur.
Modelin niyet çözümlemesi, sunucu VAD'si, not aktarımı/transkript/policy/TaskManager
kapıları ve mevcut payload'lar değişmedi. Yeni public backend olayı eklenmedi.

Başarılı yanıtın ses kuyruğu bittikten sonra otomatik dinleme yeniden açılır.
Yanıt sırasında giriş kapalıdır; barge-in yoktur. Yazılı mesaj yerel bekleme
ile yarışmaz. Stop, Pause, Disconnect, anahtar değişimi, cihaz/izin/sağlayıcı
hatası ve belirsizlik otomatik modu durdurur; yeniden başlatmak Resume ister.
Model değişimi hazır onayından önce mikrofon açmaz; manuel Pause'u kaldırmaz.
İzin reddi hazırlık yazısında asılı kalmaz. İlk kez izin penceresi gösterilebilir;
otomatik açılması platformun iznini atlama anlamına gelmez. Gerçek fiziksel
mikrofon/gürültü hassasiyeti ve yeniden açılış izin kabulü henüz yapılmadı.

Son kontrollü kabul: 737 pytest, 4 Node süiti, 0 Pyright hatası ve 10/10
hidden native faz geçti. Kanıt: ../../../docs/stage5-auto-listen-full-native.json.
Ses ve sağlayıcı sentetiktir; gerçek donanım veya ücretli API kabulü değildir.

## Önceki: canlı mikrofon / tek konuşma VAD — 22 Ekim 2026

Mic kullanıcı hareketiyle izin alır; AudioWorklet mono 16 kHz PCM'i konuşurken
100 ms paketlerle gönderir. VAD otomatik, sessizlik ayarı 700 ms; Finish & Send
gerekmez. İlk araç/model yanıtında giriş kapanır. Barge-in, kendiliğinden tekrar
dinleme ve wake word yoktur. Stop gerçek bitişi bekler; ses RAM'de kalır.

Yeni olaylar tek public event metodu üzerinden:

- `live_audio_start:{request_id}`: uzun Promise gerçek tur sonucudur;
  ready, güncel katalog/model, notes_ready ve tek sohbet kilidi korunur.
- `live_audio_feed:{request_id}`: kısa hazır sorgusu; yalnız eşleşen aktif
  akış ready:true döndürür. Setup öncesi ses gönderilmez.
- `live_audio_feed:{request_id,sequence,data}`: sıra 0'dan başlar; data katı
  base64, tam 3.200 bayt/4.268 karakter PCM'dir. data:null açık akış sonudur
  (SDK audio_stream_end); sıra kontrolü burada da geçerlidir. UI normal
  bitişi sunucu VAD'sine bırakır. Tekrar/atlama/taşma turu durdurur.

Toplam giriş 15 saniye, backend kuyruğu 20 paket, UI kuyruğu 10 paketle
sınırlıdır. Geç paket yeni isteğe taşınamaz. Kuyruk yalnız taşıma sınırıdır;
ikinci araç worker'ı veya Live sahibi değildir. İlk ses/kapalı giriş/sonuç,
Stop ve cihaz hatası UI'ın kendi mikrofonunu kapatır. Not yenileme aynı backend
okumasıdır; ikinci mutasyon/save üretmez. Eski live_audio klip sözleşmesi
uyumluluk için kalır; native Mic yeni yolu kullanır. audioChunk çıkışı değişmez.
Gerçek hesap/VAD ve fiziksel mikrofon kullanıcı kabulü beklenir. Son otomatik
kabul: 737 pytest, 4 Node süiti, 10/10 hidden WebView2 native faz ve 0 Pyright
hatası. Kanıt: ../../../docs/stage5-stream-vad-full-native.json. Native ses
kaynağı ve sağlayıcı taşıması sentetiktir; gerçek ses/VAD kabulü değildir.

## Güncel: otomatik ses cihazı listesi — 22 Ekim 2026

Scan düğmesi kaldırıldı. queryDevices() yalnız enumerateDevices ile okur;
nativeReady, ayar paneli açılışı ve devicechange çağırır. Başlangıç listelemesi
not senkronunu bekletmez. Listeleme hiçbir zaman getUserMedia çağırmaz; izin
ve mikrofon açılması yalnız Mic düğmesindedir. Mic izni başarılı olduktan sonra
liste yenilenerek erişilebilir cihaz/adlar gösterilir. Eski ask parametresi ve
geçici izin stream'i kaldırıldı; browser-only query_devices taşıması korunur.
Native dIn/dOut store/onchange otoritesi değişmedi, otomatik liste yeni tercih
veya save olayı üretmez. Save Settings kalıcı seçimi doğrular. İzin öncesinde
platformun gizlediği cihaz/adlar için sahte liste veya otomatik izin istemi yoktur.
Sürekli dinleme/VAD ayrı adımdır. Cihaz testleri kullanıcı tarafından onaylandı.

## Native UI dosyalarının güncellenmesi — 22 Ekim 2026

Native host aynı 127.0.0.1:DEFAULT_HTTP_PORT origin'ini ve storage_path'i
koruyarak mevcut Bottle WSGI desteğiyle UI'ı sunar. Açılış başına değişen
asset öneki bütün göreli modül import'larına uygulanır; no-store gerçek
dosya yanıtındadır. Eski JS/yeni export karışmasını önler. Kullanıcı notu,
ayar, localStorage veya kimlik deposu silinmez. Public event(name,data) ve
izinli backend bildirimleri değişmedi. Browser-only doğrudan HTML/localhost
açılış yöntemi değişmedi; yeni framework veya ikinci sunucu eklenmedi.

## Önceki dilim: Live ses cihazı seçimi — 22 Ekim 2026

Kullanıcı başlat/bitir mikrofon testlerini başarılı bildirdi. Native dIn/dOut
seçimi şimdi WebView MediaDevices kimliğidir; donanım indeksi değildir. Açık
Scan düğmesi geçici getUserMedia({audio:true,video:false}) izni, enumerateDevices
ve kendi geçici track'lerinin kapanışını yönetir. Kamera açılmaz. Browser-only
query_devices/device geri dönüşü korunur; native audio cihazı için backend'e
uygulanmamış device komutu gönderilmez, yeni backend metodu eklenmez.

Seçimler mevcut store.devs'dedir: System default, 'default' olarak kayıtlıdır;
özel kimlik getAudioDeviceId ile opak string olarak okunur. Eski tamsayı
indekslerde Scan/seçim gerekir; sayısal string gerçek cihaz ID'si olabilir.
Değişiklik UI cache'ine yazılır; Save Settings mevcut doğrulanmış native save
kuyruğuyla kalıcılaştırır. Kayıp cihaz tercihi korunur ve listede kullanılamaz
gösterilir. Tercih sonraki kayıt/Live yanıtında geçerlidir; aktif akış değişmez.

liveMic.start'ın üçüncü parametresi seçili deviceId'dir; özel cihaz exact
kısıtıyla açılır. liveAudio.begin(request_id,deviceId) artık await edilir;
özel çıkış setSinkId ile en çok 3 saniye hazırlanır. Stop/Disconnect/setup
değişimi hazırlığı keserse model isteği gönderilmez. Desteksiz/erişilemeyen
sink veya cihaz çıkarılması output_device_unavailable verir; sessiz fallback
yoktur. liveAudio.fail yerel ayrıntılı güvenli hata kodunu genel backend ses
teslim hatasıyla ezmez. Metin/gerçek araç sonuçları korunur.

İki modül devicechange'de yalnız kendi seçili kaynağını bırakır; liste erişimi
başarısızlığı tek başına cihazın çıkarıldığı sayılmaz. Native Scan sonrası
devicechange listeyi izin istemeden yeniler. Cihaz ID'leri browser origin/izin
kapsamındadır; yeni origin'de Scan tekrar gerekebilir. SFX seçili Live speaker'a
taşınmaz. Gerçek çoklu cihaz kabulü kullanıcıya açıktır; sürekli VAD yoktur.

## Önceki dilim: açık başlat/bitir mikrofon — 22 Ekim 2026

Kullanıcı Live ses çıkışının duyulduğunu onayladı. Sıradaki dilim mikrofon:
`live_mic.js` yalnız açık düğmeyle MediaRecorder açar; en çok 15 s/1 MiB RAM
kaydı. Finish & Send kaydı bitirip track'leri kapatır ve OfflineAudioContext
ile mono/16 kHz/16-bit PCM üretir. Kayıt bitmeden ağa ses gönderilmez; süre
dolması, Stop, Disconnect, anahtar/model değişimi ve pagehide kaydı siler.
İzin geç verilirse iptal edilmiş istek track açığını bırakmaz.

Yeni olay `live_audio:{request_id,mime_type:'audio/pcm;rate=16000',data}`;
data katı base64, en çok 640.000 karakter/480.000 bayt ve 16-bit hizalıdır,
en az 0.1 saniyedir. Host güncel katalog/model/not aktarımı kapısını korur.
Tek TextChat/PersistentLive/ModelTools hattı kullanılır. Modelden gelen
`input_text` normal kullanıcı mesajı olarak gösterilir; PCM raporlanmaz.
Transkript olmadan hiçbir araç başlatılmaz. Not mutasyonlarının gerçek ID ve
güncel verified liste koşulu aynıdır; sonuçta panel backend'den yenilenir.

Bu setup'ta otomatik VAD kapalıdır; activityStart → sınırlı PCM parçaları →
activityEnd gönderilir. Metin/ses setup değişimi eski resume bilgisini iptal
eder ve yeni oturum açar. Gönderim sonrası Stop/unknown/oynatma kuralları
mevcut Live sözleşmesidir. Mute yalnız yanıt sesidir; kayıt iptali Stop'tur.
REST ses, sürekli dinleme, otomatik VAD/barge-in ve dIn/dOut yönlendirmesi
henüz bağlı değildir. Fiziksel mikrofon kabulü kullanıcı testine açıktır.

## Önceki dilim: Live ses çıkışı ve kalıcı API anahtarı — 22 Ekim 2026

Kullanıcı son not/kısmi metin seçiminin tamamen çalıştığını bildirdi; bu manuel
kabul kapandı. Sıradaki tek dilim yazılı Live mesaja ses çıkışıdır. Mikrofon,
VAD ve giriş cihazı açılmadı. Normal UI'ın `live_text:{text,request_id}` isteği
metin transkriptiyle birlikte PCM sesini de çalar; REST metin hattı korunur.
Eski `live_text:string` ve alıcısız geliştirici probe'u ses çalmaz.

Live oturum sahibi ses parçalarını host'un isteğine bağlı alıcıya aktarır.
Bridge'in tek yeni bildirimi `window.vex.audioChunk({request_id,mime_type,data})`
(jarvis alias aynı nesne) olup data base64, mime_type audio/pcm;rate=24000'dır.
JS metodu yalnız güncel isteğin parçasını kabul edip boolean teslim onayı
verir. Bu, fiziksel hoparlör kabulü değildir. Modelden gelen başka istek ID'si
kullanılmaz; geç/eski paket yeni yanıtı etkileyemez. Backend parça boyutu en çok
128 KiB, 16-bit hizalı; tur başına en çok 2.880.000 bayt ile sınırlıdır.

`live_audio.js` kendi Web Audio context/gain/source kaynaklarının sahibidir.
PCM little-endian 16-bit mono/24 kHz olarak çözülür; OS varsayılan çıkışı
kullanılır. En çok 20 saniye/512 source kuyruğu vardır. Taşma, bozuk format,
autoplay/cihaz sorunu seste açık uyarı üretir; metin ve doğrulanmış araç
sonucu korunur. PCM dosya, log, history, localStorage veya yedeğe yazılmaz.
API yanıtındaki audio_bytes_forwarded/ audio_bytes_discarded sayısaldır;
audio_error null veya güvenli koddur, sürücü/sağlayıcı ham hatası değildir.

UI metin gelir gelmez gösterir; giriş/not kilidi ve Stop, kalan sesin bitişine
kadar tutulur. Çalma bitişi event ile izlenir, en çok 22 saniye bitiş beklenir.
Stop tuşu sesi hemen keser; model sürüyorsa aynı request_id ile native Stop
sonucu ayrıca beklenir. Model zaten bitmişse yalnız yerel çalma durdurulur,
tamamlanmış araç geri alınmış veya model iptal edilmiş sayılmaz. Mute yalnız
Live çıkış gain'idir; mikrofon/sound effects kontrolü değildir. Disconnect,
model/anahtar değişimi, hata/unknown ve sayfa kapanışı ses kaynaklarını bırakır.
Ses için bağlam GoAway/resumption sahibinden ayrıdır; tekrar ses/mesaj yürütülmez.

API anahtarının kalıcı kaydı zaten Windows Kimlik Bilgileri Yöneticisi'ndedir
(aynı Windows kullanıcısı/makine, veri profiline bağlı kayıt). Açılışta bu kayıt
yeniden kullanılır; parola kutusunun boş olması kaydın silindiği anlamına gelmez.
Kaydı gösterme/JSON'a taşıma yapılmadı. Salt okunur kontrolde mevcut profil için
configured=true, ortam anahtarı override=false görüldü; gerçek kayıt değiştirilmedi.
Farklı TASKVEX_HOME profili ayrı anahtar ister. Kayıt, API erişim/kota kanıtı değildir.

Gerçek model/ses cihazıyla yeni ses kabulü bekleniyor. Native sentetik ses
render edilmesi hoparlörün duyulabilirliğini veya mikrofonu doğrulamaz.

## Güncel not hedefi seçimi — 22 Ekim 2026

REST/Live update/delete için ortak ModelTools kontrolü genişletildi. İlk
aktarım onayı ve bu turda yeni, başarılı verified notes.list sonucu zorunlu
kalmıştır. Araç şeması `{id,text?,done?}` / `{id}` değişmedi; seçilen hedef
yine gerçek kayıt ID'sidir. Core CRUD, policy ve TaskManager atlanmaz.

Seçim sırası: tek açık kayıt ID'si; kullanıcı mesajındaki tırnaklı literal
içerik filtresi; tırnak dışında “son not” ifadesi; mevcut tek tam metin.
`içinde 'merh' geçen not`, `'merh' içeren not` ve `note containing 'merh'`
biçimleri, metninde literal sorgu geçen **tüm** kayıtları tarar. Tek aday ve
modelin ID'si aynıysa izin verilir. Tam metni 'merh' olan bir not bulunması,
başka notlar da bu parçayı içeriyorsa belirsizliği ortadan kaldırmaz.
Türkçe büyük İ, harf/boşluk ve düz/tipografik tırnak farkları tolere edilir;
regex/bulanık benzerlik, tırnaksız veya olumsuz filtre yorumlanmaz.

“Son notu/son notun”, “en son eklediğim not” ve “last/latest/newest note”
en büyük created_at ile seçilir; son düzenlenen veya listede son duran kayıt
anlamına gelmez. Her kaydın tarihi bilinmeli ve maksimum tarih tek olmalıdır.
Eksik/null tarih veya maksimum tarihte eşitlikte ID istenir. Kayıtlı UTC
zamanlar karşılaştırılır; saat sapması veya yedekten gelen tarihin gerçekliği
garanti edilmez. 'son notu' adlı literal bir notu seçmek için adı tırnakla verilir.

Birden fazla sorgu, latest + içerik filtresi, sıfır/çoklu aday veya modelin
başka ID seçmesi `note_target_required` ile açıklama ister; mutasyon oluşmaz.
Destek TR/EN'deki bu açık kalıplarla sınırlıdır, genel doğal dil çözümleyici
iddiası yoktur. Açık ID belirsizliği giderir. Aynı çağrının replay'i önceki
gerçek sonucu korur; yeni mesajda eski liste seçim izni vermez. Stop, kopma,
unknown kilidi ve UI'ın yalnız backend'den yenilemesi değişmedi.
Bu dilimin manuel kabulü kullanıcı tarafından tamamen çalışıyor diye onaylandı;
önceki CRUD kabulü korunur.

## Not oluşturulma zamanı ve kullanıcı kabulü — 22 Ekim 2026

Kullanıcı REST/Live not ekleme/listeleme/düzenleme/tamamlama/silme, aynı
metinli notta açıklama ve gerçek ID ile seçim, Stop sonrası yeni mesaj ve
tamamlanmış işlemin korunması testlerinin geçtiğini bildirdi. Aşağıdaki
önceki not CRUD kabulündeki “API limiti” kaydı bu bildirimle kapanmıştır.
Bu bildirim GoAway/resumption veya yeni zaman alanının gerçek hesap kabulü değildir.

Yeni notlar `created_at:"YYYY-MM-DDTHH:mm:ss.sssZ"` UTC zamanı taşır.
Native eklemede saati backend belirler; normal add/update parametrelerinde
zaman gönderilemez. Güncelleme/tamamlama ID'yi ve oluşturulma zamanını korur.
Backend liste/işlem yanıtları ve UI `{id?,t,d,created_at?}` önbelleği alanı
taşır; backup export/import ve ilk açık aktarım metadata'yı düşürmez.
Browser-only yeni notun saati tarayıcıdan alınır. Açık restore/aktarım
geçerli tarihi taşıyabilir; bu tarih sunucuda gözlenmiş oluşum kanıtı değildir.

Eski kayıtta eksik/null zaman **bilinmiyor** anlamındadır. Okuma dosyayı
değiştirmez, yeni tarih/ID atamaz. Tarihsiz eski yedekler yüklenebilir; restore
tarihi oluşturulma zamanı gibi gösterilmez. Geçersiz tarih normalleştirilip
başka güne kaydırılmaz: backend reddeder; UI snapshot/import ayar yazımından
önce tüm adayı reddeder. Tarih bir UTC duvar saati kaydıdır; eşit zaman veya
makine saatinin geri alınması için tek başına kesin sıra garantisi vermez.

Bu önceki ayrı dilim tarih bilgisiydi. Sonraki hedef seçimi dilimi yukarıda
güncellenmiştir. Ses veya UI temizliği bu değişikliklerde yoktur.

## Güncel model not düzenleme/silme sözleşmesi — 22 Ekim 2026

REST ve Live aynı ModelTools → registry/policy/TaskManager hattından
`notes.update:{id,text?,done?}` ve `notes.delete:{id}` kullanır. CRUD şeması,
kalıcı kimlikler ve dosya/readback doğrulaması değişmedi. İlk native not
aktarımı onaylanmadan add/list/update/delete araçlarının hiçbiri modele açılmaz.
`notes.initialize/replace` model kataloğunda yoktur; UI aktarım/restore yolunda kalır.

Host her kullanıcı turunda `begin_turn(text)` ile seçim bağlamını yeniler.
Yeni update/delete için bu turda yeni çağrı ID'siyle başarılı ve verified
`notes.list` sonucu gerekir. Kullanıcı mesajı tek bir gerçek kayıt ID'sini
veya tek bir mevcut tam not metnini içermeli ya da yukarıdaki tek içerik/zaman
seçimine uymalıdır. Metinde büyük/küçük harf ve
boşluk farkları tolere edilir; kelime sınırı gözetilir. Aynı metinli birden
fazla notu ayıramayan filtre, birden fazla eşleşen metin/ID, bilinmeyen ID veya
desteklenmeyen dolaylı tarif/sıra numarası seçim sayılmaz. Bu dar eşleştirme bir doğal dil resolver'ı
değildir; belirsiz hedefte tam metin veya ID istenir, tahminle mutasyon yapılmaz.

Reddedilen seçim `ok:false,code:note_target_required,error` ile kullanıcıya
hangi notun kastedildiğini sorar. Bu hedef için core görevi oluşturulmaz;
önceki doğrulanmış işlemler ve tool_results korunur. Yalnız bu ret unknown
sayılmaz. Mutasyon veya başarısız yeni liste eski seçim kanıtını geçersiz kılar;
eski liste sonucunu yeniden okumak onu güncel seçim kanıtına dönüştürmez.

Aynı mantıksal oturum/çağrı ID'siyle tekrar yeni yazı yapmaz; silinmiş hedef
için eski tamamlanmış sonuç da dönebilir. İçeriği değiştirilmiş tekrar manager
tarafından reddedilir. Live resume çağrı kimliklerini korur, fakat yeni mesajın
seçimi eski listeye dayanamaz. Stop/unknown/kopma davranışı aynen korunur.

UI her not araç turundan sonra mevcut `notes_init:{notes:null}` okumasıyla
backend'i yeniler; ikinci update/delete/note_done/note_del/save göndermez.
Başarı yalnız core'un succeeded + verified + read_back kanıtıdır; model
metni kanıt sayılmaz. Yazıdan sonra model bağlantısı kopsa da gerçek sonuç korunur.
Yeni testler: tests/test_model_note_mutations.py; native kanıt:
docs/stage5-model-notes-native.json (REST/Live CRUD panel yenileme, sıfır save echo).
İlk koşumda gerçek hesap kabulü API limiti nedeniyle açıktı; yukarıdaki
kullanıcı bildirimi not CRUD kabulünü kapatır. Ses/mikrofon bu dilimde yoktur.

## Güncel Live bağlantı yaşam döngüsü — 22 Ekim 2026

Bu bölüm aşağıdaki tarihsel “resumption yok” kapsamını günceller. Setup'ta
session_resumption etkindir; gerçek setup_complete gelmeden metin gönderilmez.
GoAway aktif mesajı yeniden göndermez: tur mevcut 25 saniye sınırında bitmeye
çalışır; yarım kalırsa hata ve önceki araç sonuçları korunur, eski bağlam unutulur.

Yeni kullanıcı metninden önce mevcut socket en çok 50 ms/32 kontrol mesajıyla
yoklanır. Yalnız tamamlanmış turun ardından idle durumunda alınan resumable=true
ve dolu new_handle güvenli checkpoint sayılır. Aktif üretimde gelen checkpoint
kullanılmaz; resumable=false/boş handle eskisini geçersiz kılar. GoAway veya
idle kopmada güvenli checkpoint varsa aynı ModelTools, çağrı kimlikleri ve
mantıksal oturumla devam edilir. Eski metin otomatik tekrar gönderilmez.

Bir kullanıcı isteğinde en çok bir resume setup denenir; 400/404/1008 veya
eksik setup onayında, kullanıcı metni henüz gönderilmeden tek fresh setup
denenebilir. Yetki/kota/503/ağ hatasında otomatik setup tekrarı yoktur. Güvenli
checkpoint yok/eskimişse yeni oturum açılır. Handle yalnız bellektedir; yerel
işlenişinden 2 saat sonra kullanılmaz; sağlayıcı daha önce de reddedebilir.
Stop, Disconnect, model/anahtar/araç değişimi ve başarısız aktif tur eski
devam bilgisini temizler. Idle'da beklenmedik içerik/araç çalıştırılmaz.

Sonuç alanları: session_reused aynı socket'i, session_resumed başarılı resume
setup'ını belirtir. logical_session_id host'un opak kimliğidir; resume'da kalır,
fresh başlangıçta değişir. context_reset_reason bilinen güvenli bir kod veya
null'dır. UI session reused / session resumed / new session ve gerektiğinde
context reset nedenini gösterir. GoAway görüldüyse goaway_received=true gelir.
Sağlayıcının handle/session ID'si UI, log, dosya veya yedeğe aktarılmaz.
Idle kopma anlık arka plan izlenmez; sonraki mesajın preflight'ında fark edilir.

## Güncel REST Stop sözleşmesi — 22 Ekim 2026

Native `text` artık Live ile aynı `{text:string,request_id:string}` zarfını
kullanır; eski string çağrısı korunur. Stop kimliği 1–128 karakter olmalıdır.
`stop_task:{request_id}` REST ve Live için aynı giriştir; eski/aktif olmayan
kimlik reddedilir. REST kabulü `ok:true,accepted:true,completed:false` döner;
`waiting_for` değeri `http_response`, `tool_result` veya `turn_completion` olur.
HTTP sürüyorsa UI açıkça onun bitişini beklediğini söyler; giriş/not kilidi sürer.

Stop, HTTP/araç başlatma kapısıyla sıralanır. Kabul edilmemiş sonraki araç,
retry ve fallback başlamaz; retry beklemesi sinyalle uyanır. Zaten kabul edilmiş
senkron HTTP zorla öldürülmez; yanıt/hata/timeout beklendikten sonra içeriğiyle
yeni işlem yapılmaz. Kısa yerel core görevine iptal sinyali verilir, gerçek sonuç
korunur. Tamamlanmış yazı geri alınmaz. HTTP timeout ayarı 30 saniyedir; taşıma
katmanının dönmesi beklenir, kesin 30 saniyelik toplam bitiş garantisi değildir.

Asıl `text` sonucu `ok:false,completed:true,stopped:true,request_id` ise HTTP ve
araç beklemesi bitmiştir. Pending/unknown veya iptal sonucu okunamayan görevde
`unknown:true,stopped:false` gelir ve UI yeniden açılışa kadar kilitli kalır.
Yeni mesaj ayrı istemci/sinyal alır; eski Stop ve geç Stop yanıtı yeni turu
etkilemez. UI notları backend'den okur; ikinci mutasyon göndermez. Live'ın
socket iptali değişmedi. Resumption/ses/not düzenleme-silme bu kapsamda yoktur.

## Güncel Live Stop sözleşmesi — 22 Ekim 2026

Bu bölüm aşağıdaki Stop'un kapalı olduğu tarihsel kapsamı günceller. UI
`live_text:{text:string,request_id:string}` gönderir; kimlik 1–128 karakterdir.
Eski `live_text:string` korunur. `stop_task:{request_id:string}` yalnız eşleşen
aktif Live turunda kabul edilir; `ok:true,accepted:true,completed:false` bitiş
değildir. UI asıl live_text sonucuna kadar giriş/not kilidini korur.

Asıl sonuç `stopped:true,completed:true,ok:false` ise tur/socket gerçekten
bitmiştir; önceki tool_results korunur ve not paneli backend'den okunur.
Pending/unknown araçta `stopped:false,unknown:true` vardır; kontroller açılmaz.
Stop tamamlanmış notu geri almaz. Tekrarlanan Stop aynı sinyaldir; eski istek
kimliği yeni turu kesemez, gecikmiş Stop yanıtı yeni UI durumunu değiştiremez.
Sonraki mesaj yeni oturum açar. I/O thread'i idle kalır, Disconnect onu da kapatır.
REST Stop sonraki dilimde eklendi; güncel kural yukarıdadır. Resumption eklenmedi.

## Güncel Live araç sözleşmesi — 22 Ekim 2026

Bu bölüm aşağıdaki tarihsel araçsız test kapsamını günceller. `live_text:string`
aynı kilit/katalog doğrulamasını kullanır. Model yalnız `apps.catalog` ve
`system.status` görür; backend ilk not aktarımını doğrulamışsa `notes.add`,
`notes.list`, `notes.update` ve `notes.delete` de açılır. Uygulama açma modele açılmaz.
Araç listesi değişirse eski Live bağlantısı kapatılıp yeni kapsamla açılır.

Host kaynak/kullanıcı kimliğini belirler; sağlayıcı `id/name/args` çağrısı
ModelTools → registry/policy/TaskManager hattına girer. Aynı açık oturumda aynı
çağrı kimliği aynı görevi kullanır; farklı argümanla tekrar reddedilir.
Terminal gerçek sonuç `FunctionResponse` olarak çağrı kimliğiyle geri verilir.
Bekleme/belirsizlik başarı sayılmaz; otomatik yeniden gönderme yapılmaz.

Yanıtta `mode=live_session`, `session_reused`, `tools_enabled`, `tool_results`
ve süreler bulunur. Her araç kaydı `id,name,task_id,status,result` taşır;
`result` core'un `verified/data/error/evidence` sonucudur. UI araç durumunu
loglar, not çağrısından sonra backend'den notları okur; ikinci bir yazı göndermez.
Model yanıtı başarısız olsa bile kesinleşmiş araç sonuçları korunur. `unknown`
sonucunda sohbet/not kontrolleri yeniden açılışa kadar kilitli kalır.

Tur 25 saniye, araç beklemesi 5 saniye, en çok 8 çağrıdır. Bunlar işlemi geri
alma garantisi değildir. Disconnect hâlâ yalnız idle iken çalışır. Ses çıktısı
atılır; oynatma, mikrofon ve normal Stop bu dilimde yoktur. Yeni oturum/farklı
çağrı kimliği aynı niyetin ikinci kez yürütülmesini otomatik engellemez.

## Güncel Live oturumu — mesajlar arasında aynı bağlantı

Bu bölüm aşağıdaki soğuk bağlantı testinin kaynak ömrü kuralını günceller.
`live_text` aynı API Live modelini ve aynı anahtarı kullanıyorsa SDK/WebSocket
açık kalır. PersistentLive tek I/O thread/event loop sahibidir; TaskManager'ın
worker'ına alternatif değildir. Aynı anda bir tur kuralı korunur. Araç kapsamı
yukarıdaki güncel bölümdedir; sohbet bağlamı sağlayıcıdaki oturumda kalır,
yerel sohbet geçmişi veya ses baytları kaydedilmez.

Yanıtta mode=live_session ve session_reused:boolean vardır. UI ilk turda
new session, takip eden turda session reused gösterir. connect_ms yeniden
kullanımda bağlantı kurma maliyeti içermez; first_text_ms/elapsed_ms her mesajın
kendi başlangıcına göredir. Kalıcı oturumun sonsuza kadar yaşaması garanti değildir.

`disconnect:null` yalnız idle iken socket/SDK/event loop/thread kapanışını
bekler; `{ok:true,completed:true,disconnected:true}` sonrası UI offline olur.
Aktif turda açık ret verilir; Stop/iptal değildir. Sonraki mesaj yeni oturum
açabilir. Model değişimi ve anahtar kaydı eski Live kaynağını önce kapatır.
Pencere kapanışı normalde idle bekler; GUI döngüsü beklenmedik biçimde biterse
aktif ağ işi iptal edilip Live kaynağı finally'de de bırakılır.

Hata/timeout/GoAway/kısmi tur sonrası socket tekrar kullanılmaz. Başarısız mesaj
otomatik yeniden gönderilmez ve REST'e geçilmez. Yeni kullanıcı mesajı yeni
bağlantı açabilir; eski bağlamın kaldığı varsayılmaz. Oturum devam ettirme,
otomatik reconnect ve idle sağlık bildirimi bu dilimde yoktur. Uzak idle kopma
sonraki I/O sırasında anlaşılabilir; LAST LIVE TEST son yanıt bilgisidir.

## Geçici Live gecikme testi — ses oynatma/araç yok

Sohbet altındaki `liveLatencyTest` kutusu açılışta işaretlidir; bu geçici test
tercihi yedeğe yazılmaz. İşaretliyken native UI `live_text:string` gönderir.
Backend son başarılı API kataloğundan seçilmiş Live modeli şart koşar; katalog
yüklenmeden istek açık hatayla reddedilir. Kutuyu kapatmak mevcut REST text
akışına döner. REST 3.8/3.5 retry hattı değiştirilmedi.

TextChat.run_live aynı meşgul/kapanış kilidini kullanır; API thread'inde asyncio
ile tek soğuk WebSocket oturumu açar. Asenkron/senkron SDK istemcileri ve socket
her çıkışta kapanır. Bağlantı+tur için 25 saniye timeout, en çok 2000 mesaj ve
32000 karakter sınırı vardır. Otomatik retry/model fallback yoktur. Model sesi
zorunlu AUDIO yanıtı olarak üretir; output_audio_transcription etkin, ses
biriktirilmeden atılır. Mikrofon ve hoparlör açılmaz. Sağlayıcı ses kotası yine
tüketilebilir. Hiçbir araç bildirilmez/çalıştırılmaz; not paneli güncellenmez.

Başarı normal text/elapsed_ms alanlarına ek mode=live_latency_test,
connect_ms, first_event_ms, first_text_ms, audio_bytes_discarded verir.
first_event ilk ses/içerik, first_text ilk transkript/metindir; her ikisi soğuk
bağlantı kurulumunu içerir. Tüm parçalar okunur; metin ve transkript birlikte
varsa transkript tercih edilerek iki kez gösterilmez. interaction_status varsa
IDLE bitişi, yoksa turn_complete beklenir; kesilmiş/boş/kısmi sonuç başarı olmaz.

UI tam yanıt geldiğinde yazıyı ve ilk metin/toplam süreyi gösterir; ses çalmaz.
LAST LIVE TEST son tamamlanan isteği belirtir, açık kalıcı bağlantı değildir.
Hatalar kodlu güvenli metin olarak döner; WebSocket kodu HTTP kodu gibi
etiketlenmez. Bu bir latency smoke yoludur; kalıcı Live oturumu, sesli asistan,
not araçları, iptal veya bot entegrasyonları tamamlandı anlamına gelmez.

## Metin hata/süre teşhisi

GeminiText sonuçları `elapsed_ms` (tüm tur; araç ve retry beklemesi dahil) ve
`model_attempt_details:[{model,outcome,elapsed_ms,http_status?}]` taşır. Her deneme
süresi yalnız o generate_content çağrısına aittir. outcome response, http_error,
timeout, network_error veya failed'dır; ham exception/sağlayıcı yanıtı tutulmaz.
Model/API hata alanları mevcut açık listedeki kodlardır. UI başarısızlıkta
HTTP kodu, uygulama hata kodu, son model ve toplam süreyi gösterir. Her model
denemesinin sonucu/süresi Engine Log'a güvenli metin olarak eklenir. Bu ölçüm
kota/servis/istek hatalarını ayırır; belirli bir hatanın nedenini tahmin etmez.
Başarı yanıtında da toplam süre görünür. Retry/timeout ve araç yürütme politikası
değişmedi; timeout performans iyileştirmesi veya Live bağlantısı gibi sunulmaz.

## Güncel düzeltme — normal sohbet ve API'den Live kataloğu

Bu bölüm aşağıdaki ilk metin diliminin not aktarımı ve model seçimi kurallarının
yerine geçer. Not onayı beklerken normal sohbet açıktır; host yalnız apps.catalog
ve system.status araçlarını verir. Onaydan sonra notes.add/list eklenir. Devam
eden veya sonucu belirsiz not işlemi sırasında UI mesaj gönderimini durdurur.
Browser-only açılışta gerçek backend yoksa sohbet altında app.main açılış komutu
gösterilir; girdi korunur. Not aktarımı hiç otomatik onaylanmaz.

`query_catalog:null` yalnız açık Load Live models tıklamasında çalışır. Resmi
SDK models.list bütün sayfalarda supported_actions içinde bidiGenerateContent
bildiren modelleri seçer; adında live geçmesi yeterli değildir. En çok 5 sayfa,
sayfa başına 100 istenir; HTTP beklemesi 10 saniye, SDK retry kapalıdır. Boş liste
gerçek boş sonuçtur. Hata veya limitte kısmi/sabit/yedek liste uygulanmaz. UI
65 saniyede sonucu belirsiz sayıp yeniden yüklemeyi kilitler; geç yanıt uygulanmaz.
Backend bu sırada anahtar değişimini ve ikinci katalog sorgusunu reddeder.

Başarı `{ok:true,completed:true,models:[{id,name,live:true}],currentModel}`.
Liste hesapta Live bağlantısı veya ses çıkışının çalıştığını kanıtlamaz.
`model:string` yalnız son başarılı API listesindeki kimliği kabul eder. Bu,
gelecek Live oturumu tercihidir; REST text model adıyla aynı değişken değildir.
Sonuç live_connected:false içerir; UI henüz ses bağlanmadığını açık söyler.
Genel ayar kaydı tercihi mevcut save hattında saklar. API anahtarı değişince
katalog geçersizleşir ve kullanıcı tekrar yükler; model isimleri anahtar yedeği
ile kaydedilmez. Katalog hatası önceki seçimi sunucu tarafında da geçersiz kılar.

REST metin adaptörü 3.8 Flash → kontrollü retry → 3.5 Flash-Lite politikasını
korur. UI'daki Live tercihi bu REST isteğine gönderilmez. Telegram/Discord için
bu metin hattı korunmuştur; bot entegrasyonları henüz yazılmamıştır.
Yazılı masaüstü mesajına Live ses yanıtı sonraki dilimde bağlanacak; bugün yoktur.

## Aşama 5.3 metin dilimi — tek mesaj, gerçek model ve not yenileme

- İlk uygulamada `text: string` hazır native host ve ilk not aktarımı gerektiriyordu;
  güncel davranış yukarıdadır.
  Mesaj 1–20000 karakterdir; boş metin reddedilir. Aynı anda tek model turu
  vardır. Her mesaj bağımsızdır; geçmiş sohbet/profil talimatı gönderilmez.
- Uzun ağ turu bridge RLock'unu tutmaz. PyWebView API thread'i çalıştırır;
  ikinci worker/dispatcher kurulmaz. TextChat tur sonunda SDK istemcisini kapatır.
- İzinli model araçları apps.catalog, system.status, notes.add ve notes.list'tir.
  Native notlar kullanıcı verisi olabilir; kullanıcı listeleme istediğinde bu
  araç sonucu Gemini hizmetine gider. Silme/düzenleme/uygulama açma bu dilimde
  modele açılmaz. Registry/policy/TaskManager atlanmaz.
- Başarı `ok:true,completed:true,text,tool_results,model,model_attempts` döndürür.
  completed tur fonksiyonunun bittiğidir; araçların başarılı olduğunu tek başına
  kanıtlamaz. Pending/unknown sonuçlarda UI kilitli kalır. Beklenmeyen hata
  `{ok:false,unknown:true,error}` verir; ham exception veya anahtar paylaşılmaz.
- app.js native sendText yanıtı textContent ile gösterir; model HTML'i çalışmaz.
  Native metinde emit kabulü başarı sayılmaz. Yanıt gelene kadar Send/input/model
  ve Stop kapalıdır; not mutasyon/import ayrı chat kilidiyle durur. 240 saniyede
  kesin sonuç alınamazsa unknown gösterilir, geç cevap yok sayılır, yeniden açma
  gerekir. Yeniden gönderim otomatik değildir. Gerçek iptal henüz bağlı değildir.
- Normal bitişte, başarısız yanıt öncesi not yazılmış olabileceğinden, notes_init
  salt okunur yeniden sorgulanır. Native setter/mutasyon/save echo üretilmez.
  Yenileme doğrulanamazsa not modülünün mevcut unknown kilidi korunur.
- İlk katalog desteklenen iki metin modelini bildirir; bu liste hesap erişimi
  veya online kanıtı değildir. `model: string` yalnız bu iki adı kabul eder ve
  aktif turda reddedilir. UI önce onayı bekler, sonra mevcut ayar save yoluyla
  tercihi kaydeder. Başlangıçta desteklenmeyen eski model yerine varsayılan
  seçilir. Metin sırasında fallback kalıcı seçili modeli değiştirmez.
- Net pill yalnız başarılı gerçek metin turundan sonra `TEXT · <model>` gösterir;
  bu son başarılı istek bilgisidir, sürekli Live bağlantısı değildir. Başarısız
  turda offline/hata; model seçimi değişince NOT CHECKED gösterilir. Reconnect,
  disconnect, stop_task ve ses sonraki dilimlerdir; bugün başarılı sayılmazlar.
- Aktif metin turunda Shutdown/Restart/X kapanışı reddedilir; tur bittiğinde
  tekrar kapatılabilir. İşlem tamamlanmış gibi sahte iptal gösterilmez.

Doğrulama ve kullanım: [Aşama 5](../../../docs/STAGE5_MODEL.md).

## Aşama 5.3 ilk dilim — API anahtarının native kaydı

- credentials.js API Key alanı, Save API key düğmesi ve apiKeyStatus durumunun
  sahibidir. Değişiklik/blur otomatik gönderim yapmaz; düğme veya Enter gerekir.
- `apikey: string` yalnız hazır native host'ta desteklenir. Host anahtarı profilin
  Windows Kimlik Bilgileri Yöneticisi kaydına yazar ve geri okuyarak doğrular.
  Başarı `{ok:true,completed:true,saved:true,configured:true}` biçimindedir;
  anahtarın kendisi geri dönmez. Boş girdi kayıt silmez, reddedilir.
- `query_apikey: null` yalnız `{ok:true,completed:true,configured:boolean}` verir.
  Bu, Windows'ta kayıt varlığıdır; ortam anahtarını veya API erişimini doğrulamaz.
- API key kaydında ağ isteği/model online sinyali yoktur. Anahtar genel save,
  settings.json, notes.json, localStorage, export veya timeline'a girmez.
  Kayıt başlarken password input temizlenir; onay gelmeden başarı sesi çalınmaz.
- 12 saniyede onay alınmazsa durum unknown olur; yeniden gönderim yapılmaz.
  Kontroller kilitli kalır. Native hata sonucu doğrulanmış başarıya çevrilmez.
- `apikey` browser fallback onEvent taşımasına gönderilmez. Native onEvent
  gözlemcisi yalnız `[REDACTED]` alır; anahtar olayının hata/yanıtları loglara
  ham haliyle aktarılmaz. Başka event'lerin mevcut gözlemci sözleşmesi korunur.
- Backend metin istemcisi açık GEMINI_API_KEY ortamını, yoksa mevcut profilin
  Windows kaydını kullanır. TASKVEX_HOME profilleri birbirinin kaydını kullanmaz.
  Bu ilk anahtar diliminde sohbet bağlı değildi; güncel metin sözleşmesi üsttedir.

## Aşama 3 — Native notlarda tek backend otoritesi

Native UI ilk notes_init sorgusundan sonra gerekiyorsa Use backend notes ile
açık aktarım onayı ister; iptalde eski notlar korunur. Onaylı aktarımın işareti
notlarla aynı dosyadadır, yeniden açılışta/son not silinince yeniden eklenmez.
Native not olayları {version:1,request_id,arguments} zarfını kullanır:
notes_init -> notes.initialize; note_add -> notes.add; note_done -> notes.update;
note_del -> notes.delete; notes_replace -> notes.replace. Kaynak/kullanıcıyı
bridge seçer. Bütün işlemler registry/policy/TaskManager hattından geçer.
UI yalnız completed:true/verified:true sonucunu uygular; 12 saniye/unknown
sonrasında tekrar göndermez, geç yanıtı yok sayar ve notları kilitler.
Yeniden açılış backend'deki sonucu okur. Yerel kopya önbellek/yedektir.
Native addNote/setNotes ve not içeren initApp/loadStore false döner; notlar
bu setter'larla yazılamaz. Tarayıcı-only setter ve eski yerel olay biçimleri
korunur. Detaylar: [not geçişi](../../../docs/STAGE3_NOTES.md).

## Tüm ayar kayıtları ve yedek onayı

- saveAll() yerel boolean API'sini korur; native save talepleri bağımsız JSON
  kopyalarıyla tek Promise kuyruğundan gönderilir. loadStore(...,{emitSave:true})
  da aynı kuyruğu kullanır. onSave gözlemcisi ayrı kopya alır, gönderilen veriyi
  değiştiremez. Snapshot setter'larında emitSave:false/no-echo korunur.
- Settings/Profile açık Save ve Export native completed:true/saved:true onayını
  bekler. Otomatik kayıtlarda ayar/profil panelleri kaydediliyor/kaydedildi/onay
  alınamadı durumunu gösterir. 12 saniyede onay gelmezse sonuç belirsizdir;
  gerçek istek iptal edilmez, kuyruk sırası bozulmaz ve otomatik tekrar yapılmaz.
- importBackup async boolean döndürür. Önce desteklenen yedek alanlarını ve
  koleksiyon yapısını denetler; runtime telemetri/katalog gibi dış durumları
  yedekten uygulamaz. Native'de önce ayar onayı, not içeren dosyada ayrıca
  notes_replace onayı beklenir; sonra yerel skill/rutin ve ayarlar uygulanır.
  Ret/eksik onayda henüz uygulanmamış UI alanları korunur. Import sırasında
  form kontrolleri geçici kapatılır; başarı/hata/bekleme sınırında geri açılır.
- İki depo tek transaction değildir: native ayar kaydı başarılı olup daha sonra
  localStorage yazımı başarısızsa önceki yerel tercihler geri yüklenir; native
  ayarlar ve restore edilmiş notlar yeni olabilir. Backend notları otoritedir,
  eski UI notlarına dönülmüş gibi gösterilmez. Kısmi başarı açık bildirilir. Kaynak
  yedek dosyası silinmez; otomatik yeniden içe aktarma yapılmaz.
- Export native'de kayıt onayından sonra WebView2 Save File diyaloğu açar. UI
  yalnız indirme istendiğini söyler; diyaloğun açılması dosya yazıldı onayı
  değildir. Tarayıcı-only export tarayıcının indirmesini kullanır. Kullanılmayan
  export backend olayı gönderilmez; Blob URL'si daha sonra serbest bırakılır.
- Skill/rutin tanımları yereldir. Native notların sahibi backend'dir; generic
  save koleksiyonları ikinci kez yazmaz. Not içeren import, dosyanın ön
  doğrulamasından ve ayar kaydından sonra notes_replace onayını bekler; UI not
  snapshot'ını tekrar uygulamaz. Eski yedek kimlik alır; yeni yedek kimliği
  korur. İki backend dosyası ile yerel depo tek transaction değildir; sonraki
  hata önceki başarılı yazımı geri almaz. Kısmi başarı açık bildirilir.

## Başlangıç hatası ve ayar onarımı

- Backend `startupStatus({ok:false,code,message,recoverable})` ile başlangıç
  uyarısını gösterir. `startupStatus({ok:true})` uyarıyı kaldırır. Bu durum model
  online/offline durumundan ayrıdır; mesaj textContent ile güvenli yazılır.
- Payload'sız `retry_startup` kayıt değiştirmeden başlangıcı yeniden dener.
  İlk ui_ready ile aynı doğrulama ve no-echo snapshot yolu kullanılır. Başarısız
  başlangıçta native save reddedilmeye devam eder.
- `recover_settings:{confirmed:true}` yalnız açık UI onayı sonrası gönderilir;
  bu işaret kimlik doğrulaması değildir, güvenilir yerel UI'ın onay akışıdır.
  Bozuk JSON veya ayar şeması, asıl settings.json baytları benzersiz .corrupt
  dosyasına taşınmadan değiştirilmez. Okunabilen geçerli üst alanlar korunur;
  geçersiz/okunamayan tercihler varsayılana döner. Yerel UI koleksiyonları ve
  core notes.json değişmez. Başarıdaki backup alanı yalnız yedek dosya adıdır.
- Desteklenmeyen sürüm ve dosya erişim hatası onarım yetkisi değildir; onarım
  düğmesi gösterilmez. Dosya bu sırada düzelmişse başlangıç tekrar kontrol edilir,
  sağlıklı dosya yedeklenmez/sıfırlanmaz. İptal backend çağrısı yapmaz.
- Yedekleme veya yeni dosya yazma başarısızsa başarı gösterilmez. Oluşmuş yedek
  korunur; Retry kullanılabilir. Onarım normal arayüz reset'inden ayrıdır.
- Pencere açılmadan oluşan CLI hatasında run() terminal mesajı ve Windows hata
  kutusu gösterir, çıkış kodu 1 olur. Ham exception içeriği kullanıcı mesajına
  eklenmez; başlangıç hatası otomatik veri sıfırlaması yapmaz.

## Restart, arayüz sıfırlama ve always-on-top

- Payload'sız `restart` core'u durdurur ve native pencereyi kapatır. main, GUI
  döngüsü/worker kapanınca aynı Python + app.main ile yeni süreç açar; mevcut
  TASKVEX_HOME ve debug seçimi korunur. UI'dan executable/argüman alınmaz.
  Settings > System içindeki Restart app ve eski Restart düğmesi bu yolu kullanır.
- `ontop:boolean` gerçek pencereye anlık uygulanır; doğrulanmayan istekte checkbox
  önceki konumuna döner. Kalıcılık mevcut Save modelindedir. Kayıtlı onTop hem
  başlangıç snapshot'ında hem Save/import sonrası native pencereye uygulanır.
- Payload'sız `reset` yalnız tema/renk, layout, SFX/ses, wake/noise, onTop, compact
  görünüm ve aktif ayar sekmesini varsayılana döndürür. Profil, cihaz/model/ses
  tercihleri, yerel not/skill/rutinler ve core notes.json korunur. Düğme onay sorar.
  Backend kayıt/read-back onayı ve snapshot gelmeden yerel kayıt silinmez.
  Snapshot loadStore ile no-echo uygulanır; sayfa yenilenmez. Browser-only yolda
  aynı alanlar yerel olarak sıfırlanır, koleksiyonlar/profil korunur.
- WinForms on_top setter'ı GUI thread'inde Invoke ile çalışır; API thread'inden
  doğrudan kontrol değiştirilmez. Gerçek native test bu sınırı da kapsar.

## Native pencere ve görünüm güncellemesi — 21 Ekim 2026

- Varsayılan tema ve idle reactor rengi `#a78bfa` (mor). Kayıtlı tema/renkler
  önceliklidir; güncelleme kullanıcı tercihini değiştirmez.
- F11, metin alanında da payload'sız `fullscreen` olayı gönderir; backend gerçek
  pencerenin tam ekran durumunu değiştirir. Basılı tuş tekrarları yok sayılır.
  Tarayıcı-only modda tarayıcının Fullscreen API'si kullanılır.
- Native Shutdown payload'sız `shutdown` gönderir, worker kapanışı tamamlanınca
  pencere yok edilir. Eski Restart overlay'i native yolda açılmaz. Worker durmazsa
  pencere açık kalır ve hata döner; sahte kapanış onayı verilmez.
- Yerel native host, bu süreçte WebView2 autoplay argümanını ayarlar; açılış sesi
  tıklama beklemez. SFX kapalı/ses tercihi korunur. Tarayıcı ses politikası değişmez.
- Reactor idle dahil 60 FPS çizim hedefler; 60/90/120/144 Hz zamanlamalarıyla
  test edildi. Gerçek FPS donanım, yük ve arka plan sınırlamalarına bağlıdır.

## İlk gerçek native dilim — 21 Ekim 2026

`python -m app.main` mevcut UI'ı PyWebView/EdgeChromium ile açar. Public Python
API yalnız `event(name,data)` içerir. Desteklenen olaylar: `ui_ready:{version:'1.0'}`,
izinli ayar alanlarını içeren `save`, ve payload'sız salt okunur `system_status`.
Başarılı save `{ok:true,completed:true,saved:true}` döndürür. Hatalı kayıt veya
desteklenmeyen olay `{ok:false,error:string}` döndürür; hata metni sır içermez.

Native hazır bildirimi model bağlantısı değildir; UI `MODEL OFFLINE` gösterir.
Başlangıç snapshot'ı not/skill/rutin koleksiyonlarını içermez; mevcut yerel veri
korunur. initApp/loadStore, uygulanan snapshot'ın boolean sonucunu geri döndürür.
Generic save bu koleksiyonları veya credential alanlarını backend'e yazmaz.
CPU/RAM kullanım yüzdeleri ölçülmediği için null; OS bilgisi gerçek core aracındandır.

`saveAll()` senkron yerel boolean sözleşmesini korur. Açık Settings/Profile Save
düğmeleri `saveSettingsConfirmed()` ile native completed/saved onayını bekler;
hata/eksik onayda modal açık kalır. Tarayıcı/fallback modu mevcut yerel davranışı
korur. Otomatik kayıt/import ayrıntıları yukarıdaki tek kayıt kuyruğu bölümündedir.
Desteklenmeyen skill/routine yürütme ve cihaz/model/Google
olayları açık ret alır; yerel UI davranışı fiziksel native başarı sayılmaz.

[Aşama 2 planı, test ve sınırlar](../../../docs/STAGE2_NATIVE.md).

## Not olayları — 21 Ekim 2026

Kullanıcı not ekleme/tamamlama/silme eylemleri yerel depolamayı `saveAll({emitSave:false})` ile günceller; yalnız ilgili `note_add`, `note_done` veya `note_del` mutasyon olayını bir kez gönderir. Bu eylemler ayrıca tam `save` üretmez. Timeline gibi görünüm olayları ayrı olabilir; not mutasyonu değildir. Backend `addNote`/`setNotes` çağrıları outbound not veya save üretmez.

Bu bölümün eski payload'ları yalnız tarayıcı-only modda korunur: note_add metin,
note_done `{t,d}`, note_del metin. Native sürümlü zarfı üstteki Aşama 3 bölümü
tanımlar. Açık Settings Save koleksiyon içerse de backend bunu ikinci bir not
mutasyonu saymaz. Native yedek restore yalnız notes_replace aracından geçer.

Tarayıcı-only yol backend doğrulaması sağlamaz. Native'de doğrulanmış sonuç,
sabit kimlik ve tek seferli ilk aktarım vardır; kalıcı genel görev günlüğü yoktur.

## UI hazırlık kapanışı: bekleme ve ses yaşam döngüsü

- Kamera ve konum işlemleri en fazla 12 saniye nihai yanıt/bildirim bekler. Süre dolması başarı veya başarısızlık kanıtı değildir: UI **durum bilinmiyor** gösterir; eski Promise yanıtını geçersiz kılar. Aynı düğmeye sonraki basış fiziksel işlemi tekrar etmez, yalnız durum sorgular.
- Yeni salt okunur olaylar `query_camera:null` ve `query_location:null`. Backend, önceki işlemin hâlâ çalışıp çalışmadığını da bildirmelidir. Kamera için `{pending:false,active:boolean}`, konum için `{pending:false,saved:boolean,name?,error?}` kesin durumdur. Yalnız `{ok:true}`, `pending:true` veya sadece active/saved alanı sorgu yolunda yeniden işlem izni vermez. Backend bu olayları desteklemiyorsa UI bilinmiyor durumunu korur ve yeniden sorgulanabilir; sahte başarı veya otomatik işlem tekrarı üretmez.
- Backend'den `setCamera(boolean)` / `setLocation(...)` nihai bildirimleri belirsiz durumu da sonlandırabilir. RequestId'siz protokolün sıralı otoritatif bildirim şartı devam eder. Sayfa gizlenirken bekleyen işlem başarıya/idle'a çevrilmez.
- `weather(undefined)` veriyi korur; `weather(null)` sıcaklık, açıklama ve ek alanları bilinmiyor durumuna temizler.
- `setSfxConfig` sonlu olmayan veya sayı olmayan ses seviyesini 0.8'e düşürür; sonlu sayıları 0–1 aralığına sınırlar. Snapshot'ta yanlış tip hâlâ reddedilir.
- `attachAudio` tek, paylaşılan reactor AudioContext kullanır; aynı HTMLMediaElement için MediaElementSource tekrar oluşturulmaz. Kaynak değişiminde eski graph ayrılır. `detachAudio()` yalnız reactor node bağlantılarını bırakır; çağıranın sahip olduğu MediaStream track'lerini durdurmaz. Backend kaynak sahibiyse track'leri kendisi sonlandırmalıdır. Shutdown graph'ı ayırır; sayfa gerçekten terk edilirken context kapatılır. BFCache için gizlenmede graph ayrılır ve tekrar kullanılabilir context korunur.
- Kullanılmayan `window.vex.eval` / `window.jarvis.eval` kaldırıldı. Mevcut kaynakta çağıranı bulunmadı. Harici eski bir backend bunu kullanıyorsa entegrasyon sırasında izinli native evaluate_js yoluna taşınmalıdır.
- Cihaz tercihi mevcut Save Settings modelini korur; seçim anındaki backend cihaz olayı anlık tercihtir, tarayıcı kalıcılığı için Save Settings gerekir.

## Bağımsız denetim sonrası ek kurallar

- Snapshot içinde tüketilen ek panellerin alanları da önceden doğrulanır: takvim, hatırlatıcı, timeline, cihaz, katalog, ölçümler ve ilgili ayar türleri. Geçersiz snapshot mevcut canlı/kalıcı veriyi değiştirmeden reddedilir. Depolamanın kendisinin başarısız olması ayrıca görünür hata üretir.
- Eksik skill/rutin kimlikleri çakışma denetimli UUID (desteklenmiyorsa sayaçlı fallback) alır. Aynı listede yinelenen açık kimlikler reddedilir; geçerli mevcut kimlikler korunur. Doğrudan koleksiyon setter'ları da bu sınırı kullanır.
- Yerel kayıt kurtarma alan bazındadır: geçersiz alan/kayıt atlanır, geçerli notlar korunur. Bozuk colors null değeri güvenli boş haritaya döner. Eski timeline kayıtları da doğrulanır.
- Backend `setLocation` bildirimi yerel kaydı güncelleyebilir fakat outbound save veya onSave üretmez. Kullanıcı kaynaklı tamamlanma ayrı kayıt yolunu kullanır.
- Native onEvent gözlemcisinin Promise tamamlanması emit sonucunu bekletmez; reddi ayrıca yakalanır. Fallback gerçek taşıma olduğu için onun tamamlanması beklenir.
- ui_ready gönderilmeden önce kamera handler state'i kuruludur. Senkron hazır callback'i tarayıcı testinde desteklenir; gerçek native teslimat ayrıca doğrulanmalıdır.
- Konuşma zamanlayıcısı yalnız kendi state sürümü geçerliyken idle yapabilir. Restart eski shutdown zamanlayıcılarını ve closed olayını iptal eder.
- startTimer(0) sayacı READY/00:00 durumuna sıfırlar. Geçersiz, negatif veya sonlu olmayan süre çalışan sayacı değiştirmez. Parametre verilmemesi mevcut süreyi kullanır.
- Açık boş model/ses listesi menüyü temizleyip devre dışı bırakır; eksik liste korur. Kaydedilmiş tercih gelecekte geçerli katalogda yeniden seçilebilir.
- Skill/rutin formunda kalıcılık başarısızsa bellek değişikliği geri alınır ve form korunur; tekrar deneme çift kayıt oluşturmaz. Ayar/profil modalı başarısız kayıtta açık kalır.
- Modallar dialog semantiği, arka plan inert durumu ve odak sınırı kullanır. Açılış animasyonu görünür olduğunda odak yerleştirilir; Escape kapanışı ve modal geçişleri önceki odağı doğru geri verir.

## Taşıma ve başlangıç

`window.vex === window.jarvis`. Native taşıma `window.pywebview.api.event(name, data)`; native yoksa `onEvent(name, data)` alternatifidir. Native varken onEvent yalnız gözlemci olarak çağrılır; onu ikinci bir yürütücüye bağlamayın. Gözlemci reddi native gönderimi tekrar ettirmez.

`ui_ready: {version:'1.0'}` global bridge hazır olduktan sonra, native erken veya geç yüklenmiş olsa da bir kez gönderilir. Bu model oturumunun çevrimiçi olduğunu belirtmez. Backend `online(boolean, text?)` ile model durumunu bildirir.

`emit` Promise sonucu `{ok, error, response}`. `false`, `{ok:false}` veya `{success:false}` açık başarısızlıktır; atılan hata ve Promise reddi yakalanır. Diğer yanıtlar taşımanın/isteğin kabulüdür; işlem tamamlandı anlamına gelmez. Hata metinleri ekrana yazılırken bilinen anahtar/token desenleri maskelenir; backend hata mesajlarına gizli bilgi koymamalıdır.

## Snapshot ve koleksiyonlar

`initApp(snapshot)` ve `loadStore(snapshot)` aynı doğrulama/normalizasyon hattını kullanır. notes, skills, routines için eksik/undefined alan mevcut veriyi korur; null temizler; dizi değiştirir. Geçersiz kayıt tüm snapshot'ı uygulanmadan reddeder. Başarılı toplu güncelleme tek kayıt adımı kullanır. Backend kaynaklı güncelleme outbound save üretmez; kullanıcı yedek import'u bir save üretir. Depolama hatası görünür olur ve save gönderilmez; bu durum canlı UI'ın kalıcılaştırıldığı anlamına gelmez.

Doğrudan metotlar: `addNote(text)`, `setNotes(array)`, `setSkills(array)`, `addSkill(object)`, `skillResult(id,ok)`, `setRoutines(array)`, `routineResult(id,ok)`, `routineEvent(type,value)`, `setTimeline(array)`. Snapshot doğrulamasının yerini doğrudan setters'ın alacağı varsayılmamalı; backend geçerli sözleşmeye uymalıdır.

Skill steps: nesne dizisi. Boş dizi geçerli; null/nesne/metin/sayı formda geçersizdir. Her adımın step_type değeri open_app, interact_element, hotkey, type_text veya wait olur. Verildiyse target/text/action/app_name metin, press_enter boolean, wait_after sonlu ve negatif olmayan sayıdır. Backend ayrıca araca özgü gereksinim ve izinleri doğrular; bu UI şeması yürütme yetkisi değildir. Snapshot sınırı eski JSON metnini parse ederek aynı dizi sözleşmesine çevirir. Yeni form kaydı çakışmayan kimlik alır; edit akışı mevcut kimliği korur.

## Kamera, konum, iptal

- `camera: boolean`: eski payload korunur. Yalnız kabul/undefined yanıtında bekler. `active` hedefle eşleşirse veya ters active olmadan completed:true verilirse tamamlanır. boolean true kamera açma için eski tamamlanma yanıtıdır. Nihai backend durum bildirimi `setCamera(boolean)`.
- `location: {name,auto:false}` veya `{auto:true}`. saved:true veya saved:false olmadan completed:true tamamlanma bildirir; yalnız ok:true beklemedir. Nihai bildirim `setLocation({saved,name,error?,completed?})`; eski string bildirimi kaydedilmiş ad olarak desteklenir. Yalnız name alanı tamamlanma değildir.
- Kamera ve konumda aynı anda bir kullanıcı isteği bekler; otomatik ve manuel konum aynı kilidi paylaşır. Nihai bildirim beklemeyi bitirir ve önceki Promise yanıtını geçersiz kılar. Bildirimler requestId taşımadığından backend bunları otoritatif güncel durum sırasıyla göndermelidir; eski bağımsız push'ların kimlikle ayırt edilmesi bu eski protokolde yoktur.
- `stop_task`: ok:true iptal talebinin kabulüdür. UI görev aktifken idle göstermez. stopped:true/state:'idle' yanıtı veya `setState('idle')` nihai durumu bildirir. Nihai bildirim gelmezse 12 saniye sonra durum bilinmiyor olur; kabul otomatik başarı sayılmaz. İptal düğmesi bekleme/bilinmiyor durumunda tekrar komut göndermez; görev state değeri kanıt olmadan idle yapılmaz. Bilinmiyor düğmede ve logda gösterilir. Geç gelen eski Promise yok sayılır; otoritatif `setState('idle')` kilidi kaldırır.

## Cihaz ve katalog

`setDevices({inputs,outputs,cameras})`: kayıt `{index:integer,name}` veya `{deviceId:string,label}`. İki alan da varsa geçerli index önceliklidir. Kullanıcı olayı `device:{id,index,deviceId,label}`; index ve deviceId alanlarından yalnız biri doludur. index=0 geçerlidir; rakamlardan oluşan deviceId metin kalır. Seçim kimlikleri store.devs içinde korunur.

`setCatalog({models,voices,currentModel?,currentVoice?})`: model/ses listesi kayıtlarında id ve name kullanılır. Seçim önceliği geçerli backend aktif tercihi → geçerli kayıtlı tercih → ilk seçenek. Placeholder kimlik olarak kaydedilmez.

## Ölçümler ve offline kapsamı

`telemetry({cpu,gpu,ram,cpuT,gpuT,ramTxt,bat,disk,win})` ve `network({ping,down,wifi,api})`: undefined/eksik alan korur; açık null ilgili alanı '—' yapar; sonlu sıfır geçerlidir. Tüm nesne null ise o grubun tüm alanları temizlenir. Sayısal alanlara geçersiz tür gelirse ölçüm bilinmiyor gösterilir.

`online(false)` model/API oturumunun kapandığını söyler: API gecikmesi ve token bilgisi geçersizleşir. Yerel CPU/GPU/RAM ve Wi-Fi ölçümlerini silmez. Fiziksel internet/ping/download kaybını backend ayrı `network({ping:null,down:null,...})` alanlarıyla bildirir. `tokens(used,max,isEstimated)` içindeki kullanılan 0 geçerlidir.

Diğer görüntü metotları: weather, media, setCalendar, setReminders, googleStatus, screen, task, taskDone, msg, streamMsg, streamReset, say, user, log. Bunların çağrılması ilgili dış işlemin yapıldığına UI dışından kanıt sağlamaz.

## Scheduler sahipliği

Zaman tabanlı rutin denetimi UI içinde 15 saniyede, takvim uyarı taraması 30 saniyede çalışır. Backend kendi scheduler'ını başlatmadan önce `window.vex.stopRoutineScheduler()` ve takvim uyarılarını da devralacaksa `window.vex.stopCalendarScheduler()` çağırmalıdır. Metotlar tekrar çağrılabilir; outbound olay üretmez. ES modüllerinden aynı adlarla export edilir. Durdurma sayfanın ömrü boyunca geçerlidir; yeniden yüklemede backend sahipliği tekrar kurmalıdır. Normal pagehide döngüleri temizler; BFCache geçişi zamanlayıcıları korur (tarayıcı dondurur/geri yükler). Manuel rutin çalıştırma ve routineEvent etkilenmez. Backend tarafında tetikleme kimliğiyle tekrar önleme entegrasyonda ayrıca uygulanmalıdır.

## Yerel depolama

Ayarlar yalnız `taskvex_ui`, timeline `taskvex_tl` anahtarına yazılır. `jarvis_ui` yalnız birincil kayıt yoksa eski veriyi okumak için kullanılır; normal save ve snapshot bu anahtarı yazmaz. Mevcut eski kayıt silinmez; reset iki ayar anahtarını da temizler. Yerel depolama gizli bilgi kasası değildir. Yazma/silme hatası görünürdür; localStorage'a üretim API anahtarı koymayın.

## Dosya ekleme

`file` artık dosya adı string'i yerine `{name:string,type:string,size:number,encoding:'base64',content:string}` taşır. content ham dosya baytlarının Base64 karşılığıdır; data URL öneki içermez. Boş dosya geçerlidir; MIME türü boş olabilir. UI sınırı 10 MiB'dir; daha büyük dosya gönderilmez ve görünür hata oluşur. Backend bu yeni payload'ı desteklemeli, türleri, Base64 geçerliliğini, çözülmüş bayt uzunluğunu ve boyut sınırını tekrar doğrulamalıdır. Dosya adı bir yerel yol veya yazma yetkisi değildir; güvenilmeyen girdi olarak ele alınır. Kabul analizin tamamlandığı anlamına gelmez. Okuma/taşıma reddinde başarı mesajı gösterilmez; aynı dosya yeniden seçilebilir. Projede henüz bu olayı işleyen Python backend yoktur.

## Kaynaktan çıkarılan olay ve metot envanteri

Bu liste sabit isimli emit çağrılarını gösterir; payload kuralları yukarıdaki bölümlerde ve ilgili handler kaynaklarında tanımlıdır. Yeni backend bu envanteri uygulama yetkisi olarak değerlendirmemelidir.

| UI → backend olay | Çağıran modüller |
|---|---|
| apikey / query_apikey | credentials.js |
| audio_listening | app.js |
| cal_soon | connections.js |
| camera | app.js |
| closed | app.js |
| device | settings.js |
| disconnect | app.js |
| drawer | panels.js |
| file | app.js |
| google_connect | connections.js |
| inspect | skills.js |
| layout | settings.js |
| location | connections.js |
| media | connections.js |
| mic | app.js |
| model | connections.js |
| mute | app.js |
| noise | settings.js |
| note_add | notes.js |
| note_del | notes.js |
| note_done | notes.js |
| ontop | settings.js |
| query_devices | settings.js |
| reconnect | api.js |
| reset | settings.js |
| restart | app.js |
| routine_delete | routines.js |
| routine_save | routines.js |
| run_routine | routines.js |
| run_skill | skills.js |
| save | settings.js |
| screen_share | panels.js |
| shortcut | panels.js |
| shutdown | app.js |
| skill_delete | skills.js |
| skill_save | skills.js |
| stop_task | app.js |
| text | app.js |
| timeline | panels.js |
| timeline_clear | panels.js |
| ui_ready | api.js |
| voice | connections.js |
| wake_sens | settings.js |

| Backend → UI metot | Argümanlar |
|---|---|
| msg | c, t |
| streamMsg | c, t |
| streamReset |  |
| detachAudio | — |
| say | t |
| user | t |
| log | t, l4 |
| setState | k |
| level | v |
| micLevel | v |
| setAudioListening | d |
| attachAudio | src |
| wake |  |
| wakeWait | on |
| startTimer | s |
| pauseTimer |  |
| resumeTimer |  |
| resetTimer |  |
| startStopwatch |  |
| pauseStopwatch |  |
| stopStopwatch |  |
| resumeStopwatch |  |
| resetStopwatch |  |
| telemetry | o |
| tokens | u, m, isEst |
| network | o |
| weather | o |
| media | o |
| setCalendar | a |
| setReminders | a |
| setCamera | active |
| setLocation | d |
| setDevices | d |
| setCatalog | c |
| googleStatus | s |
| screen | d |
| initApp | snapshot |
| loadStore | o |
| task | id, t |
| taskDone | id, ok, t |
| addNote | t |
| setNotes | a |
| setSkills | a |
| addSkill | o |
| skillResult | id, ok |
| setRoutines | a |
| routineResult | id, ok |
| routineEvent | type, val |
| stopRoutineScheduler | — |
| stopCalendarScheduler | — |
| action | x, ok, k |
| setTimeline | a |
| online | ok, txt |
| reconnecting | n |

