FROM python:3

ADD requirements.txt /requirements.txt

RUN pip install -r requirements.txt

ADD bot.py /

ENV TZ=Europe/Moscow

CMD [ "python", "./bot.py" ]