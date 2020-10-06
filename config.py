import os

from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config(object):
    TG_TOKEN = os.environ.get('TG_TOKEN')
    TEMP = os.environ.get('TEMP') or os.path.join(basedir, 'temp')
    BOT_USERS = [int(user_id) for user_id in os.environ.get('BOT_USERS').split(",")] if os.environ.get(
        'BOT_USERS') else None  # Users IDs; None == any user

    TESTING = False
    if os.environ.get('WEBHOOK_ENABLE') == '0':
        WEBHOOK_ENABLE = False
    else:
        WEBHOOK_ENABLE = True
    WEBHOOK_HOST = os.environ.get('WEBHOOK_HOST')
    WEBHOOK_PORT = os.environ.get('WEBHOOK_PORT') or 8443  # 443, 80, 88 or 8443 (port need to be 'open')
    WEBHOOK_LISTEN = os.environ.get('WEBHOOK_LISTEN') or '0.0.0.0'  # In some VPS you may need to put here the IP addr

    WEBHOOK_SSL_CERT = os.environ.get(
        'WEBHOOK_SSL_CERT') or basedir + '/webhook_cert.pem'  # Path to the ssl certificate
    WEBHOOK_SSL_PRIV = os.environ.get(
        'WEBHOOK_SSL_PRIV') or basedir + '/webhook_pkey.pem'  # Path to the ssl private key

    WEBHOOK_URL_BASE = os.environ.get('WEBHOOK_URL_BASE') or "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
    WEBHOOK_URL_PATH = os.environ.get('WEBHOOK_URL_PATH') or "/%s/" % (TG_TOKEN)
