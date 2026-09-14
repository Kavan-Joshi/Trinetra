FROM python:3.12-slim
ARG INSTALL_ML=false
WORKDIR /app/services/gateway
COPY packages/trinetra_core /app/packages/trinetra_core
COPY sim /app/sim
COPY services/gateway/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY services/gateway/requirements-ml.txt /tmp/requirements-ml.txt
RUN if [ "$INSTALL_ML" = "true" ]; then pip install --no-cache-dir -r /tmp/requirements-ml.txt && echo "ML deps installed"; fi
RUN if [ "$INSTALL_ML" = "true" ]; then apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg libgl1 libglib2.0-0 libxcb1 libsm6 libxext6 libxrender1 libx11-6 \
    && rm -rf /var/lib/apt/lists/*; fi
COPY services/gateway /app/services/gateway
ENV PYTHONPATH=/app/packages:/app
CMD ["python", "-m", "app.main"]
