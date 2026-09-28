FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY requirements.txt .
COPY packages/ packages/
RUN pip install -r requirements.txt
COPY . .
RUN DJANGO_DEBUG=0 DJANGO_SECRET_KEY=build python manage.py collectstatic --noinput \
    && useradd --create-home app && mkdir -p media && chown app media
USER app
EXPOSE 8000
CMD ["gunicorn", "observatoire.wsgi", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "60"]
