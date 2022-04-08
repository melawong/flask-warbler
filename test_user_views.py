"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_user_views.py


import os
from unittest import TestCase

from models import db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class UserViewTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        self.testuser2 = User.signup(username="testuser2",
                                    email="test2@test.com",
                                    password="testuser2",
                                    image_url=None)

        db.session.commit()

        self.testuser_id = self.testuser.id
        self.testuser2_id = self.testuser2.id


    def tearDown(self):
        """Clean up fouled transactions."""

        db.session.rollback()


    def test_show_userlist(self):
        """Tests if userlist shows all users if not specifically searched"""

        with self.client as c:

            resp = c.get(f"/users")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Test for rendering userlist template", html)


    def test_show_user_details(self):
        """Tests that user detail page renders correct user's profile"""

        with self.client as c:

            resp = c.get(f"/users/{self.testuser_id}")
            html = resp.get_data(as_text=True)
            user = User.query.get(self.testuser_id)

            self.assertEqual(resp.status_code, 200)
            self.assertIn(f"@{user.username}", html)
            self.assertIn("Test for rendering user show page", html)

            resp = c.get("/users/0")
            self.assertEqual(resp.status_code, 404)

    # test that logged in user going to their own page has diff buttons?

    def test_users_following_page_logged_in(self):

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            user = User.query.get(self.testuser_id)
            resp = c.get(f"/users/{user.id}/following")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Test for rendering user following page", html)
            # test users followers actually show up?

            #tests 404 is properly triggered on invalid user_id search
            resp = c.get("/users/0/following")
            self.assertEqual(resp.status_code, 404)
    # if logged in -- followers page shows up, rend temp, status code
    # if logged out -- test redirect, render home-anon "/"

    def test_users_following_page_logged_out(self):

        with self.client as c:
            user = User.query.get(self.testuser_id)
            resp = c.get(f"/users/{user.id}/following", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Tests template rendering home-anon", html)
