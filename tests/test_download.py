"""Interrupted or invalid transfers must never become cached official archives."""
import hashlib
import io
import pytest
from talentroute.data import download_archive


def test_download_publishes_only_verified_bytes(tmp_path,monkeypatch):
    import talentroute.data as data
    content=b'complete reviewed archive'
    monkeypatch.setattr(data.urllib.request,'urlopen',lambda *args,**kwargs:io.BytesIO(content))
    target=tmp_path/'oulad.zip'
    download_archive('https://example.invalid/data',target,hashlib.sha256(content).hexdigest())
    assert target.read_bytes()==content
    assert not target.with_suffix('.zip.partial').exists()
    target.unlink()
    with pytest.raises(ValueError,match='checksum'):
        download_archive('https://example.invalid/data',target,'0'*64)
    assert not target.exists() and not target.with_suffix('.zip.partial').exists()


def test_interrupted_download_does_not_poison_cache(tmp_path,monkeypatch):
    import talentroute.data as data
    class Interrupted(io.BytesIO):
        def read(self,*args,**kwargs):raise OSError('simulated interrupted transfer')
    monkeypatch.setattr(data.urllib.request,'urlopen',lambda *args,**kwargs:Interrupted())
    target=tmp_path/'oulad.zip'
    with pytest.raises(OSError,match='interrupted'):
        download_archive('https://example.invalid/data',target,'0'*64)
    assert not target.exists() and not target.with_suffix('.zip.partial').exists()


def test_bundled_csv_tampering_is_rejected_without_network(tmp_path,monkeypatch):
    import talentroute.data as data
    raw=tmp_path/'data/raw';raw.mkdir(parents=True)
    (raw/'sample.csv').write_bytes(b'original public data')
    cfg={'raw_csv_sha256':{'sample.csv':hashlib.sha256(b'original public data').hexdigest()},
         'data_url':'https://example.invalid/data','archive_sha256':'0'*64}
    monkeypatch.setattr(data,'ROOT',tmp_path);monkeypatch.setattr(data,'config',lambda:cfg)
    monkeypatch.setattr(data.urllib.request,'urlopen',lambda *a,**kw:pytest.fail('Bundled data should not access the network'))
    assert data.download().is_file()
    (raw/'sample.csv').write_bytes(b'changed')
    with pytest.raises(ValueError,match='Bundled raw CSV changed'):data.download()
