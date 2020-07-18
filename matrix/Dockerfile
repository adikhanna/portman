FROM python:3.6

RUN apt-get update \
    && apt-get install -y \
      python3-venv \
      python3-setuptools \
      build-essential

WORKDIR /app

RUN mkdir -p /var/log/nginx/healthd/

COPY *.py *.json requirements.txt Makefile ./

EXPOSE 5000

RUN make install

CMD ["make", "run"]