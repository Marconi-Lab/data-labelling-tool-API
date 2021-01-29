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
        self.user_data = [
            {
                'username': "user1",
                'email': 'test1@example.com',
                'password': 'test_password'
            }, 
            {
                'username': "Admin2",
                'email': 'test2@example.com',
                'password': 'test_password'
            }, 
            {
                'username': "Admin3",
                'email': 'test3@example.com',
                'password': 'test_password'
            }
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
        rv = self.client().get("/admin/datasets/item/", data={"dataset_id": dataset_json["id"]})

        #Make assertions
        self.assertEqual(rv.status_code, 200)

    def test_item_get_with_id(self):
        """Test if API can get item by it's id"""
        #Upload dataset
        dataset_res = self.client().post('/admin/datasets/', data=self.dataset)
        self.assertEqual(dataset_res.status_code, 201)
        dataset_json = json.loads(dataset_res.data.decode())

        #Upload item
        item_res = self.client().post('/admin/datasets/item/', data={"dataset_id":dataset_json['id'], "images":self.images}, content_type="multipart/form-data")
        item_json = json.loads(item_res.data.decode())
        #Retrieve item with id
        rv = self.client().get('/admin/datasets/item/1/')
       
        self.assertEqual(rv.status_code, 200)
        self.assertIn("images", str(rv.data))
    
    def test_item_delete(self):
        """Test if API can delete item and it's content"""
          #Upload dataset
        dataset_res = self.client().post('/admin/datasets/', data=self.dataset)
        self.assertEqual(dataset_res.status_code, 201)
        dataset_json = json.loads(dataset_res.data.decode())

        #Upload item
        item_res = self.client().post('/admin/datasets/item/', data={"dataset_id":dataset_json['id'], "images":self.images}, content_type="multipart/form-data")
        
        rv = self.client().delete('/admin/datasets/item/1/')
        self.assertEqual(rv.status_code, 200)
        #Check that item was deleted
        res = self.client().get('admin/datasets/item/1/')
        self.assertEqual(res.status_code, 404)

    def test_get_users(self):
        """Test if API can retrieve all users"""
        for user in self.user_data:
            res = self.client().post('/auth/register/', data=self.user)
            # get the results returned in json format
            result = json.loads(res.data.decode())
            self.assertEqual(res.status_code, 201)
        rv = self.client().get("/admin/users/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("user1", str(rv.data))
        self.assertIn("user2", str(rv.data))
        self.assertIn("user3", str(rv.data))

    def tearDown(self):
        """teardown all initialized variables"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

if __name__ == "__main__":
    unittest.main()