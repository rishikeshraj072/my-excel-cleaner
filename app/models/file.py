from datetime import datetime
from app.extensions import db

class UploadedFile(db.Model):
    __tablename__ = 'uploaded_files'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('cms_users.id', ondelete='CASCADE'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    total_rows = db.Column(db.Integer, default=0, nullable=False)
    status = db.Column(db.String(50), default='pending', nullable=False)  # pending, processing, completed, failed

    user = db.relationship('User', back_populates='uploaded_files')
    records = db.relationship('MasterRecord', back_populates='uploaded_file', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "filename": self.filename,
            "original_filename": self.original_filename,
            "uploaded_at": self.uploaded_at.isoformat(),
            "total_rows": self.total_rows,
            "status": self.status
        }
