"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy import exc
from flask_bcrypt import Bcrypt
from models import db, User, Message, Follows, Likes

bcrypt = Bcrypt()

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

from app import app

db.drop_all()
db.create_all()


USER_DATA_1 = {
    "email" : "test1@test.com",
    "username": "testuser_1",
    "password": "HASHED_PASSWORD"
}


class MessageModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()
        Likes.query.delete()

        user_1 = User(**USER_DATA_1)
        db.session.add(user_1)

        db.session.commit()

        self.user_1_id = user_1.id

        self.client = app.test_client()


    def tearDown(self):
        """Clean up fouled transactions."""

        db.session.rollback()


    def test_message_model_valid(self):
        """Does basic message model work when valid arguments passed?"""

        message = Message(text = "Sample Text", user_id = self.user_1_id)

        db.session.add(message)
        db.session.commit()


        user = User.query.get(self.user_1_id)
        message_test = Message.query.filter_by(user_id = self.user_1_id).one()

        self.assertIsInstance(message_test, Message)
        self.assertEqual(len(user.messages), 1)



    def test_message_model_invalid(self):
        """Does basic message model work when valid arguments passed?"""

        blank_message = Message(text = None, user_id = self.user_1_id)
        db.session.add(blank_message)
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

        db.session.rollback()

        invalid_user_message = Message(text = "Sample Text", user_id = None)
        db.session.add(invalid_user_message)
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()


    def test_message_repr(self):
        """Does __repr__ return as expected"""

        message = Message(text = "Sample Text", user_id = self.user_1_id)
        db.session.add(message)
        db.session.commit()

        m1 = Message.query.get(message.id)
        breakpoint()

        self.assertEqual(repr(m1),
            f'<Message #{m1.id}: {m1.text}, {m1.timestamp}, {m1.user_id}>')