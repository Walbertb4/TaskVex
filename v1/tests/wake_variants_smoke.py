"""Control local wake variations with real KWS and artificial SAPI sounds.

It is only a testing tool; Does not add speech audio/player to the application. pre-installed,
runtime/wake-model with hash verification is used. Network and microphone are not used;
WAV files are generated and deleted in the temporary folder. It is not physical user acceptance.
"""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile
import sys
import wave

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.session import wake_word


def run() -> None:
    """By restarting the same engine positive/negative passes the sounds through the actual PCM."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', type=Path,
                        default=Path(__file__).resolve().parents[2] / 'logs/reports/wake-variants-smoke.json')
    args = parser.parse_args()
    model = Path(__file__).resolve().parents[1] / 'runtime' / 'wake-model'
    wake_word.model_home = lambda: model
    # Fixed test texts; user text or file path is not included in the shell.
    script = r"""
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$format = New-Object System.Speech.AudioFormat.SpeechAudioFormatInfo(16000,[System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen,[System.Speech.AudioFormat.AudioChannel]::Mono)
try {
    foreach($item in @(@('vex','Vex'),@('rex','Rex'),@('ex','ex'),@('next','next'),@('normal','Hello, how are you today?'))) {
        $synth.SetOutputToWaveFile((Join-Path (Get-Location) ($item[0]+'.wav')), $format)
        $synth.Speak($item[1])
        $synth.SetOutputToNull()
    }
} finally { $synth.Dispose() }
"""
    results = []
    with tempfile.TemporaryDirectory(prefix='taskvex-wake-variants-') as folder:
        subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-Command', script],
                       cwd=folder, check=True, capture_output=True, timeout=30)
        detector = wake_word.WakeWord('Vex')
        for repeat in range(3):
            for name in ('vex', 'rex', 'ex', 'next', 'normal'):
                detector.restart()
                with wave.open(str(Path(folder) / (name + '.wav')), 'rb') as source:
                    assert (source.getframerate(), source.getsampwidth(), source.getnchannels()) == (16000, 2, 1)
                    pcm = bytes(9600) + source.readframes(source.getnframes()) + bytes(32000)
                hit = False
                boundary_valid = False
                for sequence, offset in enumerate(range(0, len(pcm), 3200)):
                    if detector.feed(sequence, pcm[offset:offset+3200].ljust(3200, b'\x00')):
                        hit = True
                        boundary_valid = 0 <= detector.start_sequence <= sequence
                        break
                expected = name in ('vex', 'rex')
                results.append({'sample': name, 'repeat': repeat + 1, 'detected': hit,
                                'boundary_valid': boundary_valid, 'ok': hit == expected and (not hit or boundary_valid)})
    report = {'ok': all(r['ok'] for r in results), 'real_local_kws': True,
              'audio': 'synthetic Windows SAPI, not a user microphone', 'results': results}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', 'utf-8')
    print(json.dumps(report, ensure_ascii=True))
    assert report['ok'], 'See the report: a positive or negative synthetic sample failed'


if __name__ == '__main__':
    run()
