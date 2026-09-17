# Copyright (c) 2026 Prilog. MIT. Generated runtime; see LICENSE.
O=Exception
N=ValueError
G=False
J=True
C=None
import atexit as T,logging as D,os as E,sys as H,threading as F
from contextlib import contextmanager as K
from importlib.metadata import entry_points as U
from urllib.parse import unquote as P,urlsplit as Q,urlunsplit as R
from opentelemetry import trace as I
from opentelemetry._logs import set_logger_provider as V
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter as W
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter as X
from opentelemetry.sdk._logs import LoggerProvider as Y,LoggingHandler as Z
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor as a
from opentelemetry.sdk.resources import Resource as b
from opentelemetry.sdk.trace import TracerProvider as c
from opentelemetry.sdk.trace.export import BatchSpanProcessor as d
from opentelemetry.sdk.trace.sampling import ParentBased as e,TraceIdRatioBased as f
from opentelemetry.trace import Status as S,StatusCode as g
A=tuple(bytes.fromhex(A).decode('utf-8')for A in('68747470','6874747073','496e76616c6964205072696c6f67206d6f6e69746f72696e672044534e','40','2f','582d5072696c6f672d4f544c502d546f6b656e','6170706c69636174696f6e','5052494c4f475f44534e','4f54454c5f4558504f525445525f4f544c505f454e44504f494e54','73616d706c655f72617465206d757374206265206265747765656e207a65726f20616e64206f6e65','736572766963652e6e616d65','6465706c6f796d656e742e656e7669726f6e6d656e742e6e616d65','736572766963652e76657273696f6e','7072696c6f672e73646b2e76657273696f6e','4f54454c5f534552564943455f4e414d45','5052494c4f475f454e5649524f4e4d454e54','70726f64756374696f6e','5052494c4f475f52454c45415345','4749544855425f534841','756e6b6e6f776e','302e312e30','2f76312f747261636573','2f76312f6c6f6773','6f70656e74656c656d65747279','73656c656374','6f70656e74656c656d657472795f696e737472756d656e746f72','7072696c6f672e6d6f6e69746f72696e67','496e737472756d656e746174696f6e20756e617661696c61626c653a202573','7072696c6f672e73746172747570','5072696c6f67206d6f6e69746f72696e6720696e697469616c697a6564','657863657074696f6e','2573'))
B=C
h=F.Lock()
def configuration(dsn):
	B=Q(dsn)
	if B.scheme not in(A[0],A[1])or not B.hostname or not B.username or B.password or B.query or B.fragment:raise N(A[2])
	C=R((B.scheme,B.netloc.rsplit(A[3],1)[1],B.path.rstrip(A[4]),'',''));return C,{A[5]:P(B.username)}
class Monitoring:
	def __init__(self,traces,logs,handler,previous_hook,previous_thread_hook):self.enabled=J;self.traces,self.logs,self.handler=traces,logs,handler;self.previous_hook,self.previous_thread_hook=previous_hook,previous_thread_hook;self.closed=G
	def shutdown(self):
		if self.closed:return
		self.closed=J;D.getLogger().removeHandler(self.handler)
		if H.excepthook is L:H.excepthook=self.previous_hook
		if F.excepthook is M:F.excepthook=self.previous_thread_hook
		self.logs.shutdown();self.traces.shutdown()
def init(dsn=C,service_name=A[6],environment=C,release=C,sample_rate=1.,auto_instrument=J):
	global B
	with h:
		if B is not C:return B
		dsn=E.environ.get(A[7])or dsn
		if not dsn:return
		K,P=configuration(dsn);K=E.environ.get(A[8],K).rstrip(A[4])
		if not 0<=sample_rate<=1:raise N(A[9])
		Q=b.create({A[10]:E.environ.get(A[14])or service_name,A[11]:environment or E.environ.get(A[15],A[16]),A[12]:release or E.environ.get(A[17])or E.environ.get(A[18],A[19]),A[13]:A[20]});traces=c(resource=Q,sampler=e(f(sample_rate)));traces.add_span_processor(d(X(endpoint=K+A[21],headers=P,timeout=5)));I.set_tracer_provider(traces);logs=Y(resource=Q);logs.add_log_record_processor(a(W(endpoint=K+A[22],headers=P,timeout=5)));V(logs);handler=Z(level=D.NOTSET,logger_provider=logs);handler.addFilter(lambda record:not record.name.startswith(A[23]));D.getLogger().addHandler(handler);B=Monitoring(traces,logs,handler,H.excepthook,F.excepthook);H.excepthook,F.excepthook=L,M
		if auto_instrument:
			G=U();G=G.select(group=A[25])if hasattr(G,A[24])else G.get(A[25],[])
			for R in G:
				try:R.load()().instrument()
				except O:D.getLogger(A[26]).warning(A[27],R.name)
		T.register(B.shutdown);S=D.getLogger(A[26]);S.setLevel(D.INFO)
		with span(A[28]):S.info(A[29],extra={A[28]:J})
		return B
def L(kind,error,tb):
	capture_exception(error)
	if B:B.logs.force_flush(timeout_millis=3000);B.traces.force_flush(timeout_millis=3000);B.previous_hook(kind,error,tb)
def M(args):
	capture_exception(args.exc_value)
	if B:B.previous_thread_hook(args)
def instrument_asyncio(loop):
	B=loop.get_exception_handler()
	def handler(current_loop,context):
		error=context.get(A[30])
		if error:capture_exception(error)
		if B:B(current_loop,context)
		else:current_loop.default_exception_handler(context)
	loop.set_exception_handler(handler)
def capture_exception(error,attributes=C):
	if B is C:return
	E=I.get_current_span()
	if not E.get_span_context().is_valid:
		with I.get_tracer(A[26]).start_as_current_span(A[30]):return capture_exception(error,attributes)
	E.record_exception(error);E.set_status(S(g.ERROR,str(error)));D.getLogger(A[26]).error(A[31],error,exc_info=(type(error),error,error.__traceback__),extra=attributes or{})
@K
def span(name,attributes=C):
	with I.get_tracer(A[26]).start_as_current_span(name,attributes=attributes,record_exception=G,set_status_on_exception=G)as B:
		try:yield B
		except O as error:capture_exception(error);raise
