# @prilog/monitoring-browser

Prilog monitoring for browser and React applications, built on OpenTelemetry. Capture application logs, page and network traces, and exceptions in your Prilog workspace.

## Install

```bash
npm install @prilog/monitoring-browser
```

## Initialize

Select **Add free Prilog monitoring** for your service in Prilog and copy its publishable ingest DSN. Initialize the SDK once in your browser entry point, before rendering your application:

```javascript
import { init } from '@prilog/monitoring-browser';

const monitoring = init({
  dsn: 'YOUR_PRILOG_DSN',
  serviceName: 'checkout-web',
  environment: 'production',
});

// Render your existing React application or start your browser application here.
```

Replace `YOUR_PRILOG_DSN` with the DSN shown in Prilog. It grants telemetry ingestion for that service. Initialization sends a startup log and span; Prilog verifies the connection when it receives them.

The package is an ES module for browser bundlers. `init` returns a disabled monitor when called without a DSN or outside a browser.

## Logs, traces, and exceptions

The SDK instruments fetch, XMLHttpRequest, and document loading, and captures global errors and unhandled promise rejections.

```javascript
import { withSpan, log, captureException } from '@prilog/monitoring-browser';

withSpan('checkout.validate', () => {
  log('info', 'Order validated', { 'order.id': 'example-order' });
});

// In an existing error boundary or handled-error path:
captureException(new Error('Checkout failed'));
```

`withSpan(name, callback, attributes?)` returns the callback's result and records and rethrows errors. `log(level, message, attributes?)` supports `debug`, `info`, `warn`, and `error`. `captureException(error)` records the exception and its stack trace.

## Configuration

| Option | Description | Default |
| --- | --- | --- |
| `dsn` | Your service's publishable ingest DSN | Required to enable monitoring |
| `serviceName` | Frontend service identity | `frontend` |
| `environment` | Deployment environment | `production` |
| `release` | Application release/version | `unknown` |
| `tracePropagationTargets` | URLs or regular expressions for API requests that receive trace headers | Current origin |

For distributed tracing across your frontend and backend, set `tracePropagationTargets` to your API origins and configure the API's CORS policy to accept `traceparent`, `tracestate`, and `baggage` headers. If your application uses Content Security Policy, include the Prilog ingest origin in `connect-src`.

The SDK attempts to flush pending telemetry on `pagehide`. Await `monitoring.shutdown()` when explicitly tearing down the monitored application.

## License

MIT. See [LICENSE](./LICENSE).

Source and issue tracker: [Prilog-ai/prilog-monitoring](https://github.com/Prilog-ai/prilog-monitoring).
