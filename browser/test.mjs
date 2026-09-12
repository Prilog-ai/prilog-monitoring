import test from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import { once } from 'node:events';
import { fileURLToPath } from 'node:url';
import { build } from 'vite';
import { chromium } from 'playwright';

test('browser SDK exports correlated OTLP over CORS without unsafe-eval', async () => {
  const bundle = await build({ configFile: false, logLevel: 'silent', build: { write: false, minify: false, lib: { entry: fileURLToPath(new URL('./index.js', import.meta.url)), name: 'PrilogMonitoring', formats: ['iife'] } } });
  const code = (Array.isArray(bundle) ? bundle[0] : bundle).output.find(output => output.type === 'chunk').code;
  const requests = [];
  const server = http.createServer(async (request, response) => {
    response.setHeader('Access-Control-Allow-Origin', '*');
    response.setHeader('Access-Control-Allow-Headers', 'Content-Type,X-Prilog-OTLP-Token,traceparent,tracestate,baggage');
    response.setHeader('Access-Control-Allow-Methods', 'POST,GET,OPTIONS');
    if (request.method === 'OPTIONS') { response.writeHead(204); response.end(); return; }
    if (request.method === 'POST') {
      const chunks = []; for await (const chunk of request) chunks.push(chunk);
      requests.push({ path: request.url, key: request.headers['x-prilog-otlp-token'], data: JSON.parse(Buffer.concat(chunks)) });
    }
    response.setHeader('Content-Type', 'application/json'); response.end('{}');
  });
  server.listen(0, '127.0.0.1'); await once(server, 'listening');
  let browser;
  try {
    browser = await chromium.launch({ headless: true });
    const page = await browser.newPage();
    await page.setContent(`<!doctype html><html><head><meta http-equiv="Content-Security-Policy" content="script-src 'unsafe-inline'; connect-src http://127.0.0.1:*"></head><body>Checkout</body></html>`);
    await page.addScriptTag({ content: code });
    await page.evaluate(async dsn => {
      const sdk = window.PrilogMonitoring;
      const monitor = sdk.init({ dsn, serviceName: 'checkout-web' });
      try { sdk.withSpan('checkout.submit', () => { sdk.log('info', 'order validated'); throw new Error('payment failed'); }); } catch { /* Application retains its error handling. */ }
      window.dispatchEvent(new ErrorEvent('error', { error: new Error('global UI error'), message: 'global UI error' }));
      await monitor.shutdown();
    }, `http://pk_prilog_test@127.0.0.1:${server.address().port}/workspace/connection`);
    const logs = requests.filter(request => request.path.endsWith('/v1/logs')).flatMap(request => request.data.resourceLogs.flatMap(resource => resource.scopeLogs.flatMap(scope => scope.logRecords)));
    const spans = requests.filter(request => request.path.endsWith('/v1/traces')).flatMap(request => request.data.resourceSpans.flatMap(resource => resource.scopeSpans.flatMap(scope => scope.spans)));
    assert.ok(requests.every(request => request.key === 'pk_prilog_test'));
    assert.ok(logs.some(record => record.body.stringValue === 'global UI error'));
    const failed = spans.find(span => span.name === 'checkout.submit');
    const error = logs.find(record => record.body.stringValue === 'payment failed');
    assert.equal(failed.status.code, 2);
    assert.equal(error.traceId, failed.traceId);
    assert.equal(error.spanId, failed.spanId);
  } finally { if (browser) await browser.close(); server.close(); server.closeAllConnections(); }
});
