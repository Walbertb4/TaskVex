# Bakım ve mimari denetim

Bu rapor mevcut kodun sınırlarını ve yapılan temizliği açıklar. “Gereksiz hiçbir
satır kalmadı” veya “artık bug yok” garantisi değildir. Güncel işler
[PLAN](PLAN.md), değişiklik kaydı [CHANGELOG](CHANGELOG.md) içindedir.

## Kapsam ve yöntem

Git'in izlediği ve bu bakımda eklenen kaynak/test/config/belgeler envantere alındı.
Python AST ve JS syntax taraması, import/caller/export aramaları; bootstrap,
bridge, model→core, not/sayaç, ses/wake/Stop ve kayıt sahipliği takip edildi.
Dinamik public bridge ve test çağıranları kontrol edilmeden export silinmedi.
Dosya bazlı yollar/satırlar/hash ve kontrol türü
[cleanup-inventory.json](reports/cleanup-inventory.json) içindedir.

Bu, bütün satırların ayrı ayrı elle ispatlandığı anlamına gelmez. Kritik yollar
okunup regresyonla sınandı; bütün kaynaklara statik envanter/syntax kontrolü uygulandı.
Sanal ortam, Git içeriği/cache, kullanıcı veri kökü, referans Mark-LVI-main ve
kurulu üçüncü taraf paket kaynakları ürün kaynak denetimine dahil edilmedi.
Arşivdeki 133 dosyanın içeriği SHA256 ile korunur; tarihsel linkleri yeniden yazılmaz.
Arşiv içeriği HEAD ile karşılaştırıldı: fark yalnız checkout CRLF/LF dönüşümüdür,
metin içeriği farkı yoktur. .gitattributes arşiv byte'larını bundan sonra sabit tutar.
UI varlıklarının tam lisans/provenance incelemesi ayrıca açıktır.

## Yapılan temizlik

| Önce | Sonra / gerekçe |
|---|---|
| app.js 1675 satır; başlangıç + kabuk + sohbet state'i | app.js 323; shell.js görsel kabuk; assistant_session.js tek sohbet/mic/uyku sahibi |
| settings.js 1033 satır; cihaz/layout aynı dosyada | settings.js 701; devices.js ve layout.js ayrı sorumluluk, preferences.js tek ortak nesne |
| Kullanılmayan MediaRecorder/decode yolu | Kaldırıldı; gerçek AudioWorklet girişi ve testleri kaldı |
| UI rutin/takvim tarayıcıları, olmayan native komutlar | Kaldırıldı; backend olmadan “başlatıldı” denmiyor |
| Serbest shortcut → native olay/fake timeline | Kaldırıldı; kayıtlı metin korundu, planlı alan disabled |
| Native runner içinde büyük senaryo blokları | native_scenarios.py'ye taşındı; aynı runner ve geçici fixture |
| REST/Live iki ayrı aynı araç listesi | Aynı modül sabitleri kullanılır; izin şeması/core değişmedi |
| Çelişkili README günlükleri ve dağınık aşama belgeleri | Güncel rehberler ve tek plan/changelog; eski içerik arşiv |

Runtime Python+JS toplamı **12.409 → 11.703 satır**, net **706 satır azalma**.
Taşınan satırlar dahil hesaplandı; belge arşivini kod silme kazanımı saymadık.
Yeni runtime bağımlılık/framework yok. Ayrıntı [metriklerde](reports/cleanup-metrics.json).

CSS tek görünümün stil dosyasıdır; yalnız 1582 satır diye parçalanmadı. schema.js
sınır doğrulamasını birlikte tutar. assistant_session.js hâlâ 942 satırdır; Stop,
wake, mikrofon ve gecikmiş yanıt kimliklerini farklı sahiplerde çoğaltmamak için
birlikte tutuldu. Native test runner'ının sentetik sağlayıcı fixture'ı da satır
sayısını düşürmek uğruna yeni test framework'üne çevrilmedi.

REST kullanıcı isteğiyle korundu. Browser-only görünüm ve legacy ayar okuma/bridge
alias'ları gerçek uyumluluk yollarıdır. Public salt okunur widget setter'ları,
testte kullanılan probe ve JSON şemaları “az çağrılıyor” diye silinmedi.
Skill/rutin editörleri ve mevcut kullanıcı tanımları korunur; yürütme ayrı açık iştir.

## Mimariye uyum ve kalan bulgular

Çalışan model eylemleri **ModelTools → registry/policy → TaskManager → alan aracı**
hattından geçer. Not/sayaç ikinci yürütücüye taşınmadı. UI kontrolleri ve yerel KWS
doğal dil router'ı değildir. Kaldırılan shortcut/scheduler yolları bu ayrımı bozuyordu.

| Öncelik | Bulgu ve kanıt | Karar |
|---|---|---|
| Kapatıldı (5.F7.3) | Kalıcı core'da 256 RAM/aktif iş sınırıdır; terminal kayıtlar SQLite'tan sorgulanır. | Eski kimlikler disk indeksinde kalır. Aktif kuyruk dolunca açık ret; disk geçmişi otomatik silinmez. |
| Kapatıldı (5.F7.2) | TaskManager kimlik/istek/sonucu SQLite FULL transaction ile tutar; core tek sahip kilidi vardır. | Restart eskiyi yürütmez; yarım başlamış iş unknown, queued iptal. Bu harici servisler için exactly-once değildir; model oturum RAM'i yeniden canlandırılmaz. |
| P2 | Günlük süresiz ve şifrelenmemiştir; unknown yeni işleri profil genelinde kilitler. | Disk/açılış maliyeti geçmişle büyür; eski not metni kalabilir. Kullanıcıya yönelik unknown uzlaştırma ve güvenli disk sıkıştırma henüz yoktur. |
| P1 | json_store.py atomik replace kullanır; native main artık veri kökü OS kilidini tutar. | 5.F7.1 native aynı-profil çakışmasını kapatır. Host dışı scriptler için JsonStore tek başına kilit sağlamaz. |
| P2 | main.py kapanışta bridge._chat._live.close gibi private sınırları bilir. | İkinci socket sahibi yok, fakat host/bridge bağlaşımı var. Sonraki lifecycle değişiminde mevcut sahibin public kapanış noktası kullanılmalı; yeni manager kurulmamalı. |
| P2 | Skill/rutin tanımları localStorage; core yürütme ve backend scheduler yok. | Bugün editör kapsamı. İleri entegrasyon tek backend sahipliğinde yapılmalı. Yerel zamanlayıcı ile geçici yürütme kurulmadı. |
| P2 | Google/Telegram/Discord/GUI henüz yok; harici veri taint/kanal principal/risk onay sistemi tamam değil. | Bunlar bugünkü sınırlı yerel araçlara varmış gibi yazılmıyor. Dış içerik ve riskli eylemler açılmadan önce zorunlu. |
| P2 | UI'da base instruction/greeting/memory/browser tercihlerinin backend karşılığı yok. | Önceden sessizce işe yarıyor görünüyordu; şimdi planlı/disabled, mevcut metin korunur. |
| P3 | NativeBridge 613 satır ve assistant_session 942 satır; yaşam döngüsü dalları yoğun. | Şimdilik tek sahip korunuyor. Yeni özellik aynı dosyaya yığılmadan gerçek sözleşme sınırıyla çıkarılmalı; sadece satır eşiğiyle bölünmemeli. |

P1'ler yeni bulunmuş her şeyin bu turda yeniden mimarileştirilmesi anlamına gelmez.
Bu bakım güvenli dead-code/doc temizliğidir; uzun oturum/dağıtım kapanışı yukarıdaki
açık sınırları kabul etmeden “üretime hazır” ilan edilemez.

## Özelleştirilebilir olması gerekenler ve sabit değerler

| Konu | Gerçek durum | Öneri |
|---|---|---|
| Yanıt sesi | Live conn.voice, belgelenmiş hazır Live listesi ve oturum speech_config'una bağlı; REST speech.py Kore sabit | Live seçimi uygulandı; REST kanalı ürünleştirilirken ayrı tercih kapsamı |
| Yanıt ses seviyesi | replyVolume aynı PCM oynatıcısında 0–1 kazançtır; Settings Audio barı, kalıcı kayıt ve reset bağlıdır | 5.F8.1'de uygulandı; efektlerden ayrıdır. Ses karakteri/voice seçimi ayrı açık iştir |
| REST varsayılan/fallback ve TTS modeli | gemini.py DEFAULT_MODEL/FALLBACK_MODEL, speech.py SPEECH_MODEL sabit | Ana masaüstü Live modeli API'den seçilip kaydoluyor; REST kanalı ürünleştirilirken ayrı sağlayıcı tercihine taşı |
| Kullanıcı talimatı/dil | pIns/pLang gerçekten ortak model instruction'a gider | Çalışıyor; güvenlik/araç izni kişisel prompt ile değiştirilemez |
| Base override / greeting / kullanıcı hafızası | pSys/pGreet/pMem yalnız saklı metin | Kalıcı hafıza ve selamlama ayrı kapsam; bugün aktif gibi göstermiyoruz |
| Browser / yeni sekme / app önceliği / shortcut | pBr/pTab/pApp/pSc yalnız legacy tercih | İlgili plugin/resolver gelince tek servise bağla; şimdilik disabled |
| Wake word | pWake backend'e bağlı; Vex/Veks/Rex ailesi, özel kelimede İngilizce sözlük sınırı | Serbest tüm diller iddiası yok; başka dil model/lexicon kalibrasyonu ayrı iş |
| Wake sensitivity, konuşma eşiği, idle sleep | Mevcut ayarlar gerçek backend/worklet'e bağlı | Sabit değillerdir; wake değişimi sonraki uykuya uygulanır |
| UI metin dili/tarih ve birkaç kabuk mesajı | UI İngilizce; model yanıt dili pLang'dan ayrı | Kullanıcı daha önce İngilizce UI istedi. Çok dilli UI istenirse tek locale katmanı; sözlük kopyalayarak değil |
| Tema/SFX/cihazlar | Varsayılan mor, eşik ve cihaz seçimi mevcut ayarlardan değişebilir | Varsayılan değer olması hardcoded davranış hatası değildir |
| Hafıza 12 tur/16k/2k, ses 15 s, deadline/PCM limitleri | Teknik güvenlik/kaynak sınırları | Her sayıyı ayara çevirme. İhtiyaç ölçülürse tek gelişmiş config; validasyon/replay/izin sınırlarını kullanıcı prompt'una bırakma |

Timer bitişindeki “boss” sabit bir model hitabı değildir; model kişisel talimatı
kullanır. UI timer/alarm metni ile kişiselleştirilmiş ses yanıtı farklı şeylerdir.

## Doğrulama ve sınırlar

İlk 5.F6 bakımının sonuçları [cleanup-checks.json](reports/cleanup-checks.json) içinde, gerçek
WebView2 sentetik kabul [cleanup-native.json](reports/cleanup-native.json) içindedir.
5.F6 sonucu: **996 pytest**, **9 JS suite**, **4 browser grubu**, **10 native aşama**
başarılı; app ve etkilenen Python dosyalarında **Pyright 0 hata/uyarı**. pip check
bağımlılık çakışması bulmadı. 78 Python ve 34 JS/MJS dosyası syntax taramasından geçti.
133 arşiv dosyasının hash'i ve güncel belge bağlantıları doğrulandı.
Python, JS, browser, tip kontrolü ve arşiv/link testleri birlikte değerlendirilir.
İlk regresyondaki dosya-konumu varsayımı testte yeni import grafiğine güncellendi;
başarısız ilk deneme son başarı diye gizlenmedi. Eski MediaRecorder self-test'i
kaldırılmış aktif davranışın kanıtı sayılmaz; stream/izin/Stop testleri kalır.

Bu bakımda gerçek Google hesabı/ücretli API, canlı resume/GoAway ve fiziksel
mikrofon/echo/cihaz değişimi yeniden denenmedi. Otomatik testler akustik doğruluk,
süresiz kararlılık, sıfır bug veya bütün olası dinamik üçüncü taraf çağıranları ispatlamaz.

## Kısa manuel kabul

1. Native uygulamayı aç; kayıtlı tema/model ve yerel tanımlar yerinde olsun.
2. Geçici bir not ekle/tamamla/sil; tek kayıt ve yenileme doğrulansın.
3. Timer/stopwatch oluştur, pause/reset ve sağ tık delete yap; doğru sekme/ID kalsın.
4. Live erişimin varsa konuş/Stop/Sleep/Wake dene; Mic Off yanıtı kesmesin.
5. Planlı Google/voice/inspect vb. kontroller işlem yapamasın; skill/rutin editörleri
   tanımı korusun ve Run henüz bağlanmadığını açık söylesin.

API limiti sürüyorsa 4. maddeyi test edilemedi bırak; diğerlerini atlama. Önceki
kullanıcı kabulü bu bakım değişikliğinin manuel kabulü yerine geçmez.


5.F8.1 güncel doğrulama: 1024 pytest, 9 JS suite, 5 browser grubu, app Pyright 0
ve 10 native aşama. [Sonuç](reports/reply-volume-checks.json),
[native](reports/reply-volume-native.json). Ses seviyesi fiziksel duyum/API
kabulü değildir; kullanıcı çalıştığını doğruladı.
