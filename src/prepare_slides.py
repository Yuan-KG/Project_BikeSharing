"""Export final analysis values for the editable presentation."""
from pathlib import Path
import json
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
def main():
    profile=pd.read_csv(ROOT/'results/development_hour_profiles.csv')
    scores=pd.read_csv(ROOT/'results/test_metrics.csv')
    groups=pd.read_csv(ROOT/'results/subgroup_metrics.csv')
    monthly=pd.read_csv(ROOT/'results/monthly_test_metrics.csv')
    payload=dict(summary=json.loads((ROOT/'results/summary.json').read_text()),
                 profile=profile.to_dict('records'),scores=scores.to_dict('records'),
                 groups=groups.to_dict('records'),monthly=monthly.to_dict('records'))
    def portable(value):
        if isinstance(value,float):
            return round(value,6)
        if isinstance(value,list):
            return [portable(x) for x in value]
        if isinstance(value,dict):
            return {k:portable(v) for k,v in value.items()}
        return value
    # Six decimals exceed displayed precision and remain within Excel's numeric precision.
    (ROOT/'presentation/slide_data.json').write_text(json.dumps(portable(payload),indent=2),encoding='utf-8')
if __name__=='__main__':
    main()
