import { test, expect } from '@playwright/test';
// الصور لا تتحدّث تلقائياً؛ اعتمادها قرار مراجعة في فرق git، داخل Linux المثبّت.
for(const theme of ['light','dark']) for(const width of [390,1440]) {
 test(`الهوية ${theme} ${width}`,async({page})=>{
  await page.setViewportSize({width,height:1000}); await page.goto(`/?theme=${theme}`); await page.evaluate(()=>document.fonts.ready);
  await expect(page).toHaveScreenshot(`identity-${theme}-${width}.png`,{fullPage:true});
 });
 test(`القائمة داخل نافذة ${theme} ${width}`,async({page})=>{
  await page.setViewportSize({width,height:1000}); await page.goto(`/?theme=${theme}#components`); await page.evaluate(()=>document.fonts.ready);
  await page.getByRole('button',{name:'إنشاء مساحة',exact:true}).click();
  await page.getByRole('button',{name:'خيارات المساحة',exact:true}).click();
  await expect(page).toHaveScreenshot(`overlay-${theme}-${width}.png`);
 });
}
