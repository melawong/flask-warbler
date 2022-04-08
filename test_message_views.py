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

        db.session.commit()

        self.testuser_id = self.testuser.id
        self.testuser2_id = self.testuser2.id


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

            resp = c.post("/messages/new", data={"text": "Test New Message Hello"},
                                            follow_redirects=True)

            #tests route followed redirects properly
            self.assertEqual(resp.status_code, 200)

            #tests message stored correctly in db
            msg = Message.query.filter_by(text="Test New Message Hello").one()
            self.assertEqual(msg.text, "Test New Message Hello")

            #tests route renders correct message/template after redirects
            html = resp.get_data(as_text=True)
            self.assertIn("Test New Message Hello", html)


    def test_add_message_logged_out(self):
        """When logged out, can anyone add a message? -> No """

        with self.client as c:

            resp = c.post("/messages/new", data={"text": "Test New Message Hello"},
                                            follow_redirects=True)

            html = resp.get_data(as_text=True)
            msg = Message.query.filter_by(text="Test New Message Hello").one_or_none()

            #tests route followed redirects properly
            self.assertEqual(resp.status_code, 200)

            #tests no message stored in db
            self.assertEqual(msg, None)

            #tests route renders correct template and flash message after redirects
            self.assertIn("Access unauthorized.", html)
            self.assertIn("Tests template rendering home-anon", html)


    def test_show_message(self):
        """ Does show_message route show single message properly?"""

        with self.client as c:

            user = User.query.get(self.testuser_id)
            message = Message(text="test message text")
            user.messages.append(message)

            db.session.commit()

            resp = c.get(f"/messages/{message.id}")

            html = resp.get_data(as_text=True)

            # does the message page give the correct status code
            self.assertEqual(resp.status_code, 200)


            # does route show correct message template
            self.assertIn("Test for rendering show-message page", html)
            self.assertIn(f"{message.text}", html)


    def test_show_message_404(self):
        """ Does show_message route show 404 when accessing non-existent message?"""

        with self.client as c:
            resp = c.get("/messages/0")
            self.assertEqual(resp.status_code, 404)


    def test_destroy_message_valid(self):
        """Does destroy_message route delete a message successfully with proper credentials"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            user = User.query.get(self.testuser_id)
            message = Message(text="test message text")
            user.messages.append(message)

            db.session.commit()

            resp = c.post(f'/messages/{message.id}/delete', follow_redirects=True)

            html = resp.get_data(as_text=True)

            # correct status code?
            self.assertEqual(resp.status_code, 200)

            # renders correct template?
            self.assertIn("Test for rendering user detail page", html)
            self.assertNotIn("test message text", html)
            self.assertIn(f"{user.username}", html)

            # check db no longer has message
            msg = Message.query.filter_by(text="test message text").one_or_none()
            self.assertEqual(msg, None)


    def test_destroy_message_invalid(self):
        """Can user delete message that is not theirs"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # add message to user2 to try to delete
            user2 = User.query.get(self.testuser2_id)
            message = Message(text="test message text")
            user2.messages.append(message)

            db.session.commit()

            resp = c.post(f'/messages/{message.id}/delete', follow_redirects=True)

            html = resp.get_data(as_text=True)

            # correct status code?
            self.assertEqual(resp.status_code, 200)

            # renders correct template?
            self.assertIn("Access unauthorized.", html)
            self.assertIn("Tests template rendering home", html)

            # check db still has message
            msg = Message.query.filter_by(text="test message text").one_or_none()
            self.assertNotEqual(msg, None)


    def test_destroy_message_logged_out(self):
        """ Does destroy_message route fail to delete message when no user
            logged in? """

        with self.client as c:

            # add message to user2 to try to delete
            user2 = User.query.get(self.testuser2_id)
            message = Message(text="test message text")
            user2.messages.append(message)

            db.session.commit()

            resp = c.post(f'/messages/{message.id}/delete', follow_redirects=True)
            html = resp.get_data(as_text=True)

            # correct status code?
            self.assertEqual(resp.status_code, 200)

            # renders correct template?
            self.assertIn("Access unauthorized.", html)
            self.assertIn("Tests template rendering home", html)

            # check db still has message
            msg = Message.query.filter_by(text="test message text").one_or_none()
            self.assertNotEqual(msg, None)