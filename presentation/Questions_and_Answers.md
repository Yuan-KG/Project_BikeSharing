# Likely questions and short answers

## 1. What is your prediction target?

The number of recorded system-wide trip starts in each hour. It measures observed use and does not include unmet demand.

中文理解：目标是每小时全系统实际记录的出发次数，不包含无车而未出发的需求。

## 2. Why use 2025 only for testing?

A later-year holdout tests transfer forward in time. I choose settings on chronological 2024 windows and do not tune on 2025.

中文理解：用下一年检验向未来迁移，2024按时间选参，2025不参与调参。

## 3. How much does weather help?

For gradient boosting, test RMSE falls from 288.48 to 241.86 rides per hour, a 16.16% reduction. This is a within-family comparison.

中文理解：比较同家族时间与时间加天气，RMSE下降16.16%，不是与基线的比较。

## 4. Did weather always help?

It improved all three regression families on 2025, but weather Ridge was worse in pooled 2024 validation. The benefit depends on model and period.

中文理解：2025三个家族都改善，但2024验证Ridge加天气更差，不能声称始终有效。

## 5. Is this an actual advance forecast?

No. I use retrospective ERA5 and same-interval rainfall. It is estimation conditional on known weather. A real forecast test needs archived issue-time forecasts.

中文理解：不是。ERA5和同小时降水是事后信息，真实提前预测要用带发布时间的历史预报另测。

## 6. How did you handle daylight saving time?

I joined on UTC and used local calendar features. I preserved ambiguous fall-back starts separately and excluded four unresolved target hours rather than guessing their offsets.

中文理解：UTC连接、本地日历特征，保留回拨歧义记录，排除4个无法确定小时，不猜偏移。

## 7. Did you replace missing ride counts with zero?

No unresolved target was filled with zero. After verifying all months and daily coverage, every other hour already had trips.

中文理解：没有把不可用目标补0。检查月份和日覆盖后，其余小时本来都有骑行。

## 8. Where could data leakage occur?

Same-hour member, bicycle-type or station trip totals could expose the target. I exclude them, fit preprocessing only on training data, and keep 2025 out of selection.

中文理解：同小时分类总量可能直接暴露目标；不使用这些量，预处理只拟合训练集。

## 9. Why keep trips with strange end times?

The target counts starts. A valid departure can still be counted when an end field is unreliable. I audit those problems without using end information as a predictor.

中文理解：目标是出发，结束字段异常不一定否定已发生的出发；审计但不作为特征。

## 10. Does R-squared 0.855 mean 85.5% accuracy?

No. R-squared compares squared error with variation around the test mean. MAE and RMSE give errors in rides per hour.

中文理解：不是分类准确率。R²是相对测试均值基准的平方误差解释指标。

## 11. Why are peak errors larger?

Peak counts are higher and unusual busy hours are difficult. Larger absolute errors alone do not prove larger percentage errors or a specific causal mechanism.

中文理解：峰值量高且异常忙碌小时难预测，绝对误差大不能直接推出相对误差大。

## 12. Can you explain the bias reversal in 2025?

The monthly sign changes are observed. System or behaviour changes are plausible explanations, but this dataset does not identify a cause. I did not fit a correction to the test errors.

中文理解：偏差反转是事实，系统和行为变化是可能解释，尚未识别因果，也没用测试误差校准。

## 13. Why not use a larger neural network?

The task has about 17,500 hourly observations and is designed for a normal computer. The small standard-model comparison answers the research questions without a large search.

中文理解：小时样本约1.75万，课程任务面向普通电脑，小规模标准模型已能回答问题。

## 14. What would you improve next?

In a new pre-specified study, I would test archived forecasts, valid lagged counts, system availability and a rolling update strategy, with a new untouched test period.

中文理解：下一次预先设计研究可加真实历史预报、可用滞后量、系统可用性和滚动更新，仍要新测试集。

## 15. Can your repository redistribute the raw data?

The raw ZIPs stay local. The research package contains the derived hourly study table, official download code, provenance and license notices, rather than a stand-alone raw-data mirror.

中文理解：原始ZIP本地保存，仓库放本研究聚合表、官方获取代码与许可，不做独立原始镜像。

