const { chromium } = require('playwright-core');
const path = require('path');

(async () => {
  const browser = await chromium.launch({
    executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
    args: ['--no-sandbox', '--disable-dev-shm-usage', '--force-color-profile=srgb'],
  });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1350 }, deviceScaleFactor: 2 });
  await page.goto('file://' + path.resolve(__dirname, 'rody2.html'), { waitUntil: 'load' });

  for (const [cls, out] of [['wbold', 'slide_rody_bold.png'], ['wthin', 'slide_rody_thin.png']]) {
    await page.evaluate((c) => { document.documentElement.className = c; }, cls);
    try { await page.evaluate(() => document.fonts.ready); } catch (e) {}
    await page.evaluate(async () => {
      await Promise.all(Array.from(document.images).map(img =>
        img.complete && img.naturalWidth > 0 ? Promise.resolve()
        : new Promise(res => { img.onload = img.onerror = res; })));
    });
    await page.waitForTimeout(500);
    const el = await page.$('#slide1');
    await el.screenshot({ path: path.resolve(__dirname, out) });
    console.log('saved', out);
  }
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
