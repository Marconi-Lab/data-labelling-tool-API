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

    def test_get_user_stats(self):
        """Test if API can retrieve user's statistics summary"""
        # Create user
        res = self.client().post('/auth/register/', data=self.user_data)
        self.assertEqual(res.status_code, 201)

        rv = self.client().get('/user/1/home/')
        self.assertEqual(rv.status_code, 200)
        self.assertIn("images", str(rv.data))
        self.assertIn("datasets", str(rv.data))

    def test_get_user_datasets(self):
        """Test if API can retrieve user assigned datasets"""
        # Create user
        res = self.client().post('/auth/register/', data=self.user_data[0])
        self.assertEqual(res.status_code, 201)
        # Create Dataset
        res1 = self.client().post('/admin/datasets/', data=self.dataset)
        self.assertEqual(res1.status_code, 201)
        # Assign dataset
        res2 = self.client().post('/admin/users/1/assignments/', data={"dataset_id": "1"})
        self.assertEqual(res2.status_code, 201)

        rv = self.client().get("/user/1/datasets/")
        self.assertEqual(rv.status_code, 200)
        self.assertIn("Cervical Infection", str(rv.data))

    def tearDown(self):
        """Teardown all initialized variables"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

if __name__ == "__main__":
    unittest.main()