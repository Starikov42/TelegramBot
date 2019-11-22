FROM python:3.7
RUN apt-get update -y && apt-get install -y \
    python3 python3-dev python3-pip libssl-dev libffi-dev libpq-dev python-psycopg2 less

EXPOSE 5001

COPY . /usr/local/src/paymnent_service/
WORKDIR /usr/local/src/paymnent_service/
RUN pip3 install -r /usr/local/src/paymnent_service/requirements.txt

RUN touch /var/log/payment_service.log.debug

ENTRYPOINT ["python3", "run.py"]
