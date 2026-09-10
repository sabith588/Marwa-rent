FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    unixodbc \
    unixodbc-dev \
    mdbtools \
    odbc-mdbtools \
    && rm -rf /var/lib/apt/lists/*

# Configure ODBC driver for MDBTools
RUN echo "[MDBTools]\nDriver = /usr/lib/x86_64-linux-gnu/odbc/libmdbodbc.so\nSetup = /usr/lib/x86_64-linux-gnu/odbc/libmdbodbc.so\nFileUsage = 1" > /etc/odbcinst.ini

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
