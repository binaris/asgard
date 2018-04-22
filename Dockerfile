FROM python:3.6-jessie

RUN apt upgrade -y
RUN apt-get update && apt-get install -y curl pep8
RUN curl -s -L https://raw.githubusercontent.com/binaris/711/master/ubuntu/node/8.x.sh | bash
RUN mkdir -p /app
WORKDIR /app

RUN pip install -U pip
COPY requirements.txt .
RUN pip install -r requirements.txt -t .

COPY package.json .
RUN npm install

ENV PATH=/app/node_modules/.bin:$PATH


COPY serverless.yml ./
COPY *.py ./
COPY *.json ./

ENTRYPOINT ["/app/node_modules/.bin/sls"]
