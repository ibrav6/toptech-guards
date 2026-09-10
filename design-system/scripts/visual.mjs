import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const updating = process.argv.includes('--update');
// صورة واحدة على الماك وCI: لا مراجع متشابهة تختلف بخطوط نظام التشغيل.
if (process.platform === 'linux') {
  const result = spawnSync(process.execPath, ['node_modules/@playwright/test/cli.js', 'test', '--project=visual', ...(updating ? ['--update-snapshots'] : [])], { stdio: 'inherit' });
  process.exit(result.status ?? 1);
}
const result = spawnSync('docker', ['run','--rm','--platform','linux/amd64','--ipc=host','-v',`${root}:/work`,'-v','toptech-design-linux-amd64-deps:/work/node_modules','-w','/work','mcr.microsoft.com/playwright:v1.63.0-noble','bash','-lc',`npm ci --no-audit --no-fund && npm run build && npm run build:gallery && npx playwright test --project=visual${updating?' --update-snapshots':''}`], { stdio:'inherit' });
if (result.error) console.error(result.error.message);
process.exit(result.status ?? 1);
