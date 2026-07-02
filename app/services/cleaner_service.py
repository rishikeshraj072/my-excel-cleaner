import re
import logging
from app.extensions import db
from app.models.record import MasterRecord
from app.models.field import FieldRegistry
from app.models.cleaning_log import CleaningLog

logger = logging.getLogger(__name__)

MASTER_COLUMNS = {'name', 'email', 'phone', 'company', 'city', 'state', 'country'}

class CleanerService:
    @staticmethod
    def get_column_display_name(column_identifier):
        """Resolves internal column names or IDs to human-readable titles"""
        if column_identifier in MASTER_COLUMNS:
            return column_identifier.capitalize()
        try:
            field = FieldRegistry.query.get(int(column_identifier))
            return field.field_name if field else f"Custom Field #{column_identifier}"
        except (ValueError, TypeError):
            return str(column_identifier)

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

    @classmethod
    def clean_pipeline(cls, rules):
        """
        Applies a batch pipeline of cleaning rules sequentially.
        rules: list of dicts [{"column": "phone", "rule": "valid_phone"}, ...]
        Returns a summary dictionary of executed operations.
        """
        results_details = []
        total_deleted = 0
        
        for rule_cfg in rules:
            col_identifier = rule_cfg.get('column', '').strip()
            rule_type = rule_cfg.get('rule', '').strip()
            
            if not col_identifier or not rule_type:
                continue
                
            # Execute standard single column clean
            deleted_count = cls.clean_records(col_identifier, rule_type)
            col_display = cls.get_column_display_name(col_identifier)
            
            # Record execution in the CleaningLog database table
            log_entry = CleaningLog(
                column_identifier=col_identifier,
                column_name=col_display,
                rule_applied=rule_type,
                records_deleted=deleted_count
            )
            db.session.add(log_entry)
            
            total_deleted += deleted_count
            results_details.append({
                "column_identifier": col_identifier,
                "column_name": col_display,
                "rule": rule_type,
                "deleted": deleted_count
            })
            
        # Commit all logging entries
        db.session.commit()
        
        return {
            "total_deleted": total_deleted,
            "details": results_details
        }
