"""Validate current guide links and translated-archive integrity.

Current hashes cover the English archive; source hashes and a Git revision retain
pre-translation provenance. Historical links are not current operating instructions.
No internet requests or real user files are involved.
"""
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[2]


def test_translated_archive_integrity_and_source_provenance():
    """Each translated file has a current hash and pre-translation provenance."""
    assert 'docs/archive/** -text' in (ROOT / '.gitattributes').read_text(encoding='utf-8')
    records = json.loads((ROOT / 'docs/archive/MANIFEST.json').read_text(encoding='utf-8'))
    assert len(records) == 133
    for record in records:
        assert re.fullmatch(r'[0-9a-f]{64}', record['source_sha256'])
        assert re.fullmatch(r'[0-9a-f]{40}', record['source_revision'])
        target = ROOT / record['archive_path']
        assert target.is_file(), record
        assert hashlib.sha256(target.read_bytes()).hexdigest() == record['sha256'], record


def test_current_document_links_resolve_inside_repository():
    """current/followed guides only: historical archives and virtual media are not scanned."""
    sources = list(ROOT.glob('*.md')) + list((ROOT / 'docs').glob('*.md'))
    sources += list((ROOT / 'docs/reference').glob('*.md')) + [ROOT / 'logs/README.md']
    sources += [ROOT / name for name in ('v1/README.md', 'v1/ui/README.md', 'v1/ui/tests/README.md')]
    for source in sources:
        text = source.read_text(encoding='utf-8')
        for link in re.findall(r'\[[^\]]*\]\(([^\s)]+)\)', text):
            if '://' in link or link.startswith('#'):
                continue
            target = (source.parent / unquote(link.split('#', 1)[0])).resolve()
            assert target.is_relative_to(ROOT), (source, link)
            assert target.exists(), (source, link)


def test_dated_documentation_snapshot_is_unchanged():
    """Dated copies retain original bytes independently of translated history."""
    snapshot = ROOT / 'docs/archive/2026-10-27'
    manifest = json.loads((snapshot / 'MANIFEST.json').read_text(encoding='utf-8'))
    for record in manifest['files']:
        target = snapshot / record['snapshot_path']
        assert hashlib.sha256(target.read_bytes()).hexdigest() == record['sha256']
