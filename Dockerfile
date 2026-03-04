FROM python:3.8-slim

ENV TZ=Europe/Moscow

WORKDIR /app

# Упрощённый Dockerfile без apt-get (tzdata),
# чтобы сборка проходила даже при проблемах с репозиториями внутри контейнера.

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY bot.py ai.py hangman.py ./

# `mnt` directory is expected to be mounted from the host, e.g.:
#   docker run -v $(pwd)/mnt:/app/mnt IMAGE

CMD ["python", "bot.py"]
