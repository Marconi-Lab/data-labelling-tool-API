import unittest
import json
from application import create_app, db
import io


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
            'password': 'test_password',
            "is_admin": ''
        }

        with self.app.app_context():
            db.create_all()

    def register_admin(
            self,
            email="admin@test.com",
            password="test1234",
            is_admin="admin",
            username="Admin",
    ):
        """Helper method for registering admin"""
        admin_data = {
            "email": email,
            "password": password,
            "is_admin": is_admin,
            "username": username,
        }
        return self.client().post("/auth/register/", data=admin_data)

    def login_admin(self, email="admin@test.com", password="test1234"):
        """Helper method for admin log in"""
        admin_data = {"email": email, "password": password}
        return self.client().post("/auth/login/", data=admin_data)

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
        self.register_admin()
        login_res = self.login_admin()
        self.assertEqual(login_res.status_code, 200)
        access_token = json.loads(login_res.data.decode())["access_token"]
        is_admin = bool(json.loads(login_res.data.decode())["is_admin"])

        # Create user
        res = self.client().post('/auth/register/', data=self.user_data)
        self.assertEqual(res.status_code, 201)
        # Create Dataset
        res1 = self.client().post('/admin/datasets/', data=self.dataset,
                                  headers=dict(Authorization="Bearer " + access_token, is_admin=is_admin))
        self.assertEqual(res1.status_code, 201)
        # Assign dataset
        res2 = self.client().post('/admin/users/1/assignments/', data={"dataset_id": "1"}, headers=dict(Authorization="Bearer " + access_token, is_admin=is_admin))
        self.assertEqual(res2.status_code, 201)

        rv = self.client().get("/user/1/datasets/")
        self.assertEqual(rv.status_code, 200)
        self.assertIn("Cervical Infection", str(rv.data))

    def test_user_get_dataset_items(self):
        """Test if API can retrieve all data items in a specific class"""
        self.register_admin()
        login_res = self.login_admin()
        self.assertEqual(login_res.status_code, 200)
        access_token = json.loads(login_res.data.decode())["access_token"]
        is_admin = bool(json.loads(login_res.data.decode())["is_admin"])

        # Create user
        res = self.client().post('/auth/register/', data=self.user_data)
        self.assertEqual(res.status_code, 201)
        # Upload dataset
        dataset_res = self.client().post('/admin/datasets/', data=self.dataset,
                                         headers=dict(Authorization="Bearer " + access_token, is_admin=is_admin))
        self.assertEqual(dataset_res.status_code, 201)
        dataset_json = json.loads(dataset_res.data.decode())

        # Upload item
        item_res = self.client().post('/admin/datasets/item/',
                                      data={"dataset_id": dataset_json['id'], "images": self.images},
                                      content_type="multipart/form-data",
                                      headers=dict(Authorization="Bearer " + access_token, is_admin=is_admin))
        self.assertEqual(item_res.status_code, 201)
        # Get items
        rv = self.client().get("/user/datasets/1/", data={"dataset_id": dataset_json["id"]})

        self.assertEqual(rv.status_code, 200)
        self.assertIn("items", str(rv.data))

    def test_item_get_with_id(self):
        """Test if API can get item by it's id"""
        self.register_admin()
        login_res = self.login_admin()
        self.assertEqual(login_res.status_code, 200)
        access_token = json.loads(login_res.data.decode())["access_token"]
        is_admin = bool(json.loads(login_res.data.decode())["is_admin"])

        # Create user
        res = self.client().post('/auth/register/', data=self.user_data)
        self.assertEqual(res.status_code, 201)
        # Upload dataset
        dataset_res = self.client().post('/admin/datasets/', data=self.dataset,
                                         headers=dict(Authorization="Bearer " + access_token, is_admin=is_admin))
        self.assertEqual(dataset_res.status_code, 201)
        dataset_json = json.loads(dataset_res.data.decode())

        # Upload item
        item_res = self.client().post('/admin/datasets/item/',
                                      data={"dataset_id": dataset_json['id'], "images": self.images},
                                      content_type="multipart/form-data",
                                      headers=dict(Authorization="Bearer " + access_token, is_admin=is_admin))
        item_json = json.loads(item_res.data.decode())
        # Retrieve item with id
        rv = self.client().get('/user/datasets/item/1/')

        self.assertEqual(rv.status_code, 200)
        self.assertIn("images", str(rv.data))

    def test_user_label_item(self):
        """Test if API can label item"""
        self.register_admin()
        login_res = self.login_admin()
        self.assertEqual(login_res.status_code, 200)
        access_token = json.loads(login_res.data.decode())["access_token"]
        is_admin = bool(json.loads(login_res.data.decode())["is_admin"])

        # Create user
        res = self.client().post('/auth/register/', data=self.user_data)
        self.assertEqual(res.status_code, 201)
        # Upload dataset
        dataset_res = self.client().post('/admin/datasets/', data=self.dataset,
                                         headers=dict(Authorization="Bearer " + access_token, is_admin=is_admin))
        self.assertEqual(dataset_res.status_code, 201)
        dataset_json = json.loads(dataset_res.data.decode())

        # Upload item
        item_res = self.client().post('/admin/datasets/item/',
                                      data={"dataset_id": dataset_json['id'], "images": self.images},
                                      content_type="multipart/form-data",
                                      headers=dict(Authorization="Bearer " + access_token, is_admin=is_admin))
        item_json = json.loads(item_res.data.decode())
        # Retrieve item with id
        rv = self.client().put('/user/datasets/item/1/',
                               data={"label": "not sure", "comment": "No comments", "labeller": "1"},
                               headers=dict(Authorization="Bearer " + access_token, is_admin=is_admin))
        self.assertEqual(rv.status_code, 200)
        results = self.client().get("/user/datasets/item/1/",
                                    headers=dict(Authorization="Bearer " + access_token, is_admin=is_admin))
        self.assertIn("not sure", str(results.data))

    def tearDown(self):
        """Teardown all initialized variables"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()


if __name__ == "__main__":
    unittest.main()
