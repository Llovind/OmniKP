import { chromium } from 'playwright';
import fs from 'node:fs/promises';
const browser = await chromium.launch({headless:true, channel:'chrome'});
const page = await browser.newPage({viewport:{width:1440,height:960}, deviceScaleFactor:1});
const errors=[];
page.on('pageerror', e => errors.push(e.message));
await page.goto('http://localhost:5173/');
await page.getByRole('button',{name:'Try demo',exact:true}).first().click();
await page.waitForURL('**/app?demo=1');
await page.getByText('Synthetic demo data',{exact:true}).waitFor();
await page.getByText('180',{exact:true}).waitFor();
await fs.mkdir('../frontend/public/landing',{recursive:true});
await page.screenshot({path:'../frontend/public/landing/workspace.png'});
await page.getByRole('button',{name:'Reset demo',exact:true}).click();
await page.getByText('180',{exact:true}).waitFor();
await page.goto('http://localhost:5173/');
for(const width of [390,768,1440]) {
  await page.setViewportSize({width,height:960});
  await page.evaluate(() => document.fonts.ready);
  const overflow=await page.evaluate(() => document.documentElement.scrollWidth>innerWidth);
  if(overflow) throw new Error(`Overflow at ${width}`);
  await page.screenshot({path:`evidence/landing-${width}.png`,fullPage:true});
}
console.log(JSON.stringify({errors, widths:[390,768,1440], screenshot:'workspace.png',demoReadings:180}));
await browser.close();
if(errors.length) process.exitCode=1;
