FROM python:3.10-slim

# Install mdbtools to convert accdb to sqlite
RUN apt-get update && apt-get install -y \
    mdbtools \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
