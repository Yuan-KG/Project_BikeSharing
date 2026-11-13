# English presentation script

Target: about 4 minutes 35 seconds at a moderate pace. Rehearse and adjust pauses to stay within 4-5 minutes. The seven numbered sections match the seven slides. The one-minute question period follows the talk.

## 1. Research question (25 seconds)

Hello, I am Yuan Kaige. My project studies hourly Capital Bikeshare use in 2024 and 2025. I ask whether weather improves predictions beyond the calendar, and when prediction errors are largest. Here, demand means recorded departures. It does not include people who wanted a bicycle but could not get one.

## 2. Data and time alignment (40 seconds)

I downloaded all twenty-four official monthly files, containing about twelve point eight million rows. I checked file integrity, missing fields, repeated ride IDs and timestamp problems. I read the files in chunks rather than loading every trip at once. After cleaning, the table has seventeen thousand five hundred and forty usable hours. Four hours remain unavailable because the autumn clock change creates ambiguous local timestamps. I did not guess their UTC offsets or fill them with zero. Weather comes from ERA5 reanalysis through Open-Meteo, using one Washington-area grid location.

## 3. Exploratory patterns (35 seconds)

This figure uses only 2024 data. Weekdays have a morning rise and a larger late-afternoon peak. Weekends have a broader afternoon pattern. These differences explain why hour and weekday should be represented together. Monthly use also changes strongly across the year. Weather plots show associations with temperature and rain, but season and time of day are related to weather. These plots therefore describe associations, rather than proving that weather causes a particular change in use.

## 4. Fair experiment (40 seconds)

I used 2024 for model development and kept the whole of 2025 for final testing. Within 2024, I used three expanding training windows, each followed by two validation months. Settings were chosen by validation RMSE. I then refitted on full 2024 and tested the fixed models on identical 2025 hours. The comparison includes a weekday-and-hour mean baseline, Ridge, random forest and gradient boosting. Each regression family is tested with calendar features alone and with calendar plus weather. Preprocessing is fitted on training data only.

## 5. Main result (55 seconds)

The model selected by 2024 validation is gradient boosting with weather. On 2025, its mean absolute error is one hundred and sixty-six point four three rides per hour, and its root mean squared error is two hundred and forty-one point eight six. The calendar-only version has RMSE two hundred and eighty-eight point four eight. Adding weather therefore reduces RMSE by sixteen point one six percent within this family. Random forest and Ridge also improve on their calendar-only test versions. However, weather did not improve Ridge in pooled 2024 validation, so the benefit is not uniform across every model and period. The simple baseline has RMSE three hundred and forty-seven point zero one.

## 6. Error groups (45 seconds)

Overall accuracy hides important differences. The selected model has MAE about two hundred and seventy-four during weekday peaks, compared with one hundred and forty-three in other hours. Wet hours also have larger errors than dry hours. Hot hours have larger absolute errors, although their observed counts are higher too. We should not interpret a larger absolute error as automatically meaning a larger percentage error. The errors show where the model is less reliable, but they were not used to change its settings after testing.

## 7. Conclusion and limits (35 seconds)

My conclusion is that known historical weather adds useful predictive information, while calendar patterns already provide a strong baseline. The monthly bias changes from underestimation early in 2025 to overestimation late in the year. System changes or exceptional events may contribute, but their causes are not established here. Finally, ERA5 is retrospective reanalysis, and interval rainfall is known after the hour. This experiment estimates use under known weather conditions. It does not verify a real advance weather forecast. Thank you.

Approximate spoken word count: 574. Timings are rehearsal targets, not a measured recording.
