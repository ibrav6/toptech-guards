import { build } from 'vite';
import react from '@vitejs/plugin-react';
import { readFile, writeFile } from 'node:fs/promises';
import { pathToFileURL } from 'node:url';
import path from 'node:path';
// LCP بقي 3ث مع CSS مبكّر لأن العنوان ينتظر JS؛ نخبز المحتوى الحقيقي ثم نربطه بالتفاعل.
const out = path.resolve('.lighthouseci/prerender');
await build({ configFile: false, plugins: [react()], build: { ssr: 'gallery/prerender.tsx', outDir: out, emptyOutDir: true } });
const { renderPages } = await import(pathToFileURL(path.join(out, 'prerender.js')).href);
// القوالب تشترك في معظم الوسوم؛ قاموس واحد يمنع تحميل نسخ كاملة لكل مظهر واتجاه.
const dictionary = [];
const ids = new Map();
const encoded = {};
for (const [key, html] of Object.entries(await renderPages())) {
 encoded[key] = (html.match(/<[^>]+>|[^<]+/g) ?? []).map(token => {
  if (!ids.has(token)) { ids.set(token, dictionary.length); dictionary.push(token); }
  return ids.get(token);
 });
}
const pages = JSON.stringify({ dictionary, encoded }).replaceAll('<', '\\u003c');
let html = await readFile('gallery-dist/index.html', 'utf8');
if (html.includes('id="gallery-prerenders"')) throw new Error('أعد build:gallery؛ لا تُلحق القوالب بمعرض مخبوز سابقاً.');
const entry = html.match(/<script type="module"[^>]*src="([^"]+)"[^>]*><\/script>/);
if (!entry) throw new Error('تعذر تحديد مدخل تفاعل المعرض');
html = html.replace(entry[0], '');
// المحتوى المخبوز يرسم أولاً؛ ربط التفاعل قبل أول إطار أعاد LCP إلى انتظار JS.
const launch = `requestAnimationFrame(()=>requestAnimationFrame(()=>{const script=document.createElement('script');script.type='module';script.src=${JSON.stringify(entry[1])};document.head.append(script);}));`;
const boot = `<script id="gallery-prerenders" type="application/json">${pages}</script><script>{const p=new URLSearchParams(location.search);const theme=['dark','auto'].includes(p.get('theme'))?p.get('theme'):'light';const dir=p.get('dir')==='ltr'?'ltr':'rtl';const section=['foundations','components','patterns','guidelines'].includes(location.hash.slice(1))?location.hash.slice(1):'overview';const data=document.getElementById('gallery-prerenders');const pages=JSON.parse(data.textContent);document.getElementById('root').inert=true;document.getElementById('root').innerHTML=pages.encoded[section+'/'+theme+'/'+dir].map(i=>pages.dictionary[i]).join('');data.remove();}${launch}</script>`;
html = html.replace('<div id="root"></div>', '<div id="root"></div>' + boot);
await writeFile('gallery-dist/index.html', html);
