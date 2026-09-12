const test = require('node:test');
const assert = require('node:assert/strict');
const http = require('node:http');
const { once } = require('node:events');
const { spawn } = require('node:child_process');
const { init, withSpan, captureException, log, configuration } = require('./index.cjs');

test('exports real correlated OTLP logs, traces, startup and exceptions to the DSN', async () => {
  for (const name of ['PRILOG_DSN', 'OTEL_EXPORTER_OTLP_ENDPOINT']) delete process.env[name];
  const requests = [];
  const server = http.createServer(async (request, response) => {
    const chunks = [];
    for await (const chunk of request) chunks.push(chunk);
    requests.push({ path: request.url, key: request.headers['x-prilog-otlp-token'], data: JSON.parse(Buffer.concat(chunks)) });
    response.setHeader('Content-Type', 'application/json');
    response.end('{}');
  });
  server.listen(0, '127.0.0.1');
  await once(server, 'listening');
  const dsn = `http://pk_prilog_test@127.0.0.1:${server.address().port}/workspace/connection`;
  try {
    assert.equal(configuration(dsn).endpoint.includes('@'), false);
    const monitoring = init({ dsn, serviceName: 'checkout', autoInstrument: false, captureConsole: false, captureUncaught: false });
    assert.equal(init({ dsn }), monitoring);
    assert.equal(withSpan('checkout.sync', () => 42), 42);
    await assert.rejects(withSpan('checkout.submit', async () => {
      log('info', 'order validated');
      throw new Error('payment failed');
    }), /payment failed/);
    captureException(new Error('detached error'));
    await monitoring.shutdown();
    const logs = requests.filter(request => request.path.endsWith('/v1/logs')).flatMap(request => request.data.resourceLogs.flatMap(resource => resource.scopeLogs.flatMap(scope => scope.logRecords)));
    const spans = requests.filter(request => request.path.endsWith('/v1/traces')).flatMap(request => request.data.resourceSpans.flatMap(resource => resource.scopeSpans.flatMap(scope => scope.spans)));
    assert.ok(requests.every(request => request.key === 'pk_prilog_test'));
    assert.ok(requests.every(request => request.path.startsWith('/workspace/connection/v1/')));
    assert.ok(spans.some(span => span.name === 'prilog.startup'));
    assert.ok(logs.some(record => record.body.stringValue === 'Prilog monitoring initialized'));
    const failed = spans.find(span => span.name === 'checkout.submit');
    assert.equal(failed.status.code, 2);
    const error = logs.find(record => record.body.stringValue === 'payment failed');
    assert.equal(error.traceId, failed.traceId);
    assert.equal(error.spanId, failed.spanId);
    assert.ok(error.attributes.some(attribute => attribute.key === 'exception.stacktrace'));
    assert.ok(logs.some(record => record.body.stringValue === 'order validated'));
  } finally {
    server.close();
    server.closeAllConnections();
  }
});

test('flushes uncaught exceptions before preserving the fatal exit status', async () => {
  const bodies = [];
  const server = http.createServer(async (request, response) => {
    const chunks = []; for await (const chunk of request) chunks.push(chunk);
    bodies.push(Buffer.concat(chunks).toString()); response.setHeader('Content-Type', 'application/json'); response.end('{}');
  });
  server.listen(0, '127.0.0.1'); await once(server, 'listening');
  try {
    const script = `require('./index.cjs').init({dsn:'http://pk_prilog_test@127.0.0.1:${server.address().port}/connection',autoInstrument:false,captureConsole:false});setImmediate(()=>{throw new Error('fatal captured');});`;
    const child = spawn(process.execPath, ['-e', script], { cwd: __dirname, stdio: 'ignore' });
    const [code] = await once(child, 'exit');
    assert.equal(code, 1);
    assert.ok(bodies.some(body => body.includes('fatal captured') && body.includes('resourceLogs')));
    assert.ok(bodies.some(body => body.includes('fatal captured') && body.includes('resourceSpans')));
  } finally { server.close(); server.closeAllConnections(); }
});
