FROM python:3.11-slim

WORKDIR /app

RUN pip install pytest pytest-cov

COPY sbac.py .

COPY test_unit.py .
COPY test_integration.py .
COPY test_regression.py .

CMD ["pytest", "--cov=sbac", "--cov-report=term-missing"]

