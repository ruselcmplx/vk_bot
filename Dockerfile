FROM python:3.10-slim

ENV TZ=Europe/Moscow

WORKDIR /app

# Install system dependencies (timezone data) and Python dependencies
RUN apt-get update \ 
    && apt-get install -y --no-install-recommends tzdata \ 
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY bot.py ai.py hangman.py ./

# `mnt` directory is expected to be mounted from the host, e.g.:
#   docker run -v $(pwd)/mnt:/app/mnt IMAGE

CMD ["python", "bot.py"]
