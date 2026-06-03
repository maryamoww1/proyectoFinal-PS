FROM python:3.11-slim

WORKDIR /app

COPY sbac.py .
COPY test_sbac.py .

CMD ["python", "-m", "unittest", "test_sbac", "-v"]
