FROM python:3.9-slim

LABEL maintainer="Yves Guimard <yves.guimard@gmail.com>"

COPY requirements.txt /tmp/requirements.txt

#Run apt update -y && apt install -y python3-pip apt-utils
Run pip install --upgrade pip
RUN pip install --no-cache-dir -r /tmp/requirements.txt

WORKDIR /app/
COPY build/start.sh /start.sh
RUN chmod +x /start.sh

COPY build/gunicorn_conf.py /gunicorn_conf.py
COPY app /app

ENV PYTHONPATH=/app
EXPOSE 80
CMD ["/start.sh"]
