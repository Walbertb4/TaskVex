"""Güncel belge yolları ve taşınmış arşivin bütünlüğü.

Arşiv eski yolları içerdiği için linkleri yeniden yazılmaz; SHA256 özgün içeriği
koruduğumuzu sınar. Güncel Markdown bağlantıları ise depoda gerçek hedefe gitmelidir.
Bu test internet adreslerini ziyaret etmez veya kullanıcı verisini okumaz.
"""
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[2]


def test_archived_document_contents_are_preserved():
    """Manifestteki eski dosya sayısı ve her yeni dosyanın byte hash'i sabittir."""
    assert 'docs/eski/** -text' in (ROOT / '.gitattributes').read_text(encoding='utf-8')
    records = json.loads((ROOT / 'docs/eski/MANIFEST.json').read_text(encoding='utf-8'))
    assert len(records) == 133
    for record in records:
        target = ROOT / record['archive_path']
        assert target.is_file(), record
        assert hashlib.sha256(target.read_bytes()).hexdigest() == record['sha256'], record


def test_current_document_links_resolve_inside_repository():
    """Yalnız güncel/izlenen rehberler: tarihsel arşiv ve sanal ortam taranmaz."""
    sources = list(ROOT.glob('*.md')) + list((ROOT / 'docs').glob('*.md'))
    sources += [ROOT / name for name in ('v1/README.md', 'v1/ui/README.md', 'v1/ui/tests/README.md')]
    for source in sources:
        text = source.read_text(encoding='utf-8')
        for link in re.findall(r'\[[^\]]*\]\(([^\s)]+)\)', text):
            if '://' in link or link.startswith('#'):
                continue
            target = (source.parent / unquote(link.split('#', 1)[0])).resolve()
            assert target.is_relative_to(ROOT), (source, link)
            assert target.exists(), (source, link)
