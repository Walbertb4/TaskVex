# Changelog

Bu dosya TaskVex değişikliklerinin tek güncel kaydıdır. Mimari kararların mevcut
hali ARCHITECTURE.md, yapılacak işler PLAN.md içindedir. Henüz sürüm yayımlanmadı.

## Unreleased

### Live ses seçimi ve anahtar durum ibaresi (5.F8.2)

- Connection altında belgelenmiş 30 hazır Live sesi [LIVE] etiketiyle listelenir.
  Tek conn.voice tercihi kalıcı ayarlardan aynı Live setup speech_config'una
  taşınır; metin/mikrofon/timer yanıtı ortaktır. Ses değişimi eski resume token'ını
  kullanmaz, aktif turu kesmez. REST TTS değişmedi; özel/TTS-only ses eklenmedi.
- API key input'u kayıtlı/eksik/belirsiz durumu placeholder'da gösterir; gerçek
  anahtar veya son karakterleri göstermez. Anahtar varlığı API erişim onayı değildir.
- gemini-live-api-dev skill'i ve Google Live sağlayıcı sözleşmesi doğrulandı.
  Ses listesi belge kaynaklıdır; model keşfi API'den kalır. Yeni bağımlılık yok.
- Önceki ses seviyesi adımı kullanıcı kabulüyle 9d67a1d commit'ine kaydedildi;
  push yok. Kullanıcı devam/commit onayı verdi; ayrı fiziksel ses testi bildirmedi.
- 1025 genel pytest + 24 son hedefli test, 9 JS suite, 5 browser grubu,
  app Pyright 0 ve 10/10 native aşama geçti. [Özet](reports/live-voices-checks.json),
  [native](reports/live-voices-native.json). SDK testinin alan adı varsayımı ve
  bir tip belirsizliği düzeltildi; başarısız denemeler raporda korunur.
  Gerçek hesap/ücretli API ve fiziksel ses denenmedi.


### Vex yanıt ses seviyesi (5.F8.1)

- Settings Audio altında tema ve klavye uyumlu Vex reply volume barı eklendi.
  Tek PCM oynatıcısının kazancını anlık değiştirir; Live/REST/timer bildiriminde
  ortaktır. Mute aç/kapat seçili seviyeyi korur; SFX ve mikrofon değişmez.
- replyVolume 0–1 arası doğrulanır; varsayılan/reset 1, sıfır korunur.
  Aynı save/snapshot/import-export yoluyla yerel ve native tercihe kaydolur.
  Yeni sağlayıcı çağrısı/oynatıcı eklenmedi. Voice/kişiselleştirme 5.F8.2 bekliyor.
- Önceki günlük/kapasite adımı kullanıcı devam onayıyla 5c21156 commit'ine
  kaydedildi; push yapılmadı. Kullanıcı bu dilimin çalıştığını doğruladı; commit onaylı.
- 1024 pytest, 9 JS suite, 5 browser grubu, app Pyright 0 ve 10/10 native
  aşama geçti. [Özet](reports/reply-volume-checks.json),
  [native kanıt](reports/reply-volume-native.json). Gerçek hesap/ücretli API ve
  fiziksel hoparlör testi yapılmadı.


### Kalıcı görev günlüğü ve kapasite (5.F7.2/3)

- Aynı TaskManager, standart kütüphane SQLite günlüğünü kullanır; kabul, handler
  öncesi ve terminal kayıtlar FULL transaction ile yazılır. İkinci core OS
  kilidiyle reddedilir; yeni bağımlılık/yürütücü/model yolu eklenmedi.
- Restart tamamlanan işi yeniden çalıştırmaz. Queued iptal, başlamış yarım iş
  unknown olur. Kimlik/içerik çakışması reddedilir; disk hatası yeni etkileri
  durdurur. Doğrulanmış araç sonucu geç kayıt hatasıyla geri alınmış sayılmaz.
- Native core'da 256 toplam ömür sınırı kaldırıldı; RAM kayıtları ve aktif işler
  sınırlıdır. Terminal RAM kopyaları çıkarılsa da eski get/wait/cancel/replay
  diskten aynı kimliği/sonucu verir. Günlüksüz test yöneticisi eski güvenli sınırı korur.
- Günlük düz yerel veri içerir, eski not metnini tutabilir, otomatik silinmez.
  Unknown uzlaştırma ekranı ve dış servis exactly-once garantisi eklenmedi.
- Eski açılış testleri artık yalnız tasks dizininin oluşmasını bekler; yeni
  gözlem restart'ta yeni request_id kullanır. İlk test turundaki eski varsayım
  hataları ve test bağlantısı ResourceWarning'i düzeltildi. İlk genel turdaki
  tek Live/asyncio uyarısı odaklı ve son genel turda tekrarlanmadı; filtre gevşetilmedi.
- 1017 pytest, 17 hedefli günlük testi, Pyright 0 ve 10/10 native aşama geçti.
  Ayrıntılar [test kanıtı](reports/task-journal-checks.json) ve
  [native raporda](reports/task-journal-native.json). Gerçek hesap/ücretli API yok;
  kullanıcı devam/commit onayı verdi; ayrı fiziksel test bildirilmedi.


### README ve oturum kapanışı

- GitHub README, uygulanan özellikler/planlı kapsam/veri akışı/açık sınırlar ve
  test kanıtını ayıracak şekilde İngilizce yeniden yazıldı. Ölçülmemiş hız/RAM,
  sınırsız otonomi veya üretime hazır güvenlik iddiası yok.
- 5.F7.2 kalıcı günlük ve 5.F7.3 güvenli kapasite/retention işleri kabul koşullarıyla
  PLAN.md'ye kaydedildi. Ses tercihleri ve ayrı yanıt seviyesi 5.F8'de bekliyor.
- Kullanıcı 5.F7.1 için devam, commit ve GitHub push onayı verdi; bu, ayrı bir
  fiziksel test sonucunun bildirildiği anlamına gelmez.


### Tek-instance güvenliği (5.F7.1)

- Aynı veri kökü için OS dosya kilidi worker/pencere açılmadan alınır; ikinci
  native instance açık hata ile reddedilir. Başka veri profili engellenmez.
- Kapanış/exception/crash kilidi bırakır; restart yeni süreci ancak bırakıldıktan
  sonra başlatır. PID/stale dosya silme, yeni bağımlılık veya ikinci state sahibi yok.
- Kullanıcının docs altına taşıdığı ana belgeler korundu; aktif linkler ve AGENTS
  yeni belge konumlarına uyarlandı. Tarihsel arşiv değiştirilmedi.
- 1000 pytest, hedefli Pyright 0 ve 10/10 sentetik native aşama geçti;
  gerçek alt süreç/crash ve native giriş/restart testleri de dahil.
  Sonuç: reports/instance-checks.json. Gerçek hesap/ücretli API kullanılmadı.
- 256 kayıt ve kalıcı replay günlüğü bu dilimde değişmedi. 5.F7.2/3 açık.


### Bakım ve belge düzeni

- 133 eski belge/kanıt dosyası özgün göreli yolları ve SHA256 manifestiyle
  docs/eski altına taşındı. Arşiv güncel yönerge değildir.
- Arşiv byte'ları .gitattributes ile Git satır sonu dönüşümünden korunur;
  manifest başka sistemde checkout yapıldığında da geçerlidir.
- ARCHITECTURE.md ve PLAN.md yeniden yazıldı; çalışan komutlar ve köprü sözleşmesi
  docs içinde tekilleştirildi. README'lerdeki çelişkili ilerleme günlükleri kaldırıldı.
- AGENTS.md yeni belge sahipliğini ve her değişiklikte bu kaydın bakımını zorunlu kılar.
- Kullanılmayan MediaRecorder/decode yolu ve yalnız onu sınayan test kaldırıldı;
  gerçek AudioWorklet akışı ve onun regresyonları korundu.
- Backend yürütücüsü olmayan UI rutin/takvim tarayıcıları ve skill/rutin sahte
  başlangıç bildirimleri kaldırıldı. Yerel tanımlar ve eski profil metinleri korundu;
  bağlı olmayan kontroller planlı olarak işaretlendi/devre dışı bırakıldı.
- Sohbet/mikrofon/uyku yaşam döngüsü assistant_session.js'e, görsel kabuk shell.js'e,
  cihazlar devices.js'e ve layout layout.js'e ayrıldı. preferences.js tek tercih
  nesnesidir; yeni framework, bağımlılık veya ikinci durum sahibi eklenmedi.
- Native kabul senaryoları runner'dan native_scenarios.py'ye taşındı.
- REST/Live araç katalogları ortak sabitlere alındı; eski politika testi tip
  uyarıları testin kasıtlı geçersiz girdileri açıkça belirtilerek düzeltildi.
- Denetim bulguları, özelleştirme boşlukları ve gerçek test kapsamı docs/AUDIT.md'dedir.

Doğrulama: 996 pytest, 9 JS suite, 4 browser grubu, 10 native aşama; hedefli
Pyright 0 hata/uyarı, pip check temiz. Runtime Python+JS net 706 satır azaldı.
İlk konum/link testi hataları ve çözümü cleanup-checks.json içinde açıkça kayıtlıdır.

Bakım kullanıcı tarafından kabul edildi, ea8aa15 commit’inde. Gerçek hesap/ücretli
API testi yapılmadı; otomatik kanıtlar docs/reports altında tutulur.

### Önceki kabul edilen temel

- `526bfed`: sayaç listesinde yalnız UI üzerinden silme; tema aksanlarını reactor
  durumundan ayırma. Bu adım kullanıcı tarafından kabul edildi.
- Önceki ayrıntılı değişiklik/kabul geçmişi Git ve docs/eski altında korunur;
  eski günlükler yeniden mimariye kopyalanmaz.
