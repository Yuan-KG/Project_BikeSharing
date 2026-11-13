"""Chronological development, locked test evaluation, and report figures."""
from pathlib import Path
import json, os, platform, time, warnings
os.environ.setdefault('OMP_NUM_THREADS','4')
os.environ.setdefault('MKL_NUM_THREADS','4')
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from threadpoolctl import threadpool_limits
import sklearn

ROOT=Path(__file__).resolve().parents[1]
SEED=42
TIME=['hour','weekday','month','weekend','holiday','weekday_hour','hour_sin','hour_cos','doy_sin','doy_cos']
WEATHER=['temperature_2m','relative_humidity_2m','precipitation','cloud_cover','wind_speed_10m']
GRIDS={'Ridge':[{'alpha':x} for x in (1,10,100)],
       'RandomForest':[{'n_estimators':160,'min_samples_leaf':x} for x in (2,8)],
       'HistGradientBoosting':[{'max_iter':250,'learning_rate':.06,'max_leaf_nodes':x,'l2_regularization':1} for x in (15,31)]}
FOLDS=[('2024-07-01','2024-09-01'),('2024-09-01','2024-11-01'),('2024-11-01','2025-01-01')]

def metrics(y,p):
    return dict(MAE=float(mean_absolute_error(y,p)),RMSE=float(np.sqrt(mean_squared_error(y,p))),
                R2=float(r2_score(y,p)),bias=float(np.mean(np.asarray(p)-np.asarray(y))))

def model(family,features,params):
    if family=='Ridge':
        cat=['hour','weekday','month','weekday_hour']
        numeric=[x for x in features if x not in cat]
        prep=ColumnTransformer([('category',make_pipeline(SimpleImputer(strategy='most_frequent'),OneHotEncoder(handle_unknown='ignore',sparse_output=False)),cat),
                                ('numeric',make_pipeline(SimpleImputer(strategy='median'),StandardScaler()),numeric)],sparse_threshold=0)
        # SVD solves the same Ridge objective while avoiding ill-conditioned normal equations.
        return make_pipeline(prep,Ridge(solver='svd',**params))
    est=(RandomForestRegressor(random_state=SEED,n_jobs=4,**params) if family=='RandomForest' else
         HistGradientBoostingRegressor(random_state=SEED,early_stopping=False,**params))
    return make_pipeline(SimpleImputer(strategy='median'),est)

def baseline(train,test):
    means=train.groupby(['weekday','hour']).rides.mean()
    keys=pd.MultiIndex.from_frame(test[['weekday','hour']])
    return means.reindex(keys).fillna(train.rides.mean()).to_numpy()

def load():
    d=pd.read_csv(ROOT/'data/processed/hourly_model_data.csv',parse_dates=['timestamp_utc'])
    d['date_local']=d.timestamp_local.str[:10]
    return d

def run(d):
    d=d.copy()
    if 'date_local' not in d.columns:
        d['date_local']=d.timestamp_local.str[:10]
    out=ROOT/'results'
    out.mkdir(exist_ok=True)
    dev=d[(d.year==2024)&d.rides.notna()].copy()
    fold_results=[]
    candidates=[]
    started=time.time()
    with threadpool_limits(limits=4):
        for family,grid in GRIDS.items():
            for variant,features in [('time',TIME),('time_weather',TIME+WEATHER)]:
                for params in grid:
                    ys,ps=[],[]
                    for fold,(begin,end) in enumerate(FOLDS,1):
                        train=dev[dev.date_local<begin]
                        val=dev[(dev.date_local>=begin)&(dev.date_local<end)]
                        est=model(family,features,params)
                        tick=time.time()
                        est.fit(train[features],train.rides)
                        p=np.maximum(est.predict(val[features]),0)
                        ys.extend(val.rides.to_numpy()); ps.extend(p)
                        fold_results.append(dict(family=family,features=variant,params=json.dumps(params,sort_keys=True),fold=fold,n_train=len(train),n_validation=len(val),seconds=time.time()-tick,**metrics(val.rides,p)))
                    row=dict(family=family,features=variant,params=params,n_validation=len(ys),**metrics(ys,ps))
                    candidates.append(row)
                    print('Validation',family,variant,params,'RMSE',round(row['RMSE'],3),flush=True)
        for fold,(begin,end) in enumerate(FOLDS,1):
            train=dev[dev.date_local<begin]; val=dev[(dev.date_local>=begin)&(dev.date_local<end)]
            fold_results.append(dict(family='WeekdayHourMean',features='time',params='{}',fold=fold,n_train=len(train),n_validation=len(val),seconds=0,**metrics(val.rides,baseline(train,val))))
        selected=[]
        for family in GRIDS:
            for variant in ('time','time_weather'):
                selected.append(min((c for c in candidates if c['family']==family and c['features']==variant),key=lambda c:c['RMSE']))
        primary=min(selected,key=lambda c:c['RMSE'])
        lock=dict(seed=SEED,folds=FOLDS,selection_metric='pooled 2024 validation RMSE',selected=selected,primary=primary,locked_before_test=True)
        # This file is saved BEFORE any 2025 model prediction or metric calculation.
        (out/'selection_lock.json').write_text(json.dumps(lock,indent=2))
        pd.DataFrame(fold_results).to_csv(out/'validation_folds.csv',index=False)
        pd.DataFrame([{**c,'params':json.dumps(c['params'],sort_keys=True)} for c in candidates]).to_csv(out/'validation_candidates.csv',index=False)
        test=d[(d.year==2025)&d.rides.notna()].copy()
        pred=test[['timestamp_utc','timestamp_local','date_local','rides','hour','weekday','month','weekend','holiday']+WEATHER].copy()
        scores=[]
        pred['WeekdayHourMean_time']=baseline(dev,test)
        scores.append(dict(model='WeekdayHourMean',features='time',fit_seconds=0,**metrics(test.rides,pred['WeekdayHourMean_time'])))
        for choice in selected:
            family,variant=choice['family'],choice['features']
            features=TIME+(WEATHER if variant=='time_weather' else [])
            est=model(family,features,choice['params'])
            tick=time.time()
            est.fit(dev[features],dev.rides)
            fit_seconds=time.time()-tick
            key=family+'_'+variant
            pred[key]=np.maximum(est.predict(test[features]),0)
            scores.append(dict(model=family,features=variant,fit_seconds=fit_seconds,**metrics(test.rides,pred[key])))
            print('Test',key,scores[-1],flush=True)
        pred.to_csv(out/'test_predictions.csv',index=False)
        pd.DataFrame(scores).to_csv(out/'test_metrics.csv',index=False)
    key=primary['family']+'_'+primary['features']
    pred['prediction']=pred[key]
    pred['error']=pred.prediction-pred.rides
    peak=(pred.weekday<5)&pred.hour.isin([7,8,9,16,17,18])
    groups={'All':np.ones(len(pred),dtype=bool),'Weekday':pred.weekday<5,'Weekend':pred.weekend==1,
            'Peak weekday':peak,'Other hours':~peak,'Dry':pred.precipitation==0,'Wet':pred.precipitation>0,
            'Cold <5C':pred.temperature_2m<5,'Mild 5-25C':pred.temperature_2m.between(5,25),'Hot >25C':pred.temperature_2m>25}
    group_rows=[dict(group=name,n=int(mask.sum()),mean_rides=float(pred.loc[mask,'rides'].mean()),**metrics(pred.loc[mask,'rides'],pred.loc[mask,'prediction'])) for name,mask in groups.items()]
    pd.DataFrame(group_rows).to_csv(out/'subgroup_metrics.csv',index=False)
    pred.groupby('month').apply(lambda g:pd.Series(dict(n=len(g),mean_rides=g.rides.mean(),**metrics(g.rides,g.prediction))),include_groups=False).to_csv(out/'monthly_test_metrics.csv')
    pred.groupby('hour').apply(lambda g:pd.Series(dict(n=len(g),**metrics(g.rides,g.prediction))),include_groups=False).to_csv(out/'hourly_test_metrics.csv')
    pred.assign(absolute_error=pred.error.abs()).nlargest(12,'absolute_error').to_csv(out/'largest_errors.csv',index=False)
    # Paired day bootstrap quantifies weather ablation uncertainty; no model selection uses this diagnostic.
    rng=np.random.default_rng(SEED)
    boot=[]
    for family in GRIDS:
        t=(pred[family+'_time']-pred.rides).abs()
        w=(pred[family+'_time_weather']-pred.rides).abs()
        daily=pd.DataFrame({'date':pred.date_local,'improvement':t-w}).groupby('date').agg(total=('improvement','sum'),n=('improvement','size'))
        ids=rng.integers(0,len(daily),size=(2000,len(daily)))
        vals=daily.total.to_numpy()[ids].sum(axis=1)/daily.n.to_numpy()[ids].sum(axis=1)
        boot.append(dict(model=family,MAE_improvement=float((t-w).mean()),lower95=float(np.quantile(vals,.025)),upper95=float(np.quantile(vals,.975))))
    pd.DataFrame(boot).to_csv(out/'weather_ablation_bootstrap.csv',index=False)
    summary=dict(primary_model=key,n_development=len(dev),n_test=len(test),seed=SEED,total_model_seconds=time.time()-started,
                 packages=dict(python=platform.python_version(),pandas=pd.__version__,numpy=np.__version__,scikit_learn=sklearn.__version__,matplotlib=matplotlib.__version__),
                 annual_counts=d.groupby('year').rides.sum().to_dict(),scores=scores,groups=group_rows)
    (out/'summary.json').write_text(json.dumps(summary,indent=2))
    figures(d,pred,primary)
    return summary

def figures(d,pred,primary):
    figdir=ROOT/'results/figures'; figdir.mkdir(exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold','figure.dpi':150,'savefig.dpi':220,'pdf.fonttype':42})
    colors=['#b43b36','#17756c']
    def save(name,fig):
        fig.tight_layout()
        fig.savefig(figdir/(name+'.png'),bbox_inches='tight')
        fig.savefig(figdir/(name+'.pdf'),bbox_inches='tight')
        plt.close(fig)
    # Development EDA is kept separate from post-lock test diagnostics.
    dev=d[(d.year==2024)&d.rides.notna()]
    monthly=d.groupby(['year','month']).rides.sum().unstack(0)
    monthly.to_csv(ROOT/'results/monthly_counts.csv')
    fig,ax=plt.subplots(figsize=(6.6,2.8))
    monthly.plot.bar(ax=ax,color=colors,width=.8)
    ax.set(xlabel='Local calendar month',ylabel='Recorded departures',title='Monthly recorded use, after documented exclusions')
    ax.ticklabel_format(axis='y',style='sci',scilimits=(6,6)); ax.tick_params(axis='x',rotation=0)
    save('monthly_counts',fig)
    profile=dev.groupby(['weekend','hour']).rides.mean().unstack(0)
    profile.to_csv(ROOT/'results/development_hour_profiles.csv')
    fig,ax=plt.subplots(figsize=(6.6,2.7))
    ax.plot(profile.index,profile[0],label='Weekday',color=colors[0],lw=2)
    ax.plot(profile.index,profile[1],label='Weekend',color=colors[1],lw=2)
    ax.set(xlabel='Local hour',ylabel='Mean departures per hour',xticks=range(0,24,3),title='2024 daily patterns'); ax.legend(frameon=False)
    save('hour_profiles',fig)
    heat=dev.groupby(['weekday','hour']).rides.mean().unstack()
    heat.to_csv(ROOT/'results/development_weekday_heatmap.csv')
    fig,ax=plt.subplots(figsize=(6.6,2.7)); im=ax.imshow(heat,aspect='auto',cmap='YlOrRd')
    ax.set(yticks=range(7),yticklabels=['Mon','Tue','Wed','Thu','Fri','Sat','Sun'],xticks=range(0,24,3),xlabel='Local hour',title='2024 weekday and hour means'); fig.colorbar(im,ax=ax,label='Departures/hour',pad=.02)
    save('weekday_heatmap',fig)
    binned=dev.assign(temp_bin=pd.cut(dev.temperature_2m,[-20,0,5,10,15,20,25,30,45]),wet=np.where(dev.precipitation>0,'Wet','Dry'))
    weather=binned.groupby(['temp_bin','wet'],observed=True).rides.agg(['mean','count']).reset_index()
    weather.to_csv(ROOT/'results/development_weather_bins.csv',index=False)
    fig,ax=plt.subplots(figsize=(6.6,2.9))
    for i,wet in enumerate(['Dry','Wet']):
        subset=weather[weather.wet==wet]; x=[v.mid for v in subset.temp_bin]
        ax.plot(x,subset['mean'],'o-',color=colors[i],label=wet)
    ax.set(xlabel='Temperature bin midpoint (C)',ylabel='Mean departures/hour',title='2024 weather associations (unadjusted)'); ax.legend(frameon=False)
    save('weather_associations',fig)
    scores=pd.read_csv(ROOT/'results/test_metrics.csv')
    fig,ax=plt.subplots(figsize=(6.6,3.2))
    order=['WeekdayHourMean','Ridge','RandomForest','HistGradientBoosting']
    for i,v in enumerate(['time','time_weather']):
        vals=[scores[(scores.model==m)&(scores.features==v)].RMSE.iloc[0] if ((scores.model==m)&(scores.features==v)).any() else np.nan for m in order]
        ax.bar(np.arange(4)+(-.18 if i==0 else .18),vals,width=.34,color=colors[i],label='Time only' if i==0 else 'Time + weather')
    ax.set(xticks=range(4),xticklabels=['Weekday-hour','Ridge','Random forest','Gradient boost'],ylabel='Test RMSE (rides/hour)',title='2025 locked-model comparison'); ax.legend(frameon=False)
    save('test_comparison',fig)
    fig,axes=plt.subplots(1,2,figsize=(6.6,3.0))
    axes[0].scatter(pred.rides,pred.prediction,s=3,alpha=.17,color=colors[1],rasterized=True)
    lim=max(pred.rides.max(),pred.prediction.max()); axes[0].plot([0,lim],[0,lim],color='#444444',lw=1)
    axes[0].set(xlabel='Observed rides/hour',ylabel='Estimated rides/hour',title='Primary model: 2025')
    err=pred.groupby('hour').error.mean(); axes[1].bar(err.index,err,color=colors[0]); axes[1].axhline(0,color='black',lw=.7)
    axes[1].set(xlabel='Local hour',ylabel='Mean error (estimate - observed)',title='Bias by time of day',xticks=range(0,24,6))
    save('error_diagnostics',fig)
    groups=pd.read_csv(ROOT/'results/subgroup_metrics.csv')
    g=groups.iloc[1:]
    fig,ax=plt.subplots(figsize=(6.6,3.1)); ax.barh(g.group,g.MAE,color=colors[1]); ax.invert_yaxis()
    ax.set(xlabel='MAE (rides/hour)',title='Primary model: 2025 error groups')
    save('subgroup_errors',fig)
    # Fixed illustrative week, chosen by date before inspecting error rankings.
    week=pred[(pred.date_local>='2025-06-02')&(pred.date_local<'2025-06-09')]
    fig,ax=plt.subplots(figsize=(6.6,2.9)); x=np.arange(len(week))
    ax.plot(x,week.rides,color='#333333',lw=1,label='Observed'); ax.plot(x,week.prediction,color=colors[0],lw=1,label='Primary model')
    ax.set(xlabel='Hours from 2 June 2025, 00:00 local',ylabel='Departures/hour',title='A fixed test week: 2-8 June 2025'); ax.legend(frameon=False,ncol=2)
    save('test_week',fig)
    m=pd.read_csv(ROOT/'results/monthly_test_metrics.csv')
    fig,ax=plt.subplots(figsize=(6.6,2.7)); ax.bar(m.month,m.bias,color=colors[0]); ax.axhline(0,color='black',lw=.7)
    ax.set(xlabel='2025 month',ylabel='Mean error (rides/hour)',title='Primary model: monthly signed error',xticks=range(1,13)); save('monthly_bias',fig)

if __name__=='__main__':
    print(json.dumps(run(load()),indent=2))
