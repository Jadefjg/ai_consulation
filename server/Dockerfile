FROM python:3.11-slim-bookworm

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TZ=Asia/Shanghai \
    ANONYMIZED_TELEMETRY=False

RUN set -eux; \
    if [ -f /etc/apt/sources.list.d/debian.sources ]; then \
      sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources; \
    fi; \
    apt-get update \
    && apt-get install -y --no-install-recommends gcc g++ curl libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
ARG PIP_INDEX_URL=https://pypi.org/simple
RUN pip install --no-cache-dir -i "${PIP_INDEX_URL}" -r requirements.txt

COPY . .

RUN mkdir -p /data/uploads/knowledge /data/uploads/avatar /data/chroma_db

EXPOSE 8000

CMD ["python", "scripts/docker_entrypoint.py"]
