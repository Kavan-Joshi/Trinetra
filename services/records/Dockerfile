FROM python:3.12-slim
WORKDIR /app/services/records
COPY packages/trinetra_core /app/packages/trinetra_core
COPY sim /app/sim
COPY services/records/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY services/records /app/services/records
ENV PYTHONPATH=/app/packages:/app
EXPOSE 8001
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
