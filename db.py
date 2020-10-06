from pymongo import MongoClient

# client = MongoClient('mongodb://{}:{}@ds213759.mlab.com:13759/monogoosito'.format('bot', 'emilbotavito'))
# client = MongoClient('mongodb://{}:{}@localhost:27017/monogoosito'.format('bot', 'bot'))
# client = MongoClient('mongodb', 27017)
client = MongoClient('localhost', 27017)
db = client['mongoosito']
search_collection = db['search_collection']
search_url_and_name_interlayer = db['url_name_interlayer']


def save_url_to_temp(uid, url):
    _remove_url_from_temp(uid)
    return search_url_and_name_interlayer.insert_one({'uid': uid, 'url': url})


def _remove_url_from_temp(uid):
    search_url_and_name_interlayer.delete_many({'uid': uid})


def get_temp_url(uid):
    url = search_url_and_name_interlayer.find_one({'uid': uid})
    _remove_url_from_temp(uid)
    return url['url']


def save_url(uid, search_url, search_name):
    """
    :param uid: идентификатор чата
    :param search_url: название для поиска, например "Поиск машины для клиента"
    :param search_name: отслеживаемая ссылка, например: https://avito.ru/kazan/avto/vaz
    :return boolean: запись добавлена / не добавлена (ошибка бд)
    """
    from app import parserr
    try:
        search_collection.update_one({'uid': uid}, {'$push': {'tracking_urls': {
            'url': search_url,
            'name': search_name,
            'ads': parserr.get_ads_list(search_url)
        }}}, upsert=True)
        return True
    except:
        return False


def is_link_already_tracking_by_user(uid, search_url):
    try:
        user_urls = search_collection.find_one({'uid': uid})
    except:
        raise Exception

    if user_urls is None or 'tracking_urls' not in user_urls:
        return False

    for _ in user_urls['tracking_urls']:
        if _['url'] == search_url:
            return True

    return False


def get_search_collection_entries():
    return list(search_collection.find({}))


def get_users_tracking_urls_list(uid):
    """
    :param uid: telegram user id
    :return: list of dicts [{'url': '', 'name': ''}]
    """
    user = search_collection.find_one({'uid': uid})

    if not user:
        return None

    tracking_urls = user['tracking_urls']

    _ = []
    for u in tracking_urls:
        _.append({
            'url': u['url'],
            'name': u['name']
        })
    return _


def delete_url_from_tracking(uid, human_index):
    """
    :param uid:
    :param human_index: > 0, [12, 45, 17] human_index = 1 : 12, human_index = 3 : 17
    :return: boolean
    """
    user = search_collection.find_one({'uid': uid})

    if not user:
        return None

    tracking_urls = user['tracking_urls']
    try:
        del tracking_urls[human_index - 1]
        search_collection.update_one({'uid': uid}, {'$set': {
            'tracking_urls': tracking_urls
        }})
        return True
    except:
        return False


def set_actual_ads(uid, tracking_urls):
    search_collection.update_one({'uid': uid}, {'$set': {
        'tracking_urls': tracking_urls
    }})
