FROM python:3.11-slim

ARG REQUIREMENTS=server/requirements.txt
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5001 \
    FATIGUE_DATA_DIR=/data \
    FATIGUE_MODEL_DIR=/app/models

WORKDIR /app
COPY server/requirements.txt server/requirements-gpu.txt /app/server/
RUN pip install --no-cache-dir -r "/app/${REQUIREMENTS}"
COPY server /app/server
COPY models /app/models
RUN mkdir -p /data

EXPOSE 5001
VOLUME ["/data"]
HEALTHCHECK --interval=20s --timeout=5s --start-period=30s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5001/api/health', timeout=3)"
CMD ["python", "-m", "server.entrypoint"]
