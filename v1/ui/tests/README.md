# UI denetim düzeltmeleri regresyon testi

Live ses/mikrofon modülleri için cihaz ve hesap açmayan kontroller (v1 içinde):

```powershell
node ui/tests/live-audio.mjs
node ui/tests/live-mic.mjs
node ui/tests/note-timestamps.mjs
node ui/tests/shutdown.mjs
node ui/tests/clocks.mjs
node ui/tests/catalog.mjs
```

clocks.mjs; model sonucu ile otomatik sekme/ID seçimi, eski snapshot, UI mutasyonu,
alarm tekrar önleme, unknown, native sahiplik latch'i ve ayrı tarayıcı fallback'ini
sınar. Gerçek Python saat/araç hattı tests/test_clocks.py, WebView2 entegrasyonu
ise tests/native_smoke.py içindedir. Hiçbiri gerçek API hesabı gerektirmez.

Mikrofon testi izin reddi/geç izin, iptal, 15 saniye/boyut sınırı, PCM
dönüşümü ve kaynak kapanışını kapsar. Gerçek MediaRecorder/WebM decoder ve
WebView2 kontrolü `tests/native_smoke.py` içindedir; sentetik stream kullanır,
fiziksel mikrofon veya gerçek hesap kabulü sayılmaz.

Cihaz diliminde aynı iki ses testi exact giriş kimliği (sayısal string dahil),
setSinkId başarısı/ret/desteksizlik/3 saniye sınırı, hazırlıkta Stop, cihazın
çıkarılması ve genel taşıma hatasının yerel cihaz hatasını ezmemesini de kapsar.
Native smoke ayrıca Scan, ayar kaydı/reset koruması ve model isteği gönderilmeden
çıkış hazırlığını iptal etmeyi denetler. Fiziksel çoklu cihaz geçişi kullanıcı
kabulüdür; sentetik cihaz listesinden böyle bir sonuç çıkarılmaz.

`audit-fixes.mjs`, gerçek Edge/Chromium üzerinde izole tarayıcı profili ve sahte native köprü kullanır. Uygulama kaynaklarını ve gerçek kullanıcı depolamasını değiştirmez; dış ağ isteklerini engeller.

Mevcut bir `playwright-core` kurulumu ile çalıştırın:

```powershell
$env:PLAYWRIGHT_MODULE = 'C:\path\to\node_modules\playwright-core\index.mjs'
node .\tests\audit-fixes.mjs
```

Edge varsayılan Windows konumunda değilse `BROWSER_PATH` ortam değişkenini tarayıcı yürütülebilir dosyasına ayarlayın. Test yaklaşık 30 saniye sürer; iptal deadline testleri gerçek 12 saniyelik süreyi bekler.

Kapsam: dosya baytları/boş dosya/tekrar seçim/boyut sınırı/okuma ve taşıma hataları; iptal kabulü, ret, tamamlanma, zaman aşımı, eski Promise ve otoritatif bildirim; rutin/takvim döngüsü devir ve pagehide temizliği; eski ayar okuması ve tek anahtar yazımı.

Gerçek Python backend, cihaz sürücüleri, OAuth veya konum sağlayıcısı testi değildir.

5.R8.2–5: catalog.mjs gerçek katalog modülünde tek yükleme, kayıtlı seçim,
hata/boş katalog ve tekrar etmeme kontrolüdür. live-stream.mjs eşik/meter
konfigürasyonu ve eski kaynak ölçümlerini sınar. clocks.mjs bildirim kuyruğunun
busy/sleep/unknown/Disconnect/eski bağlam korumasını da denetler. Native smoke,
API/cihaz yerine sentetik taşıma ve ses kullanır; fiziksel kabul değildir.
