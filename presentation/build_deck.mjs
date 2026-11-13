// Editable presentation authoring. Set BIKE_ARTIFACT_RUNTIME to the bundled dependency directory.
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
const here=path.dirname(fileURLToPath(import.meta.url));
const root=path.dirname(here);
const runtime=process.env.BIKE_ARTIFACT_RUNTIME;
const skill=process.env.BIKE_PRESENTATION_SKILL;
if(!runtime || !skill) throw Error('Set BIKE_ARTIFACT_RUNTIME and BIKE_PRESENTATION_SKILL to the supplied Codex runtime and presentation skill.');
process.env.RUNTIME_NODE_MODULES=path.join(runtime,'node/node_modules');
const {Presentation,PresentationFile}=await import(pathToFileURL(path.join(runtime,'node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs')).href);
const {finalizePresentation,applyPresentationChartFont}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
const data=JSON.parse(await fs.readFile(path.join(here,'slide_data.json'),'utf8'));
const notes=JSON.parse(await fs.readFile(path.join(here,'speaker_notes.json'),'utf8'));
const preview=path.join(root,'work/slides');
await fs.mkdir(preview,{recursive:true});
const P=Presentation.create({slideSize:{width:1280,height:720}});
P.theme.defaultFont='Arial';
const C={ink:'#173D36',red:'#B43B36',teal:'#17756C',paper:'#F6F3EB',muted:'#54665F',white:'#FFFFFF',grid:'#D7DED7'};
const font='Arial';
const shape=(s,g,x,y,w,h,fill)=>s.shapes.add({geometry:g,position:{left:x,top:y,width:w,height:h},fill,line:{fill:'none',width:0}});
function txt(s,text,x,y,w,h,size=28,color=C.ink,bold=false){
  const t=shape(s,'textbox',x,y,w,h,'none');t.text=text;
  t.text.style={fontSize:size,typeface:font,color,bold,alignment:'left',verticalAlignment:'top',insets:0,autoFit:'none',wrap:'square',lineSpacing:1.12};
  return t;
}
function slide(title,i,dark=false){
  const s=P.slides.add();s.background.fill=dark?C.ink:C.paper;
  if(title)txt(s,title,64,48,1152,110,44,dark?C.white:C.ink,true);
  txt(s,String(i).padStart(2,'0'),1170,658,46,24,16,dark?'#B9CBC3':C.muted);
  s.speakerNotes.text=notes[i-1]+'\n\nSources: Project notebook and results CSVs. Official trip data: https://capitalbikeshare.com/system-data . Weather data by Open-Meteo.com, ERA5/Copernicus, CC BY 4.0: https://open-meteo.com/en/docs/historical-weather-api .';
  return s;
}
function chart(s,type,cfg){
  const ch=s.charts.add(type,{chartFill:'none',plotAreaFill:'none',chartLine:{fill:'none',width:0},...cfg});
  applyPresentationChartFont(ch,{fontFamily:font});return ch;
}
const axis={textStyle:{typeface:font,fontSize:21,fill:C.muted},line:{fill:C.grid,width:1},majorGridlines:null};
const valueAxis={...axis,min:0,majorGridlines:{fill:C.grid,width:1},title:{text:'Rides per hour',textStyle:{typeface:font,fontSize:20,fill:C.muted}}};
// 1: title and the research question.
{
 const s=slide('',1,true);
 txt(s,'Hourly bikeshare use',64,84,1100,100,70,C.white,true);
 txt(s,'Calendar and weather in Capital Bikeshare, 2024-2025',68,204,1070,90,32,'#DDE6DD');
 txt(s,'Does weather add useful predictive information?',68,346,960,100,42,C.white,true);
 txt(s,'Yuan Kaige\n202612231033 · Machine Learning · Individual project',68,550,950,80,24,'#DDE6DD');
 // Minimal bicycle motif drawn with editable shapes, rather than a decorative photo.
 shape(s,'ellipse',1028,460,64,64,'none').line={fill:'#94B5A8',width:3};
 shape(s,'ellipse',1124,460,64,64,'none').line={fill:'#94B5A8',width:3};
 shape(s,'line',1060,443,96,49,'none').line={fill:'#94B5A8',width:3};
}
// 2: one audited measurement pipeline.
{
 const s=slide('From 24 official files to one hourly target',2);
 const xs=[64,462,860];
 const blocks=[['12.78 million','raw trip rows'],['Audit + align','IDs, timestamps, UTC'],['17,540','usable hourly targets']];
 blocks.forEach((b,i)=>{txt(s,b[0],xs[i],198,355,72,49,i===2?C.teal:C.ink,true);txt(s,b[1],xs[i],285,355,70,27,C.muted);});
 shape(s,'rightArrow',380,227,54,28,C.red);shape(s,'rightArrow',778,227,54,28,C.red);
 txt(s,'Four ambiguous autumn hours excluded from modelling',64,399,1150,44,30,C.ink,true);
 txt(s,'Count recorded departures. Unmet demand is not observed.',64,468,1150,50,28,C.muted);
 txt(s,'Weather: ERA5 reanalysis at one Washington-area grid point',64,538,1150,56,28,C.muted);
 txt(s,'Sources: Capital Bikeshare; Open-Meteo / ERA5 (CC BY 4.0)',64,650,1050,26,16,C.muted);
}
// 3: native daily-profile chart.
{
 const s=slide('Weekdays and weekends have different daily shapes',3);
 chart(s,'line',{position:{left:64,top:181,width:1140,height:410},categories:data.profile.map(r=>String(r.hour)),
   series:[{name:'Weekday',values:data.profile.map(r=>r['0']),line:{fill:C.red,width:4},marker:{symbol:'none'}},{name:'Weekend',values:data.profile.map(r=>r['1']),line:{fill:C.teal,width:4},marker:{symbol:'none'}}],
   hasLegend:true,legend:{position:'top',overlay:false,textStyle:{typeface:font,fontSize:23,fill:C.ink}},xAxis:{...axis,title:{text:'Local hour',textStyle:{typeface:font,fontSize:21,fill:C.muted}}},yAxis:{...valueAxis,max:2000,majorUnit:500}});
 txt(s,'2024 development data. System-wide averages do not identify individual trip purposes.',64,633,1100,38,20,C.muted);
}
// 4: chronological experimental design as editable blocks.
{
 const s=slide('Choose on 2024. Evaluate on 2025.',4);
 txt(s,'2024 development',64,190,680,50,34,C.ink,true);
 txt(s,'2025 final test',882,190,334,50,34,C.red,true);
 const ys=[277,351,425]; const trainWidths=[305,407,509];
 const labs=['Jan-Jun train  /  Jul-Aug validate','Jan-Aug train  /  Sep-Oct validate','Jan-Oct train  /  Nov-Dec validate'];
 ys.forEach((y,i)=>{shape(s,'rect',64,y,trainWidths[i],36,C.teal);shape(s,'rect',64+trainWidths[i]+5,y,98,36,C.red);txt(s,labs[i],64,y+40,740,28,19,C.muted);});
 shape(s,'rect',882,277,310,185,'#E5EBE3');
 txt(s,'8,758 test hours\nSame test hours\nNo retuning',902,296,276,145,27,C.ink,true);
 txt(s,'Baseline + Ridge + random forest + gradient boosting',64,565,1140,42,28,C.ink,true);
 txt(s,'Each regressor: calendar only vs calendar + weather. Train-fitted preprocessing.',64,624,1140,35,21,C.muted);
}
// 5: native comparative error chart.
{
 const s=slide('Adding weather lowers boosting RMSE by 16.16%',5);
 const fam=['Ridge','RandomForest','HistGradientBoosting'];
 const get=(m,v)=>data.scores.find(r=>r.model===m&&r.features===v);
 chart(s,'bar',{position:{left:64,top:194,width:830,height:399},categories:['Ridge','Random forest','Gradient boost'],
   series:[{name:'Calendar only',values:fam.map(m=>get(m,'time').RMSE),fill:C.red},{name:'Calendar + weather',values:fam.map(m=>get(m,'time_weather').RMSE),fill:C.teal}],
   barOptions:{direction:'column',grouping:'clustered',gapWidth:90},hasLegend:true,legend:{position:'top',overlay:false,textStyle:{typeface:font,fontSize:20,fill:C.ink}},
   xAxis:axis,yAxis:{...valueAxis,max:400,majorUnit:100,title:{text:'Test RMSE (rides/hour)',textStyle:{typeface:font,fontSize:20,fill:C.muted}}},dataLabels:{showValue:true,position:'outEnd',numberFormatCode:'0.0',textStyle:{typeface:font,fontSize:18,fill:C.ink}}});
 txt(s,'241.86',948,218,268,80,58,C.teal,true);txt(s,'Primary-model RMSE',948,304,268,60,24,C.muted);
 txt(s,'166.43',948,398,268,74,48,C.ink,true);txt(s,'Primary-model MAE',948,476,268,60,24,C.muted);
 txt(s,'2025 test. Weekly-mean baseline RMSE: 347.01. Primary model selected on 2024.',64,633,1130,34,20,C.muted);
}
// 6: diagnostic groups.
{
 const s=slide('Weekday peaks and wet hours have larger errors',6);
 const names=['Other hours','Peak weekday','Dry','Wet'];
 const g=names.map(n=>data.groups.find(r=>r.group===n));
 chart(s,'bar',{position:{left:64,top:194,width:795,height:402},categories:['Other hours','Weekday peaks','Dry','Wet'],
   series:[{name:'Primary-model MAE',values:g.map(r=>r.MAE),fill:C.teal,points:[{idx:1,fill:C.red},{idx:3,fill:C.red}]}],barOptions:{direction:'column',grouping:'clustered',gapWidth:95},hasLegend:false,
   xAxis:axis,yAxis:{...valueAxis,max:350,majorUnit:100,title:{text:'MAE (rides/hour)',textStyle:{typeface:font,fontSize:20,fill:C.muted}}},dataLabels:{showValue:true,position:'outEnd',numberFormatCode:'0.0',textStyle:{typeface:font,fontSize:22,fill:C.ink}}});
 txt(s,'Busy periods\nalso have\nhigher counts',930,217,286,170,34,C.ink,true);
 txt(s,'Larger absolute error\ndoes not automatically mean\nlarger percentage error',930,426,286,146,25,C.muted);
 txt(s,'Peak: weekdays 07-09 and 16-18 inclusive. Wet: precipitation > 0. Groups overlap.',64,632,1140,35,20,C.muted);
}
// 7: limitations grounded in the monthly bias.
{
 const s=slide('Weather helps, but estimates still drift',7,true);
 txt(s,'Monthly bias changes sign in 2025',64,180,800,44,29,C.white,true);
 txt(s,'Mean estimate minus observed (rides/hour)',64,221,740,30,19,'#DDE6DD');
 chart(s,'bar',{position:{left:64,top:246,width:720,height:286},categories:data.monthly.map(r=>String(r.month)),series:[{name:'Estimate minus observed',values:data.monthly.map(r=>r.bias),fill:'#D5B2A1',points:data.monthly.map((r,i)=>({idx:i,fill:r.bias<0?'#D5B2A1':'#98C5B4'}))}],hasLegend:false,barOptions:{direction:'column',gapWidth:50},xAxis:{...axis,textStyle:{typeface:font,fontSize:17,fill:'#E1E8E0'}},yAxis:{...axis,min:-250,max:200,majorUnit:100,textStyle:{typeface:font,fontSize:17,fill:'#E1E8E0'},majorGridlines:{fill:'#426258',width:1}}});
 txt(s,'Known weather conditions\nRecorded departures\nOne later test year',854,231,355,170,30,C.white,true);
 txt(s,'Advance weather forecasts\nand unmet demand\nneed different evidence',854,456,355,142,26,'#DDE6DD');
 txt(s,'Negative bias = underestimation',64,550,720,32,22,'#DDE6DD');
 txt(s,'Repository: github.com/Yuan-KG/Project_BikeSharing',64,631,1060,34,22,'#DDE6DD');
}
// Render every page before exporting the editable file.
for(let i=0;i<P.slides.items.length;i++){
 const blob=await P.export({slide:P.slides.items[i],format:'png',scale:1.5});
 await fs.writeFile(path.join(preview,`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await blob.arrayBuffer()));
 console.log('Rendered slide',i+1);
}
const candidate=path.join(preview,'candidate.pptx');
await (await PresentationFile.exportPptx(P)).save(candidate);
const finalPath=path.join(here,'BikeSharing_Presentation.pptx');
const result=await finalizePresentation({workspaceDir:root,candidatePath:candidate,finalPath,
 pythonExecutable:path.join(runtime,'python/python.exe'),
 integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
 layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit'],
 explicitTotalSlideCount:7,requiredNativeChartOwnerSlides:[3,5,6,7],requiredNativeTableOwnerSlides:[],
 fontPolicy:{basis:'design',families:[font]},materializeLiteralChartWorkbooks:true,verifyArtifactToolImport:true,
 receiptPath:path.join(preview,'presentation_validation.json')});
console.log(JSON.stringify(result));
