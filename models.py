#!/usr/bin/env python3
"""
Database models for Flight Tracker
SQLAlchemy ORM with SQLite for development, PostgreSQL for production
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

db = SQLAlchemy()


class Flight(db.Model):
    """Flight price record"""
    __tablename__ = 'flights'
    
    id = db.Column(db.Integer, primary_key=True)
    airline = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Integer, nullable=False)  # Per-person, cents
    departure = db.Column(db.String(100))
    arrival = db.Column(db.String(100))
    duration = db.Column(db.String(100))
    stops = db.Column(db.String(50))
    layover = db.Column(db.String(255))
    layover_time = db.Column(db.String(50))
    amadeus_id = db.Column(db.String(100), unique=True)
    source = db.Column(db.String(50), default='amadeus')
    booking_url = db.Column(db.Text)
    
    # Relationships
    collection_id = db.Column(db.Integer, db.ForeignKey('collections.id'))
    collection = db.relationship('Collection', back_populates='flights')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Flight {self.airline} ${self.price/100:.2f}>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'airline': self.airline,
            'price': self.price / 100,  # Convert cents to dollars
            'departure': self.departure,
            'arrival': self.arrival,
            'duration': self.duration,
            'stops': self.stops,
            'layover': self.layover,
            'booking_url': self.booking_url
        }


class Collection(db.Model):
    """Data collection batch"""
    __tablename__ = 'collections'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, unique=True)
    total_flights = db.Column(db.Integer)
    min_price = db.Column(db.Integer)
    max_price = db.Column(db.Integer)
    avg_price = db.Column(db.Float)
    source = db.Column(db.String(50), default='amadeus')
    
    # Relationships
    flights = db.relationship('Flight', back_populates='collection', cascade='all, delete-orphan')
    alerts = db.relationship('Alert', back_populates='collection')
    
    def __repr__(self):
        return f"<Collection {self.timestamp} ({self.total_flights} flights)>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'total_flights': self.total_flights,
            'min_price': self.min_price / 100 if self.min_price else 0,
            'max_price': self.max_price / 100 if self.max_price else 0,
            'avg_price': self.avg_price / 100 if self.avg_price else 0
        }


class Alert(db.Model):
    """Price alert record"""
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    airline = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Integer, nullable=False)  # Per-person, cents
    threshold = db.Column(db.Integer, nullable=False)  # Per-person, cents
    status = db.Column(db.String(50), default='triggered')  # triggered, sent, acknowledged
    
    # Alert methods triggered
    email_sent = db.Column(db.Boolean, default=False)
    sms_sent = db.Column(db.Boolean, default=False)
    slack_sent = db.Column(db.Boolean, default=False)
    discord_sent = db.Column(db.Boolean, default=False)
    
    # Relationships
    collection_id = db.Column(db.Integer, db.ForeignKey('collections.id'))
    collection = db.relationship('Collection', back_populates='alerts')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sent_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f"<Alert {self.airline} ${self.price/100:.2f}>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'airline': self.airline,
            'price': self.price / 100,
            'threshold': self.threshold / 100,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }


class User(db.Model):
    """User preferences and notification settings"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    phone = db.Column(db.String(20))  # For SMS alerts
    slack_webhook = db.Column(db.Text)
    discord_webhook = db.Column(db.Text)
    
    # Notification preferences
    notify_email = db.Column(db.Boolean, default=True)
    notify_sms = db.Column(db.Boolean, default=False)
    notify_slack = db.Column(db.Boolean, default=False)
    notify_discord = db.Column(db.Boolean, default=False)
    
    # Price threshold
    price_threshold = db.Column(db.Integer, default=120000)  # $1200 in cents
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<User {self.email}>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'phone': self.phone,
            'price_threshold': self.price_threshold / 100,
            'notifications': {
                'email': self.notify_email,
                'sms': self.notify_sms,
                'slack': self.notify_slack,
                'discord': self.notify_discord
            }
        }


class PriceHistory(db.Model):
    """Historical price data for analysis and prediction"""
    __tablename__ = 'price_history'
    
    id = db.Column(db.Integer, primary_key=True)
    airline = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Integer, nullable=False)  # Per-person, cents
    date = db.Column(db.Date, nullable=False)
    day_of_week = db.Column(db.Integer)  # 0-6 (Monday-Sunday)
    days_until_flight = db.Column(db.Integer)  # Days from today to June 12
    
    # Timestamps
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('airline', 'date', name='unique_airline_date'),
    )
    
    def __repr__(self):
        return f"<PriceHistory {self.airline} ${self.price/100:.2f} on {self.date}>"
    
    def to_dict(self):
        return {
            'airline': self.airline,
            'price': self.price / 100,
            'date': self.date.isoformat(),
            'days_until_flight': self.days_until_flight
        }


def init_db(app):
    """Initialize database"""
    db.init_app(app)
    with app.app_context():
        db.create_all()


def get_database_url():
    """Get database URL based on environment"""
    env = os.getenv('DATABASE_ENV', 'sqlite')
    
    if env == 'postgresql':
        # PostgreSQL (production)
        return (
            f"postgresql://{os.getenv('DB_USER', 'postgres')}:"
            f"{os.getenv('DB_PASSWORD', 'password')}@"
            f"{os.getenv('DB_HOST', 'localhost')}:"
            f"{os.getenv('DB_PORT', '5432')}/"
            f"{os.getenv('DB_NAME', 'flight_tracker')}"
        )
    else:
        # SQLite (development)
        return f"sqlite:///{os.path.expanduser('~/.flighttracker/data.db')}"
