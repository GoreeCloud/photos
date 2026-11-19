FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PHOTOS_DATA_DIR=/data
WORKDIR /app
COPY api/pyproject.toml /app/pyproject.toml
COPY api/app /app/app
RUN pip install --no-cache-dir . && useradd --create-home --uid 10001 photos && mkdir -p /data && chown 10001:10001 /data
USER 10001:10001
EXPOSE 8787
CMD ["uvicorn", "app.main:app", "--factory", "--host", "0.0.0.0", "--port", "8787", "--proxy-headers", "--forwarded-allow-ips", "127.0.0.1"]
