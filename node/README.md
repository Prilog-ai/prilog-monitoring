# @prilog/monitoring

Prilog monitoring for Node.js, built on OpenTelemetry. Collect application logs, distributed traces, and exceptions, and connect them to your Prilog System Map and issue analysis.

## Install

```bash
npm install @prilog/monitoring
```

## Initialize

Select **Add free Prilog monitoring** for your service in Prilog and copy its DSN into the `PRILOG_DSN` environment variable.

Create an `instrumentation.cjs` file:

```javascript
const { init } = require('@prilog/monitoring');

const monitoring = init({
  dsn: process.env.PRILOG_DSN,
  serviceName: 'checkout-api',
});

module.exports = monitoring;
```

Load this file before your application imports. For an application with an existing `npm start` script:

```bash
NODE_OPTIONS="--require=./instrumentation.cjs" npm start
```

If you already set `NODE_OPTIONS`, add the `--require=./instrumentation.cjs` option to it. The `.cjs` extension works in both CommonJS and ESM projects.

Initialization sends a startup log and span. Once Prilog receives them, it verifies your monitoring connection automatically. Without a DSN, initialization returns a disabled monitor.

## Logs, traces, and exceptions

Supported Node framework/client instrumentation, console capture, and uncaught-exception capture are enabled by default.

```javascript
const { withSpan, log, captureException } = require('@prilog/monitoring');

withSpan('checkout.validate', () => {
  log('info', 'Order validated', { 'order.id': 'example-order' });
});

// In an existing handled-error path:
captureException(new Error('Payment declined'));
```

`withSpan(name, callback, attributes?)` accepts synchronous or asynchronous callbacks, returns their result, and records and rethrows errors. `log(level, message, attributes?)` supports `trace`, `debug`, `info`, `warn`, `error`, and `fatal`. `captureException(error, attributes?)` records a handled exception and its stack trace.

## Configuration

Pass these options to `init`:

| Option | Description | Default |
| --- | --- | --- |
| `dsn` | Your service's ingest DSN; `PRILOG_DSN` takes precedence | `PRILOG_DSN` |
| `serviceName` | Service identity; `OTEL_SERVICE_NAME` takes precedence | `application` |
| `environment` | Deployment environment | `NODE_ENV` or `production` |
| `release` | Application release/version | `PRILOG_RELEASE`, `GITHUB_SHA`, or `unknown` |
| `sampleRate` | Root trace sampling ratio, between 0 and 1 | `1` |
| `captureConsole` | Capture console output as structured logs | `true` |
| `captureUncaught` | Capture uncaught exceptions | `true` |
| `autoInstrument` | Enable supported Node framework/client instrumentation | `true` |
| `instrumentations` | OpenTelemetry auto-instrumentation configuration overrides | `{}` |
| `resourceAttributes` | Additional OpenTelemetry resource attributes | `{}` |

## Shutdown

Await `monitoring.shutdown()` from your application's existing graceful-shutdown handler to flush pending telemetry. When the SDK owns the uncaught-exception handler, it flushes the captured error with a bounded timeout and exits with status 1.

## License

MIT. See [LICENSE](./LICENSE).

Source and issue tracker: [Prilog-ai/prilog-monitoring](https://github.com/Prilog-ai/prilog-monitoring).
