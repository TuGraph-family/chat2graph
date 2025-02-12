from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
import pytz

db = SQLAlchemy()


class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc), nullable=False)
    name = db.Column(db.String(80), nullable=True)

    messages = db.relationship(
        "Message", backref="session", lazy=True, cascade="all, delete-orphan"
    )


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(
        db.Integer, db.ForeignKey("session.id", ondelete="CASCADE"), nullable=True
    )
    role = db.Column(db.String(20), nullable=False)  # 'user' or 'assistant'
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc), nullable=False)
