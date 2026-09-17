# Prilog Monitoring for Go

OpenTelemetry logs, HTTP traces, and exception capture for Prilog. Requires Go 1.25 or later.

## Install

```bash
go get github.com/Prilog-ai/prilog-monitoring/golang@v0.1.0
```

## Initialize

Select **Add free Prilog monitoring** for your service in Prilog and set its DSN in `PRILOG_DSN`. Add initialization to your existing application's startup:

```go
package main

import (
    "context"
    "log"
    "log/slog"
    "os"

    prilog "github.com/Prilog-ai/prilog-monitoring/golang"
)

func main() {
    ctx := context.Background()
    monitoring, err := prilog.Init(ctx, prilog.Config{
        DSN: os.Getenv("PRILOG_DSN"),
        ServiceName: "checkout-api",
        Environment: "production",
    })
    if err != nil {
        log.Fatal(err)
    }
    defer monitoring.Shutdown(context.Background())

    slog.InfoContext(ctx, "Prilog SDK connected")
    // Start your existing server or worker here.
}
```

Initialization emits a startup log and span. Prilog verifies the connection once they arrive. Without a DSN, `Init` returns a disabled monitor.

## Instrumentation

- `Run(ctx, name, func(context.Context) error)` creates a span, captures returned errors, and returns them to the caller.
- `HTTPHandler(name, handler)` wraps an existing HTTP handler with tracing and panic capture.
- `CaptureError(ctx, err)` captures a handled error with trace correlation and a stack trace.
- Defer `Recover(ctx)` at goroutine entry points to capture and re-panic unexpected failures.
- `Shutdown(ctx)` flushes telemetry and restores the previous default logging configuration when still owned by the SDK.

`slog` and standard-library logging are connected to Prilog. Set `Config.LogHandler` to preserve a custom `slog.Handler`. `PRILOG_DSN`, `OTEL_SERVICE_NAME`, and `OTEL_EXPORTER_OTLP_ENDPOINT` can override the corresponding configuration.

## Distribution and development

The module contains generated, obfuscated but buildable Go source. Exported types, configuration fields, and methods retain their public API. See the repository's `BUILDING.md` for generation from separately maintained readable sources.

Run `go test -race ./...` in this directory. The integration test exports real OTLP logs and spans to a local mock collector.

Releases use `golang/vX.Y.Z` Git tags because this is a subdirectory Go module.

## License

MIT. See [LICENSE](LICENSE).
