import apiai
import json
import random
from time import localtime, strftime, sleep
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll


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
        creds = json.loads(open('creds.json', 'r').read())
        token = creds['vk_token']
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

    return json.loads(open('creds.json', 'r').read())


def request_df(token, text):
    """ Запрос на сервис Dialogflow.
    Args:
        token: Токен вк.
        text: Текст сообщения.
    Returns:
        response: Текст ответа.
    Raises:
        None
    """

    try:
        request = apiai.ApiAI(token).text_request()
        request.lang = 'ru'
        request.session_id = 'Syndrome'
        request.query = text
        responseJson = json.loads(request.getresponse().read().decode('utf-8'))
        if text and responseJson['result'] and responseJson['result']['fulfillment']['speech']:
            response = responseJson['result']['fulfillment']['speech']
            return response
        else:
            return None
    except:
        return None


def rewrite_file(phrase, bot_phrases):
    """ Перезапись файла с фразами.
    Args:
        phrase: Новая фраза.
        bot_phrases: Загруженные фразы.
    """
    with open('phrases.txt', 'a', encoding='utf8') as f:
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
        self.token = creds.get('df_token')
        self.name = creds.get('name')
        self.shitposters = {}
        with open('phrases.txt', encoding='utf8') as f:
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
            # Некому ответить, просто логируем.
            if not chat_id or not user_id:
                print('chat_id: {} \n user_id: {}'.format(chat_id, user_id))
                continue
            if text and bot.name in text[0].lower():
                # Если обратились к боту.
                if len(text) > 2 and 'добавь' in text[1].lower():
                    # Если команда "добавить".
                    affirmation = bot.add_phrase(author, text, chat_id)
                    bot.send_message(chat_id, affirmation or random.choice(bot.phrases))
                else:
                    # Просто обращение.
                    message = ' '.join(text[1:])
                    phrase = request_df(bot.token, message)
                    bot.send_message(chat_id, phrase or random.choice(bot.phrases))
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
