import fs from 'node:fs/promises';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';
const dir='../frontend/public/demo/divisions';
const readings=JSON.parse(await fs.readFile(`${dir}/expected-readings.json`,'utf8'));
const summary=JSON.parse(await fs.readFile(`${dir}/validation-summary.json`,'utf8'));
function style(sheet, cols, rows) {
  sheet.getRangeByIndexes(0,0,rows,cols).format.font.name='Calibri';
  sheet.getRangeByIndexes(0,0,1,cols).format.fill='#0B2B50';
  sheet.getRangeByIndexes(0,0,1,cols).format.font.color='#FFFFFF';
  sheet.getRangeByIndexes(0,0,1,cols).format.font.bold=true;
  sheet.getRangeByIndexes(0,0,rows,cols).format.columnWidth=22;
  sheet.getRangeByIndexes(0,0,rows,cols).format.rowHeight=32;
  sheet.freezePanes.freezeRows(1); sheet.showGridLines=false;
}
const wb=Workbook.create();
const overview=wb.worksheets.add('Validation summary');
const totals=[['SYNTHETIC DEMO - unit','KPIs','Readings','Meeting target','Missing target'],...Object.entries(summary.units).map(([name,s])=>[name,s.kpis,s.readings,s.meeting,s.missing])];
overview.getRange('A1').write(totals); style(overview,5,totals.length); overview.getRange('A:A').format.columnWidth=36;
overview.getRange('A11:E11').merge();overview.getRange('A11').values=[['Reference calculated independently from the seven exported XLSX files.']];
overview.getRange('A12:E12').merge();overview.getRange('A12').values=[['Synthetic values, targets, locations and feedback. Organizational KPI labels follow the source.']];
const sheet=wb.worksheets.add('Expected readings');
const rows=readings.map(r=>[r.division,r.kpi_name,r.location_name,r.date,r.unit,r.higher_is_better?'Higher better':'Lower better',r.actual_value,r.target_value,r.attainment_pct??'n.a.',r.status,r.source_file,r.source_row]);
sheet.getRange('A1').write([['Submitting unit','KPI','Location','Reporting date','Unit','Direction','Actual','Target','Achievement %','Expected status','Source file','Source row'],...rows]);style(sheet,12,rows.length+1);sheet.getRange('B:B').format.columnWidth=76;sheet.getRange('B:B').format.wrapText=true;sheet.getRange('I2:I181').setNumberFormat('0.00');
wb.recalculate();await(await SpreadsheetFile.exportXlsx(wb)).save(`${dir}/expected-consolidated.xlsx`);
for(const name of ['Validation summary','Expected readings']) {const p=await wb.render({sheetName:name,range:name==='Expected readings'?'A1:F7':'A1:E12',scale:1});await fs.writeFile(`evidence/division-demo/${name.replaceAll(' ','-')}.png`,new Uint8Array(await p.arrayBuffer()));}
const inputs=JSON.parse(await fs.readFile('evidence/division-demo/build-data.json','utf8'));
for(const kind of ['missing-value','changed-headers','duplicate-reading']) {
  const base=inputs.find(e=>e.division==='ED');const values=structuredClone(base.rows.slice(0,2));const headers=[...base.columns];
  if(kind==='missing-value') values[0][5]=null;
  if(kind==='changed-headers') {headers[0]='Performance measure';headers[5]='Observed outcome';}
  if(kind==='duplicate-reading') values.push([...values[0]]);
  const book=Workbook.create();const page=book.worksheets.add('Report');page.getRange('A1').write([headers,...values]);style(page,7,values.length+1);page.getRange('A:A').format.columnWidth=65;page.getRange('G:G').format.columnWidth=70;page.getUsedRange().format.wrapText=true;
  book.recalculate();await(await SpreadsheetFile.exportXlsx(book)).save(`${dir}/${kind}.xlsx`);
  const p=await book.render({sheetName:'Report',range:'A1:G4',scale:1});await fs.writeFile(`evidence/division-demo/${kind}.png`,new Uint8Array(await p.arrayBuffer()));
}
