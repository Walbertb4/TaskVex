# Changelog

Bu dosya TaskVex değişikliklerinin tek güncel kaydıdır. Mimari kararların mevcut
hali ARCHITECTURE.md, yapılacak işler PLAN.md içindedir. Henüz sürüm yayımlanmadı.

## Unreleased

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

Bu bakım diliminin kullanıcı kabulü ve commit'i bekleniyor. Gerçek hesap/ücretli
API testi yapılmadı; otomatik kanıtlar docs/reports altında tutulur.

### Önceki kabul edilen temel

- `526bfed`: sayaç listesinde yalnız UI üzerinden silme; tema aksanlarını reactor
  durumundan ayırma. Bu adım kullanıcı tarafından kabul edildi.
- Önceki ayrıntılı değişiklik/kabul geçmişi Git ve docs/eski altında korunur;
  eski günlükler yeniden mimariye kopyalanmaz.
