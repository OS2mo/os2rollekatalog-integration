FROM python:3.5.7-buster

WORKDIR /app

COPY ./requirements.txt /app/requirements.txt

RUN pip3 install -r ./requirements.txt

COPY . /app

CMD [ "python", "./os2rollekatalog_integration.py" ]