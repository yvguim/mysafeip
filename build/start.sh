#! /usr/bin/env sh
set -e
export WORKER_CLASS=${WORKER_CLASS:-"uvicorn.workers.UvicornWorker"}

exec gunicorn -k "$WORKER_CLASS" -c "/gunicorn_conf.py" "main:app"
