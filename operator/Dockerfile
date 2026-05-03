FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy operator code
COPY src/ ./src/
COPY templates/ ./templates/

# Run the operator
CMD ["kopf", "run", "--standalone", "--verbose", "src/operator.py"]
