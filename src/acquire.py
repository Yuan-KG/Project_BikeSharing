"""Download official monthly archives and ERA5 weather; preserve raw bytes."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import argparse, hashlib, json, time, zipfile
import xml.etree.ElementTree as ET
import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data' / 'raw'
BASE = 'https://s3.amazonaws.com/capitalbikeshare-data/'

def now():
    return datetime.now(timezone.utc).isoformat()

def get(url, **kwargs):
    for attempt in range(4):
        try:
            r = requests.get(url, timeout=(30, 180), **kwargs)
            r.raise_for_status()
            return r
        except requests.RequestException:
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)

def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def main():
    RAW.mkdir(parents=True, exist_ok=True)
    listing = get(BASE)
    (RAW / 'bucket_listing.xml').write_bytes(listing.content)
    ns = {'s': 'http://s3.amazonaws.com/doc/2006-03-01/'}
    objects = {x.find('s:Key', ns).text: x for x in ET.fromstring(listing.content).findall('s:Contents', ns)}
    expected = [f'{year}{month:02d}-capitalbikeshare-tripdata.zip' for year in (2024, 2025) for month in range(1, 13)]
    assert all(name in objects for name in expected), 'A requested month is absent from the official listing.'
    def download(name):
        obj = objects[name]
        size = int(obj.find('s:Size', ns).text)
        path = RAW / name
        metadata_path = RAW / (name + '.download.json')
        if path.exists() and path.stat().st_size == size and metadata_path.exists():
            meta = json.loads(metadata_path.read_text())
            assert sha256(path) == meta['sha256'], f'Checksum changed: {name}'
            print('Verified existing', name, flush=True)
            return meta
        if path.exists():
            raise FileExistsError(f'Refusing to replace an unverified existing file: {path}')
        started = now()
        temporary = path.with_suffix('.zip.part')
        for attempt in range(5):
            try:
                response = get(BASE + name, stream=True)
                with response, temporary.open('wb') as f:
                    for block in response.iter_content(1024 * 1024):
                        f.write(block)
                if temporary.stat().st_size != size:
                    raise IOError(f'Incomplete file: {name}')
                break
            except (requests.RequestException, IOError) as exc:
                print('Retrying incomplete download', name, type(exc).__name__, flush=True)
                if attempt == 4:
                    raise
                time.sleep(2 ** attempt)
        with zipfile.ZipFile(temporary) as z:
            bad = z.testzip()
            assert bad is None, f'ZIP CRC failure: {bad}'
            members = [dict(name=i.filename, bytes=i.file_size) for i in z.infolist()]
        temporary.rename(path)
        meta = dict(filename=name, source=BASE + name, started_utc=started,
                    completed_utc=now(), bytes=size, sha256=sha256(path),
                    s3_last_modified=obj.find('s:LastModified', ns).text,
                    etag=response.headers.get('ETag'), zip_crc_verified=True, members=members)
        metadata_path.write_text(json.dumps(meta, indent=2), encoding='utf-8')
        print('Downloaded', name, size, flush=True)
        return meta
    with ThreadPoolExecutor(max_workers=3) as pool:
        manifest = list(pool.map(download, expected))
    (RAW / 'trip_manifest.json').write_text(json.dumps(dict(listing_retrieved_utc=now(), files=manifest), indent=2))
    weather = RAW / 'weather_era5.json'
    if not weather.exists():
        params = dict(latitude=38.9072, longitude=-77.0369,
                      start_date='2024-01-01', end_date='2026-01-02',
                      hourly='temperature_2m,relative_humidity_2m,precipitation,cloud_cover,wind_speed_10m',
                      models='era5', timezone='UTC', timeformat='unixtime',
                      temperature_unit='celsius', wind_speed_unit='kmh', precipitation_unit='mm')
        response = get('https://archive-api.open-meteo.com/v1/archive', params=params)
        weather.write_bytes(response.content)
        meta = dict(source=response.url, requested_coordinates=[38.9072, -77.0369],
                    model='ERA5 reanalysis', retrieved_utc=now(), sha256=sha256(weather), params=params)
        (RAW / 'weather_era5.download.json').write_text(json.dumps(meta, indent=2))
    print('All 24 archives and weather are available.', flush=True)

if __name__ == '__main__':
    main()
