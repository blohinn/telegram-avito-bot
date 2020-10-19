import os

from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config(object):
    TG_TOKEN = os.environ.get('TG_TOKEN')
    TEMP = os.environ.get('TEMP') or os.path.join(basedir, 'temp')
    BOT_USERS = [int(user_id) for user_id in os.environ.get('BOT_USERS').split(",")] if os.environ.get(
        'BOT_USERS') else None  # Users IDs; None == any user

    PARSING_INTERVAL_SEC = 60 if not os.environ.get('PARSING_INTERVAL_SEC') else int(os.environ.get('PARSING_INTERVAL_SEC'))
    REQUEST_TIMEOUT = 5 if not os.environ.get('REQUEST_TIMEOUT') else int(os.environ.get('REQUEST_TIMEOUT'))

    SLEEP_START = 1 if not os.environ.get('SLEEP_START') else int(os.environ.get('SLEEP_START'))
    SLEEP_END = 10 if not os.environ.get('SLEEP_END') else int(os.environ.get('SLEEP_END'))
    if SLEEP_START > SLEEP_END:
        SLEEP_TIME = 24 % SLEEP_START + SLEEP_END
    else:
        SLEEP_TIME = SLEEP_END - SLEEP_START

    TESTING = False
    if os.environ.get('WEBHOOK_ENABLE') == '0':
        WEBHOOK_ENABLE = False
    else:
        WEBHOOK_ENABLE = True

    if os.environ.get('MONGO_HOST'):
        MONGO_HOST = os.environ.get('MONGO_HOST')
    else:
        MONGO_HOST = "mongodb"
    WEBHOOK_HOST = os.environ.get('WEBHOOK_HOST')
    WEBHOOK_PORT = os.environ.get('WEBHOOK_PORT') or 88  # 443, 80, 88 or 8443 (port need to be 'open')
    WEBHOOK_LISTEN = os.environ.get('WEBHOOK_LISTEN') or '0.0.0.0'  # In some VPS you may need to put here the IP addr

    WEBHOOK_SSL_CERT = os.environ.get(
        'WEBHOOK_SSL_CERT') or basedir + '/webhook_cert.pem'  # Path to the ssl certificate
    WEBHOOK_SSL_PRIV = os.environ.get(
        'WEBHOOK_SSL_PRIV') or basedir + '/webhook_pkey.pem'  # Path to the ssl private key

    WEBHOOK_URL_BASE = os.environ.get('WEBHOOK_URL_BASE') or "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
    WEBHOOK_URL_PATH = os.environ.get('WEBHOOK_URL_PATH') or "/%s/" % (TG_TOKEN)
