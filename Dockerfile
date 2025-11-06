FROM python:3.13.9-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# system deps
RUN apt-get update && apt-get install -y build-essential libpq-dev wget ca-certificates --no-install-recommends && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml poetry.lock* /app/

# install pip & deps (use pip for simplicity)
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && pip install -r requirements.txt

COPY . /app

# Entrypoint
COPY entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]

# not needed as Entry point used CMD ["gunicorn", "inventory_service.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2"]

