#!/usr/bin/env node
// capture-web.mjs — Playwright capture: full-page screenshot + video + trace.
//
// Invoked by capture.sh (`capture.sh web`). Loads 'playwright' relative to
// process.cwd() via createRequire, so it resolves the *project's* install no
// matter where this script lives (it ships inside a skill dir).
//
// Usage: node capture-web.mjs --url URL --out DIR --name NAME [--steps FILE] [--timeout MS]
//   --steps FILE : a JS module that default-exports `async (page) => { ... }`
//                  run after navigation (clicks, fills) before the screenshot.
// Prints {"screenshot","video","trace"} (names relative to --out) to stdout.

import { createRequire } from 'module';
import { pathToFileURL } from 'url';
import path from 'path';
import fs from 'fs';

const require = createRequire(process.cwd() + '/');

function parseArgs(argv) {
  const o = { timeout: 15000 };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--url') o.url = argv[++i];
    else if (a === '--out') o.out = argv[++i];
    else if (a === '--name') o.name = argv[++i];
    else if (a === '--steps') o.steps = argv[++i];
    else if (a === '--timeout') o.timeout = parseInt(argv[++i], 10);
    else if (a === '--help' || a === '-h') o.help = true;
  }
  return o;
}

const opt = parseArgs(process.argv.slice(2));
if (opt.help || !opt.url || !opt.out || !opt.name) {
  process.stderr.write(
    'usage: capture-web.mjs --url URL --out DIR --name NAME [--steps FILE] [--timeout MS]\n');
  process.exit(opt.help ? 0 : 1);
}

const { chromium } = require('playwright');

const shotName = `${opt.name}.png`;
const traceName = `${opt.name}-trace.zip`;
const videoName = `${opt.name}.webm`;

const browser = await chromium.launch();
const context = await browser.newContext({ recordVideo: { dir: opt.out } });
await context.tracing.start({ screenshots: true, snapshots: true });
const page = await context.newPage();

let ok = true;
try {
  await page.goto(opt.url, { waitUntil: 'load', timeout: opt.timeout });
  if (opt.steps) {
    const mod = await import(pathToFileURL(path.resolve(opt.steps)).href);
    if (typeof mod.default === 'function') await mod.default(page);
  }
  await page.screenshot({ path: path.join(opt.out, shotName), fullPage: true });
} catch (e) {
  ok = false;
  process.stderr.write(`capture-web: ${e.message}\n`);
} finally {
  await context.tracing.stop({ path: path.join(opt.out, traceName) });
  const video = page.video();
  await context.close();   // flushes the video file to disk
  await browser.close();
  if (video) {
    try { fs.renameSync(await video.path(), path.join(opt.out, videoName)); }
    catch { /* no video on immediate navigation failure */ }
  }
}

const result = {};
if (fs.existsSync(path.join(opt.out, shotName))) result.screenshot = shotName;
if (fs.existsSync(path.join(opt.out, videoName))) result.video = videoName;
if (fs.existsSync(path.join(opt.out, traceName))) result.trace = traceName;
process.stdout.write(JSON.stringify(result) + '\n');
process.exit(ok ? 0 : 5);
