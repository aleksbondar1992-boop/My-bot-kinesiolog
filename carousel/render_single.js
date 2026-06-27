const { chromium } = require('playwright-core');
const path = require('path');

// usage: node render_single.js <html> <out.png>
const htmlArg = process.argv[2] || 'rody.html';
const outArg = process.argv[3] || 'slide_rody.png';

(async () => {
  const browser = await chromium.launch({
    executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
    args: ['--no-sandbox', '--disable-dev-shm-usage', '--force-color-profile=srgb'],
  });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1350 }, deviceScaleFactor: 2 });
  await page.goto('file://' + path.resolve(__dirname, htmlArg), { waitUntil: 'load' });
  try { await page.evaluate(() => document.fonts.ready); } catch (e) {}
  await page.evaluate(async () => {
    await Promise.all(Array.from(document.images).map(img =>
      img.complete && img.naturalWidth > 0 ? Promise.resolve()
      : new Promise(res => { img.onload = img.onerror = res; })));
  });
  await page.waitForTimeout(500);
  const el = await page.$('#slide1');
  await el.screenshot({ path: path.resolve(__dirname, outArg) });
  console.log('saved', outArg);
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
