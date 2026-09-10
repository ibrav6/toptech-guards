import { defineConfig, devices } from '@playwright/test';
export default defineConfig({
  testDir: './tests', fullyParallel: true, workers: process.env.CI ? 2 : 4,
  forbidOnly: !!process.env.CI, retries: 0, timeout: 30_000,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: { baseURL: 'http://127.0.0.1:4178', locale: 'ar-SA', timezoneId: 'Asia/Riyadh', reducedMotion: 'reduce', trace: 'retain-on-failure', screenshot: 'only-on-failure' },
  expect: { timeout: 5000, toHaveScreenshot: { animations: 'disabled', maxDiffPixelRatio: .002 } },
  webServer: { command: 'npm run preview', url: 'http://127.0.0.1:4178', reuseExistingServer: false, timeout: 30_000 },
  projects: [
    { name: 'chromium', testIgnore: /visual\.spec/, use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', testIgnore: /visual\.spec/, use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', testIgnore: /visual\.spec/, use: { ...devices['Desktop Safari'] } },
    // مرجع بصري واحد: Linux داخل صورة المتصفح المثبتة نفسها على الجهاز وCI.
    { name: 'visual', testMatch: /visual\.spec/, use: { ...devices['Desktop Chrome'] } }
  ]
});
