const mobile = process.env.TT_PERF_MODE === 'mobile';
/* ‼ **ميزانيّتان لأن الآلتين ليستا واحدة** — لا تخفيفاً للحارس.
   عدّاءُ GitHub نواتان مشتركتان، والمرجع قِيس على دوكر محلّي. قياس
   الجولة 34448681317 على العدّاء بلا أي تغييرٍ في المكتبة:
     LCP  وسيط 3008 و3097 مل‌ث (الحدّ المحلّي 2500)
     CLS  وسيط 0.126 و0.143      (الحدّ المحلّي 0.10)
   ودرجةُ الأداء نفسها (.85) وTBT مرّتا — أي أن الرقمين قاسا آلةً لا
   انحداراً. فالحدّ في CI من المقيس + هامش ~15%: يبقى الحارس قادراً على
   السقوط عند انحدارٍ حقيقي، ويبقى الحدّ المحلّي هو الطموح. */
const ci = !!process.env.CI;
module.exports = { ci: {
  collect: {
    startServerCommand: 'node node_modules/vite/bin/vite.js preview --host 127.0.0.1 --port 4180 --strictPort',
    startServerReadyPattern: 'Local:',
    url: ['http://127.0.0.1:4180/', 'http://127.0.0.1:4180/?view=components#components'],
    numberOfRuns: 3,
    settings: { chromeFlags: '--headless --no-sandbox', ...(mobile ? {} : { preset: 'desktop' }), onlyCategories: ['performance','accessibility'] }
  },
  assert: { assertions: {
    'categories:performance': ['error', { minScore: .85, aggregationMethod: 'median' }],
    'categories:accessibility': ['error', { minScore: .95, aggregationMethod: 'median' }],
    'largest-contentful-paint': ['error', { maxNumericValue: ci ? 3600 : 2500, aggregationMethod: 'median' }],
    'cumulative-layout-shift': ['error', { maxNumericValue: ci ? .17 : .1, aggregationMethod: 'median' }],
    'total-blocking-time': ['error', { maxNumericValue: 200, aggregationMethod: 'median' }],
    'total-byte-weight': ['error', { maxNumericValue: 850000, aggregationMethod: 'median' }]
  } },
  upload: { target: 'filesystem', outputDir: `.lighthouseci/reports/${mobile ? 'mobile' : 'desktop'}` }
} };
