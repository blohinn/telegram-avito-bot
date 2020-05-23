import telebot
import db
import utils
import os

API_TOKEN = os.environ.get('BOT_API_TOKEN')

if not API_TOKEN:
    raise KeyError('Telegram bot token missed')


# telebot.apihelper.proxy = {'https': 'https://nl-132-134-226.fri-gate0.org:443'}
# telebot.apihelper.proxy = {'https': 'socks5h://213.136.89.190:13006'}
# telebot.apihelper.proxy = {'https': 'socks5h://75.119.217.119:49244'}
# telebot.apihelper.proxy = {'https': 'socks5h://72.11.148.222:56533'}
# telebot.apihelper.proxy = {'https': 'socks5h://45.63.97.27:31801'}
# telebot.apihelper.proxy = {'https': 'socks5://itg:yhMU6OtfTzapED736fUY@78.46.149.44:1080'}
# print(telebot.apihelper.proxy)

bot = telebot.TeleBot(API_TOKEN)


@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    msg = bot.send_message(message.chat.id, 'Данный бот следит за объявлениями по указанным ссылкам '
                                            'и присылает новые. '
                                            '\nНажмите на значек "/" для просмотра доступных команд.')


# # # Adding search # # #
@bot.message_handler(commands=['add'])
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
        bot.send_message(message.chat.id, 'Ссылка {} сохранена под именем "{}".'.format(search_url, search_name))
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
@bot.message_handler(commands=['delete'])
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
@bot.message_handler(commands=['list'])
def send_list(message):
    send_tracking_urls_list(message.chat.id)


# # # End send list of tracking urls # # #


if __name__ == '__main__':
    print("start polling...")
    bot.polling(none_stop=True)
