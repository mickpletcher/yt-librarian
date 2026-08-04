FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
COPY config ./config
COPY migrations ./migrations
COPY alembic.ini ./
RUN pip install --no-cache-dir .
RUN mkdir -p /app/data
EXPOSE 8501
CMD ["streamlit", "run", "src/youtube_knowledge_manager/ui/app.py", "--server.address=0.0.0.0"]
