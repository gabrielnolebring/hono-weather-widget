FROM python:3.11-slim

# Installera systembibliotek för Playwright/Chromium
RUN apt-get update && apt-get install -y wget gnupg ca-certificates curl fonts-liberation libappindicator3-1 libasound2 libatk-bridge2.0-0 libatk1.0-0 libcups2 libdbus-1-3 \
  libgdk-pixbuf2.0-0 libnspr4 libnss3 libx11-xcb1 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libgtk-3-0 libxshmfence1 libxinerama1 libpango-1.0-0 libpangocairo-1.0-0 libxkbcommon0 \
  --no-install-recommends && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Installera Playwright + browser-binaries
RUN python -m playwright install --with-deps

COPY . .

CMD ["gunicorn", "app:app"]
