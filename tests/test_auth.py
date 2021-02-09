import unittest
import json
from application import create_app, db


class AuthTestCase(unittest.TestCase):
    """Test case for the authentication blueprint."""

    def setUp(self):
        """Set up test variables."""
        self.app = create_app(config_name="testing")
        # initialize the test client
        self.client = self.app.test_client
        # This is the user test json data with a predefined email and password
        self.user_data = {
            'username': "Admin",
            'email': 'test@example.com',
            'password': 'test_password',
            "is_admin": True
        }

        with self.app.app_context():
            # create all tables
            db.session.close()
            db.drop_all()
            db.create_all()

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

    def login_user(self, email="user@test.com", password="test1234"):
        """Helper method for admin log in"""
        user_data = {"email": email, "password": password}
        return self.client().post("/auth/login/", data=user_data)

    def user_headers(self):
        self.register_user()
        login_res = self.login_user()
        self.assertEqual(login_res.status_code, 200)
        access_token = json.loads(login_res.data.decode())["access_token"]
        is_admin = bool(json.loads(login_res.data.decode())["is_admin"])
        user_id = json.loads(login_res.data.decode())["id"]
        return dict(Authorization="Bearer " + access_token, is_admin=is_admin, user_id=user_id)

    def test_registration(self):
        """Test user registration works correcty."""
        res = self.client().post('/auth/register/', data=self.user_data)
        # get the results returned in json format
        result = json.loads(res.data.decode())
        # assert that the request contains a success message and a 201 status code
        self.assertEqual(result['message'], "You registered successfully.")
        self.assertEqual(res.status_code, 201)

    def test_already_registered_user(self):
        """Test that a user cannot be registered twice."""
        res = self.client().post('/auth/register/', data=self.user_data)
        self.assertEqual(res.status_code, 201)
        second_res = self.client().post('/auth/register/', data=self.user_data)
        self.assertEqual(second_res.status_code, 202)
        # get the results returned in json format
        result = json.loads(second_res.data.decode())
        self.assertEqual(
            result['message'], "User already exists. Please login.")

    def test_user_login(self):
        """Test registered user can login."""
        res = self.client().post('/auth/register/', data=self.user_data)
        self.assertEqual(res.status_code, 201)
        login_res = self.client().post('/auth/login/', data=self.user_data)

        # get the results in json format
        result = json.loads(login_res.data.decode())
        # Test that the response contains success message
        self.assertEqual(result['message'], "You logged in successfully.")
        # Assert that the status code is equal to 200
        self.assertEqual(login_res.status_code, 200)
        self.assertTrue(result['access_token'])

    def test_non_registered_user_login(self):
        """Test non registered users cannot login."""
        # define a dictionary to represent an unregistered user
        not_a_user = {
            'email': 'random@example.com',
            'password': 'randomuser'
        }
        # send a POST request to /auth/login with the data above
        res = self.client().post('/auth/login/', data=not_a_user)
        # get the result in json
        result = json.loads(res.data.decode())

        # assert that this response must contain an error message 
        # and an error status code 401(Unauthorized)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(
            result['message'], "Invalid email or password, Please try again")

    def test_logout_blacklisted_token(self):
        """Test if user can logout"""
        # Register user
        res = self.client().post('/auth/register/', data=self.user_data)
        self.assertEqual(res.status_code, 201)
        # User login
        login_res = self.client().post('/auth/login/', data=self.user_data)
        self.assertEqual(login_res.status_code, 200)
        # Logout
        rv = self.client().post('/auth/logout/', headers=self.user_headers())
        self.assertIn("Successfully logged out.", str(rv.data))
        self.assertEqual(rv.status_code, 200)

        result = self.client().get('/user/1/home/', headers=self.user_headers())
        # self.assertIn("Token blacklisted", str(result.data))
        self.assertEqual(result.status_code, 401)