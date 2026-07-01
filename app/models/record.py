from datetime import datetime
from app.extensions import db

class MasterRecord(db.Model):
    __tablename__ = 'master_records'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    file_id = db.Column(db.Integer, db.ForeignKey('uploaded_files.id', ondelete='CASCADE'), nullable=False)
    
    # Rigid relational columns (indexed & nullable)
    name = db.Column(db.String(255), nullable=True, index=True)
    email = db.Column(db.String(255), nullable=True, index=True)
    phone = db.Column(db.String(50), nullable=True, index=True)
    company = db.Column(db.String(255), nullable=True, index=True)
    city = db.Column(db.String(100), nullable=True, index=True)
    state = db.Column(db.String(100), nullable=True, index=True)
    country = db.Column(db.String(100), nullable=True, index=True)
    
    # Flexible JSON column for custom dynamic attributes
    # Schema: {"<registry_id>": "<value>"} (e.g. {"1": "8783787837"})
    custom_fields = db.Column(db.JSON, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    uploaded_file = db.relationship('UploadedFile', back_populates='records')

    def to_dict(self):
        return {
            "id": self.id,
            "file_id": self.file_id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "company": self.company,
            "city": self.city,
            "state": self.state,
            "country": self.country,
            "custom_fields": self.custom_fields or {},
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
