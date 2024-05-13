"""Message View tests."""

import os
from pprint import pprint
from unittest import TestCase
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.session import close_all_sessions
from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

# Now we can import app

from app import create_app, CURR_USER_KEY

app = create_app(csrf=False)


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        app.app_context().push()
        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser1 = User.signup(username="testuser",
                                     email="test@test.com",
                                     password="testuser",
                                     image_url=None)

        self.testuser2 = User.signup(username="testuser2",
                                     email="tes2t@test.com",
                                     password="testuser2",
                                     image_url=None)

        db.session.commit()

        self.msg1 = Message(text='First message', user_id=self.testuser1.id)
        self.msg2 = Message(text='Second message', user_id=self.testuser2.id)
        db.session.add_all([self.msg1, self.msg2])
        db.session.commit()

    def test_add_message(self):
        """Can a user add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser1.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.filter_by(text='Hello').one()
            self.assertEqual(msg.text, "Hello")

    def test_add_unauthorized_message(self):
        """Can a non logged in user add a message?"""

        with self.client as client:
            resp = client.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)
            html = resp.text

            pprint(html)

            self.assertEqual(resp.status_code, 200)

            msg = Message.query.all()
            self.assertEqual(len(msg), 2)
            self.assertIn('Access unauthorized', html)

    def test_show_message(self):
        """Can a user see a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser1.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = client.get(f'/messages/{self.msg1.id}')
            html = resp.text

            self.assertEqual(resp.status_code, 200)
            self.assertIn('First message', html)

    def test_delete_message(self):
        """Can a user delete a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser1.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post(f"/messages/{self.msg1.id}/delete")

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.all()
            self.assertEqual(len(msg), 1)

    def test_delete_other_user_message(self):
        """Can a user delete a message another user created??"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser1.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post(f"/messages/{self.msg2.id}/delete", follow_redirects=True)
            html = resp.text
            # Make sure it redirects
            self.assertEqual(resp.status_code, 200)

            self.assertIn('Access unauthorized', html)

            msg = Message.query.all()
            self.assertEqual(len(msg), 2)