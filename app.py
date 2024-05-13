import os

from flask import Flask, render_template, request, flash, redirect, session, g, jsonify
# from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError

from forms import UserAddForm, LoginForm, MessageForm, UserEditForm
from models import db, connect_db, User, Message, Likes

CURR_USER_KEY = "curr_user"


def create_app(database='postgresql:///warbler', csrf=True):
    app = Flask(__name__)

    # Get DB_URI from environ variable (useful for production/testing) or,
    # if not set there, use development local db.
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        os.environ.get('DATABASE_URL', database))

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ECHO'] = False
    app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = True
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")
    app.config['WTF_CSRF_ENABLED'] = csrf

    # toolbar = DebugToolbarExtension(app)

    connect_db(app)

    ##############################################################################
    # Utils

    @app.context_processor
    def inject_new_message_form():
        form = MessageForm()
        return dict(nmf=form)

    # app name
    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html"), 404

    ##############################################################################
    # User signup/login/logout

    @app.before_request
    def add_user_to_g():
        """If we're logged in, add curr user to Flask global."""

        if CURR_USER_KEY in session:
            g.user = User.query.get(session[CURR_USER_KEY])

        else:
            g.user = None

    def do_login(user):
        """Log in user."""

        session[CURR_USER_KEY] = user.id

    def do_logout():
        """Logout user."""

        flash('You have been logged out!', 'success')
        if CURR_USER_KEY in session:
            del session[CURR_USER_KEY]

    @app.route('/signup', methods=["GET", "POST"])
    def signup():
        """Handle user signup.

        Create new user and add to DB. Redirect to home page.

        If form not valid, present form.

        If the there already is a user with that username: flash message
        and re-present form.
        """

        form = UserAddForm()

        if form.validate_on_submit():
            try:
                user = User.signup(
                    username=form.username.data,
                    password=form.password.data,
                    email=form.email.data,
                    image_url=form.image_url.data or User.image_url.default.arg,
                )
                db.session.commit()

            except IntegrityError:
                flash("Username already taken", 'danger')
                return render_template('users/signup.html', form=form)

            do_login(user)

            return redirect("/")

        else:
            return render_template('users/signup.html', form=form)

    @app.route('/login', methods=["GET", "POST"])
    def login():
        """Handle user login."""

        form = LoginForm()

        if form.validate_on_submit():
            user = User.authenticate(form.username.data,
                                     form.password.data)

            if user:
                do_login(user)
                flash(f"Hello, {user.username}!", "success")
                return redirect("/")

            flash("Invalid credentials.", 'danger')

        return render_template('users/login.html', form=form)

    @app.route('/logout')
    def logout():
        """Handle logout of user."""

        do_logout()

        return redirect('/')

    ##############################################################################
    # General user routes:

    @app.route('/users')
    def list_users():
        """Page with listing of users.

        Can take a 'q' param in querystring to search by that username.
        """
        search = request.args.get('q')

        if not search:
            users = User.query.all()
        else:
            users = User.query.filter(User.username.like(f"%{search}%")).all()

        return render_template('users/index.html', users=users)

    @app.route('/users/<int:user_id>')
    def users_show(user_id):
        """Show user profile."""

        user = User.query.get_or_404(user_id)

        # snagging messages in order from the database;
        # user.messages won't be in order by default
        messages = (Message
                    .query
                    .filter(Message.user_id == user_id)
                    .order_by(Message.timestamp.desc())
                    .limit(100)
                    .all())
        return render_template('users/show.html', user=user, messages=messages)

    @app.route('/users/<int:user_id>/likes')
    def users_likes(user_id):
        """Show list of messages this user liked."""

        if not g.user:
            flash("Access unauthorized.", "danger")
            return redirect("/")

        user = User.query.get_or_404(user_id)

        messages = user.likes

        return render_template('users/likes.html', user=user, messages=messages)

    @app.route('/users/<int:user_id>/following')
    def show_following(user_id):
        """Show list of people this user is following."""

        if not g.user:
            flash("Access unauthorized.", "danger")
            return redirect("/")

        user = User.query.get_or_404(user_id)
        return render_template('users/following.html', user=user)

    @app.route('/users/<int:user_id>/followers')
    def users_followers(user_id):
        """Show list of followers of this user."""

        if not g.user:
            flash("Access unauthorized.", "danger")
            return redirect("/")

        user = User.query.get_or_404(user_id)
        return render_template('users/followers.html', user=user)

    @app.route('/users/follow/<int:follow_id>', methods=['POST'])
    def add_follow(follow_id):
        """Add a follow for the currently-logged-in user."""

        if not g.user:
            flash("Access unauthorized.", "danger")
            return redirect("/")

        followed_user = User.query.get_or_404(follow_id)
        g.user.following.append(followed_user)
        db.session.commit()

        return redirect(f"/users/{g.user.id}/following")

    @app.route('/users/stop-following/<int:follow_id>', methods=['POST'])
    def stop_following(follow_id):
        """Have currently-logged-in-user stop following this user."""

        if not g.user:
            flash("Access unauthorized.", "danger")
            return redirect("/")

        followed_user = User.query.get(follow_id)
        g.user.following.remove(followed_user)
        db.session.commit()

        return redirect(f"/users/{g.user.id}/following")

    @app.route('/users/profile', methods=["GET", "POST"])
    def profile():
        """Update profile for current user."""

        if not g.user:
            flash("Access unauthorized.", "danger")
            return redirect("/")

        form = UserEditForm()

        if form.validate_on_submit():
            # POST - The user submitted the form. Check that they are authorized to edit the profile
            u = User.authenticate(g.user.username, form.password.data)
            if u:
                u.update_profile(form.username.data,
                                 form.email.data,
                                 form.image_url.data,
                                 form.header_image_url.data,
                                 form.bio.data)
                flash('You have successfully updated your profile!', 'success')
                return redirect(f'/users/{g.user.id}')
            else:
                flash(f"You are not allowed to edit the profile for {form.username.data}", "danger")
                return redirect('/')

        # GET - Display the form with the user's current data
        form.username.data = g.user.username
        form.email.data = g.user.email
        form.image_url.data = g.user.image_url
        form.header_image_url.data = g.user.header_image_url
        form.bio.data = g.user.bio

        return render_template('/users/edit.html', form=form)

    @app.route('/users/delete', methods=["POST"])
    def delete_user():
        """Delete user."""

        if not g.user:
            flash("Access unauthorized.", "danger")
            return redirect("/")

        do_logout()

        db.session.delete(g.user)
        db.session.commit()

        return redirect("/signup")

    ##############################################################################
    # Messages routes:

    @app.route('/messages/new', methods=["POST"])
    def messages_add():
        """Add a message:

        Show form if GET. If valid, update message and redirect to user page.
        """

        # Build a form
        form = MessageForm(text=request.form.get('text'),
                           csrf_token=request.form.get('csrf_token'))

        if not g.user:
            flash("Access unauthorized.", "danger")
            return redirect("/")

        if form.validate_on_submit():
            msg = Message(text=form.text.data)
            g.user.messages.append(msg)
            db.session.commit()

            return redirect(f"/users/{g.user.id}")


    @app.route('/messages/<int:message_id>', methods=["GET"])
    def messages_show(message_id):
        """Show a message."""

        msg = Message.query.get_or_404(message_id)
        return render_template('messages/show.html', message=msg)

    @app.route('/messages/<int:message_id>/delete', methods=["POST"])
    def messages_destroy(message_id):
        """Delete a message."""

        msg = Message.query.get_or_404(message_id)

        if not g.user or msg.user_id != g.user.id:
            flash("Access unauthorized.", "danger")
            return redirect("/")

        db.session.delete(msg)
        db.session.commit()

        return redirect(f"/users/{g.user.id}")

    @app.route('/messages/<int:message_id>/like', methods=['POST'])
    def toggle_like(message_id):
        # Only authorized users can like
        if not g.user:
            flash("Access unauthorized.", "danger")
            return redirect("/")

        # Grab the message object
        msg = Message.query.get(message_id)
        msg_liked = False

        # The current user can only like other users messages
        if msg.user_id != g.user.id:
            if msg in g.user.likes:
                # This message was already liked remove the like
                like = Likes.query.filter_by(message_id=msg.id, user_id=g.user.id).delete()
                db.session.commit()
            else:
                g.user.likes.append(msg)
                db.session.commit()
                msg_liked = True
        else:
            return jsonify({'warning': 'You can not like your own Warbles!'}), 403

        return jsonify({'like_status': msg_liked}), 200

    ##############################################################################
    # Homepage and error pages

    @app.route('/')
    def homepage():
        """Show homepage:

        - anon users: no messages
        - logged in: 100 most recent messages of followed_users
        """

        if g.user:
            user_ids = [user.id for user in g.user.following]
            user_ids.append(g.user.id)
            messages = db.session.query(Message).filter(Message.user_id.in_(user_ids)).order_by(
                Message.timestamp.desc()).limit(100).all()

            likes = [message.id for message in g.user.likes]
            return render_template('home.html', messages=messages, likes=likes)

        else:
            return render_template('home-anon.html')

    ##############################################################################
    # Turn off all caching in Flask
    #   (useful for dev; in production, this kind of stuff is typically
    #   handled elsewhere)
    #
    # https://stackoverflow.com/questions/34066804/disabling-caching-in-flask

    @app.after_request
    def add_header(req):
        """Add non-caching headers on every request."""

        req.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        req.headers["Pragma"] = "no-cache"
        req.headers["Expires"] = "0"
        req.headers['Cache-Control'] = 'public, max-age=0'
        return req

    return app

app = create_app()