FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir . "mcp<2"
CMD ["saij-mcp"]
