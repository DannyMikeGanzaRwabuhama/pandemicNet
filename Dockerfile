FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
ENV GOOGLE_API_KEY=""
EXPOSE 5000 8501
CMD ["bash", "start.sh"]