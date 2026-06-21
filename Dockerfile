FROM mcr.microsoft.com/playwright/python:latest
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files (including proxies.txt, dragon.jpg, bot.py, gates/, kill/, utils/, tools/)
COPY . .

CMD ["python", "bot.py"]
