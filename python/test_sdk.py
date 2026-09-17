import logging
import os
import threading
import unittest
from unittest.mock import patch
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from opentelemetry.proto.collector.logs.v1.logs_service_pb2 import ExportLogsServiceRequest
from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import ExportTraceServiceRequest
import prilog_monitoring as monitoring


class SDKTest(unittest.TestCase):
    @patch.dict(os.environ, {}, clear=True)
    def test_real_otlp_export_and_exception_context(self):
        requests = []

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                body = self.rfile.read(int(self.headers["Content-Length"]))
                requests.append((self.path, self.headers.get("X-Prilog-OTLP-Token"), body))
                self.send_response(200)
                self.send_header("Content-Type", "application/x-protobuf")
                self.end_headers()

            def log_message(self, *_):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            sdk = monitoring.init(dsn=f"http://pk_prilog_test@127.0.0.1:{server.server_port}/workspace/connection", service_name="checkout", auto_instrument=False)
            self.assertIs(sdk, monitoring.init())
            with self.assertRaisesRegex(ValueError, "payment failed"):
                with monitoring.span("checkout.submit"):
                    logging.getLogger("prilog.monitoring").info("order validated")
                    raise ValueError("payment failed")
            monitoring.capture_exception(RuntimeError("detached error"))
            sdk.shutdown()
            logs, spans = [], []
            for path, key, body in requests:
                self.assertEqual(key, "pk_prilog_test")
                self.assertTrue(path.startswith("/workspace/connection/v1/"))
                if path.endswith("/logs"):
                    message = ExportLogsServiceRequest.FromString(body)
                    logs.extend(record for resource in message.resource_logs for scope in resource.scope_logs for record in scope.log_records)
                else:
                    message = ExportTraceServiceRequest.FromString(body)
                    spans.extend(span for resource in message.resource_spans for scope in resource.scope_spans for span in scope.spans)
            self.assertTrue(any(span.name == "prilog.startup" for span in spans))
            failed = next(span for span in spans if span.name == "checkout.submit")
            self.assertEqual(failed.status.code, 2)
            error = next(record for record in logs if record.body.string_value == "payment failed")
            self.assertEqual(error.trace_id, failed.trace_id)
            self.assertEqual(error.span_id, failed.span_id)
            self.assertTrue(any(attribute.key == "exception.stacktrace" for attribute in error.attributes))
            self.assertTrue(any(record.body.string_value == "order validated" for record in logs))
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == "__main__":
    unittest.main()
