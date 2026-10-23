# TaskVex — Kullanıcının katılacağı gerçek kullanım kontrolleri

## Güncel kısa test — 5.R6 toplu not tamamlama

Uygulamayı yeniden aç; yalnız deneme notları olan test profilinde dene.

1. Üç farklı geçici not ekle, tarihlerini listele. “Son iki notumu tamamlandı
   işaretle” de: yalnız yeni iki kaydın kutusu işaretlensin; metin/ID/tarih korunsun.
2. “Tüm notlarımı tamamla” de; hepsi işaretlensin. “Tüm notlarımı tamamlanmadı
   işaretle” ile kutular boşalsın. Kapat/aç; son durum korunsun.
3. İki notun metninde “deneme”, diğerinde farklı içerik olsun. “İçinde deneme
   geçen notların hepsini tamamla” de; yalnız bu grup işaretlensin.
4. Aynı metinli iki not için tek notu tamamlama isteğinde açıklama istesin;
   sessizce ikisini tamamlamasın. Açık gerçek ID grubuyla yalnız o grup değişsin.
5. Engine log'da notes.select ardından notes.complete_many verified görülmeli.
   İngilizce “Mark my last two notes as completed” gibi bir ifade de dene.

REST ve Live sentetik/native kontrolleri ajan tarafından yapılır. Gerçek
sağlayıcının yeni şemayı kabulü ve dil yorumu kullanıcı tarafından başarılı
bildirildi (23 Ekim 2026). Bu sonuç tüm gelecek ifadelerin garantisi değildir.

## Önceki kısa test — 5.R5 not seçimi / toplu silme

Uygulamayı yeniden aç. Gerçek notlarının olmadığı, yalnız geçici notlarla dolu
bir test profili kullan; özellikle tümünü sil komutu o profilde denenmelidir.

1. Üç farklı deneme notu ekle. “En son eklediğim iki notu sil” de: yalnız
   iki yeni kayıt silinsin, kalan not UI'da korunsun. Kapat/aç ile doğrula.
2. İçinde “merhaba” geçen tek not oluştur. “İçinde merh geçen notu tamamlandı
   işaretle”, sonra metnini değiştir ve sil. Sabit ifade veya tırnak zorunlu değil.
3. Aynı metinli iki geçici not ekle. Tekini metinle silme isteğinde açıklama
   istesin ve ikisini korusun. Gerçek ID ile seçtiğinde yalnız o silinsin.
4. Birden fazla geçici “test” notuyla “İçinde test geçen notların hepsini sil”
   de: yalnız seçilen grup silinsin. Sonra test profilinde “Tüm notlarımı sil”
   de; panel ve yeniden açılış boş olsun. İngilizce karşılıklarını da deneyebilirsin.
5. Engine log'da notes.select ardından notes.delete_many görülmeli. Sözlü
   başarı, tool verified sonucu olmadan işlem kanıtı değildir. Notlar seçim
   sırasında değişirse tekrar seçmeni istemeli; otomatik hedef değiştirmemeli.

Stop yalnız yazıdan önce silmeyi önleyebilir; tamamlanmış silmeyi geri almaz.
Şüpheli sonuçta aynı komutu tekrar göndermeden notları listele. 5.R5 kullanıcı tarafından başarılı bildirildi ve `2120113` commit’ine alındı.

## Önceki kısa test — 5.R4 model araçlı uyku

Uygulamayı tamamen kapatıp yeniden aç, normal uyku süresini geçici olarak 0
yap. Yalnız yeni yerel test kabulüdür; gerçek hesap denemesi ajan tarafından yapılmadı.

1. “Uyku moduna kalıcı olarak gir” de/yaz. Engine log'da
   `assistant.request_sleep_mode: succeeded · verified` görülmeli; Vex'in kendi
   yanıtı ve çalması bitince SLEEPING olmalı. Bu kayıt isteğin kabulüdür;
   gerçek SLEEPING ayrı host sonucudur.
2. Uyandırıp kısa soru sor: cevap bitince tekrar uyusun. Sonra yazıyla
   “Disable persistent sleep mode” de; yanıt bittikten sonra tercih kapansın.
3. “Bir süre bekle, yalnız çağırdığımda cevap ver” gibi kendi doğal ifadenle
   tek seferlik uyku iste. Kip belirsizse soru sormalı; sözü başarı kanıtı değil.
4. “Uyku modu ne işe yarıyor?”, “Uykuya geçme” ve alıntılı bir uyku cümlesi
   anlatma isteğinde uyumamalı. Yanlış araç seçerse bildir; regex yaması eklenmez.
5. Uyku yanıtını Stop ile kes: bekleyen geçiş uygulanmasın. Sleep/Wake
   düğmesi ve Mic On/Off eskisi gibi çalışsın.

Araç çağrısı olmadan yalnız “geçiyorum” derse host uyumaz; modelin aracı
seçmemesi ayrı bir kabul hatasıdır. Durum satırını ve araç kaydını paylaş.

## Önceki kısa test — 5.R3 doğal yanıt ardından uyku

Uygulamayı yeniden aç; uyku süresini geçici olarak 0 yap.

Yeni varyant kontrolü: “Kalıcı uyku moduna geç” → yanıt ardından uyku;
uyandırıp kısa görev ver → tekrar uyku. Ardından yazıyla “Disable persistent
sleep mode” → yanıt ardından tercih kapansın. “Stay asleep” ile yeniden aç;
“Kalıcı uyku modundan çık” ile kapat. İngilizce ses testi için yanıt dilini
English seç; dil ayarı yanıt dilidir, araç izinlerini değiştirmez.

1. “Uyku moduna geç” de. Vex kendi sesiyle kısa yanıtını tamamlasın; ancak
   ardından SLEEPING olsun. Ayrı mekanik ses veya ikinci sabit mesaj olmamalı.
2. Uyandır, “Bundan sonra uyku modunda kal” de. Yanıt bittikten sonra uyusun;
   uyandırıp görev verince görev/yanıt sonrasında otomatik geri uyusun.
3. “Kalıcı uyku modunu kapat” de/yaz: kendi yanıtı bitsin, uyanık kalsın.
4. Uyku yanıtını Stop ile kes: bekleyen uyku komutu uygulanmasın. Sleep
   düğmesi doğrudan uyutsun; Mic Off yanıt sesini kesmesin.

5.R2 kullanıcı tarafından başarılı bildirildi; aşağıdakiler tarihsel testlerdir.

## Önceki kısa test — 5.R2 sesli tur sınırı

Uygulamayı tamamen kapatıp `v1` içinden yeniden aç:
`./.venv/Scripts/python.exe -m app.main --debug`.
Önce uyku zamanlayıcısını geçici olarak 0 yap; aynı Live modelinde:

1. Yazıyla “Merhaba” gönder: kontrol olarak yanıt gelsin.
2. Mic On ile “Merhaba, nasılsın?” de, ardından sessiz kal. Art arda üç ayrı
   sesli turda yanıt, transkript ve yeniden dinlemeyi kontrol et.
3. Sleep → “Vex, merhaba” ile uyan; ardından yeni bir soru sor.
4. Bir yanıtı Stop ile kesip yeniden konuş. Mic Off yalnız girişi kapatmalı.

Tekrar takılırsa durum satırının tamamını paylaş: PCM sent, events,
before/after input final, **input end: sent/missing**, **speech chars**.
Bu test geçmeden 5.R2 kapanmış veya yeni özellik sırası açılmış sayılmaz.
Otomatik 921 pytest/7 JS/10 native gerçek mikrofon/API kabulü yerine geçmez.

## Önceki kısa test — 5.R1 birleşik kararlılık

Uygulamayı yeniden aç; normal Idle sleep timer'ı 0 yap. Önce TR dilini seç.

1. “Uyku moduna gir” de/yaz. Gerçek SLEEPING sonrası “Uyku moduna geçtim”
   hem yazılmalı hem duyulmalı. Bu kısa onayın sesi Gemini'den farklıdır.
2. “Vex” diyerek uyandır, kısa bir soru sor; üç döngü dene. Sonra uzun bir
   yanıta araya gir; yanıt bitince normal sesin yeni istek olarak alınmalı.
3. “Kalıcı olarak uyku moduna gir”, ardından uyandırıp kısa soru ve yazılı
   “Kalıcı uyku modunu kapat”. İlk açılış/kapanış sesleri duyulmalı; her
   otomatik geri uyumada tekrar onay beklenmez. Mic Off yanıtı kesmemeli.
4. Mute açıkken aynı kontrol: metin/durum doğru, ses kapalı olmalı. Wake veya
   Stop onay sesi çalarken kullanılabilir; eski ses sonra geri başlamamalı.
5. Takılırsa Engine log'daki **ilk Microphone capture** nedenini ve durum
   satırını paylaş. Stopped tek başına neden değildir. “Input discarded…”
   sonrası yeni dinleyici hazırlanır; kaybolmuş isteği kendin tekrar söyle.

Fiziksel mikrofon, gerçek sağlayıcı ve oda/yankı kabulü henüz yok; 920 pytest,
7 JS, native ve yapay gerçek KWS geçişleri bunların yerine geçmez. Sabit 700 ms
sessizlik uzun düşünme duraklamasını yeni tur sınırı yapabilir. Uyanışta yeni
Live bağlantısı hâlâ kurulur; toplam gecikme garantisi verilmez. Sorun sürerse
F4/new feature eklenmeden bu ölçümler üzerinden aynı yol incelenecek.

## Güncel kısa test — 5.F3

Önce normal Idle sleep timer'ı 0 yap; sonraki testleri yanlışlıkla timer uyutmasın.

1. Uyanıkken “Uyku moduna gir” yaz; SLEEPING olmalı. Wake ile uyandırıp
   aynı sözü sesli dene; Vex hitabı zorunlu olmamalı.
2. “Kalıcı olarak uyku moduna gir” de. Uyandırıp kısa bir soru sor;
   gerçek yanıt ve ses bitince tekrar uyumalı. “Kalıcı uyku modunu kapat”
   yazıp yeni kısa sorudan sonra uyanık kaldığını kontrol et.
3. “Uyku moduna girme”, “Uyku moduna gir ne demek?” ve tırnak içinde
   `"uyku moduna gir"` yaz. Hiçbiri uyutmamalı. İngilizce karşılıklar:
   “Please switch to sleep mode”, “Return to sleep after every task”,
   “Stop returning to sleep”.

Ses alınmıyorsa aynı ifadeyi yazılı dene: niyet ayrımını giriş canlılığından
ayırır. F2 fiziksel uyanış/25 s bildirimi ve F4 yerel telaffuz hâlâ açıktır;
bu adım bunları düzeltmiş sayılmaz. Yeni testler geçmeden commit yok.

## Güncel kısa test — 5.F2

1. Uygulamayı kapatıp yeniden aç; Idle sleep timer'ı 0 yap. Sleep düğmesiyle
   uyut, “Vex” diyerek uyandır ve kısa bir soru sor. Bunu üç kez dene.
2. Uyanıp komut almıyorsa önce durum satırını kaydet. Microphone Off/On
   yapıp aynı kısa soruyu yeni istek olarak sor; toparlanıp toparlanmadığını bildir.
3. 25 s bekleme tekrarlanırsa durum satırındaki `PCM sent`, `events`,
   `before_input_final` / `after_input_final` bilgisini paylaş. Anahtar veya
   kişisel not/ses paylaşma. Motor toparlanamazsa “audio engine did not resume”
   açıkça görünmeli; On ışığı kullanıcı tercihi olduğu için yanmaya devam eder.

Fiziksel uyanış sorunu açık tutuluyor. 853 pytest ve sentetik/native test
gerçek mikrofon/sağlayıcı kabulünün yerine geçmez. “Uyku moduna gir” ve
Rex/X varyantları hâlâ F3/F4'tür; bu test Sleep düğmesini kullanır.

## Güncel kısa test — 5.F1

Uygulamayı yeniden aç; testte Idle sleep timer'ı önce 0 yap.

1. Sleep düğmesine bas: önce kısa Preparing sleep, kabul sonrası SLEEPING
   ve Wake olmalı. Uykuda Mic Off yapıp Wake'e bas: Mic Off korunmalı.
2. On ile tekrar Sleep yap. Yalnız “Vex” de, ardından kısa duraklayıp
   “Bana kısa bir selam ver” de. Asıl istek alınmalı. Wake sözcüğü tek başına
   kalıcı modda bir görev bitmiş gibi hemen yeniden uyutmamalı.
3. Mevcut tanınan “Vex bundan sonra uyku modunda kal” ile kalıcı modu aç;
   uyandırıp kısa istek ver. Gerçek yanıt ve ses bitince hemen uyumalı.
   Normal modda 3 s timer ise yalnız idle'da tek seferlik uyutmalı.

Bu tur “uyku moduna gir” listesi veya Rex/X algısı genişletilmedi. Özellikle
bu ifadelerle test edip 5.F1'in bunları düzelttiği sonucunu çıkarma; 5.F3/5.F4
açık. 25 s Thinking veya Idle'da ses almama tekrarlanırsa durum satırını
bildir; 5.F2'nin kapsamıdır. Gerçek hesap/mikrofon kabulü bu kısa testle
beklenir; otomatik/sentetik kanıt fiziksel başarının yerine geçmez.

## Güncel durum — yeni kabul istemeden önce açıkları kapat

Kullanıcının “uyku moduna gir” ve “kalıcı olarak uyku moduna gir” örnekleri
host parser'ında reddediliyor. İçeride çift boşluk da eşleşmeyi bozabiliyor.
Bunlar kullanıcı kullanım hatası değildir. Beş somut runtime açık için
[denetim](STAGE5_SLEEP_AUDIT.md) ve [güncel sıra](../aşamalar.md) tutuluyor.
Bu tur kullanıcıdan önceki testleri tekrar etmesi istenmiyor; düzeltme sonrası
ilgili açıkları hedefleyen kısa fiziksel kabul verilecek. Eski başarılı
native/pytest sonuçları bu bug'ları çözülmüş saymaz.

## Güncel test — düzeltme planı adım 1 / iki bağımsız uyku

1. Önce Ayarlar → Audio → Idle sleep timer değerini 0 yap. “Vex bundan sonra
   uyku modunda kal” de; uyandırıp kısa bir soru sor. Yanıt/ses biter bitmez
   tekrar SLEEPING olmalı. 10 saniye beklememeli. Yanıt sürerken konuşman
   ikinci bir görev/interrupt başlatmamalı; yeni görev için tekrar uyandır.
2. Uyandırıp “Vex uyku modundan kalıcı olarak çık” de. Süre 0 iken normal
   konuşmada uyanık kalmalı. Sonra Idle sleep timer'ı 3 yap: boşta üç saniye
   sonra tek seferlik uyumalı. Vex ile uyandırıp normal soru sorabilmelisin;
   kalıcı moda kendiliğinden geçmiş olmamalı.
3. Normal modda uzun yanıt iste: ses sürerken üç saniye geçti diye uyumamalı.
   Mikrofonu Off yapmak tercihini değiştirmemeli; Wake düğmesi kullanılabilir.

25 s Thinking ve Idle'da algılamama hâlâ ikinci adımda incelenecek. Rex/X wake
ve liste dışı uyku niyeti henüz eklenmedi. Bu testlerde mevcut tanınan ifadeyi
kullan. Telegram işlemi henüz entegre değil; gizlilik senaryosunu mevcut
kısa yanıt veya geçici bir test notu göreviyle dene. Gerçek mikrofon kabulü
sentetik/native testin yerine geçmez. Alttaki eski testlerde timer'ın Stay
asleep'e bağlı anlatımı bu güncel adım tarafından değiştirilmiştir.

## Güncel kısa test — kalıcı uyku / süre / efekt sesi

Önceki wake/giriş testlerini başarılı bildirdin (`701f33f`). Yeni dilim:

1. Ayarlar → Audio → Automatic return-to-sleep delay alanına 3 yazıp kaydet.
   Sound effects açıkken Microphone Off/On'a bas: kameradaki tıklama sesi
   her basışta bir kez gelmeli; On/Off davranışı değişmemeli.
2. “Vex bundan sonra uyku modunda kal” de. Uyandırıp kısa bir soru sor.
   Yanıt ve ses bittikten yaklaşık üç saniye sonra yeniden SLEEPING olmalı.
   Bunu iki kez dene. Uzun yanıt sürerken üç saniye geçti diye uyumamalı.
3. Uyandırıp “Vex uyku modundan kalıcı olarak çık” de. Sonraki yanıttan sonra
   üç saniyeden uzun bekle: tekrar uyumamalı. Normal tek seferlik “Vex uykuya
   dal” da çalışmalı; yeni sohbette kalıcı mod başlangıçta kapalı olmalı.
4. Uygulamayı kapat/aç: süre 3 kalmalı, kalıcı mod yeniden açılmamalı.
   Uyurken Mic Off ise wake sözcüğü dinlenmez; Wake düğmesi kullanılabilir.

Sentetik/native testler gerçek mikrofon, sağlayıcı ve hoparlörden efekt
 duyumunun yerine geçmez. Aşağıdaki başlıklar önceki dilimlerin kayıtlarıdır.

## Güncel tekrar test — wake yanıtı / çelişkili uyku / On–Off

Uygulamayı yeniden aç, Live ve Microphone On kullan.

1. Sleep → beş saniye bekle → yalnız “Vex” de. Kısa beklemeden sonra cevap
   veya selam isteği gelmeli; Thinking'de kalmamalı. Üç kez tekrarla. Bir turda
   “Vex, merhaba” de; sonra normal bir soru sor.
2. Sesle “Vex uykuya dal” de. SLEEPING'e geçmeli; ana bilgisayar yetkisi isteyen
   çelişkili yanıt vermemeli. “Uykuya dal ne demek?” sorusu uyutmamalı.
3. Model konuşurken Microphone Off yap: yanıt sürmeli, yeni sesin gitmemeli.
   On yapınca konuşabilmelisin. Uyku/uyanma/Stop sırasında düğmede yalnız
   Microphone On veya Off görünmeli, ışığı yalnız bu tercihi izlemeli.

Bir sorun tekrarlanırsa duyduğun yanıtı, transkripti ve durum satırını paylaş.
Native/sentetik test geçti; gerçek mikrofon ve hesap kabulünün yerine geçmez.
Alttaki Retry/Blocked düğme beklentileri eski sürümün tarihsel kayıtlarıdır.

## Güncel kısa test — yerel toparlanma / R1–R3

R0 kullanıcı tarafından başarılı bildirildi (`616125d`). Yeni dilimi sınamak
 için uygulamayı yeniden aç; Live ve Microphone On kullan.

1. Sleep'e bas, beş saniye bekle, “Vex, merhaba” de. Yanıt sonrası yeniden
   Sleep yapıp üç tur dene. Sesli “Vex, uykuya dal” da SLEEPING'e geçmeli;
   transkript Veks olursa aynı tam ifade kabul edilmeli.
2. Uykuda Mic Off yap: ışık sönmeli ve Vex demek uyandırmamalı. On yapınca
   yerel wake tekrar hazırlanmalı. Wake ile normal konuşmaya dönebilmelisin.
3. Bir hata olursa durum satırı ve log'daki kodu paylaş. Geçici yerel
   kuyruk/tampon hatasında On · Retrying, en fazla iki deneme sonrası gerçek
   engelde On · Blocked görünür. “Hazırlanıyor” yazısında sonsuza dek kalmamalı.
   Cihaz/izin hatasında cihazı düzeltip Off/On veya açık Sleep ile tekrar dene.

Geciken paket/kuyruk taşması otomatik native testte oluşturulup doğrulandı;
manuel testte bunu zorla oluşturman gerekmez. R4–R5 giriş/sessizlik hataları
henüz bu dilimde düzeltilmedi. Aşağıdaki eski test başlıkları tarihsel kayıttır.

## R0 zaman hesabı — bu adımın manuel kabulü

Uygulamayı yeniden aç. Live/Microphone On ile Sleep düğmesine bas; beş saniye
sessiz bekle, "Vex, merhaba" de. Yanıt ve normal dinleme geri gelmeli. Bunu
üç kez tekrarla; bir denemede 65 saniye bekle. "Local wake microphone failed"
olursa durum satırı ve engine log'u kaydet. Bu testi uyku düğmesiyle yapmak,
henüz düzeltilmemiş Veks transkripsiyonu sorununu zaman testinden ayırır.
Mic Off iken Wake'e basmak mikrofon tercihini On yapmamalı. Henüz R2–R5
hata toparlanması/giriş sınırları tamamlanmış sayılmaz.

## Uyku düzeltmesinin tekrar kabulü

Uygulamayı yeniden aç. Live ve Microphone On ile "Vex uykuya dal" veya
"Vex uyku moduna geç" de; SLEEPING görünmeli. Asleep iken "Vex, merhaba"
de; yanıt bekle. Olmazsa Wake'e bas: normal dinleme geri gelmeli. Mic Off
iken Wake'e basmak mikrofonu kendiliğinden On yapmamalı.
Ayarlar → Tema içinde SLEEPING rengini değiştirip kaydet; uyurken rengi
gör ve yeniden açılışta korunduğunu denetle. Wake sözcüğü profilde kalır.
Sesle uyandırma hâlâ olmazsa Asleep durum satırını ve engine log hatasını
bildir; İngilizce sözlük tabanlı yerel motor fiziksel telaffuz kabulü bekler.

## Güncel kısa test — tek seferlik uyku / wake-word

Önceki Stop gösterge testleri kullanıcı tarafından başarılı bildirildi
(515a531). Yeni uyku dilimi manuel kabul bekler. Uygulamayı yeniden aç,
Live modelini yükle ve Microphone On kullan.

1. "Vex uyku moduna geç" de veya Sleep'e bas. Asleep / LOCAL WAKE görünmeli.
   Vex demeden konuş; cevap/model turu başlamamalı.
2. "Vex, bana kısa bir selam ver" de. Aynı cümledeki istek cevaplanmalı.
   Ardından Vex demeden başka soru sor: normal konuşma devam etmeli; bu
   tek seferlik uykudur, kendiliğinden tekrar uyumamalı.
3. Yeniden Sleep'e bas. Microphone Off iken Vex de: uyanmamalı. On yapıp
   tekrar dene. Wake düğmesiyle de çıkabilmelisin; yazılı mesaj açıkça uyandırır.
4. Kişiselleştirme → Wake word: Computer kaydet. Sonraki uykuda Computer
   gösterilmeli ve bu sözcükle uyanmalı. Sonra istersen Vex'e geri dön.
5. "uyku moduna geç ne demek?" sorusu doğrudan uyutmamalı. Önceki notlar ve
   geçici sohbet bağlamı uyku/uyanışta korunmalı. Unknown kilidinde Sleep/Wake
   yeni görev başlatmak veya kilidi kaldırmak için kullanılmamalı.

Yerel model bu makinede kuruldu. Eksik kurulumda v1 içinden:
`.\.venv\Scripts\python.exe -m app.session.wake_word --setup`
Desteklenmeyen sözcük/model hatasında uyku açık kalır; Wake ile çıkıp Vex
seçimini düzelt. Gerçek mikrofon başarısı henüz ölçülmedi. 60 s stream sınırında
kaçırırsa sözcüğü tekrar söyle. Otomatik geri uyuma ve saniye ayarı sonraki adım.

## Güncel kısa test — Stop göstergeleri

Geçici hafıza testleri kullanıcı tarafından başarılı bildirildi (`dc79318`).
Bu yeni küçük gösterim düzeltmesi manuel kabul bekler.

1. Live + Microphone On ile uzun yanıt iste; Stop'a bas. Header mikrofon ışığı
   kısa süreli sönüp yanmamalı; normal bitişte dinleme tekrar hazır olmalı.
2. Model konuşurken araya gir: önceki yanıt kesilebilir, fakat normal kesme
   bağlantı rozeti kırmızı hata olmamalı. Stop sonrası nötr LIVE READY normaldir;
   bir sonraki doğrulanmış yanıtta yine normal son Live yanıt bilgisi görünür.
3. Microphone Off yap: ışık sönmeli. Disconnect/gerçek izin veya cihaz hatası
   da ışığı söndürmeli; bu düzeltme gerçek hataları yeşile çevirmemeli.

Wake-word/uyku bu tur eklenmedi; sonraki ayrı uygulama adımıdır.

## Güncel manuel test — geçici sohbet hafızası

Uygulamayı yeniden aç. Live modeli yüklendikten sonra:

1. "Bu sohbet için sevdiğim renk mor" de/yaz; ardından "Hangi rengi söyledim?"
   diye sor. Aynı konuşmayı takip etmeli; kalıcı profil kaydı iddia etmemeli.
2. Uzun bir yanıt iste ve Stop'a bas. Kontroller açılınca rengi tekrar sor.
   Yeni socket açılırsa recent conversation restored tanısı görülebilir;
   önceki renk hatırlanmalı, eski komut/not işlemi tekrar çalışmamalı.
3. Disconnect sonrası yeniden Live mesajı göndererek aynı bilgiyi sor.
   Yakın geçmiş korunmalı. Çok eski/uzun konuşma sınıra takılabilir.
4. New Chat'e basıp onayı reddet: mesajlar/bağlam kalmalı. Tekrar basıp onayla:
   konuşma temizlenmeli; notlar ve ayarlar kalmalı. Rengi sorunca eski sohbet
   bilgisi bu yeni sohbetin hafızasından gelmemeli.
5. Uygulamayı kapatıp açınca bu geçici hafıza kalmamalı. New Chat aktif turda
   veya unknown sonuç kilidinde kullanılmamalı; kurtarma düğmesi değildir.

Otomasyon: 787 pytest, 6 Node süiti, 10/10 WebView2 fazı ve Pyright 0 hata.
Bu dilim manuel kabul bekler; gerçek hesap veya ücretli API ile geliştirici
kabulü yapılmadı. Kalıcı kullanıcı hafızası, wake-word ve uyku sonraki işlerdir.

## Güncel: REST ses ve yanıtı kesmeyen Microphone Off

Önceki mikrofon tercihi testleri kullanıcı tarafından kabul edildi (`f35a13e`).
Kullanıcı 22 Ekim 2026 tarihinde bu dilimin manuel testlerini başarılı bildirdi.
Aşağıdaki liste tekrar kontrol içindir:

1. Live açıkken uzun bir yanıt iste. Konuşurken veya yanıt çalarken Microphone
   Off yap: yalnız mikrofon kapanmalı; model konuşmaya/yazmaya devam etmeli.
   Stop'a ayrıca basarsan yanıt durmalı. Off tercihi kendiliğinden açılmamalı.
2. Live kutusunu kapat, Mute kapalı olsun. Yazıyla kısa bir Türkçe soru gönder:
   metin göründükten sonra ses gelmeli; durum playback finished olmalı.
3. REST'te Mute açıp mesaj gönder: metin gelmeli, ses gelmemeli. Unmute yap.
   Uzun yanıtın sesi hazırlanırken/çalarken Stop'a bas; metin ve tamamlanan
   not işlemleri korunmalı. Bekleyen HTTP varsa bitmeden yeni mesaj açılmamalı.
4. TTS kota/erişim hatası olursa metin ekranda kalmalı, audio unavailable
   görünmeli. Mesajı/not işlemini kendiliğinden tekrar göndermemeli. Bu hata
   metin modelinin başarısız olduğu anlamına gelmez.

REST TTS ayrı API isteği/kotası kullanır; Kore varsayılanı sabittir. Live ses
seçimi REST sesini henüz değiştirmez. REST mikrofon/STT eklenmedi.
Otomasyon: 780 pytest, 6 Node süiti, 10/10 native fazı ve Pyright 0 hata.
Gerçek hesap ve fiziksel cihaz bu geliştirmede kullanılmadı; sentetik testte
sessiz PCM çalması gerçek hoparlörden duyulduğu kanıtı sayılmaz.

## Önceki: Microphone On/Off ve hata sonrası dinleme

Kullanıcı kabulü: 22 Ekim 2026 tarihinde On/Off ve hata sonrası dinleme
testleri başarılı bildirildi. Aktif girişte Off'un yanıtı kesmemesi sonraki
küçük düzeltme olarak istendi.

1. Live modelini yükle, Microphone On kalsın. Olmayan bir geçici notu silmesini
   iste. Ret/açıklama sonrasında düğmeye basmadan yeni bir soru sor; yanıt gelmeli.
2. Uzun bir yanıtı Stop ile kes. Gerçek bitişten sonra On ve sessizlikte idle
   kalmalı. Yeni bir soru sor; eski komut kendiliğinden tekrarlanmamalı.
3. Yanıt sırasında Microphone Off yap, sonra Stop'a bas. Mikrofon kapalı
   kalmalı; sonraki yazılı mesajdan sonra veya model yüklenince de açılmamalı.
   Açıkça On yapınca yeni konuşmanı almalı.
4. İzin/cihaz sorunu veya Disconnect varsa ayarı/bağlantıyı düzeltip Off→On
   kullan. Belirsiz araç sonucunda bu düğme komut kilidini kaldırmamalı; uygulamayı
   yeniden açıp kaydı kontrol etmek gerekir. On tercihi engeli aşma yetkisi değildir.

765 pytest, 6 Node süiti ve 10/10 WebView2 fazı geçti.
Bu ara istek tek başına uygulandı; REST ses çıkışı sonraki ayrı adımdır.
Testler geçici profil ve sentetik ses/sağlayıcı kullanır; fiziksel kabul bekleniyor.

## Önceki: adım 5 — durum ve Stop/log kısa testi

Kullanıcı kabulü: 22 Ekim 2026 tarihinde durum/log/süre ve idle/listening
testleri kullanıcı tarafından başarılı bildirildi; adım 5 manuel kabulü tamamlandı.

1. Live modelini yükle, birkaç saniye sus: mikrofon hazır olsa da merkez idle
   kalmalı. Normal sesle konuşunca listening; susup yanıt bekleyince thinking,
   Vex'in sesi çalarken speaking, bitişte yeniden idle görünmeli. Yerel algı
   yaklaşık 200 ms başlangıç/700 ms sessizlik içerir; sözcük bazlı ölçüm değildir.
2. Tekrar konuş veya yanıta araya gir. Eski ses/metin yeni tura karışmamalı;
   gerçek araç sonucu beklenmeden yeni konuşma yürütülmemeli.
3. Yanıt sırasında Stop kullan. Kontroller gerçek bitişten sonra açılmalı;
   Engine log'da normal durdurma kaydı bulunmalı, aynı Stop için Failed to send
   live_audio_start yazmamalı. Gerçek API/cihaz veya belirsiz sonuç hataları gizlenmemeli.
4. REST'te yazılı yanıt ve Stop'u da dene. Önceden tamamlanan geçici not korunmalı.
   Uzun kullanımda log paneli son 200 kaydı tutar; eski tanı kayıtları düşer.

765 Python testi, 6 Node süiti ve sentetik sağlayıcılı 10/10 WebView2 fazı geçti.
25 s olay bekleme / 120 s toplam Live sınırları kontrollü testlerde küçültülerek
sınandı; gerçek API'de bu kadar uzun bekleme veya ücretli çağrı yapılmadı.
Süre aşımında otomatik tekrar yoktur; unknown kontrolleri kilitli tutar.
Manuel kabul bekleniyor. REST ses çıkışı sonraki ayrı adımdır.

## Önceki: adım 4 — dil ve temel kişiselleştirme

Kullanıcı kabulü: 22 Ekim 2026 tarihinde dil/kişiselleştirme adımının
testleri kullanıcı tarafından başarılı bildirildi; adım 4 manuel kabulü tamamlandı.

1. Personalization içinde Response language = Turkish seç; kişisel talimata
   "Bana Kaptan diye hitap et; kısa cevap ver." yazıp Save profile'a bas.
   Live'da yazıyla ve sesle "Merhaba, kendini tanıt" de. Türkçe ve tercih ettiğin
   hitapla yanıt bekle. Live kapalıyken aynı yazılı testi REST'te de dene.
2. Response language = English ve talimat = "Call me Captain. Use one sentence."
   kaydet. Sonraki REST ve Live yanıtları İngilizce olmalı. Önceden açık bir
   Live bağlamı varsa sonraki mesajda scope_changed/yeni oturum beklenir;
   eski yanıta veya eski araç işlemine tekrar istek gönderilmemeli.
3. Uygulamayı kapatıp aç; dil ve talimat korunmalı, yeni mesajda uygulanmalı.
   Sonra tercih ettiğin Türkçe ayarına dön. Save başarısızsa modal kapanmamalı;
   model kayıtlı disk tercihlerini kullanır.
4. Canlı yanıt sürerken profil kaydedersen o yanıt kendi eski talimatıyla
   bitebilir; yeni tercih bir sonraki mesajda uygulanır. Stop/Disconnect ve
   önceki not koruma davranışı sürmeli.

762 pytest, 5 Node süiti ve 10/10 WebView2 fazı geçti; SDK'ye doğru talimat
taşınması sentetik sağlayıcıyla doğrulandı. Gerçek hesapla dil/stil kabulünü sen yapacaksın.
Native ses tanıma dili otomatik kalır; seçilen dil prompt ile yönlendirilir.
Diğer profil alanlarının modele aktarımı ve REST ses çıkışı bu adımda yoktur.
Yeni adımın manuel kabulü henüz bekleniyor.

## Önceki: adım 3 — VAD ve mikrofon devri için kısa manuel test

Kullanıcı kabulü: 22 Ekim 2026 tarihinde VAD/mikrofon adımı testlerinin
başarılı olduğu kullanıcı tarafından bildirildi; adım 3 manuel kabulü tamamlandı.

1. Önce kulaklıkla Live modeli yükle. Uzun bir açıklama iste; klavye/fare
   gibi kısa tıklar yanıtı kesmemeli. Normal sesle "Vazgeçtim, sadece merhaba de"
   diye araya gir. Eski ses kesilmeli, metni korunmalı, yeni söz ayrı görünmeli.
2. Yanıtın bittiği anda konuşmaya başla; mikrofon düğmesine basmadan ikinci
   yanıt gelmeli ve ilk heceler kaybolmamalı. Bunu birkaç kez dene.
3. Aynı testi normal kullandığın hoparlör sesinde yap. Vex kendi sesiyle
   kendini kesiyorsa veya normal konuşman kaçıyorsa kulaklık/hoparlör farkını
   bildir. Enerji kapısı kesin bir yankı/konuşma ayırıcı değildir.
4. Yeni konuşma yakalanırken Stop/Pause/Disconnect dene. Bekleyen söz sonradan
   gönderilmemeli; Resume ile yeni konuşma açılabilmeli. Tamamlanmış bir geçici
   not değişmeden kalmalı; bilinmeyen araç sonucu yeni komut açmamalı.

742 pytest, 5 Node süiti ve 10/10 sentetik WebView2 fazı geçti.
Gerçek hesap/donanım bu geliştirme sırasında kullanılmadı. Aktif Stop bağlamı
sıfırlayabilir; bu adım aynı socket üzerinde tam çift yönlü interruption değildir.
Dil ve kişiselleştirme sonraki ayrı adımdır. Manuel kabul henüz bekleniyor.

## Önceki: adım 2 — anlık transkript gösterimi

Kullanıcı kabulü: 22 Ekim 2026 tarihinde kullanıcı anlık transkript
testlerinin başarılı olduğunu bildirdi; adım 2 manuel kabulü tamamlandı.

1. Uygulamayı yeniden açıp Live modelini yükle. Konuştuğunda sağlayıcının
   tanıdığı sözler tek kullanıcı balonunda görünmeli; tekrar tekrar eklenmemeli.
2. Uzun bir açıklama iste. Vex konuşurken metin aynı yanıt balonunda büyümeli;
   tur bitince aynı yanıt ikinci kez eklenmemeli.
3. Vex konuşurken araya gir veya Stop'a bas. O ana kadar görünen eski metin
   kalmalı ve Interrupted yazmalı; yeni söz farklı kullanıcı/model balonuna
   gitmeli. Yeni turda eski yanıtın metni belirmemeli.
4. Yazılı Live mesajında kullanıcı metni tek kez görünmeli. Disconnect veya
   model değişiminde geç metin eski mesajı yeniden açmamalı.

Metin sağlayıcı transkripti geldiğinde görünür; sesle sözcük düzeyinde tam
senkron veya henüz gönderilmemiş yerel sesin tanınması vaat edilmez. Barge-in,
dil ve algılama sorunlarının diğer düzeltmeleri ayrı adımlardır. Gerçek hesap
bu geliştirme kontrolünde kullanılmadı; sentetik kabul fiziksel test yerine geçmez.

## Güncel: Vex konuşurken araya girme

Otomatik dinleme önceki kullanıcı testinde onaylandı. Yeni adımı kulaklıkla dene:

1. Live modelini yükle, "Bana uzun bir hikâye anlat" de. Vex konuşurken
   "Vazgeçtim, sadece merhaba de" diye araya gir. Ses kesilmeli, ardından yeni
   konuşmanın metni ve kısa yanıtı gelmeli. Düğmeye basman gerekmemeli.
2. Geçici bir not ekletip ardından uzun yanıt iste; konuşarak kes. Önceden
   tamamlanan not silinmemeli veya ikinci kez eklenmemeli; panelden kontrol et.
3. Yeni söz algılanırken Stop/Pause/Disconnect kullan. Bekleyen söz daha sonra
   kendi kendine gönderilmemeli. Resume ile yeni konuşma ayrı başlayabilmeli.
4. Birkaç kez art arda dene; eski ses yeniden çalmamalı. Sonuç belirsizse UI
   yeni komut göndermek yerine kilitli kalmalı. Eski turun kapanışı uzarsa ses
   tamponu atılabilir; bu durumda Resume ile yeniden konuş.

Aktif Stop mantıksal oturumu sıfırlayabilir; bağlam korunmuş varsayma. Bu kabul
aynı socket üzerinde tam çift yönlü sağlayıcı protokolü testi değildir. Gerçek
yankı ve gürültü hassasiyeti henüz kalibre edilmedi; sentetik WebView2 testi
fiziksel hoparlör/mikrofon kabulü yerine geçmez.

## Güncel: düğmesiz konuşma ve otomatik yeniden dinleme

1. Uygulamayı yeniden aç; Live açıkken Load Live Models ile kataloğu yükle.
   Gerekirse ilk mikrofon iznini ver. Mic'e basmadan Listening for speech
   görünmeli. Susarken model yanıtı/başarı veya periyodik model isteği oluşmamalı.
2. "Merhaba, kısa cevap ver" de. Yanıtın sesi bittikten sonra kendiliğinden
   Listening for speech gelmeli. Düğmeye dokunmadan ikinci soruyu sor.
3. Yerel beklemede yazılı mesaj da gönderilebilmeli; yanıt sonrası tekrar dinlemeli.
4. Pause listening veya Stop'a bas: kendi kendine tekrar açılmamalı. Resume
   listening ile devam et. Disconnect ve mikrofon çıkarılması da durdurmalı.
5. Yanıt sırasında konuşma bu dilimde alınmaz; bu barge-in testi değildir.
   Kısık ses/gürültüde başlangıç kırpılıyorsa bildir: yerel aday eşiği gerçek
   donanımda henüz kalibre edilmedi. Sunucu konuşma bitişini yine VAD ile bulur.

Kontrollü test gerçek WebView2 ama sentetik ses/sağlayıcı kullanır. Gerçek
hesap/fiziksel mikrofon/izin kalıcılığı kullanıcı kabulü açıktır.

## Güncel dilim: konuşurken PCM gönderimi ve otomatik VAD

Otomatik cihaz listesi kullanıcı tarafından başarılı bildirildi. Yeni VAD
diliminin gerçek hesap/mikrofon kabulü henüz yapılmadı. Kısa test:

1. Normal uygulamayı aç; Live açık, katalogdan model seçili olsun. Kulaklıkla
   Mic'e bas, Listening live yazısını görünce "Merhaba, kısa cevap ver" de.
   Bitir düğmesine basmadan sus; metin ve ses yanıtı gelmeli, mikrofon kapanmalı.
2. Yalnız geçici test notuyla "Notlarıma VAD deneme 001 ekle" de. Tek not,
   backend'den yenilenen panel ve doğrulanmış sonuç beklenir; elle silerek temizle.
3. Konuşurken Stop'a bas; mikrofon kapanmalı, gerçek bitişten sonra girişler
   açılmalı. Yeni konuşma eski paket/Stop'tan etkilenmemeli. Bitmiş işlem geri alınmaz.
4. Mic iznini reddetmek veya cihazı çıkarmak başka mikrofona sessizce geçmemeli.
   15 saniyeyi aşan giriş iptal edilir; başarı gibi gösterilmez.

Bu tek konuşma akışıdır. Yanıt sırasında konuşarak araya girme ve otomatik
yeniden dinleme sonraki adımdır. Kontroller geçici profil/sentetik sesle yapıldı;
sağlayıcı VAD kalitesi ve gerçek izinlerin yeniden açılış kalıcılığı denenmedi.

Bu belge bütün proje içindir; bugün bütün özelliklerin hazır olduğunu söylemez.

22 Ekim güncel kabul: kullanıcı açık başlat/bitir mikrofon testlerini başarılı
bildirdi. Temel mikrofon/transkript/Live ses kabulü tamamdır; sürekli dinleme
ve konuşarak araya girme henüz eklenmedi.

Aynı gün cihaz dilimi sonrası boş native pencere bildirildi. Yerel UI dosyası
önbelleği düzeltildikten sonra kullanıcı tekrar açılışın çalıştığını onayladı.
Eski konsol hatası alınamadı; bu onay çoklu cihaz veya sürekli VAD kabulü değildir.

Kullanıcı cihaz testlerini başarılı bildirdi. Son küçük cihaz iyileştirmesinde
Scan düğmesi kaldırıldı; listeleme otomatik ve izinsiz bir okumadır. İlk izin
Mic düğmesindedir. Sürekli dinleme/VAD bu değişikliğin parçası değildir.

Otomatik cihaz listesinin kısa kontrolü:

1. Uygulamayı aç, Ayarlar → Audio & Camera'ya gir: düğme olmadan liste gelmeli.
   Sırf listeleme için mikrofon veya kamera açılmamalı. İlk izin henüz yoksa
   Mic düğmesine basınca verilir; sonrasında erişilebilir cihaz adları yenilenir.
2. Mikrofonunu ve Live reply speaker cihazını seç, Save Settings'e bas.
   Sonraki başlat/bitir kaydı seçtiğin mikrofonu, Live yanıtı seçtiğin çıkışı
   kullanmalı. Efekt sesleri hâlâ OS varsayılanındadır.
3. Özel cihaz erişilemiyorsa yanlış cihazda sessizce çalmak yerine hata vermeli;
   System default seçerek yeniden dene. Kayıt sırasında seçili USB mikrofonu
   çıkarırsan kayıt gönderilmeden kapanmalı. Bu deneme için önemli komut verme.
4. Yeniden açınca tercihin korunmalı; browser origin/izin nedeniyle cihaz
   kimliği değişmişse otomatik yenilenen listeden yeni seçim gerekebilir. Kayıp tercih listede
   açıkça görünür; kendiliğinden başka cihazla değiştirilmez.

Tek cihazla yapılan test çoklu donanım veya bütün sürücülerin kabulü sayılmaz.
Kod doğrulaması, sınır durumları, taklit ağ hataları, kayıt/replay ve regresyon
testleri geliştirici/ajan tarafından yapılır. Kullanıcıdan her düzeltmeden sonra
aynı testleri yeniden çalıştırması istenmez. Aşağıdaki denemeler ilgili özellik
hazır olduğunda, kısa bir kabul oturumunda yapılır.

| Ne zaman? | Kullanıcı neyi dener? | Neden gerçek kullanıcı gerekir? |
|---|---|---|
| Aşama 4 | Not Defteri'ni kapatıp iki kez gerçek açma/replay kabulü | Gerçek Windows oturumu ve açık belgelerin güvenle kapatılması; tamamlandı, iki rapor kontrol edildi |
| Aşama 5 / metin UI hazırken | Kısa konuşma, sentetik bir not ekleme/listeleme, bir görevi durdurma; görünüm ve yanıtın anlaşılır olması | Doğal dil beklentisi ve kullanım deneyimi; API/araç doğruluğunu ajan ayrıca test eder |
| Aşama 5 / ses hazırken | Kendi mikrofon/hoparlör veya kulaklığıyla konuşma; mute/mic aç-kapat, araya girme, gecikme ve anlaşılabilirlik | Duyulan ses, ortam gürültüsü ve cihaz davranışı yalnız taklit testle doğrulanamaz |
| Aşama 6 / hesap entegrasyonu hazırken | Google/Telegram/Discord gibi seçtiği hesabın giriş/izin adımlarını kendisi tamamlama; ilk işlemi açıkça belirlenmiş test hedefinde deneme | Hesap girişi ve gerçek yetki kullanıcıya aittir; ajan izin kapsamını ve otomatik kontrolleri hazırlar |
| Aşama 7 / GUI işlemi hazırken | Kullanacağı uygulamada, kendi ekran/DPI düzeninde sentetik belgeyle tek gerçek iş akışı | Gerçek uygulama düzeni, odak ve hedef doğruluğu; erişilebilir farklı düzenleri ajan da denetler |
| Aşama 8 / rutin ve paket hazırken | Bir deneme rutinini oluşturma, uygulamayı kapat/aç ve paketlenmiş sürümü normal biçimde başlatma | Günlük kullanım ve dağıtılmış uygulamanın hedef makinedeki deneyimi |

Birden fazla monitör veya belirli cihaz bulunmuyorsa o koşul denenmedi diye
kaydedilir; sahip olmadığı donanımı edinmesi beklenmez. Kullanıcıdan kota
doldurması, gerçek verisini silmesi veya sırf hata üretmek için hesaplarını
bozması istenmez. Ağ/kota hataları önce kontrollü otomasyonla oluşturulur.

## Bugün kullanıcıdan bekleyen iş

Aşama 4 kabulü tamamlandı. Gemini 5.2 adaptörünün kontrollü testleri hazır;
3.8 Flash isteği 503 verdi; 3.5 Flash-Lite ile canlı katalog ve sentetik not kabulü geçti. Yeni retry/fallback ve UI metin hattının birleşik canlı kabulü henüz yapılmadı; 10 gerçek WebView2 senaryosu kontrollü HTTP ile geçti. Ayrı boş profil kullanan manuel komutlar STAGE5_MODEL.md sonundadır. Yerel UI anahtar kaydı
Windows kimlik deposuna bağlandı. Kullanıcı uygulamada Settings → Connection
alanından anahtarını kaydedebilir; sonraki gerekli canlı kabul bu anahtarla yapılabilir; geçmiş iki testi sırf tekrar için yeniden çalıştırmak gerekmez.
Eski GEMINI_API_KEY ortam değeri kayıtlı anahtardan önce geldiğinden bu denemede
ortam değişkeni kaldırılmalıdır. Komutlar [Aşama 5 rehberinde](STAGE5_MODEL.md).
Bu bir kod denetimi görevi değildir. Anahtar sohbet mesajına gönderilmez.
Gerçek API anahtarı/hesap verisi ve mikrofon geliştirme testlerinde kullanılmadı.

Bir özellik tamamlanınca ajan önce kendi kontrollerini yapar, sonra yalnız
gerekli gerçek kullanım denemesini; komutu, beklenen sonucu ve test verisinin
kapsamını açıkça vererek ister. Kullanıcının geçti bildirimine ek olarak varsa
rapor dosyası incelenir; denenmeyen nokta tamamlandı diye işaretlenmez.

Güncel UI düzeltmesi: ilk not aktarımı beklerken normal sohbet açıktır; not araçları onaya kadar kapalıdır. Settings → Connection → Load Live models API listesini getirir ve yalnız Live yeteneği bildirenleri gösterir. Bu seçim bugün ses bağlantısını başlatmaz; yazılı mesaja Live ses yanıtı sonraki dilimdedir. Native açılış komutları STAGE5_MODEL.md sonundadır.

Güncel Live kontrolü (22 Ekim): kullanıcı kalıcı oturumda ilk metni 0.7 s,
toplamı 3.4 s olarak gözlemledi; bu her isteğin aynı sürede biteceği garantisi
değildir. Yeni araç diliminde uygulamayı yeniden aç, Load Live models ile
seçim yap, Live session kutusunu açık bırak. Aktarım bekliyorsa Use backend
notes ile onayla. “Notlarıma Live deneme 001 ekle” / “Notlarımı listele” gönder;
tek kayıt ve doğru liste bekle. “Desteklenen uygulamaları listele” ve “Sistem
bilgilerini göster” diğer iki aracı dener. Not silme/düzenleme modele henüz
açık değildir; UI düğmeleri çalışır. Tool logunda succeeded/verified kontrol et.

Normal iki turda session reused, Disconnect sonrası new session beklenir.
Not aktarımı onayı araç listesini değiştirdiğinde bir kez yeni oturum açılması
normaldir. Hata sonrasında not gerçekten eklenmiş olabilir; kontrol etmeden
aynı ekleme komutunu tekrarlama. Araç bağlantısı kullanıcı tarafından çalışıyor
diye onaylandı; sonraki Stop dilimiyle güncel toplam 560 otomatik test geçti;
gerçek hesabınla Live araç denemesi kullanıcı tarafından onaylandı. Ses oynatma ve REST Stop sonraki
adımlardır. Bu dilimin tam native paketi kapanış bekleme testi düzeltildikten
sonra 10/10 geçti; başarısız koşumlar ve sonuç STAGE5_MODEL.md'de kayıtlıdır.

Live Stop kabulü: uygulamayı yeniden aç, Live modelini yükle/seç. “Bana uzay
hakkında 20 maddelik bir açıklama yaz” gönder ve yanıt beklerken Stop Task'a
bas. Önce Cancellation requested, sonra Stopped görülmeli; giriş yeniden
açılmalı. Ardından “Merhaba” gönder; new session ve normal yanıt bekle.
Mevcut notlar korunmalı. Model Stop'tan önce bitmişse normal yanıtın görünmesi
doğrudur; tamamlanmış tur sonradan iptal edilmiş sayılmaz. Başka bir veri yazma
komutuyla denersen Stop'un önceden kaydedilmiş veriyi geri almadığını unutma.
Bu adım gerçek hidden WebView2 + sentetik ağda 10/10 geçti; kendi API hesabınla
Live Stop kullanıcı tarafından çalışıyor diye onaylandı. Resumption, modelle not düzenleme/silme ve
ses sonraki dilimlerdir.

## Güncel REST Stop kabulü — 22 Ekim 2026

REST Stop hazırdır; sonraki aşamaya geçilmedi. Uygulamayı yeniden açıp Live
session kutusunu kapat. Uzun bir açıklama iste ve beklerken Stop Task'a bas.
Devam eden HTTP varsa “Waiting for the current HTTP request to finish” beklenir;
bu sırada giriş ve notlar kilitli kalır. İstek döndüğünde “Stopped” ve açılan
kontroller bekle. Ardından “Merhaba” gönder; normal yanıt bekle. Model Stop'tan
önce tamamlanmışsa normal yanıtın görünmesi doğrudur. Not ekleme yerine genel
sohbetle denemek yeterlidir; Stop önceden tamamlanmış yazıyı geri almaz.

578 pytest kontrolü ve tam native paket 10/10 geçti; gerçek hesap/veri veya
ücretli istek kullanılmadı. Takip düzeltmesiyle FakeWindow test nesnelerinin
7 tip hatası da giderildi; köprü süiti 72/72, birleşik Pyright 0 hata/uyarı verdi.
STAGE5_MODEL.md geçmiş bulguyu ve çözümü tutar. Bu yeni REST Stop diliminin
gerçek hesapla kullanıcı kabulü **test edilemedi — API limiti**: kullanıcı API
limitine ulaşıldığını bildirdi. Limit açılınca kısa manuel kabul yapılabilir;
bu kayıt otomatik testlerde bir başarısızlık değildir.

## Güncel Live bağlantı kabulü — 22 Ekim 2026

GoAway ve güvenli idle checkpoint ile resumption dilimi tamamlandı. 601 pytest
kontrolü, seçili üretim/resume/bridge tip kontrolü ve tam native paket 10/10
geçti. Native rapor: stage5-live-resumption-native.json. Gerçek UI/SDK/core,
sentetik taşıma kullanıldı; gerçek hesap kabulü **test edilemedi — API limiti**.

Limit açıldığında uygulamayı yeniden aç, Live modelini yükle/seç ve iki kısa
mesaj gönder: new session → session reused bekle. Doğal GoAway/kopma sonrası
güvenli checkpoint varsa session resumed, yoksa new session ve context reset
nedeni beklenir. GoAway görmeden yalnız iki mesajla resumption kabul edilmiş
sayılmaz; sentetik native test bu sınırı ayrıca denemiştir. Stop veya Disconnect
sonrası yeni mesaj new session olmalıdır. Bir hatada not daha önce kaydedilmiş
olabilir; aynı ekleme komutunu kontrol etmeden yeniden gönderme.
Aktif kopan mesaj otomatik yeniden gönderilmez; devam ettirme yalnız idle
checkpoint'ten yapılır. Ses ve modelden not düzenleme/silme bu dilimde eklenmedi.


## Modelden not düzenleme/silme kabulü — 22 Ekim 2026

Kontrollü doğrulama: 639 pytest, yeni not hedefi dosyasında 38 test, seçili
Pyright 0 hata/uyarı ve hidden WebView2 10/10. Native rapor:
[stage5-model-notes-native.json](stage5-model-notes-native.json). Gerçek
hesap kabulü **test edilemedi — API limiti**; şimdi ücretli istek gönderme.
Önceki bağlantı adımında yerel ilerlemeyi engelleyen hata yoktur; onun gerçek
hesap kabulü de açık kalır.

Limit açılınca `v1` dizininde `.\.venv\Scripts\python.exe -m app.main`
ile aç. İlk aktarım bekliyorsa Use backend notes ile onayla. Yalnız deneme
notlarıyla REST ve Live için sırayla şu kısa akışı dene:

1. “Notlarıma Vex geçici CRUD 001 ekle” ve “Notlarımı ID’leriyle listele”.
2. “Vex geçici CRUD 001 notunu Vex geçici CRUD 002 olarak değiştir”.
   Panelde yeni metin, listede aynı kayıt ID'si bekle.
3. “Vex geçici CRUD 002 notunu tamamlandı işaretle”; panelde işaret bekle.
4. “Vex geçici CRUD 002 notunu sil”; panelden ve yeni listeden kaybolmalı.
5. Aynı metinli iki deneme notu ekle; metinle silmeyi iste. Model hangi kayıt
   olduğunu sormalı veya host note_target_required ile açıklama istemeli;
   iki kayıt da korunmalı. ID’leriyle listeletip seçtiğin gerçek ID ile sil.

“Onu/ilk notu sil” gibi dolaylı seçimler bu dar güvenli dilimde çözülmez;
tam mevcut metni veya ID'yi tekrar belirt. Her yeni mutasyon yeni verified
liste ister; model bunu kendisi çağırmalıdır. Hata sonrası önce panel/listeyi
kontrol et: yazı tamamlanmış fakat model yanıtı kopmuş olabilir. Stop tamamlanmış
işlemi geri almaz. Unknown kilidinde yeniden gönderme, uygulamayı yeniden açıp
gerçek kayıtları gözle. Bu görevde ses, mikrofon ve UI temizliği eklenmedi.


## Kullanıcı kabulü güncellemesi — 22 Ekim 2026

Kullanıcı REST ve Live için ekleme → ID’leriyle listeleme → metin değiştirme →
tamamlandı işaretleme → silme akışının tamamının geçtiğini bildirdi. Aynı
metinli iki notta açıklama isteme ve açık ID ile yalnız seçileni silme de geçti.
Uzun yanıtta Stop, ardından yeni mesaj, kontrollerin açılması ve tamamlanmış
not işleminin korunması da geçti olarak bildirildi. Bu, yukarıdaki önceki not
CRUD için “API limiti nedeniyle test edilemedi” kabulünü kapatır. Gerçek
GoAway/resumption testinin yapıldığı bildirilmedi; o kabul açık kalır.

İstenen iki iyileştirme kaydedildi. Bu promptta yalnız zaman metadata’sı
eklendi; hedef çözme sonraki ayrı adımdır. Yeni notta created_at backend’in
UTC saatidir; ID ve tarih edit/done sırasında değişmez. Eski tarihsiz notun
zamanı bilinmiyor kalır, bugün oluşturulmuş gibi gösterilmez.

Kısa yeni kontrol: yalnız yeni bir deneme notu ekleyip modelden kayıt ID’si
ve oluşturulma zamanıyla listelemesini iste. Metni veya done işaretini değiştir,
yeniden listele ve uygulamayı yeniden aç: ID/tarih aynı kalmalı. Yedek alıp
açıkça geri yüklediğinde tarih korunmalı. Bu yeni timestamp değişikliğinin
kullanıcı kabulü henüz yapılmadı; önceki CRUD kabulünü tekrar yapman gerekmiyor.
“Son notu sil” ve “içinde merh geçen notu sil” hâlâ mevcut tam metin/ID
sınırına tabidir; sonraki hedef seçimi adımıyla ele alınacaktır.


## Son not ve kısmi metin seçimi — kısa kabul

22 Ekim: 707 pytest ve native 10/10 geçti. Yeni seçimin gerçek modelle kullanıcı
kabulü bekleniyor; önceki not CRUD ve Stop onayları korunur. Uygulamayı yeniden
açıp yalnız deneme notlarıyla REST ve Live için ayrı ayrı şu akışı dene:

1. 'Vex hedef merhaba 001' notunu ekle. “İçinde 'hedef merh' geçen notu
   tamamlandı işaretle” de; yalnız bu not işaretlenmeli, ID/tarih korunmalı.
2. 'Vex hedef kontrol 002' notunu ekle. “Son notu sil” de; bütün notların tarihi
   biliniyorsa yalnız en yeni olan kontrol 002 silinmeli. Eski tarihsiz not
   varsa ID istemesi beklenir. Otomatik latest başarı yolunu boş/geçici bir
   profilde deneyebilirsin; bunun için gerçek eski notlarını silme.
3. 'Vex hedef merhaba 003' ekle. “İçinde 'hedef merh' geçen notu sil” de;
   iki aday bulunduğundan açıklama istemeli, ikisi de korunmalı.
4. ID’leri listeletip birinin gerçek ID'sini belirterek sil; yalnız seçilen
   kayıt silinmeli. Deneme verilerini yine ID ile temizle.

Kısmi parçayı düz veya tipografik tırnakla yaz. Tırnaksız/olumsuz/çoklu
filtreler, bilinmeyen hedef ve maksimum tarihte eşitlik bu dilimde açıklama
ister. “Son” son edit değil, kayıtlı oluşturulma zamanıdır. Bir model hatası
sonrasında panel/listeyi kontrol etmeden komutu tekrar gönderme. Sonraki
adım bu kabulden sonra Live ses çıkışıdır; ses/mikrofon henüz eklenmedi.


## Önceki dilim: Live ses kabulü ve mikrofonun ilk dilimi — 22 Ekim 2026

Kullanıcı güncel UI yüklenince Live sesin duyulduğunu ve gecikmeyi çok düşük
hissettiğini bildirdi. Bu, ölçülmüş sıfır gecikme veya bütün cihaz/Stop/Mute
yarışlarının kabulü değildir. İlk fiziksel ses çıkışı kabulü tamamlandı.

Mikrofonu test etmek için uygulamayı güncel UI ile yeniden aç. Gerekirse
`python -m app.main --debug` ve Ctrl+Shift+R kullan; Load models ile Live seç.
Mikrofon düğmesine bas ve izin ver; kayıt göstergesi gelince “Bana Türkçe kısa
bir merhaba de” söyle. En geç 15 saniye içinde Finish & Send'e bas. Kayıt biter,
mikrofon bırakılır; transkript ve sesli yanıt gelmelidir. Yanıt bu ilk dilimde
kayıt bittikten sonra başlar. Kulaklıkla denemek dış ses etkisini azaltır.

1. Geçici bir notu sesle eklet, listelet; transkriptin doğru olduğuna ve panelin
   güncellendiğine bak. Yanlış algılanan komutu tekrarlamadan önce notu kontrol et.
2. Yeni kayıtta Stop'a bas: mikrofon kapanmalı, kayıt gönderilmemeli. Sonra
   yazılı Live mesajı hâlâ çalışmalı. Kayıt 15 saniyeyi aşarsa da gönderilmez.
3. Model yanıtı sırasında Stop ve Mute'u dene; mevcut ses kuralları korunmalı.
4. Mikrofon iznini reddet/kapat: hata görünmeli, kontroller açılmalı.
   Disconnect/model/anahtar değişimi sırasında kayıt yeni kapsama taşınmamalı.

Sürekli dinleme, otomatik VAD, konuşarak yanıtı kesme ve ayarlardaki cihaz
seçiminin uygulanması bu dilimde yoktur. REST yalnız metindir. Gerçek mikrofon
ve konuşma tanıma doğruluğu kullanıcı kabulüne açıktır; sentetik native kayıt
gerçek mikrofon kabulü olarak işaretlenmez.

## Önceki not hedefi kabulü ve Live ses kontrolü — 22 Ekim 2026

Kullanıcı son not ve kısmi metin seçimini tamamen çalışıyor diye onayladı;
önceki CRUD/Stop onaylarıyla birlikte bu kabul kapandı. Sıradaki tek dilim
Live ses çıkışıdır; gerçek sesli yanıt kabulü henüz bekleniyor.

Uygulamayı yeniden aç. Mevcut profilin API anahtarının Windows kimlik deposunda
bulunduğu anahtar gösterilmeden doğrulandı; kayıt değiştirilmedi. Ayarlarda
Key stored locally görülmeli. Kutunun boş olması normaldir; aynı profilde
tekrar anahtar girmen gerekmez. Load models ile Live modelini seç, Live session
açıkken “Bana Türkçe kısa bir merhaba de” yaz. Yazı ve OS varsayılan hoparlör/
kulaklığından ses bekle. API/model erişimi için bu kullanıcı isteği gerekir;
anahtarın kayıtlı olması erişim/kota kanıtı değildir.

Sonra biraz daha uzun yanıt iste: Mute sesi kısmalı, Unmute sonraki akışı
açmalı. Stop hem devam eden hem kalan sıradaki sesi kesmeli; yeni mesajda
eski ses çalmamalı. Model zaten bitmişse Stop yalnız sesi keser; tamamlanmış
not işlemini geri almaz. Disconnect sonrası ses kalmamalı. Ardından uygulamayı
kapat/aç ve anahtar durumunun kayıtlı kaldığını kontrol et.

Kuyruk 20 saniye/512 parçayla sınırlı. Çok hızlı/uzun üretimde taşarsa ses
uyarısı verilir, metin/araç sonucu korunur. Seçili dOut cihazının uygulanması,
mikrofon, VAD ve konuşarak araya girme henüz bu adımda yoktur. Bunlar sonraki
ayrı adımlardır. Native testin sessiz PCM çalması fiziksel duyulabilirlik
kabulü değildir; bu kısa kullanıcı denemesiyle tamamlanır.
