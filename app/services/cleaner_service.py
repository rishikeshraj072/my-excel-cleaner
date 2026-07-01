import re
import logging
from app.extensions import db
from app.models.record import MasterRecord

logger = logging.getLogger(__name__)

MASTER_COLUMNS = {'name', 'email', 'phone', 'company', 'city', 'state', 'country'}

class CleanerService:
    @staticmethod
    def clean_records(column_identifier, rule):
        """
        Applies a data cleaning rule to master_records.
        Returns the number of deleted records.
        
        column_identifier: str (e.g. 'phone' or '1' representing registry field ID)
        rule: str ('not_null', 'no_duplicate', 'valid_email', 'valid_phone')
        """
        logger.info(f"Running clean rule '{rule}' on column '{column_identifier}'")
        
        is_master = column_identifier in MASTER_COLUMNS
        
        # Load all records to process in memory
        records = MasterRecord.query.all()
        to_delete_ids = []
        
        # Helper to extract value from a record
        def get_value(record):
            if is_master:
                return getattr(record, column_identifier, None)
            else:
                custom_data = record.custom_fields or {}
                return custom_data.get(str(column_identifier), None)
        
        # Apply checks
        if rule == 'not_null':
            for r in records:
                val = get_value(r)
                if val is None or str(val).strip() == "" or str(val).strip().lower() in ('nan', 'nat', 'null'):
                    to_delete_ids.append(r.id)
                    
        elif rule == 'no_duplicate':
            seen_values = set()
            for r in records:
                val = get_value(r)
                val_str = str(val).strip().lower() if val is not None else ""
                
                # Check for duplicates of non-empty values
                if val_str:
                    if val_str in seen_values:
                        to_delete_ids.append(r.id)
                    else:
                        seen_values.add(val_str)
                        
        elif rule == 'valid_email':
            # Strict email pattern
            email_regex = re.compile(r'^[\w\.\+\-]+@[\w\.\-]+\.[\w]{2,6}$')
            for r in records:
                val = get_value(r)
                if val is not None:
                    val_str = str(val).strip()
                    if val_str and not email_regex.match(val_str):
                        to_delete_ids.append(r.id)
                        
        elif rule == 'valid_phone':
            # Phone validation: must contain at least 7 digits
            digit_regex = re.compile(r'\d')
            for r in records:
                val = get_value(r)
                if val is not None:
                    val_str = str(val).strip()
                    if val_str:
                        digits = digit_regex.findall(val_str)
                        if len(digits) < 7:
                            to_delete_ids.append(r.id)
        else:
            raise ValueError(f"Unknown cleaning rule: '{rule}'")
            
        # Delete rows that violate the constraint
        deleted_count = 0
        if to_delete_ids:
            chunk_size = 500
            for i in range(0, len(to_delete_ids), chunk_size):
                chunk = to_delete_ids[i:i+chunk_size]
                MasterRecord.query.filter(MasterRecord.id.in_(chunk)).delete(synchronize_session=False)
            db.session.commit()
            deleted_count = len(to_delete_ids)
            logger.info(f"Successfully deleted {deleted_count} records violating rule '{rule}' on column '{column_identifier}'")
            
        return deleted_count
