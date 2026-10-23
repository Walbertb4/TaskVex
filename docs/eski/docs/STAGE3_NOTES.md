# Aşama 3 — Notların backend'e devri

Bu belge not CRUD geçişini açıklar. CRUD; ekleme, okuma, güncelleme ve silmedir.
Native uygulamada kalıcı sahibi Python/backend, tarayıcı-only modda yerel UI'dır.

## İlerleme — 21 Ekim 2026

| Adım | Durum |
|---|---|
| Core'da sabit kimlikle CRUD; registry/policy/testler | Tamamlandı |
| Native olaylar, kesin sonuç ve UI kimlik eşlemesi | Tamamlandı |
| Onaylı eski not aktarımı; yeniden açılışta backend otoritesi | Tamamlandı |
| Eski/yeni not yedeğini core üzerinden yükleme ve kimlikli export | Tamamlandı |
| Tarayıcı yerel modu ve gerçek WebView2 otomatik kabul | Tamamlandı |
| Görünür pencere ve gerçek dosya diyaloğuyla kabul | Computer Use ile tamamlandı; [gözlenen sonuçlar](STAGE3_VISIBLE_ACCEPTANCE.md) |

## Kullanım ve sahiplik

İlk native açılışta notlar salt okunur bekler. `Use backend notes` düğmesi
aktarım onayı ister. İptalde dosya yazılmaz, eski yerel notlar korunur. Onayda
eski core notları korunarak UI notları ayrı kimliklerle eklenir. Aynı metinli
iki not birleştirilmez; tamamlanma durumları taşınır. Boş liste de açık onayla
backend sahipliğine geçirilebilir. İşaret varsa sonraki açılış otomatik bağlanır.

`notes.json` zarfı version=1, data biçimi `{notes:[{id,text,done,created_at?}],ui_migrated:true}`.
Eski yalnız-not-listeli core dosyası hâlâ okunur. `ui_migrated` notlarla aynı
atomik replace içinde yazılır; ayrı bir işaret dosyası yoktur. Son not silinse
de işaret korunur. Böylece gecikmiş yanıt, çökme veya yeniden açılış eski listeyi
ikinci kez eklemez. İşaretli backend varken localStorage yeni veri otoritesi
sayılmaz; görünüm/backup önbelleğidir. Bozuk mevcut depo otomatik sıfırlanmaz.

Not eylemi sırasında ilgili kontroller kapalıdır. UI listeyi yalnız doğrulanmış
backend sonucuyla değiştirir. Ret halinde ekleme metni korunur. 12 saniyede yanıt
yoksa veya taşıma/kayıt sonucu belirsizse otomatik tekrar yapılmaz; not eylemleri
kilitlenir, uygulamayı kapatıp yeniden açarak diskteki sonuç görülmelidir. Geç
eski yanıt bu görünümü değiştiremez. Backend wait süresi 8 saniyedir; bu süre
iptal değildir. Gerçek kayıt yapıldıysa geç iptal kaydı geri almış sayılmaz.

Generic `save` notları yazmaz. Native'de eski `window.vex.addNote/setNotes` ve
not içeren `initApp/loadStore` kalıcı otoriteyi atlayamaz; false döner. Normal
ayar snapshot'ları ve arayüz reset'i notları korur. Başlangıç ayarı onarıldığında
not bağlantısı tekrar okunur. Tarayıcı-only modun eski yerel davranışı korunur.

## Olay ve araç sözleşmesi

Native not zarfı: `{version:1,request_id,arguments}`. Kaynak ve principal güvenilir
bridge tarafından desktop/local-user seçilir; UI'dan alınmaz. Bütün işlemler
aynı registry/policy/tek worker hattını kullanır. Yeni bağımlılık eklenmedi.

| UI olayı | Core aracı | arguments |
|---|---|---|
| notes_init | notes.initialize | `{notes:null}` salt okuma; `{notes:[{text,done}]}` onaylı ilk aktarım |
| note_add | notes.add | `{text}` |
| note_done | notes.update | `{id,done}`; core ayrıca text güncelleyebilir |
| note_del | notes.delete | `{id}` |
| notes_replace | notes.replace | `{notes:[{id,text,done}]}` açık yedek yükleme |

Başarı yanıtı `{ok:true,completed:true,verified:true,task_id,data}` içerir. CRUD
sonucunda data.note, initialize/replace sonucunda data.notes ve data.migrated
vardır. Hata başarıya dönüştürülmez; belirsizlikte `unknown:true` gelir. İstek
kimliği manager'a aynen aktarılır. Mutasyonlar notes.write, listeleme notes.read
ister. Kimlikler yeniden açılışta değişmez; hedef metin veya dizi sırası değildir.

Metin en fazla 10.000 karakterdir ve yalnız boşluk olamaz. done boolean'dır.
Bilinmeyen alan, bozuk kayıt veya yinelenen id reddedilir. Bulunmayan id
FAILED/not_found döndürür; dosya yaratılmaz/yazılmaz. Her mutasyon tam belgeyi
geri okuyarak doğrulanır; uyuşmazlık UNKNOWN/commit_unverified'dır. Manager
belirsizlikte yeni işleri durdurur. Replay engeli açık manager oturumundadır;
kalıcı görev günlüğü ve çok süreçli eşzamanlı yazma henüz yoktur.

## Yedek ve kısmi hata

Export kimlikleri korur. Eski `{t,d}` veya metin yedeği yeni kimlik alır; yeni
kimlikli yedek mevcut kimlikleri korur. Native import önce dosyayı doğrular,
sonra ayar kaydını, ardından tek notes.replace komutunu uygular. Yerel snapshot
notları ikinci kez uygulamaz. İlk aktarım bitmeden veya not işi sürerken not
import'u başlamaz. Kontroller import boyunca korunur; bitince geri açılır.

Ayar dosyası, not dosyası ve localStorage tek transaction değildir. Ayarlar
başarılı, not restore başarısız olabilir; bunu tam import başarısı saymayız.
Backend notları yazılıp yerel cache/skill/rutin kaydı başarısızsa backend'deki
yeni notlar geri alınmış gibi gösterilmez; önceki yerel tercihler geri yüklenir,
kısmi kayıt açıkça bildirilir. Kaynak yedek dosyası silinmez. Yerel önbellek
hatası başarıyla kaydedilmiş backend notunu yok saymaz.

## Test kanıtı

- `.\.venv\Scripts\python.exe -m pytest -q -W error`: **321 test geçti**.
- Gerçek WebView2: [stage3-native-smoke.json](stage3-native-smoke.json), sekiz
  süreç. Gerçek UI ekle/tamamla/sil, aynı metinli farklı kimlikler, yeniden açma,
  yazma reddinde formu koruma, çift tıklamada tek komut, geç yanıtı yok sayma,
  import/export, ayar kurtarma ve pencere kontrollerini kapsar.
- [stage3-browser-notes.json](stage3-browser-notes.json): tarayıcı-only ve
  simüle native. Eski not aktarımını iptal/onay, tekrar açma, setter/snapshot
  engeli, eski/yeni yedek, yinelenen kimlik reddi ve sıfır pageerror/rejection.
  Betik mevcut çalışma alanında work/diagram-check/stage3-browser-notes.mjs'dir.
- Python testleri gerçek geçici dosyalarda ilk aktarımın tek seferliğini,
  işaretin son not silinse de kalmasını, bozuk veri ve yazma hatası korumasını,
  geri okuma belirsizliğini, sabit kimliği ve izinleri denetler.

Native pencereler hidden'dır. Confirm seçimi ve export dosya seçim sonucu testte
kontrollüdür; gerçek Blob export dosyası yazılıp içeriği okunur. Bunlar görünür
pencerede insanın diyalogla etkileşimi veya fiziksel ses/donanım testi değildir.
Testler kullanıcı verisi/hesabı kullanmaz. İlk native denemelerde test raporu
adı notes.json ile çakıştı; raporlar report- önekiyle ayrıldı ve bütün fazlar
sonrasında yeniden çalıştırıldı. Başarısız denemeler uygulama başarısı sayılmadı.

## Görünür kabul ve sonraki aşama

İzole TASKVEX_HOME ile görünür pencerede aktarımı iptal/onay, not ekle/tamamla/sil,
gerçek Save As/Open ile export/import ve iptal, gerçek restart ve Shutdown
kontrol edildi. [Görünür kabul belgesi](STAGE3_VISIBLE_ACCEPTANCE.md) kullanılan
sentetik veriyi ve gözlenen sonuçları açıklar. İlk aktarımın bu görünür turu boş
listeyleydi; boş olmayan eski notlar Python/tarayıcı testlerinde doğrulandı.
Aşama 3'ün planlı kabulü tamamlandı; insan UX araştırması veya fiziksel ses
testi yapıldı anlamına gelmez. [Aşama 4](STAGE4_APPS.md) ilk uygulama plugininin
adımlarını ve tamamlanan katalog dilimini açıklar.


## 22 Ekim — Oluşturulma zamanı uzantısı

Not kaydı isteğe bağlı `created_at` alanını taşır. Yeni ekleme backend’in
UTC ISO milisaniyeli saatini yazar; normal update/delete argümanları alanı
kabul etmez. Edit/done, ID ve tarihi korur. Eski kayıtta eksik/null bilinmiyor
anlamındadır; eski dosya okumak yeni tarih veya ID üretmez. İlk aktarım ve
yedek restore geçerli alanı korur; browser-only yeni notun saati tarayıcıda
alınır. Takvimde geçersiz, zaman dilimsiz veya standart dışı tarih reddedilir.
Bu alan çoklu yazar/sıralama garantisi değildir. Güncel sınır ve testler
[STAGE5_MODEL.md](STAGE5_MODEL.md) içindedir.
