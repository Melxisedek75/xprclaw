FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 xprclaw && \
    mkdir -p /app && \
    chown -R xprclaw:xprclaw /app

RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir fastapi uvicorn httpx pydantic pydantic-settings tenacity structlog

COPY --chown=xprclaw:xprclaw src/xprclaw_mirofish/ xprclaw_mirofish/

USER xprclaw

EXPOSE 8088

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LOG_LEVEL=info

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8088/healthz').raise_for_status()" || exit 1

CMD ["uvicorn", "xprclaw_mirofish.api:app", "--host", "0.0.0.0", "--port", "8088"]
