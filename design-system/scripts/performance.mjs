import { chromium } from '@playwright/test';
import { spawnSync } from 'node:child_process';
for (const mode of ['desktop','mobile']) {
  const result = spawnSync(process.execPath, ['node_modules/@lhci/cli/src/cli.js', 'autorun', '--config=lighthouserc.cjs'], { stdio: 'inherit', env: { ...process.env, CHROME_PATH: chromium.executablePath(), TT_PERF_MODE: mode } });
  if (result.error) console.error(result.error.message);
  if (result.status !== 0) process.exit(result.status ?? 1);
}
