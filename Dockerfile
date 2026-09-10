FROM python:3.10-slim

# Install system dependencies including mdbtools and ODBC support
RUN apt-get update && apt-get install -y \
    unixodbc \
    unixodbc-dev \
    mdbtools \
    libmdbodbc \
    && rm -rf /var/lib/apt/lists/*

# Configure ODBC driver for MDBTools
RUN echo "[MDBTools]\nDriver = /usr/lib/x86_64-linux-gnu/odbc/libmdbodbc.so\nSetup = /usr/lib/x86_64-linux-gnu/odbc/libmdbodbc.so\nFileUsage = 1" > /etc/odbcinst.ini

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
