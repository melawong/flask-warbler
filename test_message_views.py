"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

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


class MessageViewTestCase(TestCase):
    """Test views for messages."""

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

        self.testuser2_id = self.testuser2.id

        db.session.commit()


    def tearDown(self):
        """Clean up fouled transactions."""

        db.session.rollback()


    def test_add_message_valid(self):
        """Can valid user add a message for themselves?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"},
                                            follow_redirects=True)

            #tests route followed redirects properly
            self.assertEqual(resp.status_code, 200)

            #tests message stored correctly in db
            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

            #tests route renders correct message/template after redirects
            html = resp.get_data(as_text=True)
            self.assertIn("Hello", html)

    def test_add_message_logged_out(self):
        """When logged out, can anyone add a message? -> No """

        with self.client as c:

            resp = c.post("/messages/new", data={"text": "Hello"},
                                            follow_redirects=True)

            html = resp.get_data(as_text=True)
            msg = Message.query.one_or_none()

            #tests route followed redirects properly
            self.assertEqual(resp.status_code, 200)

            #tests no message stored in db
            self.assertEqual(msg, None)

            #tests route renders correct template and flash message after redirects
            self.assertIn("Access unauthorized.", html)
            self.assertIn("Tests template rendering home-anon", html)


    def test_add_message_invalid_user(self):
        """When logged in, can user add message for different user? -> No """

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
                sess["other_user"] = self.testuser2.id

            resp = c.post("/messages/new",
                data={"text": "hihihi", "user_id": sess["other_user"],
                  "blah": "blah"},
                                                follow_redirects=True)

            html = resp.get_data(as_text=True)
            msg = Message.query.one_or_none()
            print("length of messages",len(Message.query.all()))

            #tests route followed redirects properly
            self.assertEqual(resp.status_code, 200)

            #tests route renders correct template after redirect
            #route will redirect to user detail page because user is logged in
            self.assertIn("Test for rendering user detail page", html)

            #tests no message was added to other user
            self.assertFalse(msg.user_id == sess["other_user"])
            #self.assertEqual(msg, None)



    def test_show_message(self):
        """ Does show_message route show single message properly?"""
        # does the message page give the correct status code
        # does message page give correct message --> render_temp
        # does going to non-existent message page show 404
        pass


    def test_destroy_message(self):
        """Does destroy_message route delete a message"""
        # check can a curr_user delete their own message? (Yes) --> resp code + rend + db check
        # can curr_user delete message that is not theirs? (No) --> resp code + rend
        # can you delete any message when logged out? (No) --> resp code + rend
        pass
