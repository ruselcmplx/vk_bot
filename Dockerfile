FROM python:3

ADD requirements.txt requirements.txt

RUN pip install -r requirements.txt

ADD bot.py bot.py
ADD ai.py ai.py
ADD hangman.py hangman.py

ENV TZ=Europe/Moscow

CMD [ "python", "bot.py" ]