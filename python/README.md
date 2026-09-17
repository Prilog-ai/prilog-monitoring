# prilog-monitoring

Prilog monitoring for Python, built on OpenTelemetry. Collect application logs, traces, and exceptions and connect them to your Prilog System Map.

## Install

```bash
python -m pip install prilog-monitoring
```

Python 3.9 or later is required.

## Initialize

Select **Add free Prilog monitoring** for your service in Prilog and set the provided DSN as `PRILOG_DSN` in your application environment. Initialize before importing or starting your application framework:

```python
import os
import prilog_monitoring

monitoring = prilog_monitoring.init(
    dsn=os.environ.get("PRILOG_DSN"),
    service_name="checkout-api",
)
```

Initialization sends a startup log and span; Prilog verifies the connection when it receives them. Without a DSN, `init()` returns `None`.

The SDK attaches a handler to Python logging and captures unhandled main-thread and thread exceptions. Your application's configured logging levels govern which messages are emitted. Installed OpenTelemetry instrumentor entry points are loaded automatically; install the instrumentor packages for frameworks and clients you use.

## Logs, spans, and handled errors

```python
import logging
from prilog_monitoring import capture_exception, span

with span("checkout.validate"):
    logging.getLogger("prilog.monitoring").info("Order validated")

try:
    raise ValueError("Payment declined")
except ValueError as error:
    capture_exception(error)
```

`span(name, attributes=None)` records and rethrows errors while preserving trace/log correlation. `capture_exception(error, attributes=None)` records handled exceptions and their stack traces.

For unhandled asyncio errors, call `prilog_monitoring.instrument_asyncio(loop)` with your application's event loop.

## Configuration and shutdown

`init` accepts `dsn`, `service_name`, `environment`, `release`, `sample_rate` (0–1, default 1), and `auto_instrument` (default `True`). `PRILOG_DSN` and `OTEL_SERVICE_NAME` environment variables take precedence over their corresponding arguments.

Flush pending telemetry from your existing graceful-shutdown handler:

```python
if monitoring is not None:
    monitoring.shutdown()
```

An `atexit` hook is also registered. The package includes a generated, obfuscated pure-Python runtime; see the repository's `BUILDING.md` for the reproducible build process.

## License and source repository

MIT. See [LICENSE](LICENSE).

Repository and issues: [Prilog-ai/prilog-monitoring](https://github.com/Prilog-ai/prilog-monitoring).
