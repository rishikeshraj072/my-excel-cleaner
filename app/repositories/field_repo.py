from app.extensions import db
from app.models.field import FieldRegistry, FieldAlias

class FieldRepository:
    # --- FieldRegistry Operations ---
    @staticmethod
    def get_field_by_id(field_id):
        return FieldRegistry.query.get(field_id)

    @staticmethod
    def get_field_by_normalized_name(normalized_name):
        return FieldRegistry.query.filter_by(normalized_name=normalized_name).first()

    @staticmethod
    def create_field(field_name, normalized_name, data_type='VARCHAR', is_active=True, searchable=True, filterable=True):
        field = FieldRegistry(
            field_name=field_name,
            normalized_name=normalized_name,
            data_type=data_type,
            is_active=is_active,
            searchable=searchable,
            filterable=filterable,
            usage_count=1  # Starts at 1 when first registered / discovered
        )
        db.session.add(field)
        db.session.commit()
        return field

    @staticmethod
    def increment_field_usage(field_id):
        field = FieldRegistry.query.get(field_id)
        if field:
            field.usage_count += 1
            db.session.commit()
        return field

    @staticmethod
    def get_all_fields():
        return FieldRegistry.query.order_by(FieldRegistry.usage_count.desc()).all()

    @staticmethod
    def get_active_fields():
        return FieldRegistry.query.filter_by(is_active=True).all()

    @staticmethod
    def update_field_status(field_id, is_active=None, searchable=None, filterable=None):
        field = FieldRegistry.query.get(field_id)
        if field:
            if is_active is not None:
                field.is_active = is_active
            if searchable is not None:
                field.searchable = searchable
            if filterable is not None:
                field.filterable = filterable
            db.session.commit()
        return field

    # --- FieldAlias Operations ---
    @staticmethod
    def get_alias_by_normalized(normalized_alias):
        return FieldAlias.query.filter_by(normalized_alias=normalized_alias).first()

    @staticmethod
    def create_alias(alias, normalized_alias, target_type, target_identifier):
        field_alias = FieldAlias(
            alias=alias,
            normalized_alias=normalized_alias,
            target_type=target_type,
            target_identifier=target_identifier
        )
        db.session.add(field_alias)
        db.session.commit()
        return field_alias

    @staticmethod
    def get_all_aliases():
        return FieldAlias.query.order_by(FieldAlias.alias.asc()).all()

    @staticmethod
    def delete_alias(alias_id):
        alias = FieldAlias.query.get(alias_id)
        if alias:
            db.session.delete(alias)
            db.session.commit()
            return True
        return False
