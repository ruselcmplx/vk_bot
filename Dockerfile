FROM python:3

ADD bot.py creds.json /

RUN pip install apiai vk_api

CMD [ "python", "./bot.py" ]