from datetime import datetime
from app.extensions import db

class FieldRegistry(db.Model):
    __tablename__ = 'field_registry'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    field_name = db.Column(db.String(255), nullable=False)
    normalized_name = db.Column(db.String(255), unique=True, nullable=False, index=True)
    data_type = db.Column(db.String(50), default='VARCHAR', nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    searchable = db.Column(db.Boolean, default=True, nullable=False)
    filterable = db.Column(db.Boolean, default=True, nullable=False)
    usage_count = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "field_name": self.field_name,
            "normalized_name": self.normalized_name,
            "data_type": self.data_type,
            "is_active": self.is_active,
            "searchable": self.searchable,
            "filterable": self.filterable,
            "usage_count": self.usage_count,
            "created_at": self.created_at.isoformat()
        }


class FieldAlias(db.Model):
    __tablename__ = 'field_aliases'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    alias = db.Column(db.String(255), nullable=False)
    normalized_alias = db.Column(db.String(255), unique=True, nullable=False, index=True)
    target_type = db.Column(db.String(50), nullable=False)  # 'master' or 'custom'
    target_identifier = db.Column(db.String(255), nullable=False)  # column name (e.g. 'phone') or registry ID string (e.g. '1')

    def to_dict(self):
        return {
            "id": self.id,
            "alias": self.alias,
            "normalized_alias": self.normalized_alias,
            "target_type": self.target_type,
            "target_identifier": self.target_identifier
        }
