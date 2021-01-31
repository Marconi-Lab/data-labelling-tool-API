import json
import unittest

from application import create_app, db


class AuthTestCase(unittest.TestCase):
    """Test case for the admin blueprint"""

    def setUp(self):
        """Set up test variables"""
        self.app = create_app(config_name="testing")
        # initialize the test client
        self.client = self.app.test_client

        self.user_data = {
            "username": "Admin",
            "email": "test@example.com",
            "password": "test_password",
        }
        self.dataset = {
            "name": "Cervical Infection",
            "classes": ["Positive", "Negative", "Not Sure"],
        }
        self.item = {}

        # Binds application to current context
        with self.app.app_context():
            # create all tables
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

    def admin_headers(self):
        self.register_admin()
        login_res = self.login_admin()
        self.assertEqual(login_res.status_code, 200)
        access_token = json.loads(login_res.data.decode())["access_token"]
        is_admin = bool(json.loads(login_res.data.decode())["is_admin"])
        user_id = json.loads(login_res.data.decode())["id"]
        return dict(Authorization="Bearer " + access_token, is_admin=is_admin, user_id=user_id)

    def test_dataset_creation(self):
        """Test if API can create a dataset. (POST request)"""

        res = self.client().post(
            "/admin/datasets/",
            data=self.dataset,
            headers=self.admin_headers()
        )
        print("Res: ", res)
        self.assertEqual(res.status_code, 201)
        self.assertIn("Cervical Infection", str(res.data))

    def test_api_can_get_all_datasets(self):
        """Test if API can get all datasets. (GET request)"""

        res = self.client().post("/admin/datasets/", data=self.dataset,
                                 headers=self.admin_headers())
        self.assertEqual(res.status_code, 201)

        res1 = self.client().get("/admin/datasets/",
                                headers=self.admin_headers())
        self.assertEqual(res1.status_code, 200)
        self.assertIn("Cervical Infection", str(res.data))

    def test_api_can_get_dataset_by_id(self):
        """Test if API can get dataset by it's id"""

        res = self.client().post("/admin/datasets/", data=self.dataset,
                                 headers=self.admin_headers())
        self.assertEqual(res.status_code, 201)
        json_res = json.loads(res.data.decode("utf-8").replace("'", '"'))
        result = self.client().get("/admin/datasets/{}".format(json_res["id"]),
                                   headers=self.admin_headers())
        self.assertEqual(result.status_code, 200)
        self.assertIn("Cervical Infection", str(result.data))
        self.assertIn("progress", str(result.data))

    def test_dataset_can_be_edited(self):
        """Test if API can edit and existing dataset. (PUT request)"""
        res = self.client().post("/admin/datasets/", data=self.dataset,
                                 headers=self.admin_headers())
        self.assertEqual(res.status_code, 201)
        put_res = self.client().put(
            "/admin/datasets/1",
            data={
                "name": "COVID Ultrasound",
                "classes": ["Positive", "Negative", "Not Sure"],
            }, headers=self.admin_headers()
        )
        self.assertEqual(put_res.status_code, 200)
        results = self.client().get("/admin/datasets/1",
                                    headers=self.admin_headers())
        self.assertIn("COVID Ultrasound", str(results.data))

    def test_dataset_deletion(self):
        """Test if API can delete an existing dataset. (DELETE request)"""

        res = self.client().post(
            "/admin/datasets/",
            data={
                "name": "Dogs",
                "classes": ["labrador", "German Shepherd", "Golden Retriever", "Husky"],
            }, headers=self.admin_headers()
        )
        self.assertEqual(res.status_code, 201)
        delete_res = self.client().delete("/admin/datasets/1",
                                          headers=self.admin_headers())
        self.assertEqual(delete_res.status_code, 200)
        result = self.client().get("/admin/datasets/1",
                                   headers=self.admin_headers())
        self.assertEqual(result.status_code, 404)

    def tearDown(self):
        """teardown all initialized variables"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()


if __name__ == "__main__":
    unittest.main()
