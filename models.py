from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False, index=True)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    households = db.relationship('Household', backref='owner', lazy=True, cascade='all, delete-orphan')
    preferences = db.relationship('UserPreference', backref='user', uselist=False, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


class Household(db.Model):
    __tablename__ = 'households'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    household_name = db.Column(db.String(150), nullable=False)
    num_members = db.Column(db.Integer, default=1)
    location = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    food_items = db.relationship('FoodItem', backref='household', lazy=True, cascade='all, delete-orphan')
    waste_records = db.relationship('WasteRecord', backref='household', lazy=True, cascade='all, delete-orphan')
    alerts = db.relationship('Alert', backref='household', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Household {self.household_name}>'


class FoodCategory(db.Model):
    __tablename__ = 'food_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String(100), unique=True, nullable=False)
    perishability_level = db.Column(db.Enum('Low', 'Medium', 'High'), default='Medium')
    avg_shelf_life_days = db.Column(db.Integer, default=7)
    
    # Relationships
    food_items = db.relationship('FoodItem', backref='category', lazy=True)
    
    def __repr__(self):
        return f'<FoodCategory {self.category_name}>'


class FoodItem(db.Model):
    __tablename__ = 'food_items'
    
    id = db.Column(db.Integer, primary_key=True)
    household_id = db.Column(db.Integer, db.ForeignKey('households.id'), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('food_categories.id'), nullable=False)
    item_name = db.Column(db.String(150), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), nullable=False)
    unit = db.Column(db.String(50), nullable=False)
    purchase_date = db.Column(db.Date, nullable=False)
    expiry_date = db.Column(db.Date, nullable=False, index=True)
    initial_quantity = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.Enum('Active', 'Consumed', 'Wasted', 'Donated'), default='Active', index=True)
    waste_risk_score = db.Column(db.Numeric(5, 2), default=0, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    consumption_logs = db.relationship('ConsumptionLog', backref='food_item', lazy=True, cascade='all, delete-orphan')
    waste_records = db.relationship('WasteRecord', backref='food_item', lazy=True, cascade='all, delete-orphan')
    alerts = db.relationship('Alert', backref='food_item', lazy=True, cascade='all, delete-orphan')
    recommendations = db.relationship('Recommendation', backref='food_item', lazy=True, cascade='all, delete-orphan')
    
    @property
    def days_until_expiry(self):
        if self.expiry_date:
            delta = self.expiry_date - datetime.now().date()
            return delta.days
        return None
    
    @property
    def consumption_rate(self):
        """Calculate daily consumption rate"""
        if not self.consumption_logs:
            return 0
        
        days_since_purchase = (datetime.now().date() - self.purchase_date).days
        if days_since_purchase <= 0:
            return 0
        
        total_consumed = sum(float(log.quantity_consumed) for log in self.consumption_logs)
        return total_consumed / days_since_purchase
    
    def __repr__(self):
        return f'<FoodItem {self.item_name}>'


class ConsumptionLog(db.Model):
    __tablename__ = 'consumption_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    food_item_id = db.Column(db.Integer, db.ForeignKey('food_items.id'), nullable=False, index=True)
    consumption_date = db.Column(db.Date, nullable=False, index=True)
    quantity_consumed = db.Column(db.Numeric(10, 2), nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ConsumptionLog {self.id}>'


class WasteRecord(db.Model):
    __tablename__ = 'waste_records'
    
    id = db.Column(db.Integer, primary_key=True)
    food_item_id = db.Column(db.Integer, db.ForeignKey('food_items.id'), nullable=False)
    household_id = db.Column(db.Integer, db.ForeignKey('households.id'), nullable=False, index=True)
    waste_date = db.Column(db.Date, nullable=False, index=True)
    quantity_wasted = db.Column(db.Numeric(10, 2), nullable=False)
    waste_reason = db.Column(db.Enum('Expired', 'Spoiled', 'Over-purchased', 'Forgot', 'Other'), nullable=False)
    estimated_value = db.Column(db.Numeric(10, 2))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<WasteRecord {self.id}>'


class Alert(db.Model):
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    food_item_id = db.Column(db.Integer, db.ForeignKey('food_items.id'), nullable=False)
    household_id = db.Column(db.Integer, db.ForeignKey('households.id'), nullable=False, index=True)
    alert_type = db.Column(db.Enum('High Risk', 'Medium Risk', 'Expiring Soon', 'Expired'), nullable=False)
    alert_message = db.Column(db.Text, nullable=False)
    recommendation = db.Column(db.Text)
    is_read = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<Alert {self.alert_type}>'


class Recommendation(db.Model):
    __tablename__ = 'recommendations'
    
    id = db.Column(db.Integer, primary_key=True)
    food_item_id = db.Column(db.Integer, db.ForeignKey('food_items.id'), nullable=False, index=True)
    recommendation_type = db.Column(db.Enum('Use Soon', 'Preserve', 'Donate', 'Recipe Suggestion'), nullable=False)
    recommendation_text = db.Column(db.Text, nullable=False)
    priority = db.Column(db.Integer, default=1, index=True)
    is_completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Recommendation {self.recommendation_type}>'


class UserPreference(db.Model):
    __tablename__ = 'user_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    alert_frequency = db.Column(db.Enum('Real-time', 'Daily', 'Weekly'), default='Daily')
    email_notifications = db.Column(db.Boolean, default=True)
    waste_threshold = db.Column(db.Numeric(5, 2), default=50.00)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<UserPreference for User {self.user_id}>'