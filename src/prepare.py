"""Audit monthly trip files in chunks and construct an hourly UTC-indexed table."""
from collections import Counter
from pathlib import Path
import json, sqlite3, zipfile, time
import numpy as np
import pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar

ROOT = Path(__file__).resolve().parents[1]
TZ = 'America/New_York'
CHUNK = 200_000

def prepare():
    raw, out = ROOT / 'data/raw', ROOT / 'data/processed'
    auditdir = ROOT / 'results'
    out.mkdir(parents=True, exist_ok=True)
    auditdir.mkdir(exist_ok=True)
    cache = ROOT / 'work'
    cache.mkdir(exist_ok=True)
    dbfile = cache / 'seen.sqlite'
    # This derived cache can be regenerated. Raw files are never changed.
    if dbfile.exists():
        dbfile.unlink()
    db = sqlite3.connect(dbfile)
    db.execute('PRAGMA journal_mode=OFF')
    db.execute('PRAGMA synchronous=OFF')
    db.execute('PRAGMA cache_size=-64000')
    db.execute('CREATE TABLE seen (id TEXT PRIMARY KEY, hash TEXT) WITHOUT ROWID')
    count = Counter()
    ambiguous_counts = Counter()
    monthly = []
    schema = None
    for year in (2024, 2025):
        for month in range(1, 13):
            stem = f'{year}{month:02d}'
            p = raw / f'{stem}-capitalbikeshare-tripdata.zip'
            a = Counter()
            missing = Counter()
            stations = set()
            minstart, maxstart = None, None
            with zipfile.ZipFile(p) as z:
                names = [n for n in z.namelist() if n.endswith('.csv') and not n.startswith('__MACOSX/')]
                assert names, f'No CSV in {p}'
                for name in names:
                    with z.open(name) as f:
                        for chunk in pd.read_csv(f, chunksize=CHUNK, dtype=str):
                            if schema is None:
                                schema = list(chunk.columns)
                            assert list(chunk.columns) == schema, f'Schema change in {stem}'
                            a['raw_rows'] += len(chunk)
                            for col, n in chunk.isna().sum().items():
                                missing[col] += int(n)
                            hashes = pd.util.hash_pandas_object(chunk.fillna(''), index=False).map(lambda x: f'{x:016x}')
                            ids = chunk.ride_id.fillna('')
                            a['missing_ride_id'] += int(ids.eq('').sum())
                            keys = ids.where(ids.ne(''), 'NO_ID_' + hashes)
                            incoming = pd.DataFrame({'id':keys.to_numpy(), 'hash':hashes.to_numpy()})
                            within = incoming.duplicated('id')
                            a['duplicate_id_rows'] += int(within.sum())
                            if within.any():
                                a['conflicting_duplicate_rows'] += int(incoming.groupby('id')['hash'].nunique().gt(1).sum())
                            distinct = incoming.loc[~within]
                            db.execute('DROP TABLE IF EXISTS incoming')
                            db.execute('CREATE TABLE incoming (id TEXT PRIMARY KEY, hash TEXT) WITHOUT ROWID')
                            db.executemany('INSERT INTO incoming VALUES (?,?)', distinct.itertuples(index=False, name=None))
                            prior = db.execute('SELECT i.id, i.hash != s.hash FROM incoming i JOIN seen s ON i.id=s.id').fetchall()
                            duplicate_ids = {x[0] for x in prior}
                            a['duplicate_id_rows'] += len(prior)
                            a['conflicting_duplicate_rows'] += sum(x[1] for x in prior)
                            db.execute('INSERT OR IGNORE INTO seen SELECT * FROM incoming')
                            db.commit()
                            keep = (~within & ~incoming.id.isin(duplicate_ids)).to_numpy()
                            d = chunk.loc[keep].copy()
                            starts = pd.to_datetime(d.started_at, format='mixed', errors='coerce')
                            ends = pd.to_datetime(d.ended_at, format='mixed', errors='coerce')
                            a['invalid_start'] += int(starts.isna().sum())
                            a['invalid_end'] += int(ends.isna().sum())
                            duration = (ends - starts).dt.total_seconds()
                            a['negative_duration_local_clock'] += int(duration.lt(0).sum())
                            a['duration_over_24h'] += int(duration.gt(86400).sum())
                            a['duration_under_60s'] += int(duration.between(0,59.999).sum())
                            inmonth = starts.dt.year.eq(year) & starts.dt.month.eq(month)
                            a['outside_nominal_month'] += int((starts.notna() & ~inmonth).sum())
                            # Files are monthly releases, but valid starts elsewhere inside scope are counted at their true time.
                            valid_scope = starts.ge('2024-01-01') & starts.lt('2026-01-01')
                            a['outside_study_scope'] += int((starts.notna() & ~valid_scope).sum())
                            starts = starts.loc[valid_scope]
                            stations.update(d.loc[valid_scope, 'start_station_id'].dropna().unique())
                            if len(starts):
                                current_min, current_max = starts.min(), starts.max()
                                minstart = current_min if minstart is None else min(minstart,current_min)
                                maxstart = current_max if maxstart is None else max(maxstart,current_max)
                            localized = starts.dt.tz_localize(TZ, ambiguous='NaT', nonexistent='NaT')
                            # ambiguous=False only resolves fall-back, so remaining NaT identifies spring gaps.
                            probe = starts.dt.tz_localize(TZ, ambiguous=False, nonexistent='NaT')
                            amb = localized.isna() & probe.notna()
                            nonexist = probe.isna()
                            a['ambiguous_fallback_start'] += int(amb.sum())
                            a['nonexistent_spring_start'] += int(nonexist.sum())
                            for key, n in starts.loc[amb].dt.floor('h').value_counts().items():
                                ambiguous_counts[str(key)] += int(n)
                            times = localized.dropna().dt.tz_convert('UTC').dt.floor('h')
                            a['assigned_departures'] += len(times)
                            count.update({t:int(n) for t,n in times.value_counts().items()})
            row = dict(month=stem, filename=p.name, csv_members=names, **a,
                       first_start=str(minstart), last_start=str(maxstart),
                       unique_start_station_ids=len(stations), missing_fields=dict(missing))
            assert a['raw_rows'] == (a['duplicate_id_rows'] + a['invalid_start'] + a['outside_study_scope'] + a['nonexistent_spring_start'] + a['ambiguous_fallback_start'] + a['assigned_departures'])
            monthly.append(row)
            print(stem, a['raw_rows'], 'rows;', a['duplicate_id_rows'], 'duplicates', flush=True)
    db.close()
    start = pd.Timestamp('2024-01-01',tz=TZ).tz_convert('UTC')
    end = pd.Timestamp('2026-01-01',tz=TZ).tz_convert('UTC')
    grid = pd.date_range(start,end,freq='h',inclusive='left')
    hourly = pd.DataFrame(index=grid)
    hourly.index.name='timestamp_utc'
    hourly['rides'] = pd.Series(count,dtype='float64').reindex(grid)
    local = grid.tz_convert(TZ)
    naive = local.tz_localize(None)
    ambiguous_grid = naive.duplicated(keep=False)
    # Complete verified archives plus every expected local date observed are necessary for zeros.
    daily_presence = pd.Series(count,dtype='float64').groupby(lambda t:t.tz_convert(TZ).date()).sum()
    dates = pd.date_range('2024-01-01','2025-12-31',freq='D').date
    assert all(date in daily_presence.index for date in dates), 'An entire local day has no recorded trips: investigate before zero filling.'
    empty = hourly.rides.isna() & ~ambiguous_grid
    hourly.loc[empty,'rides']=0
    hourly.loc[ambiguous_grid,'rides']=np.nan
    hourly['target_status']=np.where(ambiguous_grid,'unresolved_DST',np.where(empty,'zero_after_coverage_checks','observed'))
    hourly['timestamp_local'] = local.astype(str)
    hourly['year']=local.year
    hourly['hour']=local.hour
    hourly['weekday']=local.dayofweek
    hourly['month']=local.month
    hourly['weekend']=(local.dayofweek>=5).astype(int)
    holidays=USFederalHolidayCalendar().holidays('2024-01-01','2025-12-31')
    hourly['holiday']=naive.normalize().isin(holidays).astype(int)
    hourly['weekday_hour'] = hourly.weekday*24+hourly.hour
    for key, values, period in [('hour',local.hour,24),('doy',local.dayofyear-1,365.2425)]:
        hourly[key+'_sin']=np.sin(2*np.pi*values/period)
        hourly[key+'_cos']=np.cos(2*np.pi*values/period)
    weather=json.loads((raw/'weather_era5.json').read_text(encoding='utf-8'))
    wh=weather['hourly']
    wi=pd.to_datetime(wh['time'],unit='s',utc=True)
    w=pd.DataFrame({k:v for k,v in wh.items() if k!='time'},index=wi)
    assert w.index.is_unique and (w.index.to_series().diff().dropna()==pd.Timedelta(hours=1)).all()
    for col in w.columns:
        hourly[col]=w[col].reindex(grid).to_numpy()
    # precipitation at t+1 summarizes [t,t+1), matching the target interval.
    hourly['precipitation']=w.precipitation.reindex(grid+pd.Timedelta(hours=1)).to_numpy()
    weather_cols=list(w.columns)
    assert not hourly[weather_cols].isna().any().any(), 'Weather gap: inspect instead of silently filling.'
    assert len(grid)==17544 and sum(ambiguous_grid)==4
    assert hourly.index.is_unique
    hourly.to_csv(out/'hourly_model_data.csv')
    pd.DataFrame([dict(local_hour=k,rides=n) for k,n in ambiguous_counts.items()]).to_csv(out/'unresolved_dst_counts.csv',index=False)
    daily = hourly.groupby(naive.normalize()).agg(rides=('rides',lambda x:x.sum(min_count=1)), available_hours=('rides','count'))
    daily.index.name='local_date'
    daily.to_csv(auditdir/'daily_coverage.csv')
    audit=dict(schema=schema, chunk_rows=CHUNK, monthly=monthly,
               totals=dict(sum((Counter({k:v for k,v in row.items() if isinstance(v,int)}) for row in monthly),Counter())),
               total_grid_hours=len(grid), unresolved_dst_hours=int(sum(ambiguous_grid)),
               zero_hours_after_checks=int(empty.sum()), all_expected_days_present=True,
               weather_metadata={k:v for k,v in weather.items() if k!='hourly'},
               zero_policy='Verified all 24 ZIP CRCs and all expected dates have trips; empty non-ambiguous hours interpreted as observed zeros. Unknown partial source outages remain a limitation.',
               timezone_assumption='Naive trip starts interpreted as America/New_York local wall time; source has no UTC offset. Fall-back starts kept separately, both UTC hours masked; no fold guessed.')
    (auditdir/'data_audit.json').write_text(json.dumps(audit,indent=2,default=str),encoding='utf-8')
    pd.DataFrame([{k:v for k,v in row.items() if k not in ('missing_fields','csv_members')} for row in monthly]).to_csv(auditdir/'monthly_audit.csv',index=False)
    print('Prepared',len(hourly),'hours;',hourly.rides.notna().sum(),'eligible',flush=True)
    return hourly

if __name__=='__main__':
    prepare()
