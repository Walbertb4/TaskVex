# Uyku / gecikme / Stopped incelemesi

## Güncel 5.R3 — ayrı onay sesi kaldırıldı

5.R2 testleri kullanıcı tarafından başarılı bildirildi. Ardından kullanıcının
isteğiyle altı WAV ve onay oynatma kodu kaldırıldı; komutla uyku artık Vex'in
kendi yanıtı ve çalması bittikten sonra uygulanır. Aşağıdaki R1 yerel ses
anlatımı tarihseldir. Güncel sözleşme UI_BACKEND_CONTRACT.md, kabul
USER_ACCEPTANCE.md ve ilerleme aşamalar.md içindedir.

## Güncel 5.R2 notu — R1 protokol seçiminin yerine

Kullanıcı sonrasında yazının çalıştığını, sesin 14 PCM / 2 olay / before input
final ile 25 s takıldığını bildirdi. Bu nedenle aşağıdaki R1 hibrit VAD/EOS
anlatımı tarihsel uygulamadır: güncel ses protokolü otomatik VAD kapalıyken
activityStart → PCM → activityEnd'dir. Yerel 700 ms sessizlik korunur.
Yeni sınır tanısı input end: sent/missing ve speech chars gösterir.
921 pytest, 7 JS, Pyright 0 ve 10/10 native geçti; kanıt
[native raporu](stage5-manual-activity-native.json). Gerçek hesap/mikrofon
denenmedi; bildirilen arızanın tamamen çözüldüğü veya kesin nedeni kanıtlanmadı.
Manuel kabul [USER_ACCEPTANCE.md](USER_ACCEPTANCE.md) başındadır.

23 Ekim 2026. Kullanıcı uyku onayının sesli olmamasını, uyanış/algılama
gecikmesini ve bazen Stopped sonrasında Idle'da komut alınmamasını bildirdi.
Bu inceleme yeni özellik aşaması değildir; F4 önüne alınan 5.R1 stabilizasyonudur.
AGENTS, mimari/sözleşme, engineering:debug, Gemini Live ve Ponytail izlenmiştir.

## Kanıtlanan nedenler ve değişiklikler

| Bulgu | Kanıt | Düzeltme |
|---|---|---|
| S01: giriş kapatılıyor, sunucuya EOS gitmeyebiliyor | Yalnız EOS sonrası cevap üreten sentetik socket eski kodda yanıt veremedi | Final transkriptle gönderici bırakılırken eksik EOS aynı Live sahibinden gönderilir; önceki/bitmiş araç tekrarı yok |
| S02: yanıt sırasında öğrenilen gürültü normal sesi engelliyor | 5 s boyunca .02 seviye ses, ardından normal modda .03 aday eski worklet'te hiç tetiklenmedi | Yanıt → normal dinleme sınırında yalnız gürültü tabanı sıfırlanır; yarım aday/ön tampon korunur |
| S03: yerel uyku yanıtı ses hattını atlıyor | local_sleep, Live PCM ve REST read_reply dallarının ikisine de girmiyordu | Host kabulünden sonra seçili TR/EN sabit metin ve yerel WAV, aynı LiveAudio sahibinden oynatılır |
| S04: her uykuda pahalı wake motoru kuruluyor | Yerel ölçüm: 1177 ms yeni motor, .21 ms yeniden decoder/input hazırlığı | Tek doğrulanmış motor RAM'de; her uyku yeni stream/ID/sıra/tampon. Hata veya wake sözcüğü değişiminde motor yenilenir |
| S05: wake'ten devredilmiş kaynak hatası yerel wake hatası sanılıyor | Awake durumundaki stream_backpressure eski wake handler'ında bloke kalıyordu | Normal mikrofon hata/Stop yolu kullanılır; gerçek bitişten sonra yalnız geçici hatada en fazla iki yeni boş dinleyici hakkı |

S05 kullanıcıdaki son durumla uyumludur: `Stopped. Completed actions were not
undone` tek başına sağlayıcı arızası demek değildir. UI setup sırasında kaybolan
kaynağı görünce kendisi Stop gönderebilir. Eski başarı/Stopped metni micBlocked
nedenini örtebiliyordu. Artık giriş hatası loglanır; kesin bitişte sınırlı
yeniden hazırlık veya açık Off/On gereği görünür. Kullanıcıdaki her olayın
tam nedeninin bu olduğu uzaktan kanıtlanmış sayılmaz.

S01, önceki 5.F1 giriş-kapatma düzeltmesinin bıraktığı bir boşluktur. Eski
sentetik sunucu EOS beklemeden cevap üretiyordu; bu yüzden geçen testler gerçek
protokol gereğini yakalamadı. Yeni test sunucu cevabını EOS koşuluna bağlar.

## Konuşma sonu: protokolü açık yapmak

Yerel konuşma adayı ile sunucunun konuşma sonu farklıdır. Önceki yol bazı
koşullarda yalnız sunucudan final bekliyor, kendisi ses sonunu 15 s'ye kadar
bildirmiyordu. Artık backend hazır onayından sonra worklet `arm-end` alır;
700 ms yerel sessizlikte, tüm bekleyen PCM onayları bittikten sonra EOS gider.
Wake hazırlığı sırasındaki duraklama tek başına EOS üretmez. 15 s/150 paket
güvenlik sınırı, Stop ve unknown korunur. Kaybolmuş ses otomatik tekrar edilmez.

Bu, Google'ın [hibrit VAD rehberi](https://ai.google.dev/gemini-api/docs/live-api/capabilities)
ile uyumludur: otomatik VAD açık kalırken yerel konuşma sonu `audio_stream_end`
ile bildirilebilir. [Protokol referansı](https://ai.google.dev/api/live) bu
alanı otomatik VAD ile kullanılacak ses-akışı bitişi olarak tanımlar.
700 ms tüm kullanıcı/oda koşulları için kalibre edilmiş bir garanti değildir.

## Onay sesi ve doğru başarı anlamı

- once: “Uyku moduna geçtim.”
- persistent: “Kalıcı uyku moduna geçtim.”
- off: “Kalıcı uyku modunu kapattım.”

Personalization pLang seçimine göre İngilizce karşılıklar da vardır. once ve
persistent sesleri yalnız host sleeping=true onayından sonra çalar; off mevcut
sohbet tercihinin başarılı kapanışından sonra. Ret/unknown başarı sesi üretmez.
Her görev sonrası otomatik geri uyumada aynı onay tekrar edilmez.
Uykuya giriş onayı çalarken yerel wake hazırlığı bekletilmez; kullanıcı
uyandırmak için onay sesinin bitmesini beklemek zorunda değildir.

Altı WAV, yerel Windows Tolga/Zira sesleriyle üretildi. Model/TTS HTTP'si,
yeni bağımlılık veya kullanıcı kaydı yoktur. Bu kısa onayların sesi Gemini
konuşma sesinden farklıdır. Aynı LiveAudio sahibiyle Mute, seçilen hoparlör,
Stop, eski fetch/decode sonucu ve bağlantı değişimi sınırları korunur.
Dosya/çıkış hatası gerçek modu geri almaz; ses hatası açık loglanır.

## REST şüphesi ve kalan maliyetler

Normal mikrofon yolu `live_audio_start → TextChat.run_live → PersistentLive`
üzerinden gidiyor. Bu yolda REST model fallback veya REST TTS yoktur. Git'in
eldeki ilk commit'i zaten Live/REST ikisini içerir; REST eklenmeden önceki
tam çalışan sürümle ölçüm karşılaştırması yapılamadı. Bu nedenle tüm sorunu
REST'e bağlamak için kanıt yoktur; yukarıdaki yeniden üretimler bizim ses
yaşam döngüsü kodumuzdadır.

Uyku hâlâ Live socket'ini kapatır. Tekrar uyanınca güvenli yeni bağlantının
kurulum süresi vardır; wake_only turu da yeniden bağlantı gerektirebilir.
Metin/akış/klip setup kapsam değişimleri bağlantıyı yenileyebilir. Bunlar bu
tur güvenlik kuralları kaldırılarak gizlenmedi. Gerçek hesap olmadan sağlayıcı
gecikmesi veya toplam uçtan uca hız için sayı vaat edilmez.

## Doğrulama ve açıklar

- S01 ve S02 testleri değişiklikten önce başarısız gösterildi, sonra geçti.
- 920 pytest; 7 JS süiti; app/hedefli Pyright 0 hata/uyarı.
- Native 10/10: stage5-sleep-stability-native.json; son hybrid/cache dilimi
  için ek chat de geçti: stage5-sleep-stability-final-chat.json.
- Ek chat'in ilk denemesi Thinking anını zamanla yakalamaya çalışan testte
  başarısızdı: stage5-sleep-stability-chat-timing-failure.json. Hızlı EOS
  cevabından sonraki gerçek durum Idle/cevap tamam idi. Test açık sunucu
  bariyeriyle düzeltildi; başarısız deneme silinmedi.
- Gerçek KWS, üretilmiş tek WAV ile üç restart/detection: her döngü başarılı,
  yeni ID, .19–.21 ms restart; yeni motor 1036.93 ms (tek yerel ölçüm).
  Rapor stage5-sleep-stability-real-kws.json. Bunlar CPU/model hazırlık
  ölçümleridir; gerçek mikrofon veya toplam yanıt gecikmesi değildir.
- Gerçek kullanıcı notları, sesleri, anahtarı veya ücretli API kullanılmadı.
  Fiziksel cihaz/oda/yankı, farklı konuşma seviyeleri ve gerçek sağlayıcıda
  uzun süreli kabul hâlâ açık. F4 telaffuz/yanlış wake çalışması yapılmadı.

## Sonraki kabul sırası

1. Aynı anda yeni özellik eklemeden, normal timer 0 ile üç Sleep/Wake/konuşma
   döngüsü; sonra persistent ve off onayları.
2. Kısa/duraklamalı komut, uzun yanıt, barge-in, Stop ve yeni komut; aynı
   boyutta iş yükünde ilk ses/EOS/final/cevap sürelerini karşılaştır.
3. Sorun sürerse yeni durum satırı/logdaki **ilk giriş hatası** ile PCM/EOS
   ölçümünü al. Stopped son satırını tek başına neden kabul etme.
4. Ardından F4/F5 gerçek yerel wake/negatif ses ve fiziksel uzun kullanım.
   Bu kabul olmadan uyku katmanı tamamen kararlı veya Aşama 5 kapalı denmez.
