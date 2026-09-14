FROM python:3.12-slim
WORKDIR /app/services/notifier
COPY packages/trinetra_core /app/packages/trinetra_core
COPY services/notifier/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY services/notifier /app/services/notifier
ENV PYTHONPATH=/app/packages
CMD ["python", "-m", "app.main"]
