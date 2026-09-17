package prilog

import (
	"context"
	"errors"
	"io"
	"log/slog"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync"
	"testing"

	collectorlogspb "go.opentelemetry.io/proto/otlp/collector/logs/v1"
	collectortracepb "go.opentelemetry.io/proto/otlp/collector/trace/v1"
	logspb "go.opentelemetry.io/proto/otlp/logs/v1"
	tracepb "go.opentelemetry.io/proto/otlp/trace/v1"
	"google.golang.org/protobuf/proto"
)

func TestSDKExportsCorrelatedLogsAndTraces(t *testing.T) {
	t.Setenv("PRILOG_DSN", "")
	t.Setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")
	var mu sync.Mutex
	var logs []*logspb.LogRecord
	var spans []*tracepb.Span
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Header.Get("X-Prilog-OTLP-Token") != "pk_prilog_test" {
			t.Errorf("missing ingest key")
		}
		body, _ := io.ReadAll(r.Body)
		mu.Lock()
		defer mu.Unlock()
		switch r.URL.Path {
		case "/workspace/connection/v1/logs":
			var request collectorlogspb.ExportLogsServiceRequest
			if err := proto.Unmarshal(body, &request); err != nil {
				t.Error(err)
			}
			for _, resource := range request.ResourceLogs {
				for _, scope := range resource.ScopeLogs {
					logs = append(logs, scope.LogRecords...)
				}
			}
		case "/workspace/connection/v1/traces":
			var request collectortracepb.ExportTraceServiceRequest
			if err := proto.Unmarshal(body, &request); err != nil {
				t.Error(err)
			}
			for _, resource := range request.ResourceSpans {
				for _, scope := range resource.ScopeSpans {
					spans = append(spans, scope.Spans...)
				}
			}
		default:
			t.Errorf("unexpected export endpoint: %s", r.URL.Path)
		}
		w.Header().Set("Content-Type", "application/x-protobuf")
		w.WriteHeader(200)
	}))
	defer server.Close()
	monitor, err := Init(context.Background(), Config{DSN: strings.Replace(server.URL, "http://", "http://pk_prilog_test@", 1) + "/workspace/connection", ServiceName: "checkout"})
	if err != nil {
		t.Fatal(err)
	}
	err = monitor.Run(context.Background(), "checkout.submit", func(ctx context.Context) error {
		slog.InfoContext(ctx, "order validated")
		return errors.New("payment failed")
	})
	if err == nil {
		t.Fatal("application error swallowed")
	}
	if err := monitor.Shutdown(context.Background()); err != nil {
		t.Fatal(err)
	}
	mu.Lock()
	defer mu.Unlock()
	var failed *tracepb.Span
	var errorLog *logspb.LogRecord
	startup := false
	for _, span := range spans {
		if span.Name == "prilog.startup" {
			startup = true
		}
		if span.Name == "checkout.submit" {
			failed = span
		}
	}
	for _, record := range logs {
		if record.Body.GetStringValue() == "payment failed" {
			errorLog = record
		}
	}
	if !startup || failed == nil || errorLog == nil {
		t.Fatalf("missing startup or error telemetry: spans=%v logs=%v", spans, logs)
	}
	if failed.Status.Code != tracepb.Status_STATUS_CODE_ERROR || string(errorLog.TraceId) != string(failed.TraceId) || string(errorLog.SpanId) != string(failed.SpanId) {
		t.Fatal("exception was not correlated with its trace")
	}
}
