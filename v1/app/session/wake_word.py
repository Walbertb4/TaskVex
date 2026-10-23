"""Yerel sherpa-onnx anahtar sözcük algısı; model veya araç çalıştırmaz.

16 kHz PCM yalnız bu CPU işlemine verilir; ağ, disk ses kaydı ve ikinci mikrofon
yoktur. --setup açıkça çalıştırılırsa sabit upstream modelini indirir; uygulama
başlangıcında sessiz indirme yapılmaz. Ağırlıklar TaskVex MIT lisansı sayılmaz.
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


# Bu liste komut niyeti çözmez: yalnız aynı hitabın yerel ses/yazım
# karşılıklarıdır. Tek başına X/EX, sıradan konuşmayı uyandırmamak için yoktur.
VEX_SPELLINGS = ('Vex', 'Veks', 'Rex')


def wake_spellings(word: str) -> tuple[str, ...]:
    """Seçili hitabın sınırlı varyasyonları; özel isimde yalnız o isim geçerli.

    Yerel KWS ve Live'ın yalnız-hitap ayrımı aynı tanımı kullanır. Benzerlik
    tahmini veya uygulama komutu yorumlaması yapmaz; profil değerini değiştirmez.
    """
    return VEX_SPELLINGS if word.casefold() in {s.casefold() for s in VEX_SPELLINGS} else (word,)


def is_wake_only(text: str, word: str) -> bool:
    """Tam transkript yalnız hitapsa True; hitap ardından gelen görev korunur."""
    return text.casefold().strip(' \t\r\n.!?,:') in {s.casefold() for s in wake_spellings(word)}


class WakeAlignmentError(ValueError):
    """Algı var fakat güvenli ses sınırı yok; paket/cihaz hatasından ayrılır."""


def model_home() -> Path:
    """Kaynak kodundan ve credential dosyasından ayrı model cache'i."""
    return get_data_home() / 'models' / 'wake'


def setup():
    """Sabit SHA256 ile indir; arşiv yollarını çalıştırma/serbestçe çıkartma."""
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
    """Bridge'in kısa kilidinde seri PCM alır; kendi thread/worker'ı yoktur."""

    def __init__(self, word: str):
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
        # Veks aynı VEX fonemleridir; REX ayrı telaffuzdur. Aynı akustik
        # diziyi iki kez eklemeyiz; bütün adaylar tek mevcut motoru kullanır.
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
        # C++ motoru boş keyword dosyasında process'i sonlandırır; önce
        # doğrulanmış fonemleri bu örneğe özgü config dosyasına yaz.
        keyword_file = directory/f'keyword-{uuid4().hex}.txt'
        keyword_file.write_text(''.join(phones + ' @WAKE\n' for phones in pronunciations), encoding='utf-8')
        try:
            self._spotter = sherpa_onnx.KeywordSpotter(tokens=str(directory/'tokens.txt'),
                encoder=str(directory/'encoder-epoch-13-avg-2-chunk-8-left-64.int8.onnx'),
                decoder=str(directory/'decoder-epoch-13-avg-2-chunk-8-left-64.onnx'),
                joiner=str(directory/'joiner-epoch-13-avg-2-chunk-8-left-64.int8.onnx'),
                keywords_file=str(keyword_file), num_threads=1, keywords_threshold=0.25, num_trailing_blanks=1)
        finally:
            keyword_file.unlink(missing_ok=True)
        self.restart()

    def restart(self):
        """Ağırlıklar RAM'de kalır; her uyku yeni ID, decoder ve boş tampon alır.

        Eski ses/hit/sıra tekrar kullanılmaz. Aynı bridge'in seri kilidinde
        çağrılır; modelin pahalı doğrulama/yüklemesini yeniden yapmak gerekmez.
        """
        self._stream = self._spotter.create_stream()
        self.id = uuid4().hex
        self._sequence = self._packets = 0
        self.start_sequence = 0
        self._recent: deque[tuple[int, bytes]] = deque(maxlen=30)

    def _boundary(self, result, sequence: int) -> int:
        """Hit'i en çok 3 s yerel sesle yeniden doğrula; araç/API tekrarı değildir.

        1.13.8 decoder sessizlikte kendi zaman sayacını sıfırlar; Python sonucu
        bu sıfırlamanın global ofsetini açmaz. Eski timestamps'ı global saymak
        yerine yalnız hit anında kısa, başlangıcı bilinen bir doğrulama stream'i
        açılır. Sözcük süresi dışındaki pay 1.5 s iç-reset eşiğinden kısadır;
        böylece yeni hit'in önünde gizli sessizlik reset'i olamaz. Bu şart veya
        ses sınırı doğrulanamazsa zaman uydurulmaz, Live'a ses gönderilmez.
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
        # Yeni encoder'in kısa ileri bakışını doldur; bu sıfırlar yalnız
        # doğrulamaya aittir. Live'a aktarılmaz ve hit zamanına dahil edilmez.
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
        """Tek 100 ms PCM; bozuk sıra/ses reddedilir, sessiz sınırsız kuyruk yoktur."""
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
        # shortcut: 60 s'de sınırlı stream yenilenir; sınırdaki bir sözcük
        # kaçarsa kullanıcı tekrar söylemeli. Fiziksel kabulde bu aralık ölçülür.
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
