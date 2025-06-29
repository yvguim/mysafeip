import multiprocessing
import os


forwarded_allow_ips='*'
bind = os.getenv('WEB_BIND', '0.0.0.0:80')

loglevel = 'info'
accesslog = '-'
access_log_format = "%(h)s %(l)s %(u)s %(t)s '%(r)s' %(s)s %(b)s '%(f)s' '%(a)s' in %(D)sµs"

workers = int(os.getenv('WEB_CONCURRENCY', multiprocessing.cpu_count() * 2))
threads = int(os.getenv('PYTHON_MAX_THREADS', 1))
