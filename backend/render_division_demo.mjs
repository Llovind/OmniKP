import fs from 'node:fs/promises';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';
const dir = '../frontend/public/demo/divisions';
const data = JSON.parse(await fs.readFile('evidence/division-demo/build-data.json', 'utf8'));
for (const entry of data) {
  const wb = Workbook.create();
  const sheet = wb.worksheets.add('Report');
  const end = String.fromCharCode(64 + entry.columns.length);
  sheet.getRange(`A1:${end}1`).merge();
  sheet.getRange('A1').values = [[`${entry.division} | Synthetic division report | June 2026`]];
  sheet.getRange(`A2:${end}2`).merge();
  sheet.getRange('A2').values = [['Reconstructed demo input. Values, targets, locations and feedback are synthetic. Use reporting date 2026-06-30.']];
  sheet.getRange(`A3:${end}3`).merge();
  sheet.getRange('A3').values = [['KPI names, units, direction and ownership: KPI WISA FM JUNI 2026 / WISA REKON BARU / SUB-UNIT REG BARU.']];
  sheet.getRange('A4').write([entry.columns, ...entry.rows]);
  if (end === 'H') {
    for (let row = 5; row <= entry.rows.length + 4; row++) {
      for (const [actual, achievement] of [['E','F'],['G','H']]) {
        sheet.getRange(`${achievement}${row}`).formulas = [[`=IF(C${row}="HIGHER BETTER",IF(D${row}=0,IF(${actual}${row}=0,100,"n.a."),${actual}${row}/D${row}*100),IF(${actual}${row}=0,IF(D${row}=0,100,"n.a."),D${row}/${actual}${row}*100))`]];
        sheet.getRange(`${achievement}${row}`).setNumberFormat('0.00');
      }
    }
  }
  sheet.getRange(`A1:${end}${4 + entry.rows.length}`).format.font.name = 'Calibri';
  sheet.getRange(`A1:${end}1`).format.fill = '#0B2B50';
  sheet.getRange(`A1:${end}1`).format.font.color = '#FFFFFF';
  sheet.getRange(`A1:${end}1`).format.font.bold = true;
  sheet.getRange(`A1:${end}1`).format.rowHeight = 32;
  sheet.getRange(`A2:${end}3`).format.rowHeight = 30;
  sheet.getRange(`A2:${end}3`).format.wrapText = true;
  sheet.getRange(`A4:${end}4`).format.fill = '#DCE9F8';
  sheet.getRange(`A4:${end}4`).format.font.bold = true;
  sheet.getRange(`A4:${end}${4 + entry.rows.length}`).format.rowHeight = 38;
  sheet.getRange(`A4:${end}${4 + entry.rows.length}`).format.wrapText = true;
  sheet.getRange('A:A').format.columnWidth = 64;
  sheet.getRange(`B:${end}`).format.columnWidth = 20;
  if (end === 'G') sheet.getRange('G:G').format.columnWidth = 60;
  sheet.freezePanes.freezeRows(4);
  sheet.showGridLines = false;
  wb.recalculate();
  console.log((await wb.inspect({kind:'table', range:'Report!A4:D6', tableMaxRows:3, tableMaxCols:4})).ndjson);
  await (await SpreadsheetFile.exportXlsx(wb)).save(`${dir}/${entry.filename}`);
  const preview = await wb.render({sheetName:'Report', range:`A1:${end}8`, scale:1, format:'png'});
  await fs.writeFile(`evidence/division-demo/${entry.division.replaceAll(/[^a-z0-9]/gi,'-')}.png`, new Uint8Array(await preview.arrayBuffer()));
}
