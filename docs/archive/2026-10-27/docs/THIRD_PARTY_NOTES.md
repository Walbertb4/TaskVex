# Third-party sources and license boundaries

TaskVex's original contributions are offered under the root MIT LICENSE.
This does not relicense third-party code, assets or dependencies.

## Mark LVI reference checkout

- Local directory: Mark-LVI-main/.
- Upstream identified by its README: https://github.com/FatihMakes/Mark-LVI .
- Local LICENSE: copyright 2026 FatihMakes, CC BY-NC 4.0.
- Purpose: inspection/reference only. No code was imported into a TaskVex backend in stage 0.
- Excluded from version control by .gitignore; future packages must also exclude it explicitly. Git ignore rules alone are not a packaging rule and do not untrack already tracked files.
- Modifying or renaming a copied file does not remove its original license conditions. Any future reuse requires a recorded source/version, applicable license and notices, modifications, and a compatible intended use.

Official license summary: https://creativecommons.org/licenses/by-nc/4.0/ .

## Existing UI and assets

The UI predates stage 0. Its complete authorship/asset license provenance was not audited in this stage. The root MIT file is not proof that all pre-existing icons, fonts, sounds or external code may be relicensed. Check source and redistribution terms before a public release; retain required notices. Do not publish real credentials or runtime data.

## Dependencies

Runtime dependencies are declared in v1/pyproject.toml; the exact tested development environment is v1/requirements-dev.lock.txt. Third-party packages keep their own licenses. A distributable package notice/SBOM and pre-existing UI asset provenance review remain release work. Do not inherit the reference repository requirements wholesale.

## Local keyword spotting — Stage 5

- sherpa-onnx and sherpa-onnx-core 1.13.8: upstream code https://github.com/k2-fsa/sherpa-onnx , Apache-2.0; installed as dependencies, not copied/relicensed. Retain upstream notices when packaging.
- Model: sherpa-onnx-kws-zipformer-zh-en-3M-2025-12-20, official kws-models release. Archive SHA256: 68447f4fbc67e70eee3a93961f36e81e98f47aef73ce7e7ca00885c6cd3616a6. TaskVex uses only chunk8 int8 encoder/joiner, fp32 decoder, tokens and pronunciation lexicon.
- Source/setup: https://k2-fsa.github.io/sherpa/onnx/kws/pretrained_models/index.html . Runtime files live outside Git in the user's local model cache. No model, training data, audio corpus or upstream Python example was imported into TaskVex MIT source. The wrapper is TaskVex code.
- Do not infer a weight/data redistribution license from the code license. Upstream weight-license clarification is tracked at https://github.com/k2-fsa/sherpa-onnx/issues/3760 ; confirm the applicable weight/lexicon terms before bundling a release. This development setup downloads directly from upstream and does not redistribute the weights.
- Windows SAPI synthetic speech was used only in ignored runtime test files; no user voice was collected. Engine-positive/negative tests do not establish real-microphone accuracy.


## Windows media API projection — 6.2.5a

- PyWinRT: winrt-runtime, winrt-Windows.Foundation, winrt-Windows.Media and
  winrt-Windows.Media.Control, all 3.2.1. Source: https://github.com/pywinrt/pywinrt ;
  MIT license. Installed as dependencies; no upstream source was copied into app/.
- These are Windows API Python type projections, not a media player or AI provider.
  Pins and Windows-only project markers are in pyproject.toml; the tested Windows
  environment is requirements-dev.lock.txt. Preserve upstream notices in packaging.


## Weather and place data — 6.4

- Open-Meteo forecast/geocoding are external public services, not copied source
  code or an installed dependency. TaskVex source remains MIT; no AGPL server code
  is imported. Weather data is CC BY 4.0 with attribution; place data originates
  from GeoNames. README links credit Open-Meteo and GeoNames.
- The default public API is for non-commercial use under provider request limits;
  commercial deployment needs a provider arrangement/configuration review. Do not
  claim the free endpoint permits every distribution or unlimited service use.
- [Terms](https://open-meteo.com/en/terms),
  [forecast API](https://open-meteo.com/en/docs),
  [geocoding/source attribution](https://open-meteo.com/en/docs/geocoding-api).
- Explicit weather setup sends place searches or approximate coordinates to these
  services. No Gemini key or personal account is used for weather requests.

## Demo packaging tools

PyInstaller 6.22.3 and hooks-contrib 2026.9 are pinned in the separate build lock;
PyInstaller is GPL with its distribution exception. Keep the supplied license
and exception notices: https://pyinstaller.org/en/stable/license.html . The demo
copies installed distribution license/NOTICE files into THIRD_PARTY_NOTICES.
BUILD_ENVIRONMENT.json records installed build packages, not an exact bundled
SBOM. Wake weights/lexicon are deliberately excluded; the existing explicit
upstream setup remains optional. This does not close the full UI asset
provenance audit or signed-production-release work.
