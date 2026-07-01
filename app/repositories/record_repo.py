from sqlalchemy import func
from app.extensions import db
from app.models.record import MasterRecord

class RecordRepository:
    @staticmethod
    def bulk_insert(records_list):
        """
        Inserts a list of dictionaries into master_records in a single batch.
        records_list: list of dicts, each dict matches MasterRecord column names and values.
        """
        if not records_list:
            return
        db.session.bulk_insert_mappings(MasterRecord, records_list)
        db.session.commit()

    @staticmethod
    def get_by_id(record_id):
        return MasterRecord.query.get(record_id)

    @staticmethod
    def search_records(master_filters=None, custom_field_id=None, custom_field_value=None, page=1, per_page=25):
        """
        Unified search querying relational fields via SQL WHERE and dynamic JSON attributes
        using MySQL 8 native JSON functions via SQLAlchemy.
        
        master_filters: dict of {column_name: value} (e.g. {'name': 'John', 'city': 'Dallas'})
        custom_field_id: str or int (e.g. 1 representing 'Passport Number' registry ID)
        custom_field_value: str search value
        """
        query = MasterRecord.query
        
        # Apply Master relational filters (case-insensitive partial match)
        if master_filters:
            for field, value in master_filters.items():
                if value and hasattr(MasterRecord, field):
                    col = getattr(MasterRecord, field)
                    query = query.filter(col.ilike(f"%{value}%"))

        # Apply Custom JSON filter using MySQL native JSON operations
        if custom_field_id and custom_field_value:
            # Construct JSON path path: e.g. '$."1"'
            json_path = f'$."{custom_field_id}"'
            
            # Using JSON_UNQUOTE(JSON_EXTRACT(custom_fields, '$."1"'))
            # We match partial strings case-insensitively using ILIKE
            query = query.filter(
                func.json_unquote(
                    func.json_extract(MasterRecord.custom_fields, json_path)
                ).ilike(f"%{custom_field_value}%")
            )
            
        # Paginate results
        pagination = query.order_by(MasterRecord.created_at.desc()).paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return {
            "items": pagination.items,
            "total": pagination.total,
            "page": pagination.page,
            "pages": pagination.pages,
            "per_page": pagination.per_page
        }
