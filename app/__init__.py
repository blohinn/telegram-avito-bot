import logging

from flask import Flask

from config import Config


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    app.logger.setLevel(logging.INFO)
    if not config_class.TESTING and config_class.TG_TOKEN:
        from app.bot import Bot
        Bot(Config.TG_TOKEN, Config.BOT_USERS, app).start()
    else:
        print("App is not configured. Check config.py")
    return app
