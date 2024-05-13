import multiprocessing
import os
from pathlib import Path

from gunicorn.config import (
	ChildExit, NumWorkersChanged,
	OnExit,
	OnReload,
	OnStarting,
	PostRequest,
	PostWorkerInit,
	Postfork,
	PreExec, Prefork, WhenReady, WorkerAbort, WorkerExit, WorkerInt,
)

from app.core.Settings import get_settings
settings = get_settings()
workers_per_core_str = settings.WORKERS_PER_CORE
max_workers_str = settings.MAX_WORKERS
use_max_workers = None
if max_workers_str:
	use_max_workers = int(max_workers_str)
web_concurrency_str = settings.WEB_CONCURRENCY

use_bind = f"{settings.BACKEND_SERVER_HOST}:{settings.BACKEND_SERVER_PORT}"

cores = multiprocessing.cpu_count()
workers_per_core = float(workers_per_core_str)
default_web_concurrency = workers_per_core * cores + 1

if web_concurrency_str:
	web_concurrency = int(web_concurrency_str)
	assert web_concurrency > 0
else:
	web_concurrency = max(int(default_web_concurrency), 2)
	if use_max_workers:
		web_concurrency = min(web_concurrency, use_max_workers)
if settings.DEBUG:
	web_concurrency = 1

graceful_timeout_str = settings.GRACEFUL_TIMEOUT
timeout_str = settings.TIMEOUT
keepalive_str = settings.KEEP_ALIVE

""" process naming """
proc_name = "gunicorn"
default_proc_name = "gunicorn"

""" security """
limit_request_line = 4094
limit_request_field_size = 8190
limit_request_fields = 100

""" ssl """
# keyfile = None
# certfile = None
# ssl_version = 2
# cert_reqs = 0
# ca_certs = None
# suppress_ragged_eofs = True
do_handshake_on_connect = True
ciphers = None

"""     Server Socket       """
bind = use_bind
# backlog = 2048
# backlog = 2048

"""     Worker Processes    """
workers = web_concurrency
worker_class = 'uvicorn.workers.UvicornWorker'
worker_connections = 1000  # The maximum number of simultaneous clients.
threads = 2  # Run each worker with the specified number of threads.
max_requests = 0  # The maximum number of requests a worker will process before restarting
max_requests_jitter = 0
timeout = int(timeout_str)  # Workers silent for more than this many seconds are killed and restarted.
graceful_timeout = int(graceful_timeout_str)
keepalive = int(keepalive_str)

"""     Server Mechanics    """
preload_app = True
sendfile = None
reuse_port = False
# chdir = '/app/'
daemon = False
# raw_env = ["FOO=1"]
# user = 1000
# group = 1000
initgroups = False
umask = 0
worker_tmp_dir = str(Path(__name__).resolve().parent / "logs/gunicorn/")

pidfile = str(Path(__name__).resolve().parent / "logs/gunicorn/pid")  # A filename to use for the PID file.
tmp_upload_dir = None
# secure_scheme_headers = {'X-FORWARDED-PROTOCOL': 'ssl', 'X-FORWARDED-PROTO': 'https', 'X-FORWARDED-SSL': 'on'}
secure_scheme_headers = {'X-FORWARDED-PROTOCOL': 'ssl', 'X-FORWARDED-PROTO': 'https', 'X-FORWARDED-SSL': 'on'}
# forwarded_allow_ips               = ['127.0.0.1']
# paste = None
# pythonpath = None
proxy_protocol = False
# proxy_allow_ips = "['127.0.0.1','*']"
# raw_paste_global_conf = []
strip_header_spaces = False

""" logging """
if settings.DEBUG:
	accesslog = '-' # Using '-' for FILE makes gunicorn log to stderr.
	errorlog = '-'
else:
	accesslog = settings.ACCESS_LOG
	errorlog = settings.ERROR_LOG
# access_log_format = "{'remote_ip':'%(h)s','request_id':'%({X-Request-Id}i)s','response_code':'%(s)s','request_method':'%(m)s','request_path':'%(U)s','request_querystring':'%(q)s','request_timetaken':'%(D)s','response_length':'%(B)s'}"
# access_log_format                 = %(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"

disable_redirect_access_to_syslog = False

capture_output = True
logger_class = 'gunicorn.glogging.Logger'
logconfig = None
logconfig_dict = {}
# syslog_addr                       = unix://localhost:514
# syslog_facility                   = "user"
# syslog_prefix = "Backend"
syslog = False
enable_stdio_inheritance = False
# statsd_host = "host:port"
dogstatsd_tags = ''
statsd_prefix = ''

""" Gunicorn config variables """
wsgi_app = "app.main:app"
if settings.DEBUG:
	reload = True
	reload_engine = "auto"
	reload_extra_files = []
# user = "gunicorn_user"  # must exist
check_config = False
print_config = False
spew = False

"""  server hooks  """


def on_starting(server):
	OnStarting.on_starting(server)
 
def on_reload(server):
	OnReload.on_reload(server)


def when_ready(server):
	WhenReady.when_ready(server)


def pre_fork(server, worker):
	Prefork.pre_fork(server=server, worker=worker)


def post_fork(server, worker):
	Postfork.post_fork(server, worker)


def post_worker_init(worker):
	PostWorkerInit.post_worker_init(worker)


def worker_int(worker):
	#  for reload to work in development
	os.system(f'kill -HUP {worker.pid}')
	print('reloadddddd')
	WorkerInt.worker_int(worker)


def worker_abort(worker):
	WorkerAbort.worker_abort(worker=worker)


def pre_exec(server):
	PreExec.pre_exec(server)


def pre_request(worker, req):
	worker.log.debug("%s %s" % (req.method, req.path))


def post_request(worker, req, environ, resp):
	PostRequest.post_request(worker, req, environ, resp)


def child_exit(server, worker):
	ChildExit.child_exit(server, worker)


def worker_exit(server, worker):
	WorkerExit.worker_exit(server, worker)


def nworkers_changed(server, new_value, old_value):
	NumWorkersChanged.nworkers_changed(server, new_value, old_value)


def on_exit(server):
	OnExit.on_exit(server)



# # For debugging and testing
# log_data = {
# 	"loglevel": settings.LOG_LEVEL,
# 	"workers": workers,
# 	"bind"            : use_bind,
# 	"graceful_timeout": graceful_timeout,
# 	"timeout": timeout,
# 	"keepalive": keepalive,
# 	"errorlog": errorlog,
# 	"accesslog": accesslog,
# 	# Additional, non-gunicorn variables
# 	"workers_per_core": workers_per_core,
# 	"use_max_workers": use_max_workers,
# 	"wsgi_app": wsgi_app
# }
# print(json.dumps(log_data))
