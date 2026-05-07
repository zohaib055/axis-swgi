FROM registry.access.redhat.com/ubi9/python-311:latest

LABEL name="swgi-operator" \
      vendor="Axis Systems" \
      maintainer="support@example.com" \
      version="0.1.0" \
      release="1" \
      summary="SWGI operator control plane" \
      description="Kubernetes operator that manages SWGI operand deployment, scaling, lifecycle, and configuration."

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /opt/app-root/src

COPY axis-swgi-operator/requirements.txt requirements.txt
USER 0
RUN dnf upgrade -y python3.11 python3.11-libs \
    && dnf remove -y vim-minimal python3.11-devel libxslt-devel \
    && dnf clean all
RUN pip install --no-cache-dir -r requirements.txt

COPY axis-swgi-operator /opt/app-root/src/axis-swgi-operator
COPY axis-swgi-operator/licenses /licenses

USER 1001

ENTRYPOINT ["kopf", "run", "/opt/app-root/src/axis-swgi-operator/controller/main.py"]
