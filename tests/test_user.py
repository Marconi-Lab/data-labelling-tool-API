import io
import json
import unittest

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
        self.image = (io.BytesIO(b"abcdef"), "test4.jpg")
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

    def register_user(
            self,
            email="user@test.com",
            password="test1234",
            is_admin="",
            username="User",
    ):
        """Helper method for registering admin"""
        user_data = {
            "email": email,
            "password": password,
            "is_admin": is_admin,
            "username": username,
        }
        return self.client().post("/auth/register/", data=user_data)

    def login_admin(self, email="admin@test.com", password="test1234"):
        """Helper method for admin log in"""
        admin_data = {"email": email, "password": password}
        return self.client().post("/auth/login/", data=admin_data)

    def login_user(self, email="user@test.com", password="test1234"):
        """Helper method for admin log in"""
        user_data = {"email": email, "password": password}
        return self.client().post("/auth/login/", data=user_data)

    def admin_headers(self):
        self.register_admin()
        login_res = self.login_admin()
        self.assertEqual(login_res.status_code, 200)
        access_token = json.loads(login_res.data.decode())["access_token"]
        is_admin = bool(json.loads(login_res.data.decode())["is_admin"])
        user_id = json.loads(login_res.data.decode())["id"]
        return dict(Authorization="Bearer " + access_token, is_admin=is_admin, user_id=user_id)

    def user_headers(self):
        self.register_user()
        login_res = self.login_user()
        self.assertEqual(login_res.status_code, 200)
        access_token = json.loads(login_res.data.decode())["access_token"]
        is_admin = bool(json.loads(login_res.data.decode())["is_admin"])
        user_id = json.loads(login_res.data.decode())["id"]
        return dict(Authorization="Bearer " + access_token, is_admin=is_admin, user_id=user_id)

    def test_get_user_stats(self):
        """Test if API can retrieve user's statistics summary"""
        # Create user
        res = self.client().post('/auth/register/', data=self.user_data, headers=self.user_headers())
        self.assertEqual(res.status_code, 201)

        rv = self.client().get('/user/1/home/', headers=self.user_headers())
        self.assertEqual(rv.status_code, 200)
        self.assertIn("images", str(rv.data))
        self.assertIn("datasets", str(rv.data))

    def test_get_user_datasets(self):
        """Test if API can retrieve user assigned datasets"""

        # Create user
        res = self.client().post('/auth/register/', data=self.user_data)
        self.assertEqual(res.status_code, 201)
        # Create Dataset
        res1 = self.client().post('/admin/datasets/', data=self.dataset,
                                  headers=self.admin_headers())
        self.assertEqual(res1.status_code, 201)
        # Assign dataset
        res2 = self.client().post('/admin/users/1/assignments/', data={"dataset_id": "1"},
                                  headers=self.admin_headers())
        self.assertEqual(res2.status_code, 201)

        rv = self.client().get("/user/1/datasets/", headers=self.user_headers())
        self.assertEqual(rv.status_code, 200)
        self.assertIn("Cervical Infection", str(rv.data))

    def test_user_get_dataset_items(self):
        """Test if API can retrieve all data items in a specific class"""

        # Create user
        res = self.client().post('/auth/register/', data=self.user_data)
        self.assertEqual(res.status_code, 201)
        # Upload dataset
        dataset_res = self.client().post('/admin/datasets/', data=self.dataset,
                                         headers=self.admin_headers())
        self.assertEqual(dataset_res.status_code, 201)
        dataset_json = json.loads(dataset_res.data.decode())

        # Upload item
        item_res = self.client().post(f"/admin/{dataset_json['id']}/item/",
                                      data={"name": "item"},
                                      headers=self.admin_headers())
        self.assertEqual(item_res.status_code, 201)
        # Get items
        rv = self.client().get("/user/datasets/1/", data={"dataset_id": dataset_json["id"]},
                               headers=self.user_headers())

        self.assertEqual(rv.status_code, 200)
        self.assertIn("items", str(rv.data))

    def test_item_get_with_id(self):
        """Test if API can get item by it's id"""

        # Create user
        res = self.client().post('/auth/register/', data=self.user_data)
        self.assertEqual(res.status_code, 201)
        # Upload dataset
        dataset_res = self.client().post('/admin/datasets/', data=self.dataset,
                                         headers=self.admin_headers())
        self.assertEqual(dataset_res.status_code, 201)
        dataset_json = json.loads(dataset_res.data.decode())

        # Upload item
        item_res = self.client().post(f"/admin/{dataset_json['id']}/item/",
                                      data={"name": "item"},
                                      headers=self.admin_headers())
        item_json = json.loads(item_res.data.decode())
        # Retrieve item with id
        rv = self.client().get('/user/item/1/', headers=self.user_headers())

        self.assertEqual(rv.status_code, 200)
        self.assertIn("images", str(rv.data))

    def test_user_label_item(self):
        """Test if API can label item"""
        # Create user
        res = self.client().post('/auth/register/', data=self.user_data)
        self.assertEqual(res.status_code, 201)
        # Upload dataset
        dataset_res = self.client().post('/admin/datasets/', data=self.dataset,
                                         headers=self.admin_headers())
        self.assertEqual(dataset_res.status_code, 201)
        dataset_json = json.loads(dataset_res.data.decode())

        # Upload item
        item_res = self.client().post(f"/admin/{dataset_json['id']}/item/",
                                      data={"name":"item"},
                                      headers=self.admin_headers())
        item_json = json.loads(item_res.data.decode())
        # Retrieve item with id
        rv = self.client().put('/user/item/1/',
                               data={"label": "not sure", "comment": "No comments", "labeller": "1"},
                               headers=self.user_headers())
        self.assertEqual(rv.status_code, 200)
        results = self.client().get("/user/item/1/",
                                    headers=self.user_headers())
        self.assertIn("not sure", str(results.data))

    # def test_user_get_image_by_id(self):
    #     """Testing if user can retrieve image by its id"""
    #     # Create user
    #     res = self.client().post('/auth/register/', data=self.user_data)
    #     self.assertEqual(res.status_code, 201)
    #     # Upload dataset
    #     dataset_res = self.client().post('/admin/datasets/', data=self.dataset,
    #                                      headers=self.admin_headers())
    #     self.assertEqual(dataset_res.status_code, 201)
    #     dataset_json = json.loads(dataset_res.data.decode())
    #
    #     # Upload item
    #     image_res = self.client().post('/admin/datasets/images/',
    #                                   data={"dataset_id": dataset_json["id"], "image": self.image},
    #                                   content_type="multipart/form-data",
    #                                   headers=self.admin_headers())
    #     self.assertEqual(image_res.status_code, 201)
    #     # Retrieve item with id
    #     rv = self.client().get('/user/images/1/', headers=self.user_headers())
    #
    #     self.assertEqual(rv.status_code, 200)
    #     self.assertIn("image", str(rv.data))
    #
    # def test_user_label_image(self):
    #     """Test if user can label image"""
    #     # Upload dataset
    #     dataset_res = self.client().post('/admin/datasets/', data=self.dataset,
    #                                      headers=self.admin_headers())
    #     self.assertEqual(dataset_res.status_code, 201)
    #     dataset_json = json.loads(dataset_res.data.decode())
    #
    #     # Upload image
    #     item_res = self.client().post(
    #         "/admin/datasets/images/",
    #         data={"dataset_id": dataset_json["id"], "image": self.image},
    #         content_type="multipart/form-data",
    #         headers=self.admin_headers()
    #     )
    #     item_json = json.loads(item_res.data.decode())
    #
    #     # Retrieve item with id
    #     rv = self.client().put('/user/images/1/',
    #                            data={"label": "not sure", "labeller": "1"},
    #                            headers=self.user_headers())
    #     print("Response", rv.data)
    #     self.assertEqual(rv.status_code, 200)
    #     results = self.client().get("/user/images/1/",
    #                                 headers=self.user_headers())
    #     self.assertIn("not sure", str(results.data))


    def tearDown(self):
        """Teardown all initialized variables"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()


if __name__ == "__main__":
    unittest.main()
