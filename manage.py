import os
import unittest

from flask_script import Manager # class for handling a set of commands
from flask_migrate import Migrate, MigrateCommand
from application import db, create_app
from application import models

from dotenv import load_dotenv
load_dotenv()

app = create_app(config_name=os.environ.get('APP_SETTINGS'))
migrate = Migrate(app, db)
manager = Manager(app)

manager.add_command('db', MigrateCommand)

# define  command for testing
@manager.command
def test():
    """Runs the unit tests without test coverage"""
    tests = unittest.TestLoader().discover('./tests', pattern="test*.py")
    result = unittest.TextTestRunner(verbosity=2).run(tests)
    if result.wasSuccessful():
        return 0
    return 1

if __name__ == '__main__':
    manager.run()