FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
WORKDIR /app
COPY requirements-api.txt ./
RUN pip install --no-cache-dir -r requirements-api.txt
COPY src ./src
COPY scripts/start_api.py ./scripts/start_api.py
RUN useradd --uid 10001 --create-home appuser
USER 10001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=90s CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:'+os.environ.get('PORT','8000')+'/health',timeout=4)"
CMD ["python", "scripts/start_api.py"]
