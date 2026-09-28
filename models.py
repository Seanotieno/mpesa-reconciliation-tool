from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Transaction(db.Model):
    """One row from the M-Pesa statement."""
    id = db.Column(db.Integer, primary_key=True)
    receipt_no = db.Column(db.String(20))
    completion_time = db.Column(db.DateTime)
    details = db.Column(db.String(255))
    amount = db.Column(db.Float)          # positive = paid in, negative = withdrawn
    balance = db.Column(db.Float)
    match_status = db.Column(db.String(20), default="unmatched")  # unmatched / matched / mismatched

class SaleRecord(db.Model):
    """One row from the shop owner's own sales log."""
    id = db.Column(db.Integer, primary_key=True)
    sale_date = db.Column(db.Date)
    description = db.Column(db.String(255))
    amount = db.Column(db.Float)
    match_status = db.Column(db.String(20), default="unmatched")

class Match(db.Model):
    """Links one transaction to one sale record when they're confirmed as the same event."""
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey("transaction.id"))
    sale_record_id = db.Column(db.Integer, db.ForeignKey("sale_record.id"))
    match_type = db.Column(db.String(20))     # "exact" or "fuzzy"
    confidence = db.Column(db.Float)          # 1.0 for exact, lower for fuzzy
    created_at = db.Column(db.DateTime, default=datetime.utcnow)