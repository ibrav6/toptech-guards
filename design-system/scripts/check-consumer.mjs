import { readFileSync, existsSync } from 'node:fs';
import { gunzipSync } from 'node:zlib';
import { createHash } from 'node:crypto';
import path from 'node:path';
const manifest = JSON.parse(readFileSync('package.json','utf8'));
const web = path.resolve('../../web');
// الحزمة قابلة للنقل؛ هذا السلك يخص مستهلك المناقصات عندما يكون حاضراً.
if (!existsSync(path.join(web,'package.json'))) process.exit(0);
const consumer = JSON.parse(readFileSync(path.join(web,'package.json'),'utf8'));
const dependency = consumer.dependencies?.['@toptech/ui'];
if (!dependency?.startsWith('file:vendor/')) throw new Error('مستهلك الهوية لا يشير إلى الإصدار المحلي المثبّت');
const tar = gunzipSync(readFileSync(path.join(web, dependency.slice(5))));
const entries = new Map();
for(let offset=0; offset+512<=tar.length;) {
 const header=tar.subarray(offset,offset+512); const name=header.subarray(0,100).toString().replace(/\0.*$/s,'');
 if(!name) break;
 const size=parseInt(header.subarray(124,136).toString().replace(/\0.*$/s,''),8) || 0;
 entries.set(name,tar.subarray(offset+512,offset+512+size)); offset+=512+Math.ceil(size/512)*512;
}
const digest = bytes => createHash('sha256').update(bytes).digest('hex');
for(const name of ['index.js','index.d.ts','styles.css','tokens.css']) {
 const archived=entries.get(`package/dist/${name}`);
 if(!archived || digest(archived)!==digest(readFileSync(`dist/${name}`))) throw new Error(`إصدار web بائت: ${name}. أعد npm pack ثم ثبّت الملف في web.`);
}
const packed=JSON.parse(entries.get('package/package.json').toString());
if(packed.version!==manifest.version || JSON.stringify(packed.dependencies)!==JSON.stringify(manifest.dependencies)) throw new Error('إصدار الحزمة أو اعتمادياتها لا يطابق المصدر');
console.log('✓ الحزمة المركّبة تطابق المخرَج المخبوز');
