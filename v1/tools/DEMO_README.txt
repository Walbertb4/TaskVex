TaskVex Demo - Windows x64

Unzip the WHOLE archive to a writable local folder, then run TaskVexDemo.exe.
Do not move the EXE out of its folder. Python does not need to be installed.
Supported target: Windows 10/11 x64, .NET Framework 4.8 and Microsoft Edge WebView2 Runtime.
ARM64, 32-bit Windows, macOS and Linux are not supported by this build.

If WebView2 is missing, install it from Microsoft:
https://developer.microsoft.com/microsoft-edge/webview2/
Internet and your own Gemini API key are needed for AI responses.
This unsigned demo may trigger Windows SmartScreen. It is not a signed installer.

Data and credentials: %LOCALAPPDATA%\TaskVexDemo (separate from development TaskVex).
No developer API key, notes or personal settings are included.

Optional wake word setup:
Close the app, then run "Setup wake model.cmd" once with an internet connection.
This explicitly downloads hash-verified model files directly from upstream.
Wake model weights are NOT redistributed in this demo; without setup, local
wake from sleeping is unavailable. Normal text/Live features remain separate.
Model origin/license notes: https://github.com/k2-fsa/sherpa-onnx/issues/3760

This is a development demo, not a finished product. Media information is read-only;
media playback controls and other planned integrations are not implemented.
Other hardware, clean PCs and real AI-account acceptance have not been certified.
See LICENSE.txt and THIRD_PARTY_NOTICES for bundled dependency license notices.
BUILD_ENVIRONMENT.json lists the build environment, not a precise bundled-file SBOM.
