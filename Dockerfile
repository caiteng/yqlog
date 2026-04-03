FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p /app/data /app/uploads

ENV FLASK_SECRET_KEY=change-me-in-production
EXPOSE 8000

CMD ["python", "app.py"]
