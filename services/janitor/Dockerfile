FROM python:3.12-slim
WORKDIR /app/services/janitor
COPY packages/trinetra_core /app/packages/trinetra_core
COPY services/janitor/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY services/janitor /app/services/janitor
ENV PYTHONPATH=/app/packages
CMD ["python", "-m", "app.main"]
