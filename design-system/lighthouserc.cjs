const mobile = process.env.TT_PERF_MODE === 'mobile';
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
    'largest-contentful-paint': ['error', { maxNumericValue: 2500, aggregationMethod: 'median' }],
    'cumulative-layout-shift': ['error', { maxNumericValue: .1, aggregationMethod: 'median' }],
    'total-blocking-time': ['error', { maxNumericValue: 200, aggregationMethod: 'median' }],
    'total-byte-weight': ['error', { maxNumericValue: 850000, aggregationMethod: 'median' }]
  } },
  upload: { target: 'filesystem', outputDir: `.lighthouseci/reports/${mobile ? 'mobile' : 'desktop'}` }
} };
