# Aşama 3 — Görünür Windows kabulü

Bu belge önceki hidden WebView2 ve simüle diyalog testlerinden kalan görünür
pencere/gerçek dosya diyaloğu kontrolünü kaydeder. Tarih: 21 Ekim 2026.
Windows arayüzü Computer Use (`@oai/sky`) ile kullanıldı; onay ve dosya
diyalogları değiştirilmedi veya taklit edilmedi. Bu insan kullanılabilirlik
araştırması ya da fiziksel ses testi değildir.

## İzolasyon

Uygulama ayrı TASKVEX_HOME ile açıldı:
`C:/Users/batue/Documents/Codex/2026-10-20/mi/work/stage3-visible-acceptance`.
Kullanıcının asıl TaskVex veri dizini kullanılmadı. Oluşturulan tek notun metni
`Stage 3 visible acceptance` idi; bütün ekleme/silme/restore işlemleri bu sentetik
not üzerinde yapıldı. İlk aktarım kontrolünde boş yerel liste kullanıldı;
boş olmayan eski kayıtların aktarımı önceki Python/tarayıcı testleriyle doğrulandı.

## Gözlenen sonuçlar

| Kontrol | Sonuç |
|---|---|
| Görünür başlangıç | Mor tema, reactor, paneller ve MODEL OFFLINE durumu gözlendi; not bekleme mesajı ve aktarım düğmesi okunabiliyor |
| İlk aktarımı iptal | Gerçek confirm penceresinde Cancel seçildi; notes.json oluşmadı, not kontrolleri beklemede kaldı |
| İlk aktarımı onay | Gerçek confirm penceresinde OK seçildi; not kontrolleri açıldı ve tek seferlik aktarım işareti yazıldı |
| Not ekleme | Gerçek giriş alanı ve + düğmesi kullanıldı; not görünümü ve notes.json eşleşti |
| Not tamamlama | Checkbox tıklandı; görünümde üzeri çizildi, diskte done=true doğrulandı |
| Gerçek export | Settings > System > Export ile Windows Save As açıldı; dosya test dizinine kaydedildi; JSON içeriği okundu |
| Export iptali | İkinci gerçek Save As diyaloğunda Cancel seçildi; uygulama dosya yazıldı diye bildirmedi |
| Not silme | Yalnız sentetik notun ✕ düğmesi kullanıldı; diskte notes=[] ve ui_migrated=true doğrulandı |
| Gerçek import | Windows Open diyaloğundan az önceki JSON seçildi; not aynı id ve done=true ile geri geldi; başarı durumu gösterildi |
| Import iptali | İkinci gerçek Open diyaloğu Escape ile iptal edildi; notlar değişmedi |
| Gerçek restart | UI Restart app düğmesi kullanıldı; eski pencere kapandı ve farklı pencere kimliğiyle yeni süreç açıldı |
| Yeniden açılış | Notun tamamlanmış görünümü, kimliği ve tek kayıt olarak kalması doğrulandı; tekrar aktarım istenmedi |
| Normal kapanış | UI Shutdown kullanıldı; test penceresinin kapandığı ayrıca kontrol edildi |

Yedek `visible-backup.json` dosyasında notun id/t/d alanları, backend dosyasında
aynı id/text/done alanları karşılaştırıldı. Kimlik eşitliği ve done=true bir
assertion ile ayrıca kontrol edildi. Ekran görüntüleri kontrol sırasında
görüldü; bu belgeye görsel dosya arşivi eklenmedi.

## Araç sınırları ve kapsam

Bazı UI Automation öğeleri modal/indirme paneli açılınca geçersiz koordinat
verdi. Yeni gözlem alındı; gerekli yerlerde güncel ekran koordinatı veya normal
klavye kullanıldı. WebView2 indirme bildirimi ayar düğmesini kapatınca ayarlara
mevcut Ctrl+K > Settings komutuyla ulaşıldı. Bu hatalar başarılı tıklama diye
sayılmadı. Gerçek dosya yazımı ve backend sonucu ayrıca dosyadan doğrulandı.

Aşama 3'ün önceki **321 Python**, **8 hidden native süreç** ve **2 tarayıcı**
kabulü bu görünür kontrolle tamamlanır. Aşama 4 katalog eklemesinden sonra bütün
Python süiti ayrıca **332 geçti**. Bu görünür turda yeni UI düzeltmesi gerekmedi.
Gerçek hesap/donanım, çok süreçli yazma ve ayrı depolara ortak transaction
garantisi verilmez. Sonraki geliştirme [Aşama 4](STAGE4_APPS.md) içindedir.
