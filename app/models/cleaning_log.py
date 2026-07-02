from datetime import datetime
from app.extensions import db

class CleaningLog(db.Model):
    __tablename__ = 'cms_cleaning_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    executed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    column_identifier = db.Column(db.String(50), nullable=False)
    column_name = db.Column(db.String(100), nullable=False)
    rule_applied = db.Column(db.String(50), nullable=False)
    records_deleted = db.Column(db.Integer, default=0, nullable=False)
    
    def __init__(self, column_identifier, column_name, rule_applied, records_deleted=0):
        self.column_identifier = column_identifier
        self.column_name = column_name
        self.rule_applied = rule_applied
        self.records_deleted = records_deleted
    
    def to_dict(self):
        return {
            "id": self.id,
            "executed_at": self.executed_at.isoformat(),
            "column_identifier": self.column_identifier,
            "column_name": self.column_name,
            "rule_applied": self.rule_applied,
            "records_deleted": self.records_deleted
        }
