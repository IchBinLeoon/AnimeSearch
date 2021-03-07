FROM python:3.8.6-buster

WORKDIR /anisearch-discord-bot

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8765

CMD [ "python", "-m", "anisearch" ]