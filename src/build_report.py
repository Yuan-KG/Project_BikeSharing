"""Generate report numbers and tables directly from final experiment outputs."""
from pathlib import Path
import json, shutil
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'report'

def main():
    a=json.loads((ROOT/'results/data_audit.json').read_text(encoding='utf-8'))
    s=json.loads((ROOT/'results/summary.json').read_text(encoding='utf-8'))
    lock=json.loads((ROOT/'results/selection_lock.json').read_text())
    scores=pd.read_csv(ROOT/'results/test_metrics.csv')
    groups=pd.read_csv(ROOT/'results/subgroup_metrics.csv').set_index('group')
    boot=pd.read_csv(ROOT/'results/weather_ablation_bootstrap.csv').set_index('model')
    folds=pd.read_csv(ROOT/'results/validation_folds.csv')
    worst=pd.read_csv(ROOT/'results/largest_errors.csv').iloc[0]
    primary=scores[(scores.model=='HistGradientBoosting')&(scores.features=='time_weather')].iloc[0]
    time=scores[(scores.model=='HistGradientBoosting')&(scores.features=='time')].iloc[0]
    baseline=scores[scores.model=='WeekdayHourMean'].iloc[0]
    t=a['totals']
    missing={k:sum(row['missing_fields'].get(k,0) for row in a['monthly']) for k in a['schema']}
    annual=s['annual_counts']
    vals=dict(NRaw=f"{t['raw_rows']:,}",NTest=f"{s['n_test']:,}",NDev=f"{s['n_development']:,}",NGrid=f"{a['total_grid_hours']:,}",
              NDuplicates=t['duplicate_id_rows'],NMissingStartStation=f"{missing['start_station_id']:,}",NMissingEndStation=f"{missing['end_station_id']:,}",
              NNegativeDuration=f"{t['negative_duration_local_clock']:,}",NLongDuration=f"{t['duration_over_24h']:,}",NShortDuration=f"{t['duration_under_60s']:,}",
              NOutsideMonth=f"{t['outside_nominal_month']:,}",NAmbiguous=f"{t['ambiguous_fallback_start']:,}",
              NAmbiguousTwentyFour=sum(x.get('ambiguous_fallback_start',0) for x in a['monthly'] if x['month'].startswith('2024')),
              NAmbiguousTwentyFive=sum(x.get('ambiguous_fallback_start',0) for x in a['monthly'] if x['month'].startswith('2025')),
              NAssigned=f"{t['assigned_departures']:,}",NAnnualTwentyFour=f"{int(annual['2024']):,}",NAnnualTwentyFive=f"{int(annual['2025']):,}",
              AnnualGrowth=f"{100*(annual['2025']/annual['2024']-1):.2f}",NValidation=f"{lock['primary']['n_validation']:,}",
              PythonVersion=s['packages']['python'],SklearnVersion=s['packages']['scikit_learn'],
              PrimaryMAE=f"{primary.MAE:.2f}",PrimaryRMSE=f"{primary.RMSE:.2f}",PrimaryRSquared=f"{primary.R2:.3f}",PrimaryBias=f"{primary.bias:.2f}",
              PrimaryValRMSE=f"{lock['primary']['RMSE']:.2f}",BoostTimeRMSE=f"{time.RMSE:.2f}",BaselineRMSE=f"{baseline.RMSE:.2f}",
              WeatherRMSEGain=f"{100*(1-primary.RMSE/time.RMSE):.2f}",BaselineRMSEGain=f"{100*(1-primary.RMSE/baseline.RMSE):.2f}",
              WeatherMAEChange=f"{time.MAE-primary.MAE:.2f}",BootstrapLow=f"{boot.loc['HistGradientBoosting','lower95']:.2f}",BootstrapHigh=f"{boot.loc['HistGradientBoosting','upper95']:.2f}",
              WorstHour=f"{str(worst.timestamp_local)[:10]} at {str(worst.timestamp_local)[11:16]} local time",
              WorstObserved=f"{int(worst.rides):,}",WorstPredicted=f"{worst.prediction:,.2f}")
    for macro,group in [('Peak','Peak weekday'),('Other','Other hours'),('Wet','Wet'),('Dry','Dry'),('Hot','Hot >25C'),('Cold','Cold <5C')]:
        vals[macro+'MAE']=f"{groups.loc[group,'MAE']:.2f}"
    OUT.mkdir(exist_ok=True)
    (OUT/'numbers.tex').write_text('\n'.join('\\newcommand{\\'+k+'}{'+str(v)+'}' for k,v in vals.items())+'\n',encoding='utf-8')
    def table(name,columns,rows,align):
        text='\\begin{tabular}{'+align+'}\n\\toprule\n'+' & '.join(columns)+' \\\\\n\\midrule\n'
        text+=''.join(' & '.join(str(x) for x in row)+' \\\\\n' for row in rows)
        text+='\\bottomrule\n\\end{tabular}\n'
        (OUT/name).write_text(text,encoding='utf-8')
    table('audit_table.tex',['Stage','Rows'],[
        ['Raw monthly rows',f"{t['raw_rows']:,}"],['Repeated IDs removed',f"{t['duplicate_id_rows']:,}"],
        ['Invalid or out-of-scope starts','0'],['Unresolved DST starts',f"{t['ambiguous_fallback_start']:,}"],
        ['Assigned hourly departures',f"{t['assigned_departures']:,}"]],'lr')
    names={'Ridge':'Ridge','RandomForest':'Random forest','HistGradientBoosting':'Gradient boosting','WeekdayHourMean':'Weekday--hour mean'}
    settings=[]
    for c in lock['selected']:
        p=c['params']; field=('alpha='+str(p['alpha']) if c['family']=='Ridge' else 'leaf min='+str(p['min_samples_leaf']) if c['family']=='RandomForest' else 'leaves='+str(p['max_leaf_nodes']))
        settings.append([names[c['family']],'Time' if c['features']=='time' else '+ weather',field])
    table('settings_table.tex',['Model','Inputs','Selected setting'],settings,'lll')
    rows=[]
    for c in scores.to_dict('records'):
        if c['model']=='WeekdayHourMean':
            f=folds[folds.family=='WeekdayHourMean']; val=(sum(f.RMSE**2*f.n_validation)/sum(f.n_validation))**.5
        else:
            val=next(x['RMSE'] for x in lock['selected'] if x['family']==c['model'] and x['features']==c['features'])
        rows.append([names[c['model']],'Time' if c['features']=='time' else 'Time + weather',f'{val:.2f}',f"{c['MAE']:.2f}",f"{c['RMSE']:.2f}",f"{c['R2']:.3f}",f"{c['bias']:.2f}"])
    table('results_table.tex',['Model','Inputs','Val. RMSE','Test MAE','Test RMSE','$R^2$','Bias'],rows,'llrrrrr')
    rows=[]
    for group,r in groups.iterrows():
        label=group.replace('<5C','$<5$ C').replace('5-25C','5--25 C').replace('>25C','$>25$ C')
        rows.append([label,f'{int(r.n):,}',f'{r.mean_rides:.2f}',f'{r.MAE:.2f}',f'{r.RMSE:.2f}',f'{r.bias:.2f}'])
    table('groups_table.tex',['Group','Hours','Mean count','MAE','RMSE','Bias'],rows,'lrrrrr')
    (ROOT/'results/report_numbers.json').write_text(json.dumps(vals,indent=2),encoding='utf-8')
    print('Report numbers and tables generated from final results.')

if __name__=='__main__':
    main()
