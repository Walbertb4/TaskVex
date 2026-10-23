# Yerel uyku onay sesleri

Bu altı WAV, gerçek host sonucu için sabit kısa TR/EN onaylarıdır. İnternet,
API anahtarı, model çağrısı veya kullanıcı sesi gerektirmez. Windows System.Speech
ile Microsoft Tolga (tr-TR) / Microsoft Zira Desktop (en-US) seslerinden bu
proje için üretildi; model ağırlığı veya ses motoru dağıtılmaz. Gemini'nin
konuşma sesi değildir. Her dosya mono, 24 kHz, PCM16 WAV biçimindedir.

- once: “Uyku moduna geçtim.” / “Sleep mode is on.”
- persistent: “Kalıcı uyku moduna geçtim.” / “Stay asleep mode is on.”
- off: “Kalıcı uyku modunu kapattım.” / “Stay asleep mode is off.”

Yalnız host onayı sonrasında mevcut LiveAudio sahibi oynatır; Mute/Stop ve
seçilen hoparlör uygulanır. Uyku başarısız/belirsizse başarı sesi çalınmaz.
