FROM jrottenberg/ffmpeg:4.1-alpine
RUN apk add --no-cache python3 py3-pip
WORKDIR /app
COPY . .
RUN pip3 install -r requirements.txt --break-system-packages
CMD ["python3", "main.py"]
