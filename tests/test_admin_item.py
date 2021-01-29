import unittest
import json
from application import create_app, db
import io

class AuthTestCase(unittest.TestCase):
    """Test case for the admin blueprint"""

    def setUp(self):
        """Set up test variables"""
        self.app = create_app(config_name="testing")
        # initialize the test client
        self.client = self.app.test_client

        self.user_data = {
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

        # Binds application to current context
        with self.app.app_context():
            #create all tables
            db.create_all()

        #===================================================================
    def test_item_upload(self):
        """Test if API can add item to dataset"""
        #Upload dataset
        dataset_res = self.client().post('/admin/datasets/', data=self.dataset)
        self.assertEqual(dataset_res.status_code, 201)
        dataset_json = json.loads(dataset_res.data.decode())

        #Upload item

        item_res = self.client().post('/admin/datasets/item/', data={"dataset_id":dataset_json['id'], "images":self.images}, content_type="multipart/form-data")
        print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        print("Item Response: ", item_res)
        print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")

        self.assertEqual(item_res.status_code, 201)
        self.assertIn("Item was successfully added", str(item_res.data))

    def test_item_get(self):
        """Test if API can retrieve items"""
        #Upload dataset
        dataset_res = self.client().post('/admin/datasets/', data=self.dataset)
        self.assertEqual(dataset_res.status_code, 201)
        dataset_json = json.loads(dataset_res.data.decode())

        #Upload item
        item_res = self.client().post('/admin/datasets/item/', data={"dataset_id":dataset_json['id'], "images":self.images}, content_type="multipart/form-data")
        rv = self.client().post("/admin/datasets/item/", data={"dataset_id": dataset_json["id"]})

        #Make assertions
        self.assertEqual(res.status_code, 200)
        self.assertIn("items", str(rv.data))
        self.assertIn("images", str(rv.data))


    def tearDown(self):
        """teardown all initialized variables"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()


if __name__ == "__main__":
    unittest.main()