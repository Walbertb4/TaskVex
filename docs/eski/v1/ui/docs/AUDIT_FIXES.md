# Bağımsız denetim sonrası düzeltmeler

R01–R14 bulguları UI/tarayıcı sözleşmesi seviyesinde düzeltildi:

- Snapshot ek alanları ve eski yerel kayıtlar doğrulanır; bozuk alanlar geçerli veriyi silmeden kurtarılır.
- Skill/rutin kimlikleri bütün giriş yollarında çakışma kontrolünden geçer; açık tekrar kimlikler reddedilir.
- Backend konum bildirimi outbound save üretmez; observer native sonucu kilitlemez.
- Ready bildirimi kamera state'i kurulduktan sonra gönderilir.
- Eski konuşma ve shutdown zamanlayıcıları yeni durumu/Restart'ı etkileyemez.
- Başarısız form kayıtları geri alınır; tekrar deneme çift kayıt oluşturmaz.
- Bearer hata biçimi maskelenir; bozuk timeline aramayı çökertmez.
- Açık boş katalog seçenekleri temizler; sıfır süre sayacı doğru sıfırlar.
- Modallar odak ve dialog semantiği kullanır; arka plan etkileşimi sınırlandırılır.

Bkz. [Güncel sözleşme](UI_BACKEND_CONTRACT.md). HTML/CSS ve tasarım değiştirilmedi. Doğrulamalar sentetik backend ile yerel HTTP/Edge ortamında yapıldı; gerçek native/donanım/dış servis onayı değildir.
