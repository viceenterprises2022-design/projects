FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir -e .

COPY . .

EXPOSE 8000

CMD ["python", "app/main.py"]
