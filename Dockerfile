# Multi-stage build for optimized Lambda container
FROM python:3.12-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --target /app/dependencies -r requirements.txt

# Production stage
FROM public.ecr.aws/lambda/python:3.12

# Copy dependencies from builder stage
COPY --from=builder /app/dependencies ${LAMBDA_RUNTIME_DIR}

# Copy application code
COPY agent.py ${LAMBDA_RUNTIME_DIR}/lambda_function.py
COPY aws_config.py ${LAMBDA_RUNTIME_DIR}/aws_config.py
COPY tools/ ${LAMBDA_RUNTIME_DIR}/tools/

# Set the CMD to your handler
CMD ["lambda_function.lambda_handler"]
