import unittest
import json
from application import create_app, db

class AuthTestCase(unittest.TestCase):
    """Test case for the user blueprint"""

    def setUp(self):
        self.app = create_app(config_name="testing")
        
        self.client = self.app.test_client

         self.admin_data = {
            'username': "Admin",
            'email': 'test@example.com',
            'password': 'test_password'
        }
        self.dataset = {'name': 'Cervical Infection', 'classes': ["Positive", "Negative", "Not Sure"]}
        self.images = [
            (io.BytesIO(b"abcdef"), 'test.jpg'),
            (io.BytesIO(b"abcdef"), 'test1.jpg'),
            (io.BytesIO(b"abcdef"), 'test3.jpg'),
            (io.BytesIO(b"abcdef"), 'test4.jpg')
        ]
        self.user_data = {
            'username': "User",
            'email': 'user@example.com',
            'password': 'test_password'
        }

        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        """Teardown all initialized variables"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

if __name__ == "__main__":
    unittest.main()