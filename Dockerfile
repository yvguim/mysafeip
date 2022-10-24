FROM python:3.9-slim

LABEL maintainer="Yves Guimard <yves.guimard@gmail.com>"

COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r /tmp/requirements.txt

WORKDIR /app/
COPY build/start.sh /start.sh
RUN chmod +x /start.sh

COPY build/gunicorn_conf.py /gunicorn_conf.py

COPY build/start-reload.sh /start-reload.sh
RUN chmod +x /start-reload.sh

COPY app /app

ENV PYTHONPATH=/app

EXPOSE 80
COPY app/ /app/
# Run the start script, it will check for an /app/prestart.sh script (e.g. for migrations)
# And then will start Gunicorn with Uvicorn
CMD ["/start.sh"]
