"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy.exc import IntegrityError
from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

# Now we can import app

from app import create_app

app = create_app()

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

with app.app_context():
    db.drop_all()
    db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        with app.app_context():
            User.query.delete()
            Message.query.delete()
            Follows.query.delete()

            db.session.commit()

            self.client = app.test_client()

    def test_user_model(self):
        """Does creating a user work?"""

        with app.app_context():
            u1 = User(
                email="test@test.com",
                username="testuser",
                password="HASHED_PASSWORD"
            )

            db.session.add(u1)
            db.session.commit()

            # User should have no messages & no followers
            self.assertEqual(len(u1.messages), 0)
            self.assertEqual(len(u1.followers), 0)

            # Create a user with the same username. This should fail
            u2 = User(
                email="test2@test.com",
                username="testuser",
                password="HASHED_PASSWORD"
            )

            db.session.add(u2)

            with self.assertRaises(IntegrityError):
                db.session.commit()
                db.session.rollback()

    def test_user_signup(self):
        """
        Can a user sign up?
        """
        with app.app_context():
            user = User.signup(
                username='testuser',
                password='HASHED_PASSWORD',
                email='test2@test.com',
                image_url=User.image_url.default.arg
            )

            db.session.add(user)
            db.session.commit()
            self.assertIsNotNone(user.id)

    def test_user_authentication(self):
        """
        Can a user be authenticated?
        """
        with app.app_context():
            # Create a user
            user = User.signup(
                username='testuser',
                password='HASHED_PASSWORD',
                email='test2@test.com',
                image_url=User.image_url.default.arg
            )

            db.session.add(user)
            db.session.commit()

            # Try to log in with the correct password
            self.assertEqual(user, User.authenticate('testuser', 'HASHED_PASSWORD'))

            # Try to log in with the wrong password
            self.assertFalse(User.authenticate('testuser', 'dsfafdsa'))

            # Try to log in with the wrong username
            self.assertFalse(User.authenticate('blahblah', 'HASHED_PASSWORD'))

    def test_user_without_username(self):
        """
        Does creating a user with empty username fail?
        """
        with app.app_context():
            # Create a user without an email. This should fail
            u1 = User(
                email='test@test.com',
                password='HASHED_PASSWORD'
            )
            db.session.rollback()

            db.session.add(u1)

            with self.assertRaises(IntegrityError):
                db.session.commit()
                db.session.rollback()

    def test_user_without_password(self):
        """
        Does creating a user with empty password fail?
        Returns:

        """
        with app.app_context():
            # Create a user without an email. This should fail
            u1 = User(
                email='test@test.com',
                username="testuser2",
            )
            db.session.rollback()

            db.session.add(u1)

            with self.assertRaises(IntegrityError):
                db.session.commit()
                db.session.rollback()

    def test_user_without_email(self):
        """
        Does creating a user with empty email fail?
        Returns:

        """
        with app.app_context():
            # Create a user without an email. This should fail
            u1 = User(
                username="testuser2",
                password="HASHED_PASSWORD"
            )
            db.session.rollback()

            db.session.add(u1)
            with self.assertRaises(IntegrityError):
                db.session.commit()
                db.session.rollback()

    def test_user_repr(self):
        """Does the model return the proper rper?"""

        with app.app_context():
            u = User(
                email="test@test.com",
                username="testuser",
                password="HASHED_PASSWORD"
            )

            db.session.add(u)
            db.session.commit()

            # User should have no messages & no followers
            self.assertEqual(u.__repr__(), f'<User #{u.id}: testuser, test@test.com>')

    def test_user_is_following(self):
        """Is is_following working?"""

        with app.app_context():
            # Create users
            u1 = User(
                email="test@test.com",
                username="testuser",
                password="HASHED_PASSWORD"
            )

            u2 = User(
                email="test2@test.com",
                username="testuser2",
                password="HASHED_PASSWORD"
            )

            db.session.add_all([u1, u2])
            db.session.commit()

            # Confirm that U1 is not following U2
            self.assertFalse(u1.is_following(u2))

            # U1 follows U2
            u1.following.append(u2)
            db.session.commit()

            # U1 should now be following U2
            self.assertTrue(u1.is_following(u2))

    def test_user_is_followed_by(self):
        """Is is_followed_by working?"""

        with app.app_context():
            # Create users
            u1 = User(
                email="test@test.com",
                username="testuser",
                password="HASHED_PASSWORD"
            )

            u2 = User(
                email="test2@test.com",
                username="testuser2",
                password="HASHED_PASSWORD"
            )

            db.session.add_all([u1, u2])
            db.session.commit()

            # Confirm that U1 is not following U2
            self.assertFalse(u2.is_followed_by(u1))

            # U1 follows U2
            u1.following.append(u2)
            db.session.commit()

            # U1 should now be following U2
            self.assertTrue(u2.is_followed_by(u1))

    def test_user_authentication(self):
        with app.app_context():
            # Create users
            u1 = User(
                email="test@test.com",
                username="testuser",
                password="HASHED_PASSWORD"
            )
