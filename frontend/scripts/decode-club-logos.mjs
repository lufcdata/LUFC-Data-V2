import { readFile, writeFile } from 'node:fs/promises';

const source = new URL('../public/club-logos-sprite.webp.b64', import.meta.url);
const target = new URL('../public/club-logos-sprite.webp', import.meta.url);

const base64 = (await readFile(source, 'utf8')).trim();
if (!base64) throw new Error('Club crest sprite source is empty');

const bytes = Buffer.from(base64, 'base64');
if (bytes.length === 0) throw new Error('Club crest sprite decode produced no bytes');

await writeFile(target, bytes);
console.log(`Generated club crest sprite: ${bytes.length} bytes`);
