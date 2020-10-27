import subprocess

from config import Config

if Config.WEBHOOK_ENABLE == '0':
    bashCommand = "gunicorn bot:app -k eventlet".format
else:
    bashCommand = "gunicorn --certfile {0} --keyfile {1} -b {2}:{3} bot:app -k eventlet".format(
        Config.WEBHOOK_SSL_CERT, Config.WEBHOOK_SSL_PRIV, Config.WEBHOOK_LISTEN, Config.WEBHOOK_PORT
    )
process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
output, error = process.communicate()
