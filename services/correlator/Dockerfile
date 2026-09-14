FROM python:3.12-slim
WORKDIR /app/services/correlator
COPY packages/trinetra_core /app/packages/trinetra_core
COPY sim /app/sim
COPY services/correlator/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY services/correlator /app/services/correlator
ENV PYTHONPATH=/app/packages:/app
CMD ["python", "-m", "app.main"]
