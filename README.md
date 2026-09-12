# Prilog Monitoring

OpenTelemetry-based JavaScript SDKs for collecting logs, distributed traces, and exceptions in Prilog.

The runtime implementation in this repository is distributed as an obfuscated build. Public entry points expose the documented API. See [BUILDING.md](BUILDING.md) for reproducible generation from separately maintained readable sources.

## Packages

| Runtime | npm package | Latest published version | Documentation |
| --- | --- | --- | --- |
| Node.js | [@prilog/monitoring](https://www.npmjs.com/package/@prilog/monitoring) | 0.1.0 | [Node SDK](node/README.md) |
| Browser / React | [@prilog/monitoring-browser](https://www.npmjs.com/package/@prilog/monitoring-browser) | 0.1.0 | [Browser SDK](browser/README.md) |

### Node.js

```bash
npm install @prilog/monitoring
```

Create `instrumentation.cjs`:

```javascript
const { init } = require('@prilog/monitoring');

module.exports = init({
  dsn: process.env.PRILOG_DSN,
  serviceName: 'checkout-api',
});
```

Set `PRILOG_DSN` to the DSN shown for your service in Prilog. Preload the instrumentation file before application imports:

```bash
NODE_OPTIONS="--require=./instrumentation.cjs" npm start
```

If your application already sets `NODE_OPTIONS`, add the `--require` option to its existing value. See the [Node SDK documentation](node/README.md) for configuration, custom spans, error capture, and graceful shutdown.

### Browser / React

```bash
npm install @prilog/monitoring-browser
```

Initialize in your browser entry point before rendering the application:

```javascript
import { init } from '@prilog/monitoring-browser';

const monitoring = init({
  dsn: 'YOUR_PRILOG_DSN',
  serviceName: 'checkout-web',
});
```

Replace `YOUR_PRILOG_DSN` with the service's publishable ingest DSN from Prilog. See the [browser SDK documentation](browser/README.md) for trace propagation, configuration, and error boundaries.

## Development

The committed runtimes are ready to test. To regenerate them, follow [BUILDING.md](BUILDING.md).

Run the Node SDK integration tests from `node/`:

```bash
npm ci
npm test
```

Run the browser SDK integration test from `browser/`:

```bash
npm ci
npx playwright install chromium --only-shell
npm test
```

The tests export real OTLP telemetry to local mock collectors and verify startup signals, exceptions, and log/trace correlation. Browser tests run in Chromium.

## Releases

See [PUBLISHING.md](PUBLISHING.md) for npm authentication, package inspection, publishing, and verification. Each package's `prepublishOnly` hook runs its tests before publication.

The npm `0.1.0` releases predate the obfuscated distribution. Publishing these updated artifacts requires a new package version.

## License

MIT. See [LICENSE](LICENSE).
