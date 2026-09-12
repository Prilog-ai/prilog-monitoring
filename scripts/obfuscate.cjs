'use strict';

const fs = require('node:fs/promises');
const path = require('node:path');
const JavaScriptObfuscator = require('javascript-obfuscator');

const root = path.resolve(__dirname, '..');
const platforms = [
  { directory: 'node', entry: 'index.cjs', runtime: 'runtime.cjs', target: 'node', exports: ['init', 'captureException', 'withSpan', 'log', 'configuration'] },
  { directory: 'browser', entry: 'index.js', runtime: 'runtime.js', target: 'browser-no-eval', exports: ['init', 'log', 'captureException', 'withSpan'] },
];

async function main() {
  const [sourceDirectory, ...flags] = process.argv.slice(2);
  if (!sourceDirectory || flags.some(flag => flag !== '--check')) {
    throw new Error('Usage: npm run build -- /path/to/readable-sdk [--check]');
  }
  const sourceRoot = await fs.realpath(sourceDirectory);
  const relativeSource = path.relative(await fs.realpath(root), sourceRoot);
  if (!relativeSource || (!relativeSource.startsWith(`..${path.sep}`) && relativeSource !== '..' && !path.isAbsolute(relativeSource))) {
    throw new Error('Readable SDK sources must be outside this distribution repository.');
  }

  const outputs = [];
  for (const platform of platforms) {
    const code = await fs.readFile(path.join(sourceRoot, platform.directory, platform.entry), 'utf8');
    const result = JavaScriptObfuscator.obfuscate(code, {
      target: platform.target,
      seed: 0x5052494c,
      compact: true,
      identifierNamesGenerator: 'hexadecimal',
      renameGlobals: true,
      renameProperties: false,
      reservedNames: platform.exports.map(name => `^${name}$`),
      ignoreImports: true,
      numbersToExpressions: true,
      stringArray: true,
      stringArrayEncoding: ['base64'],
      stringArrayThreshold: 1,
      stringArrayIndexShift: true,
      stringArrayRotate: true,
      stringArrayShuffle: true,
      controlFlowFlattening: false,
      deadCodeInjection: false,
      debugProtection: false,
      disableConsoleOutput: false,
      selfDefending: false,
      sourceMap: false,
    });
    if (result.getSourceMap()) throw new Error('Obfuscated SDK builds must not contain source maps.');

    const banner = '/*! Copyright (c) 2026 Prilog. MIT. Generated runtime; see LICENSE. */\n';
    outputs.push({ file: path.join(platform.directory, platform.runtime), code: banner + result.getObfuscatedCode() + '\n' });

    // Static public exports preserve CommonJS/ESM interop and bundler discovery.
    const entry = platform.directory === 'node'
      ? "'use strict';\n\nconst runtime = require('./runtime.cjs');\n\n" + platform.exports.map(name => `exports.${name} = runtime.${name};`).join('\n') + '\n'
      : `export { ${platform.exports.join(', ')} } from './runtime.js';\n`;
    outputs.push({ file: path.join(platform.directory, platform.entry), code: entry });
  }

  for (const output of outputs) {
    const destination = path.join(root, output.file);
    if (flags.includes('--check')) {
      if (await fs.readFile(destination, 'utf8') !== output.code) {
        throw new Error(`${output.file} does not match the reproducible obfuscation build.`);
      }
      console.log(`Verified ${output.file}`);
    } else {
      await fs.writeFile(destination, output.code);
      console.log(`Generated ${output.file}`);
    }
  }
}

main().catch(error => {
  console.error(error.message);
  process.exitCode = 1;
});
