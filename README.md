# TaskVex

Windows için Python/PyWebView2 ve vanilla JavaScript ile geliştirilen masaüstü
asistanı. Ana konuşma yolu Gemini Live'dır. Model araç önerir; registry, policy
ve tek TaskManager doğrulanan işlemi yürütür. Proje geliştirme aşamasındadır.

## Çalışan kapsam

- Yazı/ses sohbeti, akış halinde transkript/ses, Stop, Mute ve mikrofon kontrolü.
- Yerel wake-word, tek seferlik/persistent uyku ve bağımsız idle sleep ayarı.
- Onaylı backend not aktarımı; ID/tarih/filtre ile CRUD ve atomik toplu silme/tamamlama.
- Çoklu timer/stopwatch; UI ve model aynı backend durumunu kullanır.
- Tema/profil/düzen kaydı, Windows Credentials'da API anahtarı, API Live model kataloğu.
- Allowlist uygulama araçları core'da; model yalnız kataloğu görebilir.

Google, Telegram/Discord, kalıcı kullanıcı hafızası, skill/rutin yürütme ve dört GUI
katmanı henüz uygulanmadı. Yerel skill/rutin editörleri tanımları saklar. REST adaptörü
korunur; ana masaüstü deneyimi Live'dır. Bu bir sınırsız bilgisayar kontrol ajanı değildir.

## Başlatma

PowerShell, mevcut geliştirme ortamında:

```powershell
cd C:\Users\batue\OneDrive\Desktop\TaskVex\v1
.\.venv\Scripts\python.exe -m app.main
```

Debug için `--debug` ekleyin. Yeni ortam, yerel wake modeli ve testler için
[v1 rehberini](v1/README.md) okuyun. Tarayıcı görünümü için [UI rehberi](v1/ui/README.md).
Anahtar Settings üzerinden açıkça kaydedilir; key/token'ı kaynak koda koymayın.

## Belgeler

- [Mimari](ARCHITECTURE.md): bugünkü sahiplikler ve hedef tasarım.
- [Plan](PLAN.md): aşamalar, açık işler ve kabul durumu.
- [Changelog](CHANGELOG.md): değişikliklerin tek kaydı.
- [Komutlar](docs/COMMANDS.md): çalışan kullanıcı yetenekleri.
- [Sözleşme](docs/UI_BACKEND_CONTRACT.md) ve [denetim](docs/AUDIT.md).
- [Arşiv](docs/README.md): eski belgeler özgün yollar/hash ile korunur.

## Sınırlar ve lisans

Aktif ses/model işlemleri Google'a gider; uyku sırasında wake algılama yereldir.
Kullanıcı verisi repo dışında tutulur. Tek süreç/yerel kullanıcı hedeflenir; görev
kayıt kapasitesi, restart sonrası replay ve çoklu instance sınırları denetimde açıktır.
RAM/latency için genel performans garantisi verilmez; ağ, model ve cihaz etkiler.

Özgün katkılar [MIT](LICENSE). Bağımlılık/varlık/model hakları ayrı değerlendirilir:
[THIRD_PARTY_NOTES](THIRD_PARTY_NOTES.md). Referans repo TaskVex runtime'ının parçası değildir.
