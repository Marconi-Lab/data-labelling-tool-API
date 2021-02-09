import io
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

        self.dataset = {
            "name": "Cervical Infection",
            "classes": ["Positive", "Negative", "Not Sure"],
        }
        self.image = (io.BytesIO(b"abcdef"), "test4.jpg")
        self.images = [
            (io.BytesIO(b"abcdef"), "test.jpg"),
            (io.BytesIO(b"abcdef"), "test1.jpg"),
            (io.BytesIO(b"abcdef"), "test3.jpg"),
            (io.BytesIO(b"abcdef"), "test5.jpg"),
        ]
        self.user_data = [
            {
                "username": "user1",
                "email": "test1@example.com",
                "password": "test_password",
                "is_admin": ""
            },
            {
                "username": "user2",
                "email": "test2@example.com",
                "password": "test_password",
                "is_admin": ""
            },
            {
                "username": "user3",
                "email": "test3@example.com",
                "password": "test_password",
                "is_admin": ""
            },
        ]
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

    def test_item_upload(self):
        """Test if API can add item to dataset"""

        # Upload dataset
        dataset_res = self.client().post("/admin/datasets/", data=self.dataset,
                                         headers=self.admin_headers())
        self.assertEqual(dataset_res.status_code, 201)
        dataset_json = json.loads(dataset_res.data.decode())

        # Upload item

        item_res = self.client().post(
            f"/admin/{dataset_json['id']}/item/",
            data={"name": "item", "classes": ["acid", "no acid"]},
            headers=self.admin_headers()
        )

        self.assertEqual(item_res.status_code, 201)
        self.assertIn("Item was successfully added", str(item_res.data))

        data_res = self.client().get(
            "/admin/datasets/1/", headers=self.admin_headers()
        )

        self.assertIn("acid", str(data_res.data))

    def test_item_get(self):
        """Test if API can retrieve items"""

        # Upload dataset
        dataset_res = self.client().post("/admin/datasets/", data=self.dataset,
                                         headers=self.admin_headers())
        self.assertEqual(dataset_res.status_code, 201)
        dataset_json = json.loads(dataset_res.data.decode())

        # Upload item
        item_res = self.client().post(
            f"/admin/{dataset_json['id']}/item/",
            data={ "name": "item"},
            headers=self.admin_headers()
        )
        rv = self.client().get(
            f"/admin/{dataset_json['id']}/item/",
            headers=self.admin_headers()
        )

        # Make assertions
        self.assertEqual(rv.status_code, 200)

    def test_item_get_with_id(self):
        """Test if API can get item by it's id"""

        # Upload dataset
        dataset_res = self.client().post("/admin/datasets/", data=self.dataset,
                                         headers=self.admin_headers())
        self.assertEqual(dataset_res.status_code, 201)
        dataset_json = json.loads(dataset_res.data.decode())

        # Upload item
        item_res = self.client().post(
            f"/admin/{dataset_json['id']}/item/",
            data={ "name": "item"},
            headers=self.admin_headers()
        )
        item_json = json.loads(item_res.data.decode())
        # Retrieve item with id
        rv = self.client().get(
            "/admin/item/1/",
            data={"dataset_id": dataset_json["id"]},
            headers=self.admin_headers()
        )

        self.assertEqual(rv.status_code, 200)
        self.assertIn("images", str(rv.data))

    def test_item_delete(self):
        """Test if API can delete item and it's content"""

        # Upload dataset
        dataset_res = self.client().post("/admin/datasets/", data=self.dataset,
                                         headers=self.admin_headers())
        self.assertEqual(dataset_res.status_code, 201)
        dataset_json = json.loads(dataset_res.data.decode())

        # Upload item
        item_res = self.client().post(
            f"/admin/{dataset_json['id']}/item/",
            data={"name": "item"},
            headers=self.admin_headers()
        )

        rv = self.client().delete("/admin/item/1/",
                                  headers=self.admin_headers())
        self.assertEqual(rv.status_code, 200)
        # Check that item was deleted
        res = self.client().get("admin/item/1/",
                                headers=self.admin_headers())
        self.assertEqual(res.status_code, 404)

    def test_get_users(self):
        """Test if API can retrieve all users"""

        for user in self.user_data:
            res = self.client().post("/auth/register/", data=user,
                                     headers=self.admin_headers())
            # get the results returned in json format
            self.assertEqual(res.status_code, 201)

        rv = self.client().get("/admin/users/", headers=self.admin_headers())
        self.assertEqual(rv.status_code, 200)
        self.assertIn("user1", str(json.loads(rv.data.decode())))
        self.assertIn("user2", str(rv.data))
        self.assertIn("user3", str(rv.data))

    def test_post_assign_user_datasets(self):
        """Test if API can assign datasets to a user"""

        # Create user
        res = self.client().post("/auth/register/", data=self.user_data[0],
                                 headers=self.admin_headers())
        self.assertEqual(res.status_code, 201)
        # Create Dataset
        res1 = self.client().post("/admin/datasets/", data=self.dataset,
                                  headers=self.admin_headers())
        self.assertEqual(res.status_code, 201)
        # Assign user a dataset
        rv = self.client().post("/admin/users/1/assignments/", data={"dataset_id": "1"},
                                headers=self.admin_headers())
        self.assertEqual(rv.status_code, 201)
        self.assertIn("Cervical Infection", str(rv.data))

    def test_retract_user_dataset_assignment(self):
        """Test if API can remove user dataset assignment"""
        # Create user
        res = self.client().post("/auth/register/", data=self.user_data[0],
                                 headers=self.admin_headers())
        self.assertEqual(res.status_code, 201)
        # Create Dataset
        res1 = self.client().post("/admin/datasets/", data=self.dataset,
                                  headers=self.admin_headers())
        self.assertEqual(res.status_code, 201)
        # Assign dataset
        res2 = self.client().post(
            "/admin/users/1/assignments/", data={"dataset_id": "1"},
            headers=self.admin_headers()
        )
        self.assertEqual(res2.status_code, 201)
        # Delete assignment
        rv = self.client().delete(
            "/admin/users/1/assignments/", data={"dataset_id": "1"},
            headers=self.admin_headers()
        )
        self.assertEqual(rv.status_code, 200)
        self.assertIn("Message", str(rv.data))

        result = self.client().get("/admin/users/datasets/1/", data={"user_id": "1"},
                                   headers=self.admin_headers())
        self.assertEqual(result.status_code, 404)

    def test_get_all_user_dataset_assignments(self):
        """Test if API can retrieve all user dataset assignments"""

        # Create user
        res = self.client().post("/auth/register/", data=self.user_data[0],
                                 headers=self.admin_headers())
        self.assertEqual(res.status_code, 201)
        # Create Dataset
        res1 = self.client().post("/admin/datasets/", data=self.dataset,
                                  headers=self.admin_headers())
        self.assertEqual(res1.status_code, 201)
        # Assign dataset
        res2 = self.client().post(
            "/admin/users/1/assignments/", data={"dataset_id": "1"},
            headers=self.admin_headers()
        )
        self.assertEqual(res2.status_code, 201)

        rv = self.client().get("/admin/users/1/assignments/",
                               headers=self.admin_headers())
        self.assertEqual(rv.status_code, 200)
        self.assertIn("Cervical Infection", str(rv.data))

    def test_get_user_stats(self):
        """Test if API can retrieve admin's statistics summary"""

        # Create user
        res = self.client().post("/auth/register/", data=self.user_data[0],
                                 headers=self.admin_headers())
        self.assertEqual(res.status_code, 201)
        # Create Dataset
        res1 = self.client().post("/admin/datasets/", data=self.dataset,
                                  headers=self.admin_headers())
        self.assertEqual(res1.status_code, 201)
        # Assign dataset
        res2 = self.client().post(
            "/admin/users/1/assignments/", data={"dataset_id": "1"},
            headers=self.admin_headers()
        )
        self.assertEqual(res2.status_code, 201)

        rv = self.client().get("/admin/1/home/",
                               headers=self.admin_headers())
        self.assertEqual(rv.status_code, 200)
        self.assertIn("users", str(rv.data))
        self.assertIn("datasets", str(rv.data))

        # Test images upload to folder

    def test_admin_can_upload_images_to_item(self):
        """Test if API can upload images to item (Folder)"""
        # Upload dataset
        dataset_res = self.client().post("/admin/datasets/", data=self.dataset,
                                         headers=self.admin_headers())
        self.assertEqual(dataset_res.status_code, 201)
        dataset_json = json.loads(dataset_res.data.decode())

        # Create item (Folder)
        item_res = self.client().post(f"/admin/{dataset_json['id']}/item/",
                                      data=dict(dataset_id=dataset_json["id"], name="item_name"),
                                      headers=self.admin_headers())
        self.assertEqual(item_res.status_code, 201)
        item_json = json.loads(item_res.data.decode())

        image_res = self.client().post(
            "/admin/item/1/",
            data={"item_id": item_json["id"], "images": self.images},
            content_type="multipart/form-data",
            headers=self.admin_headers()
        )
        print("Response", image_res.data)
        self.assertEqual(image_res.status_code, 201)
        self.assertIn("Images were successfully added", str(image_res.data))

    # Test image upload to dataset
    def test_admin_can_upload_image_to_dataset(self):
        """Test if admin can upload image to a dataset"""
        # Upload dataset
        dataset_res = self.client().post("/admin/datasets/", data=self.dataset,
                                         headers=self.admin_headers())
        self.assertEqual(dataset_res.status_code, 201)
        dataset_json = json.loads(dataset_res.data.decode())

        image_res = self.client().post(
            "/admin/datasets/images/",
            data={"dataset_id": dataset_json["id"], "image": self.image},
            content_type="multipart/form-data",
            headers=self.admin_headers()
        )
        print(image_res.data)
        self.assertEqual(image_res.status_code, 201)
        self.assertIn("Image was successfully added", str(image_res.data))

    def test_admin_can_delete_image_by_id(self):
        """Test if admin can delete image by id"""
        # Upload dataset
        dataset_res = self.client().post("/admin/datasets/", data=self.dataset,
                                         headers=self.admin_headers())
        self.assertEqual(dataset_res.status_code, 201)
        dataset_json = json.loads(dataset_res.data.decode())

        image_res = self.client().post(
            "/admin/datasets/images/",
            data={"dataset_id": dataset_json["id"], "image": self.image},
            content_type="multipart/form-data",
            headers=self.admin_headers()
        )

        self.assertEqual(image_res.status_code, 201)

        rv = self.client().delete("/admin/images/1/",
                                  headers=self.admin_headers())
        self.assertEqual(rv.status_code, 200)
        # Check that item was deleted
        res = self.client().get("/user/images/1/",
                                headers=self.admin_headers())
        self.assertEqual(res.status_code, 404)

    def tearDown(self):
        """teardown all initialized variables"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()


if __name__ == "__main__":
    unittest.main()
