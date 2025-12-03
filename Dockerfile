FROM python:3.11-slim
WORKDIR /app

# Install minimal deps
RUN apt-get update \
 && apt-get install -y --no-install-recommends gcc libffi-dev build-essential ffmpeg \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy current directory (backend source) into the image
COPY . /app/

ENV PORT=8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
