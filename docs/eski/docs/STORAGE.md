# Atomik JSON kayıt — Aşama 1, sıra 6

Bu belge `v1/app/storage/json_store.py` kayıt katmanını ve `v1/app/config.py`
veri yolu seçimini açıklar. Amaç küçük core verilerini diske kaydederken eski
dosyayı yarım bırakmamaktır. UI, not servisi veya credential deposu değildir.

## Basitçe nasıl çalışır?

Doğrudan notes.json dosyasını açıp içini silerek yazmak yerine yeni içerik aynı
dizinde benzersiz bir geçici dosyaya yazılır. Yazma tamamlanır, bellek tamponu
boşaltılır ve fsync çağrılır; dosya kapandıktan sonra os.replace ile asıl dosyanın
yerine geçirilir. Replace öncesinde hata olursa eski kayıt yerinde kalır.

Bu, atomik değiştirmedir: bu dosyayı okuyan taraf eski veya yeni tam dosyayı görür.
Kaydetme hatası hata olarak döner; 'kaydedildi' diye başarı uydurulmaz.

Dosya biçimi şöyledir; alanların iş kurallarını ileride ilgili servis doğrular:

```json
{"version": 1, "data": {"notes": []}}
```

Sürüm, dosya biçimini belirtir; kayıt revizyonu değildir. Eski sürümden dönüşüm
henüz yoktur. Desteklenmeyen sürüm okunamaz ve üstüne yazılamaz; böylece yeni bir
uygulamanın verisi eski sürüm tarafından yanlışlıkla silinmez.

## Veri konumu ve kullanım

get_data_home() her çağrıldığında önce TASKVEX_HOME'a bakar. Ayarlanmışsa mutlak
bir yol olmalıdır. Yoksa Windows'ta %LOCALAPPDATA%/TaskVex seçilir. Göreli/boş
ayar hatadır; kaynak dizinine yazmaya geri düşülmez. Import ve nesne oluşturma
dosya/dizin yaratmaz; dizin ilk yazma sırasında oluşturulur.

```python
from app.config import get_data_home
from app.storage.json_store import JsonStore

# Bu çağrılar gerçek veri dizinini kullanır; testlerde TASKVEX_HOME geçicidir.
store = JsonStore(get_data_home() / "notes.json")
current = store.read()  # Dosya yoksa None; geçerli boş nesne varsa {}.
# store.write({"notes": []}) yalnız servis açıkça kaydetmek istediğinde çağrılır.
```

read yeni bir nesne döndürür. Okunan sözlüğü değiştirmek diski değiştirmez.
write yalnız JSON nesnesi kabul eder: null/False/0 korunur; tuple, özel nesne,
metin olmayan anahtar, döngü ve sonsuz sayılar reddedilir. Bu sınır ortak
contracts.copy_json yardımcısını kullanır. Diskte yinelenen JSON anahtarları da
sessizce son değer seçilerek kabul edilmez.

## Bozuk dosya ve hata davranışı

| Durum | Davranış |
|---|---|
| Dosya henüz yok | read → None; otomatik dosya oluşturulmaz |
| Geçerli boş data | read → {}; eksik dosyadan ayrıdır |
| Bozuk JSON/UTF-8/zarf | corrupt_data; asıl dosya korunur, üstüne yazma reddedilir |
| Desteklenmeyen sürüm | unsupported_version; silme/sıfırlama yapılmaz |
| Okuma/yazma erişim hatası | read_failed / write_failed; içerik hata mesajına taşınmaz |
| Bellekte geçersiz yeni veri | invalid_data; diske dokunulmaz |

Bozuk dosyayı kurtarmak için host hata durumunu görünür kıldıktan sonra açıkça
recover_corrupt() çağırabilir. Bu metot yalnız bozuk dosyayı benzersiz `.corrupt`
adına taşır ve yedek yolunu döndürür; asıl baytlar değişmez. Bundan sonra read
None döndürür. Varsayılan/veri içe aktarma kararı servise aittir. Sağlıklı dosya
taşınmaz; sürüm veya erişim hatası kurtarma bahanesiyle sıfırlanmaz.
Kurtarma taşıması başarısız olursa recovery_failed döner ve asıl yerinde kalır.
İsteğe bağlı validate callback'i uygulama şemasını da denetler: ContractError
ile reddedilen kayıt korunarak taşınabilir; beklenmeyen validator hatası sağlıklı
veriyi bozuk diye taşımaz. Argümansız eski kullanım korunur. Native ayar onarımı
bu yolu açık kullanıcı onayıyla kullanır; ayrıntı STAGE2_NATIVE.md içindedir.

## Sınırlar

- Tek host/yazıcı varsayılır; read → değiştir → write dizisi bir transaction
  değildir. İleride paralel servisler veya ikinci uygulama süreci yazacaksa
  kayıp güncellemeyi önlemek için ayrıca kilit/transaction gerekir.
- Yol güvenilir host tarafından seçilir. Bu sınıf modelden gelen dosya yolunu
  yetkilendiren bir dosya aracı veya symlink güvenlik sınırı değildir.
- API anahtarı/token/parola bu sıradan JSON dosyalarına konmaz. Şifreleme veya
  credential yönetimi eklenmedi; çağıran servis izinli veri alanlarını seçmelidir.
- Süreç aniden kapanırsa artık `.tmp` kalabilir; açılışta kayıt sayılmaz ve
  otomatik içe alınmaz. Normal hata yollarında geçici dosya temizlenir; temizlik
  erişimi de engelliyse artık kalabilir. Otomatik artık dosya temizleyici yoktur.
- fsync + aynı dizinde replace kullanılır; donanım arızası, güç kesintisi,
  ağ/paylaşımlı dosya sistemi ve OneDrive senkronizasyonu için garanti verilmez.
  Üretim varsayılanı OneDrive altındaki kaynak kodu değil LOCALAPPDATA'dır.
- UI localStorage'ı taşınmadı/değiştirilmedi. Not araçları ve native bağlantı
  bir sonraki aşamalarda bu kayıt katmanını kullanacak.

## Denenenler

`v1` içinde `.\.venv\Scripts\python.exe -m pytest -q -W error`:
**184 test geçti**; önceki 140 teste 44 kayıt/yol testi eklendi. Gerçek geçici
dosyalarla okuma/yazma, UTF-8, boş/eksik ayrımı, bozuk veri kurtarma, sürüm reddi,
geçici dosyaya kısmi yazma, fsync/replace/dizin/erişim hataları doğrulandı.
Alt Python süreci replace öncesi os._exit ile aniden sonlandırıldı; önceki
kaydın okunabildiği ve artık geçici dosyanın kullanılmadığı görüldü.

Gerçek elektrik kesintisi, çok süreçli ortak yazma ve native UI denenmedi.
notes.add/list ile gerçek kayıt hattı da artık test edildi; güncel **215 test**
ve Aşama 1 kabul sonuçları [STAGE1_CORE.md](STAGE1_CORE.md) içindedir.
