"""Seed database with sample data from CSV Files."""

from csv import DictReader
from app import db, create_app
from models import User, Message, Follows

app = create_app()
with app.app_context():
    db.drop_all()
    db.create_all()

    with open('generator/users.csv') as users:
        db.session.bulk_insert_mappings(User, DictReader(users))

    with open('generator/messages.csv') as messages:
        db.session.bulk_insert_mappings(Message, DictReader(messages))

    with open('generator/follows.csv') as follows:
        db.session.bulk_insert_mappings(Follows, DictReader(follows))

    db.session.commit()
