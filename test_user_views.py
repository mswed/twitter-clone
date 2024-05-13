"""User views tests."""

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


class UserViewsGetTestCase(TestCase):
    """Test views for user GET routes."""

    def setUp(self):
        """Create test client, add sample data."""
        app.app_context().push()
        close_all_sessions()
        db.drop_all()
        db.create_all()

        self.user1 = User.signup('testuser',
                                 'test@test.com',
                                 'testpassword',
                                 None)

        self.user2 = User.signup('testuser2',
                                 'test2@test.com',
                                 'testpassword',
                                 None)

        db.session.commit()

        self.u1_m1 = Message(text='This is a test message',
                             user_id=self.user1.id)

        self.u2_m1 = Message(text='This is another test message',
                             user_id=self.user1.id)

        db.session.add_all([self.u1_m1, self.u2_m1])
        db.session.commit()

        self.client = app.test_client()

    def test_root_without_user(self):
        """Do we get the right page when we go to /"""
        with self.client as client:
            response = client.get('/')
            html = response.text

            self.assertEqual(response.status_code, 200)
            self.assertIn('New to Warbler?', html)

    def test_root_with_user(self):
        """Do we get the right page when we go to / with a user logged in?"""

        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.user1.id

            response = client.get('/')
            html = response.text

            self.assertEqual(response.status_code, 200)
            self.assertIn('<p>@testuser</p>', html)

    def test_user_signup(self):
        """
        Do we get a signup form?
        """

        with self.client as client:
            response = client.get('/signup')
            html = response.text

            self.assertEqual(response.status_code, 200)
            self.assertIn('<h2 class="join-message">Join Warbler today.</h2>\n', html)

    def test_user_login(self):
        """
        Do we get a login form?
        """

        with self.client as client:
            response = client.get('/login')
            html = response.text

            self.assertEqual(response.status_code, 200)
            self.assertIn('<button class="btn btn-primary btn-block btn-lg">Log in</button>\n', html)

    def test_user_logout(self):
        """
        Can the user logout?
        """
        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.user1.id

            response = client.get('/logout')

            self.assertEqual(response.status_code, 302)

    def test_users_list(self):
        """
        Can we get a list of users?
        """

        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.user1.id

            response = client.get('/users', follow_redirects=True)
            html = response.text
            pprint(html)
            self.assertEqual(response.status_code, 200)
            self.assertIn('<div class="card user-card">\n', html)

    def test_show_user_home(self):
        """
        Can we get a user's home with messages
        """

        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.user1.id

            response = client.get(f'/users/{self.user1.id}', follow_redirects=True)
            html = response.text

            self.assertEqual(response.status_code, 200)
            self.assertIn('<h4 id="sidebar-username">@testuser</h4>\n', html)
            self.assertIn('This is a test message', html)

    def test_show_user_likes(self):
        """
        Can we get a user's likes?
        """

        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.user1.id

            self.user1.likes.append(self.u2_m1)
            db.session.commit()

            response = client.get(f'/users/{self.user1.id}/likes')
            html = response.text

            self.assertEqual(response.status_code, 200)
            self.assertIn('<h4 id="sidebar-username">@testuser</h4>\n', html)
            self.assertIn('his is another test message', html)

    def test_show_user_following(self):
        """
        Can we get a users the user is following??
        """

        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.user1.id

            self.user1.following.append(self.user2)
            db.session.commit()

            response = client.get(f'/users/{self.user1.id}/following')
            html = response.text
            pprint(html)
            self.assertEqual(response.status_code, 200)
            self.assertIn('@testuser2', html)

    def test_show_user_followers(self):
        """
        Can we get a list of users who follow the user?
        """

        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.user2.id

            self.user1.following.append(self.user2)
            db.session.commit()

            response = client.get(f'/users/{self.user2.id}/followers')
            html = response.text
            pprint(html)
            self.assertEqual(response.status_code, 200)
            self.assertIn('<p>@testuser</p>', html)

    def test_edit_user_profile(self):
        """
        Can we get a user profile form?
        """

        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.user1.id

            response = client.get('/users/profile')
            html = response.text

            self.assertEqual(response.status_code, 200)
            self.assertIn('Edit Your Profile.', html)


class UserViewsPostTestCase(TestCase):
    """Test views for user POST routes."""

    def setUp(self):
        """Create test client, add sample data."""
        app.app_context().push()
        close_all_sessions()
        db.drop_all()
        db.create_all()

        self.user1 = User.signup('testuser',
                                 'test@test.com',
                                 'testpassword',
                                 None)

        self.user2 = User.signup('testuser2',
                                 'test2@test.com',
                                 'testpassword',
                                 None)

        db.session.commit()

        self.u1_m1 = Message(text='This is a test message',
                             user_id=self.user1.id)

        self.u2_m1 = Message(text='This is another test message',
                             user_id=self.user2.id)

        db.session.add_all([self.u1_m1, self.u2_m1])
        db.session.commit()

        self.client = app.test_client()

    def test_user_signup(self):
        """
        Can we submit a signup form?
        """

        with self.client as client:
            response = client.post('/signup', data={'username': 'newuser',
                                                    'email': 'newuser@new.com',
                                                    'password': 'test123'}, follow_redirects=True)
            html = response.text

            self.assertEqual(response.status_code, 200)
            self.assertIn('alt="Image for newuser"', html)

    def test_user_login(self):
        """
        Can we submit a login form?
        """

        with self.client as client:
            response = client.post('/login', data={'username': 'testuser',
                                                   'password': 'testpassword'}, follow_redirects=True)
            html = response.text
            pprint(html)
            self.assertEqual(response.status_code, 200)
            self.assertIn('@testuser', html)

    def test_add_remove_like(self):
        """
        Can a user like or unlike a message?
        """

        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.user1.id

            # Like the message
            response = client.post(f'/messages/{self.u2_m1.id}/like')

            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(self.user1.likes), 1)

            # Unlike the message
            response = client.post(f'/messages/{self.u2_m1.id}/like')

            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(self.user1.likes), 0)

    def test_follow_unfollow(self):
        """
        Can a user follow and unfollow another user?
        """

        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.user1.id

            # Follow a user
            response = client.post(f'/users/follow/{self.user2.id}')

            self.assertEqual(response.status_code, 302)
            self.assertEqual(len(self.user1.following), 1)
            self.assertEqual(len(self.user2.followers), 1)

            # Unlike the message
            response = client.post(f'/users/stop-following/{self.user2.id}')

            self.assertEqual(len(self.user1.following), 0)
            self.assertEqual(len(self.user2.followers), 0)

    def test_user_profile_edit(self):
        """
        Can we submit a profile update form?
        """

        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.user1.id

            response = client.post('/users/profile',
                                   data={'username': 'editeduser',
                                         'email': 'edited@email.com',
                                         'image_url': 'http://test_image.jpg',
                                         'header_image_url': 'http://test_header.jpg',
                                         'bio': 'edited user bio',
                                         'password': 'testpassword'},
                                   follow_redirects=True)
            html = response.text

            self.assertEqual(response.status_code, 200)
            self.assertIn('@editeduser', html)
            self.assertIn('edited user bio', html)

    def test_delete_user(self):
        """
        Can we delete a user?
        """

        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.user1.id

            response = client.post('/users/delete')

            # We should redirect
            self.assertEqual(response.status_code, 302)

            # The user should be logged out
            with client.session_transaction() as session:
                self.assertNotIn(CURR_USER_KEY, session)

            # We should have one less users
            users = User.query.all()
            self.assertEqual(len(users), 1)


class UserViewsAutharizationTestCase(TestCase):
    """Test views for user authorization."""

    def setUp(self):
        """Create test client, add sample data."""
        app.app_context().push()
        close_all_sessions()
        db.drop_all()
        db.create_all()

        self.user1 = User.signup('testuser',
                                 'test@test.com',
                                 'testpassword',
                                 None)

        self.user2 = User.signup('testuser2',
                                 'test2@test.com',
                                 'testpassword',
                                 None)

        db.session.commit()

        self.u1_m1 = Message(text='This is a test message',
                             user_id=self.user1.id)

        self.u2_m1 = Message(text='This is another test message',
                             user_id=self.user2.id)

        db.session.add_all([self.u1_m1, self.u2_m1])
        db.session.commit()

        self.client = app.test_client()


    def test_edit_user_profile(self):
        """
        Can we see the profile page without loging in?
        """

        with self.client as client:
            response = client.get('/users/profile', follow_redirects=True)
            html = response.text

            self.assertEqual(response.status_code, 200)
            self.assertIn('Access unauthorized', html)

            response = client.post('/users/profile', follow_redirects=True)
            html = response.text

            self.assertEqual(response.status_code, 200)
            self.assertIn('Access unauthorized', html)


    def test_show_user_following(self):
        """
        Can we see who the user is following without loging in?
        """

        with self.client as client:
            response = client.get(f'/users/{self.user1.id}/following', follow_redirects=True)
            html = response.text

            self.assertEqual(response.status_code, 200)
            self.assertIn('Access unauthorized', html)


    def test_show_user_followers(self):
        """
        Can we see who is following the user without logging in?
        """

        with self.client as client:
            response = client.get(f'/users/{self.user1.id}/followers', follow_redirects=True)
            html = response.text

            self.assertEqual(response.status_code, 200)
            self.assertIn('Access unauthorized', html)


    def test_show_user_likes(self):
        """
        Can we which messages the user liked without logging in?
        """

        with self.client as client:
            response = client.get(f'/users/{self.user1.id}/likes', follow_redirects=True)
            html = response.text

            self.assertEqual(response.status_code, 200)
            self.assertIn('Access unauthorized', html)


    def test_delete_user(self):
        """
        Can delete a user without logging in?
        """

        with self.client as client:
            response = client.post(f'/users/delete', follow_redirects=True)
            html = response.text
            pprint(html)

            self.assertEqual(response.status_code, 200)
            self.assertIn('Access unauthorized', html)
