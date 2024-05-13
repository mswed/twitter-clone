"""Message model tests."""

import os
from unittest import TestCase
from sqlalchemy.exc import IntegrityError, DataError
from models import db, User, Message, Follows


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


class MessageModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        app.app_context().push()
        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        db.session.commit()

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        self.u = u


        self.client = app.test_client()

    def test_message_model(self):
        """Does creating a message work?"""

        with app.app_context():

            m = Message(
                text='test message',
                user_id=self.u.id
            )
            db.session.add(m)
            db.session.commit()

            self.assertIsNotNone(m.id)

    def test_message_char_limit(self):
        """Creating a message longer than 140 characters should fail"""

        with app.app_context():
            m = Message(
                text='b' * 141,
                user_id=self.u.id
            )
            db.session.add(m)
            with self.assertRaises(DataError):
                db.session.commit()

    def test_message_like(self):
        """Can a user like a message?"""

        m = Message(
            text='liked message',
            user_id=self.u.id
        )
        db.session.add(m)
        db.session.commit()

        msg = Message.query.get(m.id)
        self.u.likes.append(msg)
        db.session.commit()

        self.assertEqual(len(self.u.likes), 1)



