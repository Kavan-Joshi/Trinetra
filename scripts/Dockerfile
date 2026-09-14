FROM python:3.12-slim
WORKDIR /app/scripts
COPY packages/trinetra_core /app/packages/trinetra_core
COPY sim /app/sim
COPY scripts/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY scripts /app/scripts
ENV PYTHONPATH=/app/packages:/app
CMD ["python", "seed.py"]
