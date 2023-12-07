#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import json
import os
import random
import re
from time import localtime, strftime, sleep
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll
from hangman import HANGMAN


def get_session(token):
    """ Получение сессии.
    Args:
        token: Токен приложения/паблика вк.
    Returns:
        session: Сессия вк.
    Raises:
        Exception: Ошибка авторизации.
    """

    try:
        session = vk_api.VkApi(token=token)
        print('Authorised succesfully!')
        return session
    except vk_api.AuthError as err:
        raise Exception('Authorisation error: {}'.format(err))


def get_credentials():
    """ Получение параметров для логина.
    Returns:
        creds: Объект с данными для авторизации.
    """

    return json.loads(open('./mnt/creds.json', 'r', encoding='utf-8').read())


def rewrite_file(phrase, bot_phrases):
    """ Перезапись файла с фразами.
    Args:
        phrase: Новая фраза.
        bot_phrases: Загруженные фразы.
    """
    with open('./mnt/phrases.txt', 'a', encoding='utf8') as f:
        f.write(phrase+'\n')
        bot_phrases.append(phrase)


class Shitposter():
    def __init__(self, user_id, first_msg_time):
        """Инициализация шитпостера"""
        self.user_id = user_id
        self.shitpost_count = 0
        self.first_msg_time = first_msg_time


class BOT():
    def __init__(self):
        """Инициализация бота"""
        creds = get_credentials()
        self.session = get_session(creds.get('vk_token'))
        if not self.session:
            return None

        self.api = self.session.get_api()
        self.name = creds.get('name')
        self.shitposters = {}
        self.game = None
        with open('./mnt/phrases.txt', encoding='utf8') as f:
            self.phrases = f.readlines()

    def add_phrase(self, author, text):
        """Добавление фразы"""
        phrase = ' '.join(text[2:])
        if not (self.name in phrase.lower() or '@' in phrase.lower()):
            rewrite_file(phrase, self.phrases)
            return '[id'+author + '|Филтан], я добавил: "'+phrase+'"'
            
        return None

    def send_message(self, chat_id, message):
        """Метод для отправки сообщения message в чат c chat_id"""
        if message:
            random_id = random.randint(0, 2147483647*2)
            self.api.messages.setActivity(
                peer_id=chat_id,
                type='typing'
            )
            sleep(1)
            self.api.messages.send(
                peer_id=chat_id,
                message=message,
                random_id=random_id
            )

    def get_user_info(self, user_id):
        info = self.api.users.get(user_ids=[user_id])
        return info and info[0]


def main():
    bot = BOT()
    if not bot.session or not bot.api:
        raise Exception('API или Сессия не получены')
    longpoll = VkBotLongPoll(bot.session, 140214622)

    for event in longpoll.listen():
        if event.type.name == 'MESSAGE_NEW':
            data = event.obj
            text = data.text.split()
            chat_id = data.peer_id
            user_id = data.from_id
            msg_time = data.date
            author = str(user_id)
            # /roll
            if text and text[0] == '/roll':
                message = str(random.randint(0, int(text[1]) if len(text) > 1 and re.match(r'^([\s\d]+)$', text[1]) else 100))
                bot.send_message(chat_id, message)
                continue
            # Закроем игру если прошло время
            if bot.game and bot.game.game_start and msg_time - bot.game.game_start > 180:
                bot.game = None
            # Некому ответить, просто логируем
            if not chat_id or not user_id:
                print('chat_id: {} \n user_id: {}'.format(chat_id, user_id))
                continue
            if text and bot.name in text[0].lower():
                # Если обратились к боту
                if len(text) >= 2:
                    if 'добавь' in text[1].lower():
                        # Если команда "добавить".
                        affirmation = bot.add_phrase(author, text)
                        bot.send_message(chat_id, affirmation or random.choice(bot.phrases))
                    elif 'виселица' in text[1].lower():
                        message = ''
                        if bot.game:
                            user = bot.get_user_info(bot.game.player_id)
                            message = '{name} уже играет'.format(name=user['first_name'])
                        else:
                            bot.game = HANGMAN(author, msg_time)
                            shown_word = ' '.join(bot.game.shown_word)
                            user = bot.get_user_info(author)
                            message = '{name}, ты в игре, слово {word}'.format(name=user['first_name'], word=shown_word)
                        bot.send_message(chat_id, message)
                    else:
                        # Просто обращение.
                        message = ' '.join(text[1:])
                        # phrase = request_df(bot.token, message)
                        bot.send_message(chat_id, random.choice(bot.phrases))
            elif bot.game and bot.game.player_id == author and text and len(text) == 1 and text[0]:
                letter = text[0].strip().lower()
                message = ''
                if len(letter) == 1:
                    res = bot.game.guess(letter)
                    message = res[1]
                    bot.send_message(chat_id, message)
                    if not res[0]:
                        bot.game = None                                                                    
            else:
                # Обработчик шитпоста.
                if not user_id in bot.shitposters:
                    bot.shitposters[user_id] = Shitposter(user_id, msg_time)
                else:
                    user = bot.shitposters[user_id]
                    if msg_time - user.first_msg_time > 180:
                        user.first_msg_time = msg_time
                        user.shitpost_count = 0
                    if user.shitpost_count >= 7:
                        phrase = random.choice(bot.phrases)
                        bot.send_message(chat_id, phrase)
                        dt = strftime("%d.%m.%Y %H:%M:%S", localtime())
                        print(dt + ' / ' + str(user.user_id) +
                              ' shitposted in chat #' + str(chat_id) + '!')
                        user.shitpost_count = 0
                    user.shitpost_count += 1


if __name__ == "__main__":
    while True:
        try:
            main()
        except Exception as err:
            sleep(10)
            print('-'*50)
            print('Error: {}'.format(err))
            print(strftime("%d.%m.%Y %H:%M:%S", localtime()))
            pass
