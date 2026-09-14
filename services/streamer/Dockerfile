ARG INSTALL_WEBRTC=false
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg fonts-dejavu-core && rm -rf /var/lib/apt/lists/*
WORKDIR /app/services/streamer
COPY packages/trinetra_core /app/packages/trinetra_core
COPY sim /app/sim
COPY services/streamer/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY services/streamer/requirements-webrtc.txt /tmp/requirements-webrtc.txt
RUN if [ "$INSTALL_WEBRTC" = "true" ]; then pip install --no-cache-dir -r /tmp/requirements-webrtc.txt; fi
COPY services/streamer /app/services/streamer
ENV PYTHONPATH=/app/packages:/app
EXPOSE 8002
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
