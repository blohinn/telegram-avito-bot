import datetime
import threading
import time

import flask
import telebot

import db
import utils
from app.parserr import get_ads_list, get_new_ads
from config import Config


class Bot(threading.Thread):

    def __init__(self, tg_token, bot_users, app):
        super().__init__()
        self.tg_token = tg_token
        self.app = app
        self.bot_users = bot_users
        self.l = app.logger
        self.bot = telebot.TeleBot(self.tg_token)
        self.photo_warn_last_time = 0
        self.photo_warn_timeout = 60

    def run(self):
        self.l.info("Bot starting")
        self.init_commands()
        self.use_webhooks(Config.WEBHOOK_ENABLE)

    def use_webhooks(self, value):
        bot = self.bot
        app = self.app
        bot.remove_webhook()
        time.sleep(0.1)
        if value:
            if not Config.WEBHOOK_HOST:
                raise Exception("WEBHOOK_HOST is not defined")

            @app.route('/', methods=['GET', 'HEAD'])
            def index():
                return ''

            @app.route(Config.WEBHOOK_URL_PATH, methods=['POST'])
            def webhook():
                if flask.request.headers.get('content-type') == 'application/json':
                    json_string = flask.request.get_data().decode('utf-8')
                    update = telebot.types.Update.de_json(json_string)
                    bot.process_new_updates([update])
                    self.l.debug("hook: " + json_string)
                    return ''
                else:
                    flask.abort(403)

            bot.set_webhook(url=Config.WEBHOOK_URL_BASE + Config.WEBHOOK_URL_PATH,
                            certificate=open(Config.WEBHOOK_SSL_CERT, 'r'))
        else:
            while (True):
                try:
                    bot.polling(none_stop=True)
                except BaseException as e:
                    self.l.error(e)
                    time.sleep(30)
        self.l.info("Webhook enabled: " + str(value))

    def init_commands(self):
        bot = self.bot
        app = self.app

        def is_allowed(message):
            return message.chat.title is None and (self.bot_users is None or message.from_user.id in self.bot_users)

        @bot.message_handler(commands=['help', 'start'], func=lambda message: is_allowed(message))
        def send_welcome(message):
            msg = bot.send_message(message.chat.id, 'Данный бот следит за объявлениями по указанным ссылкам '
                                                    'и присылает новые. '
                                                    '\nНажмите на значек "/" для просмотра доступных команд.')

        # # # Adding search # # #
        @bot.message_handler(commands=['add'], func=lambda message: is_allowed(message))
        def add_search(message):
            bot.send_message(message.chat.id,
                             'Укажите ссылку на поисковую выдачу Avito с нужными Вам фильтрами.\n'
                             'Пример:\n'
                             'https://m.avito.ru/kazan/avtomobili/s_probegom/toyota?i=1\n'
                             '(Автомобили с пробегом марки Toyota в Казани).\n'
                             'Обратите внимание на то, что используется мобильная версия Avito.\n',
                             disable_web_page_preview=True)
            bot.send_message(message.chat.id, 'Если вы используете полноценную версию - добавьте `.m` в начале ссылки.',
                             parse_mode='markdown')
            msg = bot.send_message(message.chat.id, 'Ожидаю ссылку...')

            bot.register_next_step_handler(msg, waiting_url_step)

        # Waiting url
        def waiting_url_step(message):
            search_url = message.text
            # На случай, если пользователь отравит такое сообщение: "https://avito.ru/kazan/avto/vaz бла бла"
            search_url = search_url.split(' ')[0]

            if not utils.check_avito_url(search_url):
                msg = bot.send_message(message.chat.id, 'Неккоректная ссылка.')
                return

            try:
                if db.is_link_already_tracking_by_user(message.chat.id, search_url):
                    bot.send_message(message.chat.id, 'Вы уже отслеживаете данную ссылку.')
                    return
            except:
                msg = bot.send_message(message.chat.id, 'Ошибка сервера. Повторите попытку позже.')
                return

            try:
                search_url = search_url.split(' ')[0]
                db.save_url_to_temp(message.chat.id, search_url)
            except:
                msg = bot.send_message(message.chat.id, 'Ошибка сервера. Повторите попытку позже.')
                return

            msg = bot.send_message(message.chat.id, 'Укажите название для поиска. Например: "Лодки в Самаре".')
            bot.register_next_step_handler(msg, select_search_name_step)

        # Waiting name for tracking results
        def select_search_name_step(message):
            search_name = message.text
            # TODO Validate title (search_name)
            try:
                search_url = db.get_temp_url(message.chat.id)
            except:
                bot.send_message(message.chat.id, 'Ошибка сервера. Повторите попытку позже.')
                return

            if db.save_url(message.chat.id, search_url, search_name):
                bot.send_message(message.chat.id,
                                 'Ссылка {} сохранена под именем "{}".'.format(search_url, search_name))
                bot.send_message(message.chat.id, 'Теперь вы будете получать уведомления о новых объявлениях.')

            else:
                bot.send_message(message.chat.id, 'Произошла ошибка при добавлении. Повторите ошибку позже.')

        # # # End adding search # # #

        def send_tracking_urls_list(uid):
            user_tracking_urls_list = db.get_users_tracking_urls_list(uid)

            if not user_tracking_urls_list:
                bot.send_message(uid, 'Вы не ничего отслеживаете.')
                return

            msg = ''
            i = 1
            for url in user_tracking_urls_list:
                msg += str(i) + '. ' + url['name'] + '\n'
                msg += url['url'] + '\n'
                i += 1

            bot.send_message(uid, msg, disable_web_page_preview=True)

        # # # Deleting search # # #
        @bot.message_handler(commands=['delete'], func=lambda message: is_allowed(message))
        def deleting_search(message):
            if not db.get_users_tracking_urls_list(message.chat.id):
                bot.send_message(message.chat.id, 'Вы ничего не отслеживаете.')
                return
            send_tracking_urls_list(uid=message.chat.id)
            msg = bot.send_message(message.chat.id, 'Отправьте порядковый номер удаляемой ссылки.')
            bot.register_next_step_handler(msg, waiting_num_to_delete)

        def waiting_num_to_delete(message):
            try:
                delete_url_index_in_list = int(message.text)
            except:
                bot.send_message(message.chat.id, 'Отправьте только число.')
                return

            if delete_url_index_in_list <= 0:
                bot.send_message(message.chat.id, 'Порядковый номер должен быть больше нуля.')
                return

            if db.delete_url_from_tracking(message.chat.id, delete_url_index_in_list):
                bot.send_message(message.chat.id, 'Ссылка удалена из отслеживаемых.')
            else:
                bot.send_message(message.chat.id, 'Ошибка сервера. Повторите попытку позже.')

        # # # End deleting search # # #

        # # # Send list of tracking urls # # #
        @bot.message_handler(commands=['list'], func=lambda message: is_allowed(message))
        def send_list(message):
            send_tracking_urls_list(message.chat.id)

        # # # End send list of tracking urls # # #

        MSG = "{0}: {1}\n{2}\n{3}\n{4}"

        def send_updates():
            sce = db.get_search_collection_entries()

            for i in sce:
                tracking_urls = []
                for url in i['tracking_urls']:
                    old_ads = url['ads']
                    self.l.debug("handling updates for " + url['name'])
                    actual_ads = get_ads_list(url['url'], self.l)
                    while not actual_ads:
                        time.sleep(5)
                        actual_ads = get_ads_list(url['url'], self.l)
                    self.l.debug(f'parsed ads count = {len(actual_ads)}')
                    new_ads = get_new_ads(actual_ads, old_ads)
                    if new_ads:
                        self.l.info(f'new_ads count = {len(new_ads)}')

                    for n_a in new_ads:
                        msg = MSG.format(url['name'], n_a['title'].rstrip(), n_a['price'].rstrip(),
                                         n_a['created'].rstrip(),
                                         n_a['url'])

                        # if n_a['img']:
                        #     from utils import get_img_file_by_url
                        #
                        #     img_file = get_img_file_by_url(n_a['img'])
                        #     if img_file:
                        #         bot.send_photo(i['uid'], img_file)

                        bot.send_message(i['uid'], msg)

                    timestamp = int(time.time())

                    filtered = [u for u in old_ads if 'parsed' in u and u['parsed'] + 604800 > timestamp]
                    url['ads'] = filtered
                    url['ads'].extend(new_ads)
                    self.l.debug(f"ads in db {str(len(url['ads']))}")
                    tracking_urls.append(url)

                    import random
                    time.sleep(random.randint(1, 15) / 10)
                db.set_actual_ads(i['uid'], tracking_urls)

        def in_between(now, start, end):
            if start <= end:
                return start <= now < end
            else:
                return start <= now or now < end

        def send_updates_thread():
            import schedule

            send_updates()
            schedule.every(Config.PARSING_INTERVAL_SEC).seconds.do(send_updates)

            while True:
                schedule.run_pending()
                cur_time = datetime.datetime.now().time()
                if in_between(cur_time, datetime.time(Config.SLEEP_START),
                              datetime.time(Config.SLEEP_END)):
                    self.l.info(f"It's ime to sleep for {str(Config.SLEEP_TIME)} hours!")
                    time.sleep(3600 * Config.SLEEP_TIME)  # not accurate
                    self.l.info("Bot is waking up")
                else:
                    time.sleep(1)

        thread = threading.Thread(target=send_updates_thread)
        thread.start()
