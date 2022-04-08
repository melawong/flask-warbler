"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy import exc
from flask_bcrypt import Bcrypt
from models import db, User, Message, Follows, Likes

bcrypt = Bcrypt()


# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.drop_all()
db.create_all()


USER_DATA_1 = {
    "email" : "test1@test.com",
    "username": "testuser_1",
    "password": "HASHED_PASSWORD"
}

USER_DATA_2 = {
    "email" : "test2@test.com",
    "username": "testuser_2",
    "password": "HASHED_PASSWORD"
}



class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()
        Likes.query.delete()

        user_1 = User(**USER_DATA_1)
        db.session.add(user_1)

        user_2 = User(**USER_DATA_2)
        db.session.add(user_2)

        db.session.commit()

        self.user_1_id = user_1.id
        self.user_2_id = user_2.id

        self.client = app.test_client()

    def tearDown(self):
        """Clean up fouled transactions."""

        db.session.rollback()

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)


    def test_user_repr(self):
        """Does __repr__ return as expected"""

        u1 = User.query.get(self.user_1_id)

        self.assertEqual(repr(u1), f'<User #{u1.id}: {u1.username}, {u1.email}>')


    def test_is_following(self):
        """Test that is_following function properly detects following and not-following"""

        u1 = User.query.get(self.user_1_id)
        u2 = User.query.get(self.user_2_id)

        # make u1 follow u2
        new_follow = Follows(user_being_followed_id = u2.id, user_following_id = u1.id)
        db.session.add(new_follow)
        db.session.commit()

        self.assertTrue(u1.is_following(u2))
        self.assertFalse(u2.is_following(u1))


    def test_is_followed_by(self):
        """Test that is_followed_by function properly detects followed by and not-followed-by"""

        u1 = User.query.get(self.user_1_id)
        u2 = User.query.get(self.user_2_id)

        # make u1 follow u2
        new_follow = Follows(user_being_followed_id = u2.id, user_following_id = u1.id)
        db.session.add(new_follow)
        db.session.commit()

        self.assertTrue(u2.is_followed_by(u1))
        self.assertFalse(u1.is_followed_by(u2))


    def test_user_signup_valid(self):
        """Test that User.signup creates new user successfully"""

        USER_DATA_valid = {
            "email" : "valid@email.com",
            "username": "valid_un",
            "password": "HASHED_PASSWORD",
            "image_url": ""
        }

        valid_user = User.signup(**USER_DATA_valid)
        db.session.commit()

        #self.assertIsInstance(valid_user, User)
        self.assertTrue(User.query.get(valid_user.id))
        self.assertEqual(valid_user.username, "valid_un")
        self.assertEqual(valid_user.email, "valid@email.com")
        self.assertNotEqual(valid_user.password, "HASHED_PASSWORD")
        self.assertTrue(valid_user.password.startswith("$2b$12$"))


    def test_user_signup_invalid_email(self):
        """Test User.signup fails when email is null or repeated"""

        USER_DATA_invalid_em = {
            "email" : None,
            "username": "testuser_3",
            "password": "HASHED_PASSWORD",
            "image_url": ""
        }

        USER_DATA_repeat_em = {
            "email" : "test1@test.com",
            "username": "testuser_4",
            "password": "HASHED_PASSWORD",
            "image_url": ""
        }

        User.signup(**USER_DATA_invalid_em)
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

        db.session.rollback()
        User.signup(**USER_DATA_repeat_em)
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()


    def test_user_signup_invalid_username(self):
        """Test User.signup fails when username is null or repeated"""

        USER_DATA_null_un = {
            "email" : "test3@test.com",
            "username": None,
            "password": "HASHED_PASSWORD",
            "image_url": ""
        }

        USER_DATA_repeat_un = {
            "email" : "test4@test.com",
            "username": "testuser_1",
            "password": "HASHED_PASSWORD",
            "image_url": ""
        }

        User.signup(**USER_DATA_null_un)
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

        db.session.rollback()
        User.signup(**USER_DATA_repeat_un)
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()


    def test_user_signup_null_password(self):
        """Test User.signup fails when password is null"""

        USER_DATA_empty_pw = {
            "email" : "test5@test.com",
            "username": "testuser_5",
            "password": "",
            "image_url": ""
        }

        USER_DATA_null_pw = {
            "email" : "test5@test.com",
            "username": "testuser_5",
            "password": None,
            "image_url": ""
        }

        with self.assertRaises(ValueError) as context:
            User.signup(**USER_DATA_empty_pw)

        with self.assertRaises(ValueError) as context:
            User.signup(**USER_DATA_null_pw)


    def test_user_authenticate_valid(self):
        """Test User.authenticate succeeds when passed valid arguments"""

        valid_user = User.query.get(self.user_1_id)
        hashed_pwd = bcrypt.generate_password_hash(valid_user.password).decode('UTF-8')
        valid_user.password = hashed_pwd
        db.session.commit()

        resp = User.authenticate(valid_user.username, 'HASHED_PASSWORD')
        self.assertIsInstance(resp, User)


    def test_user_authenticate_invalid_un(self):
        """Test User.authenticate fails when passed invalid username"""

        valid_user = User.query.get(self.user_1_id)
        hashed_pwd = bcrypt.generate_password_hash(valid_user.password).decode('UTF-8')
        valid_user.password = hashed_pwd
        db.session.commit()

        resp = User.authenticate('INVALID_USERNAME', 'HASHED_PASSWORD')
        self.assertFalse(resp)


    def test_user_authenticate_invalid_pw(self):
        """Test User.authenticate fails when passed invalid password"""

        valid_user = User.query.get(self.user_1_id)
        hashed_pwd = bcrypt.generate_password_hash(valid_user.password).decode('UTF-8')
        valid_user.password = hashed_pwd
        db.session.commit()

        resp = User.authenticate(valid_user.username, 'INVALID_PASSWORD')
        self.assertFalse(resp)

