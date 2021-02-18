import os
import logging

from application import create_app

config_name = os.getenv("APP_SETTINGS")
app = create_app(config_name)

if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

if __name__ == "__main__":
    app.run()