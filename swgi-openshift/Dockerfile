FROM registry.access.redhat.com/ubi9/ubi-minimal

LABEL name="swgi-core" \
      vendor="Axis Systems" \
      maintainer="Zohaib Ahmad" \
      version="0.1.0" \
      release="1" \
      summary="SWGI core service" \
      description="Core service for the SWGI platform."

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /opt/app-root/src

RUN microdnf install -y python3.11 python3.11-pip shadow-utils && microdnf clean all
RUN ln -sf /usr/bin/python3.11 /usr/bin/python3 && ln -sf /usr/bin/pip3.11 /usr/bin/pip3

COPY swgi_core /opt/app-root/src/swgi_core
COPY swgi-openshift /opt/app-root/src/swgi-openshift
COPY swgi-openshift/licenses /licenses

WORKDIR /opt/app-root/src/swgi-openshift
RUN pip3 install --upgrade pip && pip3 install -r requirements.txt
RUN useradd --uid 10001 --create-home --shell /sbin/nologin appuser && \
    mkdir -p /tmp/secrets && \
    chown -R 10001:0 /opt/app-root/src /tmp/secrets && \
    chmod -R g=u /opt/app-root/src /tmp/secrets

USER 10001

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 CMD python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/healthz', timeout=3).read()"

CMD ["python3", "-m", "app.main"]
