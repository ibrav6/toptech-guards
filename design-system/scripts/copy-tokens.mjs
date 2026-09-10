import { readFile, writeFile } from 'node:fs/promises';
const source = await readFile('src/tokens.css', 'utf8');
const block = source.match(/\.tt-theme\[data-theme='dark'\] \{([\s\S]*?)\n\}/);
if (!block) throw new Error('كتلة رموز الداكن غير موجودة');
const auto = `\n@media (prefers-color-scheme: dark) { .tt-theme[data-theme='auto'] {${block[1]}\n} }\n`;
await writeFile('dist/tokens.css', source + auto);
const compiled = await readFile('dist/styles.css', 'utf8');
await writeFile('dist/styles.css', compiled + auto);
