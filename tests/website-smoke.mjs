import { test } from "node:test";
import { strict as assert } from "node:assert";
import { readFile, readdir } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(__dirname, "..");

const htmlFiles = (await readdir(repoRoot))
  .filter((name) => name.endsWith(".html"))
  .sort();

assert.ok(htmlFiles.length > 0, "expected at least one root *.html file");

for (const file of htmlFiles) {
  test(`${file} renders non-empty HTML with title and content`, async () => {
    const path = join(repoRoot, file);
    const html = await readFile(path, "utf8");

    assert.ok(html.length > 0, `${file} is empty`);

    const titleMatch = html.match(/<title>([\s\S]*?)<\/title>/i);
    assert.ok(titleMatch, `${file} is missing a <title> tag`);
    assert.ok(
      titleMatch[1].trim().length > 0,
      `${file} has an empty <title>`,
    );

    const hasContent = /<a[\s>]|<h1[\s>]|<h2[\s>]/i.test(html);
    assert.ok(
      hasContent,
      `${file} has no <a>, <h1>, or <h2> elements`,
    );
  });
}
