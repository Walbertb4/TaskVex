"""Local sherpa-onnx keyword detection; Does not operate model or tool.

16 kHz PCM is given to this CPU process only; network, disk audio recording and second microphone
There is no. If --setup is run explicitly, it will download the fixed upstream model; application
There is no silent download at the beginning. Weights do not count towards the TaskVex MIT license.
"""
from array import array
from collections import deque
from hashlib import sha256
from pathlib import Path
import re
import sys
import math
from uuid import uuid4

from app.config import get_data_home

ARCHIVE = 'sherpa-onnx-kws-zipformer-zh-en-3M-2025-12-20'
ARCHIVE_HASH = '68447f4fbc67e70eee3a93961f36e81e98f47aef73ce7e7ca00885c6cd3616a6'
FILES = {
    'decoder-epoch-13-avg-2-chunk-8-left-64.onnx': '63a22dd60f40fff082ac3e09afa507f6787da36df76ded2fbe145fa233e22c21',
    'en.phone': 'f7000ec3a90544c0c7c16090d8951779c2b322e14dad5006290f498567d439ea',
    'encoder-epoch-13-avg-2-chunk-8-left-64.int8.onnx': '2ca84d6bfe73e1ea3c9c49f600f7cad1c9ddd423c53c906b8bfe802444dd78d5',
    'joiner-epoch-13-avg-2-chunk-8-left-64.int8.onnx': '190d4067b4cc20b72a42a1916e69d92052000fb7051a427ebb1bc72a69207dc1',
    'tokens.txt': '2d3f32311f9b692b964da3c90e830258d3e78e013cb0c992dbfb15cd5a1a71b0',
}


# This list does not resolve the command intent: only the locale of the same address voice/spelling
# are their counterparts. The X/EX alone is not meant to evoke casual conversation.
VEX_SPELLINGS = ('Vex', 'Veks', 'Rex')


def wake_spellings(word: str) -> tuple[str, ...]:
    """Limited variations of the selected address; In a proper name, only that name is valid.

    Local KWS and Live's solo-address distinction use the same definition. similarity
    does not perform prediction or execution command interpretation; It does not change the profile value.
    """
    return VEX_SPELLINGS if word.casefold() in {s.casefold() for s in VEX_SPELLINGS} else (word,)


def is_wake_only(text: str, word: str) -> bool:
    """True if the full transcript addresses only; The task following the address is preserved."""
    return text.casefold().strip(' \t\r\n.!?,:') in {s.casefold() for s in wake_spellings(word)}


class WakeAlignmentError(ValueError):
    """There is perception, but there is no safe volume limit; It leaves error packet/device."""


def model_home() -> Path:
    """Model cache separate from source code and credential file."""
    return get_data_home() / 'models' / 'wake'


def setup():
    """Download with constant SHA256; extracting archive paths run/freely."""
    from io import BytesIO
    import tarfile
    from urllib.request import urlopen
    with urlopen(f'https://github.com/k2-fsa/sherpa-onnx/releases/download/kws-models/{ARCHIVE}.tar.bz2', timeout=60) as response:
        data = response.read(40_000_001)
    if len(data) > 40_000_000 or sha256(data).hexdigest() != ARCHIVE_HASH:
        raise ValueError('Wake model archive integrity check failed')
    directory = model_home()
    directory.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=BytesIO(data), mode='r:bz2') as archive:
        for name, digest in FILES.items():
            member = archive.getmember(f'{ARCHIVE}/{name}')
            if not member.isfile() or member.size > 10_000_000:
                raise ValueError('Invalid model archive member')
            source = archive.extractfile(member)
            assert source is not None
            content = source.read()
            if sha256(content).hexdigest() != digest:
                raise ValueError('Wake model file integrity check failed')
            target = directory / name
            temporary = target.with_suffix(target.suffix + '.tmp')
            temporary.write_bytes(content)
            temporary.replace(target)
    print('Local wake model installed. Audio is not uploaded.')


class WakeWord:
    """Receives serial PCM on bridge's short lock; It does not have its own thread/worker."""

    def __init__(self, word: str, sensitivity: float = 50):
        if type(sensitivity) not in (int, float) or not math.isfinite(sensitivity) or not 0 <= sensitivity <= 100:
            raise ValueError('Wake sensitivity must be between 0 and 100')
        # Higher sensitivity is a lower acoustic probability threshold; 50 retains the old 0.25.
        threshold = .45 - .004 * sensitivity
        import sherpa_onnx
        if sherpa_onnx.__version__ != '1.13.8':
            raise ValueError('Wake alignment requires the pinned sherpa-onnx version')
        if not isinstance(word, str) or not re.fullmatch(r'[A-Za-z]+(?: [A-Za-z]+){0,2}', word) or len(word) > 64:
            raise ValueError('Use one to three supported English words')
        directory = model_home()
        for name, digest in FILES.items():
            path = directory/name
            if not 0 < path.stat().st_size <= 10_000_000 or sha256(path.read_bytes()).hexdigest() != digest:
                raise ValueError('Wake model integrity check failed; run wake setup')
        # Veks are the same VEX phonemes; REX is a separate pronunciation. same acoustic
        # we don't add the array twice; All candidates use one available engine.
        phrases = [['VEX' if part == 'VEKS' else part for part in s.upper().split()] for s in wake_spellings(word)]
        requested = {part for phrase in phrases for part in phrase}
        lexicon = {}
        for line in (directory / 'en.phone').read_text(encoding='utf-8').splitlines():
            parts = line.split()
            if parts and parts[0] in requested:
                lexicon.setdefault(parts[0], parts[1:])
        if any(item not in lexicon for item in requested):
            raise ValueError('Wake word is not in the local English pronunciation dictionary')
        pronunciations = list(dict.fromkeys(' '.join(phone for item in phrase for phone in lexicon[item]) for phrase in phrases))
        tokens = {line.split()[0] for line in (directory/'tokens.txt').read_text(encoding='utf-8').splitlines() if line.split()}
        if any(phone not in tokens for phones in pronunciations for phone in phones.split()):
            raise ValueError('Wake pronunciation has unsupported tokens')
        # The C++ engine terminates the process on the empty keyword file; before
        # Write the verified phonemes to the config file specific to this instance.
        keyword_file = directory/f'keyword-{uuid4().hex}.txt'
        keyword_file.write_text(''.join(phones + ' @WAKE\n' for phones in pronunciations), encoding='utf-8')
        try:
            self._spotter = sherpa_onnx.KeywordSpotter(tokens=str(directory/'tokens.txt'),
                encoder=str(directory/'encoder-epoch-13-avg-2-chunk-8-left-64.int8.onnx'),
                decoder=str(directory/'decoder-epoch-13-avg-2-chunk-8-left-64.onnx'),
                joiner=str(directory/'joiner-epoch-13-avg-2-chunk-8-left-64.int8.onnx'),
                keywords_file=str(keyword_file), num_threads=1, keywords_threshold=threshold, num_trailing_blanks=1)
        finally:
            keyword_file.unlink(missing_ok=True)
        self.restart()

    def restart(self):
        """Weights remain in RAM; Each sleep gets new ID, decoder and empty buffer.

        The old sound/hit/sequence is not reused. In the serial lock of the same bridge
        is called; There is no need to rebuild the expensive model verification/installation.
        """
        self._stream = self._spotter.create_stream()
        self.id = uuid4().hex
        self._sequence = self._packets = 0
        self.start_sequence = 0
        self._recent: deque[tuple[int, bytes]] = deque(maxlen=30)

    def _boundary(self, result, sequence: int) -> int:
        """Reverify hit with local audio for up to 3 s; It is not a repeat of tool/API.

        1.13.8 decoder resets its time counter in silence; Python result
        this does not turn on the global offset of the reset. Counting old timestamps as global
        Instead, a short verification stream whose beginning is known only at the time of hit.
        opens. The margin outside the word duration is shorter than the 1.5 s internal-reset threshold;
        so there can't be a hidden silence reset before the new hit. This condition or
        If the volume limit cannot be verified, the time will not be fitted and no audio will be sent to Live.
        """
        times = list(result.timestamps)
        if not times or any(not math.isfinite(t) or t < 0 for t in times) or times != sorted(times):
            raise WakeAlignmentError('Wake boundary was not confirmed')
        span = times[-1] - times[0]
        count = math.ceil((span + .8) * 10)
        if count > 30:
            raise WakeAlignmentError('Wake utterance exceeds the local prefix')
        window = list(self._recent)[-count:]
        verify = self._spotter.create_stream()
        samples = array('h')
        samples.frombytes(b''.join(pcm for _, pcm in window))
        if sys.byteorder != 'little':
            samples.byteswap()
        # Fill in the short look-ahead of the new encoder; these zeros alone
        # belongs to verification. It is not transferred to Live and is not included in the hit time.
        verify.accept_waveform(16000, [sample / 32768 for sample in samples] + [0.0] * 4800)
        while self._spotter.is_ready(verify):
            self._spotter.decode_stream(verify)
            checked = self._spotter.keyword_spotter.get_result(verify)
            stamps = list(checked.timestamps)
            if checked.keyword == result.keyword and stamps:
                if (any(not math.isfinite(t) or t < 0 for t in stamps) or stamps != sorted(stamps)
                        or stamps[-1] >= len(window) / 10
                        or len(window) / 10 + .3 - (stamps[-1] - stamps[0]) >= 1.5):
                    raise WakeAlignmentError('Wake alignment could include an untracked reset')
                start = window[0][0] + math.floor(stamps[0] * 10)
                if not window[0][0] <= start <= sequence:
                    raise WakeAlignmentError('Wake alignment is outside the local prefix')
                return start
        raise WakeAlignmentError('Wake boundary could not be verified')

    def feed(self, sequence: int, pcm: bytes) -> bool:
        """Single 100ms PCM; corrupt queue/voice is rejected, there is no silent unlimited queue."""
        if type(sequence) is not int or sequence != self._sequence or type(pcm) is not bytes or len(pcm) != 3200:
            raise ValueError('Invalid local wake packet')
        self._sequence += 1
        self._recent.append((sequence, pcm))
        samples = array('h'); samples.frombytes(pcm)
        if sys.byteorder != 'little':
            samples.byteswap()
        self._stream.accept_waveform(16000, [sample / 32768 for sample in samples])
        while self._spotter.is_ready(self._stream):
            self._spotter.decode_stream(self._stream)
            result = self._spotter.keyword_spotter.get_result(self._stream)
            if result.keyword:
                self.start_sequence = self._boundary(result, sequence)
                return True
        self._packets += 1
        # shortcut: limited stream refreshes in 60 s; a borderline word
        # If it escapes, the user must say it again. This range is measured in physical acceptance.
        if self._packets >= 600:
            self._stream = self._spotter.create_stream()
            self._packets = 0
        return False


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Install the pinned local wake-word model')
    parser.add_argument('--setup', action='store_true', required=True)
    parser.parse_args()
    setup()
