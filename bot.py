#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import random
import re
from time import localtime, sleep, strftime
import sys
import os

import vk_api
from vk_api import VkUpload
from vk_api.bot_longpoll import VkBotLongPoll
from ai import ImageGenerator

from hangman import HANGMAN


class MessageData(dict):
    def __init__(self, chat_id, user_id, user_name, msg_time, full_message_text, first_command, second_command, other_text):
        self.chat_id = chat_id
        self.user_id = user_id
        self.user_name = user_name
        self.msg_time = msg_time
        self.full_message_text = full_message_text
        self.first_command = first_command
        self.second_command = second_command
        self.other_text = other_text

    def __repr__(self):
        return self


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
        print("Authorised succesfully!")
        return session
    except vk_api.AuthError as err:
        raise Exception("Authorisation error: {}".format(err))


def get_credentials():
    """ Получение параметров для логина.
    Returns:
        creds: Объект с данными для авторизации.
    """

    return json.loads(open("./mnt/creds.json", "r", encoding="utf-8").read())


def rewrite_file(phrase, bot_phrases):
    """ Перезапись файла с фразами.
    Args:
        phrase: Новая фраза.
        bot_phrases: Загруженные фразы.
    """
    with open("./mnt/phrases.txt", "a", encoding="utf8") as f:
        f.write(phrase+"\n")
        bot_phrases.append(phrase)


class Shitposter():
    def __init__(self, user_id, first_msg_time):
        """Инициализация шитпостера"""
        self.user_id = user_id
        self.shitpost_count = 0
        self.first_msg_time = first_msg_time


class BOT():
    actions = ["добавь", "нарисуй", "виселица"]

    def __init__(self):
        """Инициализация бота"""
        creds = get_credentials()
        self.session = get_session(creds.get("vk_token"))
        self.api = self.session.get_api()
        if not self.session or not self.api:
            raise Exception("API или Сессия не получены")
        self.longpoll = VkBotLongPoll(self.session, creds.get("group_id"))
        self.upload = VkUpload(self.session)
        self.name = creds.get("name")
        self.shitposters = {}
        self.game = None
        self.image_generator = ImageGenerator()
        with open("./mnt/phrases.txt", encoding="utf8") as f:
            self.phrases = f.readlines()

    def add_phrase(self, author_id, text):
        """Добавление фразы"""
        phrase = " ".join(text)
        if not (self.name in phrase.lower() or "@" in phrase.lower()):
            rewrite_file(phrase, self.phrases)
            return "[id{author_id}|Филтан], я добавил: \"{phrase}\"".format(author_id=author_id, phrase=phrase)

        return None

    def send_message(self, chat_id, message):
        """Метод для отправки сообщения message в чат c chat_id"""
        if message:
            random_id = random.randint(0, 2147483647*2)
            self.api.messages.setActivity(
                peer_id=chat_id,
                type="typing"
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

    def generate_image_and_send(self, chat_id, author_id, request_phrase):
        attachments = []
        try:
            image_bytes = self.image_generator.get_image(request_phrase)
            if (not image_bytes):
                self.send_message(chat_id, "Не удалось загрузить изображение")
                return
            photo = self.upload.photo_messages(
                photos=[image_bytes], peer_id=chat_id)[0]
            attachments.append(
                "photo{}_{}".format(photo["owner_id"], photo["id"])
            )
            random_id = random.randint(0, 2147483647*2)
            self.api.messages.setActivity(
                peer_id=chat_id,
                type="typing"
            )
            sleep(3)
            self.api.messages.send(
                peer_id=chat_id,
                attachment=",".join(attachments),
                message="[id{author_id}|Филтан], я нарисовал какую-то хрень".format(
                    author_id=author_id),
                random_id=random_id
            )
        except Exception as error:
            self.send_message(chat_id, "[id{author_id}|Филтан], не вышло, ${err_message}".format(
                author_id=author_id, err_message=error))

    def get_message_data_from_event(self, event) -> MessageData:
        data = event.obj
        user_id = str(data.from_id)
        full_message_text = data.text
        words = full_message_text.split()
        user_info = self.get_user_info(user_id)
        first_command = words[0].strip().lower() if len(words) > 0 else ""
        second_command = words[1].strip().lower() if len(words) > 1 else ""
        other_text = words[2:] if second_command in self.actions else words[1:]
        return MessageData(
            data.peer_id,
            user_id,
            user_info["first_name"],
            data.date,
            full_message_text,
            first_command,
            second_command,
            other_text
        )

    def roll_handler(self, chat_id, user_name, roll_number):
        print("{} rolled".format(user_name))
        random_number = str(random.randint(0, int(roll_number)
                                           if roll_number and re.match(r"^([\s\d]+)$", roll_number) else 100))
        self.send_message(chat_id, random_number)

    def bot_conversation_handler(self, data: MessageData):
        user_id = data.user_id
        chat_id = data.chat_id
        if (data.second_command in self.actions):
            print("Обработка команды \"{}\"".format(data.second_command))

            if "добавь" == data.second_command:
                # Если команда "добавить"
                affirmation = self.add_phrase(user_id, data.other_text)
                self.send_message(
                    chat_id, affirmation or random.choice(self.phrases))
                return

            if "виселица" == data.second_command:
                # Если команда "виселица"
                message = ""
                if self.game:
                    if data.user_id == self.game.player_id:
                        message = "Игра окончена, слово: {}".format(
                            self.game.word)
                        self.game = None
                    else:
                        message = "{name} уже играет".format(
                            name=data.user_name)
                    self.send_message(chat_id, message)
                    return
                else:
                    self.game = HANGMAN(user_id, data.msg_time)
                    shown_word = " ".join(self.game.shown_word)
                    message = "{name}, ты в игре, у тебя 3 минуты, слово {word}".format(
                        name=data.user_name, word=shown_word)
                    self.send_message(chat_id, message)
                    return

            if "нарисуй" == data.second_command:
                # Если команда "нарисовать"
                phrase = " ".join(data.other_text)
                self.send_message(chat_id, "Ща погодь")
                self.generate_image_and_send(chat_id, user_id, phrase)
                return
        else:
            if self.game and self.game.player_id == data.user_id and data.second_command:
                # Если идет игра
                print("Обработка игры {}".format(data.user_name))
                letter = data.second_command
                if len(letter) == 1:
                    res = self.game.guess(letter)
                    message = res[1]
                    self.send_message(chat_id, message)
                    # Если выиграли, заканчиваем игру
                    if res[0]:
                        self.game = None
                return
            else:
                # Просто ответ
                message = " ".join(data.other_text)
                self.send_message(chat_id, random.choice(self.phrases))
                return

    def shitpost_handler(self, data: MessageData):
        msg_time = data.msg_time
        user = self.shitposters[data.user_id]
        chat_id = data.chat_id
        if msg_time - user.first_msg_time > 180:
            user.first_msg_time = msg_time
            user.shitpost_count = 0
            return
        if user.shitpost_count >= 7:
            phrase = random.choice(self.phrases)
            self.send_message(chat_id, phrase)
            dt = strftime("%d.%m.%Y %H:%M:%S", localtime())
            print(dt + " / " + str(user.user_id) +
                  " shitposted in chat #" + str(chat_id) + "!")
            user.shitpost_count = 0
            return
        user.shitpost_count += 1


def main():
    bot = BOT()

    for event in bot.longpoll.listen():
        if event.type.name == "MESSAGE_NEW":
            message_data = bot.get_message_data_from_event(event)
            user_id = message_data.user_id

            # Закроем игру если прошло время
            if bot.game and bot.game.game_start and message_data.msg_time - bot.game.game_start > 180:
                print("Game ended")
                bot.game = None
                bot.send_message(
                    message_data.chat_id, "Игра окончена, слово: {}".format(bot.game.word))

            # /roll
            if message_data.first_command == "/roll":
                roll_number = message_data.second_command
                bot.roll_handler(message_data.chat_id,
                                 message_data.user_name, roll_number)
                continue

            # Обращение к боту
            if bot.name in message_data.first_command:
                print("Bot asked")
                bot.bot_conversation_handler(message_data)
                continue

            # Обработчик шитпоста
            if not user_id in bot.shitposters:
                print("Shitposter added")
                bot.shitposters[user_id] = Shitposter(
                    user_id, message_data.msg_time)
                continue
            elif user_id in bot.shitposters:
                print("Shitpost handling")
                bot.shitpost_handler(message_data)
                continue

            # Некому ответить, просто логируем
            if not message_data.chat_id or not user_id:
                print("Chat_id {} \n {}".format(
                    message_data.chat_id, message_data.user_name))
                continue


if __name__ == "__main__":
    while True:
        try:
            print("Started!")
            main()
        except Exception as err:
            sleep(10)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            print("-"*50)
            # print("Error: {}".format(err))
            # print(strftime("%d.%m.%Y %H:%M:%S", localtime()))
            pass
