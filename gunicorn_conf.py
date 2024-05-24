import multiprocessing
import os

from gunicorn.config import (
    ChildExit,
    NumWorkersChanged,
    OnExit,
    OnReload,
    OnStarting,
    PostRequest,
    PostWorkerInit,
    Postfork,
    PreExec,
    Prefork,
    WhenReady,
    WorkerAbort,
    WorkerExit,
    WorkerInt,
)

from wg_backend.core.settings import get_settings

config = get_settings()

""" Debugging """
check_config = False
print_config = True
spew = False

""" Logging """
loglevel = config.LOG_LEVEL
logger_class = "gunicorn.glogging.Logger"
accesslog = config.gunicorn_access_log_path
disable_redirect_access_to_syslog = False
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
errorlog = config.gunicorn_error_log_path
capture_output = True
logconfig = None
logconfig_dict = {}
# logconfig_json = None
# syslog_addr= unix://localhost:514
syslog_prefix = "Backend==>"
# syslog_facility = 'user
# syslog = False
# enable_stdio_inheritance = False
# statsd_host = "host:port"
# dogstatsd_tags = ""
# statsd_prefix = ""

""" Process Naming """
proc_name = config.GUNICORN_PROC_NAME

wsgi_app = "wg_backend.main:wg_backend"

""" SSL """
# keyfile="/wg_backend/gunicorn/cert/localhost.decrypted.key"
# certfile="/wg_backend/gunicorn/cert/localhost.crt"
# ssl_version = 2
# cert_reqs = 0
# ca_certs = None
# suppress_ragged_eofs = True
# do_handshake_on_connect = True
# ciphers = None

""" Security """
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

""" Server Mechanics """
pidfile = config.gunicorn_pid_file
worker_tmp_dir = str(config.TMP_DIR / "gunicorn")
tmp_upload_dir = str(config.TMP_DIR / "gunicorn")
user = config.APP_USER
group = config.APP_GROUP
umask = config.APP_UMASK
preload_app = not config.DEBUG
reuse_port = False
# sendfile= None
# chdir = str(BASE_DIR)
# daemon = True
# raw_env = [
#     # 'SPAM=eggs',
# ]
# initgroups = False
secure_scheme_headers = {
    'X-FORWARDED-PROTOCOL': 'ssl',
    'X-FORWARDED-PROTO': 'https',
    'X-FORWARDED-SSL': 'on',
}
forwarded_allow_ips = '127.0.0.1'
# pythonpath = None
# paste = None
proxy_protocol = False
proxy_allow_ips = '127.0.0.1'
# raw_paste_global_conf=[]
# strip_header_spaces = False
# permit_unconventional_http_method = False
# permit_unconventional_http_version = False
# casefold_http_method = False
# header_map = 'drop'
# tolerate_dangerous_framing
reload = config.DEBUG or config.STAGE
reload_engine = 'auto'
reload_extra_files = []

""" Server Socket """
bind = config.GUNICORN_BIND
backlog = 2048

#   backlog - The number of pending connections. This refers
#       to the number of clients that can be waiting to be
#       served. Exceeding this number results in the client
#       getting an error when attempting to connect. It should
#       only affect servers under significant load.
#
#       Must be a positive integer. Generally set in the 64-2048
#       range.
#

""" Worker processes """
cores = multiprocessing.cpu_count()
workers_per_core = float(config.WORKERS_PER_CORE)
default_web_concurrency = workers_per_core * cores + 1

use_max_workers = config.MAX_WORKERS if config.MAX_WORKERS else None
if config.WEB_CONCURRENCY:
    web_concurrency = config.WEB_CONCURRENCY
    assert web_concurrency > 0
else:
    web_concurrency = max(int(default_web_concurrency), 2)
    if use_max_workers:
        web_concurrency = min(web_concurrency, use_max_workers)
if config.DEBUG:
    web_concurrency = 1

worker_class = 'uvicorn.workers.UvicornH11Worker'
worker_connections = 1000  # The maximum number of simultaneous clients.
threads = 2  # Run each worker with the specified number of threads.
max_requests = (
    0  # The maximum number of requests a worker will process before restarting
)
# max_requests_jitter = 1
# Workers silent for more than this many seconds are killed and restarted.
timeout = config.TIMEOUT
graceful_timeout = config.GRACEFUL_TIMEOUT
keepalive = config.KEEP_ALIVE

"""  server hooks  """


def on_starting(server):
    OnStarting.on_starting(server)
    server.log.info("Worker starting (pid: %s)")
    server.log.info(f"===> current user is  {os.system('echo whoami')}")


def on_reload(server):
    OnReload.on_reload(server)
    # server.log.info("Worker reloading ...")


def when_ready(server):
    WhenReady.when_ready(server)
    # server.log.info("Server is ready. Spawning workers")


def pre_fork(server, worker):
    Prefork.pre_fork(server = server, worker = worker)


#     server.log.info("Worker removed (pid: %s)", worker.pid)

def post_fork(server, worker):
    Postfork.post_fork(server, worker)
    # server.log.info("Worker spawned (pid: %s)", worker.pid)


def post_worker_init(worker):
    PostWorkerInit.post_worker_init(worker)


#     worker.log.info("post_worker_init ... ")

def worker_int(worker):
    #  for reload to work in development
    os.system(f"kill -HUP {worker.pid}")
    WorkerInt.worker_int(worker)
    worker.log.info("worker received INT or QUIT signal")

    ## get traceback info
    import threading, sys, traceback
    id2name = {th.ident: th.name for th in threading.enumerate()}
    code = []
    for threadId, stack in sys._current_frames().items():
        code.append("\n# Thread: %s(%d)" % (id2name.get(threadId, ""), threadId))
        for filename, lineno, name, line in traceback.extract_stack(stack):
            code.append('File: "%s", line %d, in %s' % (filename, lineno, name))
            if line:
                code.append("  %s" % (line.strip()))
    worker.log.debug("\n".join(code))


def worker_abort(worker):
    WorkerAbort.worker_abort(worker = worker)
    # worker.log.info("worker received SIGABRT signal")


def pre_exec(server):
    PreExec.pre_exec(server)


#     server.log.info("Forked child, re-executing.")

def pre_request(worker, req):
    worker.log.debug("%s %s" % (req.method, req.path))
    # worker.log.debug("%s %s", req.method, req.path)


def post_request(worker, req, environ, resp):
    PostRequest.post_request(worker, req, environ, resp)


def child_exit(server, worker):
    ChildExit.child_exit(server, worker)
    # worker.log.debug("%s %s", )


def worker_exit(server, worker):
    WorkerExit.worker_exit(server, worker)


#     worker.log.debug('worker exits')

def nworkers_changed(server, new_value, old_value):
    NumWorkersChanged.nworkers_changed(server, new_value, old_value)


def on_exit(server):
    OnExit.on_exit(server)
    # server.log.info('on_exit')


def ssl_context(conf, default_ssl_context_factory):
    import ssl
    context = default_ssl_context_factory()
    context.minimum_version = ssl.TLSVersion.TLSv1_3
    return context


# Worker processes
#
#   workers - The number of worker processes that this server
#       should keep alive for handling requests.
#
#       A positive integer generally in the 2-4 x $(NUM_CORES)
#       range. You'll want to vary this a bit to find the best
#       for your particular application's work load.
#
#   worker_class - The type of workers to use. The default
#       sync class should handle most 'normal' types of work
#       loads. You'll want to read
#       http://docs.gunicorn.org/en/latest/design.html#choosing-a-worker-type
#       for information on when you might want to choose one
#       of the other worker classes.
#
#       A string referring to a Python path to a subclass of
#       gunicorn.workers.base.Worker. The default provided values
#       can be seen at
#       http://docs.gunicorn.org/en/latest/config.html#worker-class
#
#   worker_connections - For the eventlet and gevent worker classes
#       this limits the maximum number of simultaneous clients that
#       a single process can handle.
#
#       A positive integer generally set to around 1000.
#
#   timeout - If a worker does not notify the master process in this
#       number of seconds it is killed and a new worker is spawned
#       to replace it.
#
#       Generally set to thirty seconds. Only set this noticeably
#       higher if you're sure of the repercussions for sync workers.
#       For the non sync workers it just means that the worker
#       process is still communicating and is not tied to the length
#       of time required to handle a single request.
#
#   keepalive - The number of seconds to wait for the next request
#       on a Keep-Alive HTTP connection.
#
#       A positive integer. Generally set in the 1-5 seconds range.
#   spew - Install a trace function that spews every line of Python
#       that is executed when running the server. This is the
#       nuclear option.
#
#       True or False
#

# Server mechanics
#
#   daemon - Detach the main Gunicorn process from the controlling
#       terminal with a standard fork/fork sequence.
#
#       True or False
#
#   raw_env - Pass environment variables to the execution environment.
#
#   pidfile - The path to a pid file to write
#
#       A path string or None to not write a pid file.
#
#   user - Switch worker processes to run as this user.
#
#       A valid user id (as an integer) or the name of a user that
#       can be retrieved with a call to pwd.getpwnam(value) or None
#       to not change the worker process user.
#
#   group - Switch worker process to run as this group.
#
#       A valid group id (as an integer) or the name of a user that
#       can be retrieved with a call to pwd.getgrnam(value) or None
#       to change the worker processes group.
#
#   umask - A mask for file permissions written by Gunicorn. Note that
#       this affects unix socket permissions.
#
#       A valid value for the os.umask(mode) call or a string
#       compatible with int(value, 0) (0 means Python guesses
#       the base, so values like "0", "0xFF", "0022" are valid
#       for decimal, hex, and octal representations)
#
#   tmp_upload_dir - A directory to store temporary request data when
#       requests are read. This will most likely be disappearing soon.
#
#       A path to a directory where the process owner can write. Or
#       None to signal that Python should choose one on its own.
#

# Server hooks
#
#   post_fork - Called just after a worker has been forked.
#
#       A callable that takes a server and worker instance
#       as arguments.
#
#   pre_fork - Called just prior to forking the worker subprocess.
#
#       A callable that accepts the same arguments as after_fork
#
#   pre_exec - Called just prior to forking off a secondary
#       master process during things like config reloading.
#
#       A callable that takes a server instance as the sole argument.
#
