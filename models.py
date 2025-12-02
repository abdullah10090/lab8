from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

# Initialize SQLAlchemy
db = SQLAlchemy()

class Student(db.Model):
    """Model for the Student table."""
    roll = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    dept = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f"<Student {self.name} (Roll: {self.roll})>"

class User(db.Model, UserMixin):
    """Model for the User table (Task 5)."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False) # Store hash, not password

    def __repr__(self):
        return f"<User {self.username}>"

    def print3():
        print("HEllo world")