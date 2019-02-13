import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from time import localtime, gmtime, strftime
import apiai
import random
import requests
import json


SCOPE = 'offline,messages,docs'
BOT_NAME = 'синдром'
IS_ERROR = False


# Получить сессию вк
def get_session(l, p, a_id, sc):
    session = vk_api.VkApi(l, p, a_id, sc, captcha_handler=captcha_handler)
    try:
        session.auth()
        print('Authorised succesfully!')
        return session
    except vk_api.AuthError as error_msg:
        raise Exception('Authorisation error: {}'.format(error_msg))


# Вычитываем данные для авторизации
def parse_credentials():
    """
    Вычитка параметров для логина
    returns: [login, passwd, vk_app_id, df_token] 
    """
    data = json.loads(open('creds.json', 'r').read())
    return [data[d] for d in data]


def request_df(token, text):
    """
    Запрос на сервис Dialogflow
    """
    request = apiai.ApiAI(token).text_request()
    request.lang = 'ru'
    request.session_id = 'Syndrome'
    request.query = text
    responseJson = json.loads(request.getresponse().read().decode('utf-8'))
    if text and responseJson['result'] and responseJson['result']['fulfillment']['speech']:
        response = responseJson['result']['fulfillment']['speech']
        return response
    else:
        return 'Я Вас не совсем понял!'


def rewrite_file(phrase, bot_phrases):
    with open('phrases.txt', 'a', encoding='utf8') as f:
        f.write(phrase)
        bot_phrases.append(phrase)


def captcha_handler(captcha):
    """ 
    При возникновении капчи вызывается эта функция и ей передается объект
    капчи. Через метод get_url можно получить ссылку на изображение.
    Через метод try_again можно попытаться отправить запрос с кодом капчи
    """

    key = input("Enter captcha code {0} ".format(captcha.get_url())).strip()

    # Пробуем снова отправить запрос с капчей
    return captcha.try_again(key)


class Shitposter():
    def __init__(self, user_id, first_msg_time):
        self.user_id = user_id
        self.shitpost_count = 0
        self.first_msg_time = first_msg_time


    def inc_counter(self):
        self.shitpost_count += 1


class BOT():
    def __init__(self):
        [login, password, app_id, df_token] = parse_credentials()
        self.session = get_session(login, password, app_id, SCOPE)

        if not self.session:
            return None
        
        self.api = self.session.get_api()
        self.token = df_token
        self.shitposters = {}
        with open('phrases.txt', encoding='utf8') as f:
            self.bot_phrases = f.readlines()


    # Отправка сообщения пользователю чате с chat_id
    def send_message(self, chat_id, message):
        random_id = random.randint(0,2147483647*2)
        self.api.messages.setActivity(
            peer_id=chat_id,
            type='typing'
        )
        self.api.messages.send(
            peer_id=chat_id,
            message=message,
            random_id=random_id
        )


def main():
    bot = BOT()
    if not bot.session or not bot.api:
        raise Exception('API или Сессия не получены')
    longpoll = VkLongPoll(bot.session)
    
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW:
            text = event.text.split()
            chat_id = event.peer_id
            user_id = event.user_id
            msg_time = event.timestamp
            author = str(user_id)
            # Некому ответить, просто логируем
            if not chat_id or not user_id:
                print('chat_id: {} \n user_id: {}'.format(chat_id, user_id))
                continue
            # Если обратились к боту
            if text and BOT_NAME in text[0].lower():
                message = ' '.join(text[1:])
                if len(text) > 2 and 'добавь' in text[1].lower():
                    phrase = ' '.join(text[2:])
                    rewrite_file(phrase, bot.bot_phrases)
                    affirmation = '[id'+author+'|Филтан], я добавил: "'+phrase+'"'
                    bot.send_message(chat_id, affirmation)
                else:
                    phrase = request_df(bot.token, text)
                    bot.send_message(chat_id, phrase)
            else:              
                if not user_id in bot.shitposters:
                    bot.shitposters[user_id] = Shitposter(user_id, msg_time)
                else:
                    user = bot.shitposters[user_id]
                    if msg_time - user.first_msg_time > 180:
                        user.first_msg_time = msg_time
                        user.shitpost_count = 0
                    if user.shitpost_count >= 7:
                        phrase = random.choice(bot.bot_phrases)
                        bot.send_message(chat_id, phrase)
                        dt = strftime("%d.%m.%Y %H:%M:%S", localtime())
                        print(dt + ' / ' + str(user.user_id) + ' shitposted in chat #' + str(chat_id) + '!')
                        user.shitpost_count = 0
                    user.inc_counter()


if __name__ == "__main__":
    while not IS_ERROR:
        try:
            main()
        except Exception as e:
            IS_ERROR = True
            print('PIZDARIQUE')
            print(e)
            print(strftime("%d.%m.%Y %H:%M:%S", localtime()))
            pass
