FROM python:3.12-slim
WORKDIR /app/services/core_api
COPY packages/trinetra_core /app/packages/trinetra_core
COPY sim /app/sim
COPY services/core_api/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY services/core_api /app/services/core_api
ENV PYTHONPATH=/app/packages:/app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
