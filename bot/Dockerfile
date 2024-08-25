FROM python:3.12-alpine

WORKDIR /bot

COPY . .

RUN apk update && \
    apk upgrade && \
    rm -rf /var/cache/apk/*

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

CMD [ "python", "-m", "anisearch" ]