FROM python:3.11
# FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

LABEL maintainer="Arman Soltanian"

COPY requirements.txt /tmp/requirements.txt

RUN apt update
RUN apt install -y wireguard-tools net-tools iproute2
RUN pip install --no-cache-dir -r /tmp/requirements.txt
RUN apt install -y iptables
# COPY ./start.sh /start.sh
# RUN chmod +x /start.sh

# COPY ./gunicorn_conf.py /gunicorn_conf.py

# RUN mkdir /etc/wireguard/
COPY . /app
WORKDIR /app/
ENV PYTHONPATH=/app
EXPOSE 8000 51820 51870
# Run the start script, it will check for an /app/prestart.sh script (e.g. for migrations)
# And then will start Gunicorn with Uvicorn
CMD ["/app/start.sh"]