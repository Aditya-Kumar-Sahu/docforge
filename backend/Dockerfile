FROM python:3.12-slim
RUN pip install uv
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml ./

# Enable bytecode compilation and move venv outside the mounted volume
ENV UV_COMPILE_BYTECODE=1
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Sync dependencies to /opt/venv
RUN uv sync || echo "No lockfile yet"

# Copy the rest of the app
COPY . .

CMD ["uv", "run", "fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]
