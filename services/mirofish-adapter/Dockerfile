FROM python:3.12-slim as builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml pyproject.toml
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e . --no-build-isolation

FROM python:3.12-slim

WORKDIR /app

RUN useradd -m -u 1000 xprclaw && \
    mkdir -p /app && \
    chown -R xprclaw:xprclaw /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY --chown=xprclaw:xprclaw src/ src/

USER xprclaw

EXPOSE 8088

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LOG_LEVEL=info

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8088/healthz').raise_for_status()" || exit 1

CMD ["uvicorn", "xprclaw_mirofish.api:app", "--host", "0.0.0.0", "--port", "8088"]
