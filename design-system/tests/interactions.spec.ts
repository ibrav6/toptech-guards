import { test, expect, type Page, type Locator } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
async function visibleWithin(page: Page, locator: Locator) {
  await expect(locator).toBeVisible();
  // Popper يضع العنصر خارج الشاشة قبل حساب الموضع؛ ننتظر النتيجة المستقرة لا إطار التركيب.
  const viewport = page.viewportSize()!;
  await expect.poll(async () => {
    const b = await locator.boundingBox();
    return !!b && b.x >= -1 && b.y >= -1 && b.x + b.width <= viewport.width + 1 && b.y + b.height <= viewport.height + 1;
  }).toBe(true);
  const box = await locator.boundingBox();
  expect(box).not.toBeNull();
  expect(box!.x).toBeGreaterThanOrEqual(-1); expect(box!.y).toBeGreaterThanOrEqual(-1);
  expect(box!.x + box!.width).toBeLessThanOrEqual(viewport.width + 1);
  expect(box!.y + box!.height).toBeLessThanOrEqual(viewport.height + 1);
}
async function noOverflow(page: Page) {
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
}
for (const width of [320,390,768,980,1440]) {
 test(`التنقل والمحتوى داخل شاشة ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 900 }); await page.goto('/');
  await expect(page.getByRole('heading', { name: 'وضوحٌ يقود العمل.' })).toBeVisible(); await noOverflow(page);
  if(width < 1024) {
   const trigger = page.getByRole('button',{name:'فتح التنقل'}); await trigger.click();
   const drawer = page.getByRole('dialog',{name:'التنقل'}); await visibleWithin(page,drawer);
   await drawer.getByRole('link',{name:'المكوّنات',exact:true}).click(); await expect(drawer).toBeHidden();
   await expect(page.getByRole('heading',{name:'مكوّنات تتصرّف باتساق'})).toBeVisible();
   await expect(page.locator('body')).not.toHaveAttribute('data-scroll-locked');
  } else {
   const trigger = page.getByRole('button',{name:'طيّ التنقل'}); const before = await trigger.boundingBox();
   const mainBefore=await page.getByRole('main').boundingBox(); await trigger.click();
   await expect(trigger).toHaveAttribute('aria-expanded','false');
   await expect.poll(async () => (await page.getByRole('main').boundingBox())!.width).toBeGreaterThan(mainBefore!.width);
   expect((await trigger.boundingBox())!.x).toBe(before!.x);
   await page.getByRole('navigation',{name:'التنقل الرئيسي'}).getByRole('link',{name:'المكوّنات',exact:true}).click();
  }
  await noOverflow(page);
 });
}
for (const dir of ['rtl','ltr']) {
 test(`قائمة داخل نافذة: الاتجاه والتركيز والحواف ${dir}`, async ({page})=>{
  await page.setViewportSize({width:390,height:844}); await page.goto(`/?dir=${dir}&theme=dark#components`);
  const trigger=page.getByRole('button',{name:'إنشاء مساحة',exact:true}); await trigger.click();
  const dialog=page.getByRole('dialog',{name:'مساحة جديدة للفريق'}); await visibleWithin(page,dialog);
  await dialog.getByRole('button',{name:'خيارات المساحة',exact:true}).click();
  const menu=page.getByRole('menu').first(); await visibleWithin(page,menu);
  await expect(menu).toHaveCSS('direction',dir);
  await expect(menu).toHaveCSS('background-color','rgb(49, 49, 47)');
  await page.keyboard.press('Escape'); await expect(menu).toBeHidden(); await expect(dialog).toBeVisible();
  await expect(dialog.getByRole('button',{name:'خيارات المساحة',exact:true})).toBeFocused();
  await page.keyboard.press('Escape'); await expect(dialog).toBeHidden(); await expect(trigger).toBeFocused();
  await expect(page.locator('body')).not.toHaveAttribute('data-scroll-locked');
 });
}
test('التحقق من الحقل ثم نجاح الإجراء',async({page})=>{
 await page.goto('/#components'); await page.getByRole('button',{name:'إنشاء مساحة',exact:true}).click();
 const dialog=page.getByRole('dialog',{name:'مساحة جديدة للفريق'});
 await dialog.getByRole('button',{name:'إنشاء المساحة',exact:true}).click();
 const input=dialog.getByLabel('اسم المساحة'); await expect(input).toHaveAttribute('aria-invalid','true');
 await expect(dialog.getByRole('alert')).toHaveText('اكتب اسم المساحة للمتابعة.');
 await input.fill('القطاع الصحي'); await dialog.getByRole('button',{name:'إنشاء المساحة',exact:true}).click();
 await expect(dialog).toBeHidden(); await expect(page.getByText('أُنشئت «القطاع الصحي» في المعاينة')).toBeVisible();
});
test('Select داخل الدرج يحصر القيمة الطويلة',async({page})=>{
 await page.setViewportSize({width:320,height:640}); await page.goto('/#components');
 await page.getByRole('button',{name:'فتح الفلاتر',exact:true}).click(); const drawer=page.getByRole('dialog',{name:'تصفية النتائج'});
 await drawer.getByRole('combobox').click(); await visibleWithin(page,page.getByRole('listbox'));
 await page.getByRole('option',{name:'منطقة مكة المكرمة',exact:true}).click();
 await expect(drawer.getByRole('combobox')).toContainText('منطقة مكة المكرمة');
 await drawer.getByRole('combobox').click();
 await page.getByRole('option',{name:'منطقة ذات اسم عربي طويل لا ينبغي أن يتجاوز حدود شاشة الجوال',exact:true}).click();
 await visibleWithin(page,drawer.getByRole('combobox'));
 await page.keyboard.press('Escape'); await expect(drawer).toBeHidden(); await noOverflow(page);
});
test('الدرج يحصر التركيز ويغلق عند توسيع الشاشة',async({page})=>{
 await page.setViewportSize({width:390,height:844}); await page.goto('/'); await page.getByRole('button',{name:'فتح التنقل'}).click();
 const drawer=page.getByRole('dialog',{name:'التنقل'});
 await expect(page.locator('body')).toHaveAttribute('data-scroll-locked');
 for(let i=0;i<9;i++){ await page.keyboard.press('Tab'); expect(await drawer.evaluate(el=>el.contains(document.activeElement))).toBe(true); }
 await page.setViewportSize({width:1440,height:900}); await expect(drawer).toBeHidden();
 await expect(page.locator('body')).not.toHaveAttribute('data-scroll-locked');
 await expect(page.getByRole('button',{name:'طيّ التنقل'})).toBeVisible();
});
test('النقر خارج القائمة يغلقها، والأسهم تفتح القائمة الفرعية وفق RTL',async({page})=>{
 await page.goto('/#components'); await page.getByRole('button',{name:'إجراءات المشروع',exact:true}).click();
 const sub=page.getByRole('menuitem',{name:'مشاركة مع الفريق'}); await sub.focus(); await page.keyboard.press('ArrowLeft');
 await expect(page.getByRole('menuitem',{name:'للقراءة فقط',exact:true})).toBeVisible();
 await page.getByRole('menuitem',{name:'للقراءة فقط',exact:true}).click();
 await expect(page.getByText('تم اختيار صلاحية القراءة')).toBeVisible();
 await page.getByRole('button',{name:'إجراءات المشروع',exact:true}).click(); await page.mouse.click(2,2);
 await expect(page.getByRole('menu')).toBeHidden();
});
test('الحالة الفارغة والخطأ يعرضان إجراء يمكن إكماله',async({page})=>{
 await page.goto('/#components');
 await expect(page.getByRole('heading',{name:'مساحتك جاهزة لأول فرصة'})).toBeVisible();
 await page.getByRole('button',{name:'إضافة فرصة تجريبية'}).click();
 await expect(page.getByRole('table')).toBeVisible();
 await page.getByRole('tab',{name:'خطأ',exact:true}).click();
 await expect(page.getByRole('heading',{name:'تعذّر تحميل المحتوى'})).toBeVisible();
 await page.getByRole('button',{name:'إعادة المحاولة',exact:true}).click();
 await expect(page.getByRole('table')).toBeVisible();
});
for(const section of ['overview','foundations','components','patterns','guidelines']) {
 test(`فحص الإتاحة وتجاوز الصفحة ${section}`,async({page})=>{
  await page.setViewportSize({width:390,height:844}); await page.goto(`/#${section}`); await page.evaluate(()=>document.fonts.ready);
  await noOverflow(page);
  const results=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();
  expect(results.violations).toEqual([]);
 });
}
test('تكبير النص لا يحجب إجراءات النافذة',async({page})=>{
 await page.setViewportSize({width:390,height:844}); await page.goto('/#components');
 await page.addStyleTag({content:'html { font-size: 200%; }'});
 await page.getByRole('button',{name:'إنشاء مساحة',exact:true}).click(); const dialog=page.getByRole('dialog',{name:'مساحة جديدة للفريق'});
 await visibleWithin(page,dialog); await dialog.getByRole('button',{name:'إلغاء',exact:true}).click(); await expect(dialog).toBeHidden();
});

test('قائمة فرعية داخل نافذة على أصغر عرض',async({page})=>{
 await page.setViewportSize({width:320,height:640}); await page.goto('/#components');
 await page.getByRole('button',{name:'إنشاء مساحة',exact:true}).click();
 await page.getByRole('button',{name:'خيارات المساحة',exact:true}).click();
 const trigger=page.getByRole('menuitem',{name:'مشاركة مع الفريق'}); await trigger.focus(); await page.keyboard.press('ArrowLeft');
 const child=page.getByRole('menu').filter({has:page.getByRole('menuitem',{name:'للقراءة فقط',exact:true})});
 await visibleWithin(page,child);
 await page.getByRole('menuitem',{name:'للقراءة فقط',exact:true}).click();
 await expect(page.getByRole('dialog',{name:'مساحة جديدة للفريق'})).toBeVisible();
});
test('اللمس يفتح القائمة ويختار القيمة داخل درج الجوال',async({browser,browserName})=>{
 test.skip(browserName==='firefox','محاكاة اللمس ليست متاحة في Firefox عبر Playwright');
 const context=await browser.newContext({viewport:{width:390,height:844},hasTouch:true,isMobile:true,locale:'ar-SA'});
 const page=await context.newPage();
 await page.goto('http://127.0.0.1:4178/#components'); await page.getByRole('button',{name:'فتح الفلاتر',exact:true}).tap();
 const drawer=page.getByRole('dialog',{name:'تصفية النتائج'}); await drawer.getByRole('combobox').tap();
 await page.getByRole('option',{name:'المنطقة الشرقية',exact:true}).tap();
 await expect(drawer.getByRole('combobox')).toContainText('المنطقة الشرقية');
 await drawer.getByRole('button',{name:'إغلاق',exact:true}).tap(); await expect(drawer).toBeHidden(); await context.close();
});
test('إتاحة النافذة المفتوحة في المظهرين',async({page})=>{
 for(const theme of ['light','dark']) {
  await page.goto(`/?theme=${theme}#components`); await page.getByRole('button',{name:'إنشاء مساحة',exact:true}).click();
  const results=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();
  expect(results.violations).toEqual([]);
 }
});

test('قوالب التفاصيل والإعدادات تعمل على الجوال',async({page})=>{
 await page.setViewportSize({width:390,height:844}); await page.goto('/#patterns');
 await page.getByRole('tab',{name:'تفاصيل',exact:true}).click();
 await expect(page.getByRole('heading',{name:'تطوير منصة لخدمات المستفيدين'})).toBeVisible(); await noOverflow(page);
 await page.getByRole('tab',{name:'إعدادات',exact:true}).click();
 await page.getByLabel('اسم الفريق').fill('فريق المشروع'); await page.getByRole('button',{name:'حفظ التغييرات',exact:true}).click();
 await expect(page.getByRole('status')).toHaveText('حُفظت التفضيلات في المعاينة'); await noOverflow(page);
});
test('وضع النظام يرث الداكن قبل التفاعل ويحمله إلى البوابة',async({page})=>{
 await page.emulateMedia({colorScheme:'dark'}); await page.goto('/?theme=auto#components');
 await page.getByRole('button',{name:'إنشاء مساحة',exact:true}).click();
 await expect(page.getByRole('dialog',{name:'مساحة جديدة للفريق'})).toHaveCSS('background-color','rgb(39, 39, 37)');
});
