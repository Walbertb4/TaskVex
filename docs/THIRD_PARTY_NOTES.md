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
