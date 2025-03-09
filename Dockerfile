FROM python:3.9-slim

WORKDIR /app

COPY tidalrip.py .

RUN pip install --no-cache-dir requests==2.31.0 && \
    chmod +x tidalrip.py

ENTRYPOINT ["python", "tidalrip.py"]