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

# set version label
ARG BUILD_DATE
ARG VERSION
ARG WIREGUARD_RELEASE

RUN \
  echo "**** install dependencies ****" && \
  apt install -y git bc grep iproute2 iptables net-tools openresolv jq && echo "wireguard" >> /etc/modules && \
  cd /sbin && \
  for i in ! !-save !-restore; do \
    rm -rf iptables$(echo "${i}" | cut -c2-) && \
    rm -rf ip6tables$(echo "${i}" | cut -c2-) && \
    ln -s iptables-legacy$(echo "${i}" | cut -c2-) iptables$(echo "${i}" | cut -c2-) && \
    ln -s ip6tables-legacy$(echo "${i}" | cut -c2-) ip6tables$(echo "${i}" | cut -c2-); \
  done && \
  echo "**** install wireguard-tools ****" && \
  if [ -z ${WIREGUARD_RELEASE+x} ]; then \
    WIREGUARD_RELEASE=$(curl -sX GET "https://api.github.com/repos/WireGuard/wireguard-tools/tags" \
    | jq -r .[0].name); \
  fi && \
  cd /app && \
  git clone https://git.zx2c4.com/wireguard-tools && \
  cd wireguard-tools && \
  git checkout "${WIREGUARD_RELEASE}" && \
  sed -i 's|\[\[ $proto == -4 \]\] && cmd sysctl -q net\.ipv4\.conf\.all\.src_valid_mark=1|[[ $proto == -4 ]] \&\& [[ $(sysctl -n net.ipv4.conf.all.src_valid_mark) != 1 ]] \&\& cmd sysctl -q net.ipv4.conf.all.src_valid_mark=1|' src/wg-quick/linux.bash && \
  make -C src -j$(nproc) && \
  make -C src install && \
  rm -rf /etc/wireguard && \
  ln -s /config/wg_confs /etc/wireguard && \
  echo "**** clean up ****" && \
  rm -rf \
    /tmp/*
RUN mkdir -p /config/wg_confs
# ports and volumes
EXPOSE 51820/udp 8000/tcp
# Run the start script, it will check for an /app/prestart.sh script (e.g. for migrations)
# And then will start Gunicorn with Uvicorn
ENTRYPOINT ["/app/start.sh"]
