# Aşama 1 / sıra 1 — Python ortamı

21 Ekim 2026. Tamamlanan kapsam: v1/.venv, pyproject.toml, geliştirme test aracı ve geçici veri izolasyonu. Core sözleşmeleri/yürütücüsü henüz yazılmadı.

- Ortam, sistemde bulunan Python 3.14.7 ile oluşturuldu; proje minimumu Python 3.11 olarak belirtildi. Diğer Python sürümlerinde henüz test yapılmadı.
- Üretim bağımlılığı şimdilik yok. pywebview, Gemini, ses veya Mark bağımlılıkları kurulmadı.
- pyproject.toml tek bağımlılık bildirim kaynağı. dev grubu pytest>=9,<10 içerir; çözülen sürüm pytest 9.1.1.
- requirements-dev.lock.txt, kurulan geliştirme paketlerinin tam sürüm snapshot'ıdır; pyproject.toml'dan bağımsız elle yönetilecek ikinci liste değildir. Hash içeren evrensel lock veya yayın güvenliği garantisi sayılmaz.
- tests/conftest.py, test başına geçici TASKVEX_HOME tanımlar. Uygulama config modülü yazılırken ortam değişkeni bootstrap aşamasında okunmalı; gerçek kullanıcı verisiyle test yapılmamalı.
- pip check geçti. pyproject TOML parse edildi; doğru proje ve boş runtime bağımlılıkları doğrulandı; interpreter'ın venv içinde çalıştığı doğrulandı.
- pytest toplama komutu çalıştı; henüz davranış testi bulunmadığından `no tests collected` / exit 5 beklenen sonuçtur. Bu, core testleri geçti demek değildir. Gerçek core testleri Aşama 1 / sıra 2 ve sonrasında eklenecek.

Kurulum/çalıştırma komutları: [v1 README](../v1/README.md).

## Not düzeltmesi

notes.js içinde üç yerel kayıt çağrısı emitSave:false oldu. Ekleme, tamamlama ve silme yalnız ilgili note_* mutasyonunu gönderiyor. Aynı metinli kayıtların kimlikle yönetilmesi, backend onayına bağlı UI ve kayıt hatasında rollback bu küçük değişikliğin kapsamı değildir; native not geçişinde ele alınacak. HTML/CSS görünümü değiştirilmedi.

Tarayıcı kanıtı: [note-events-fix.json](note-events-fix.json). Native taşıma simüledir; gerçek PyWebView denenmedi.
