import os
import math
import logging
import pandas as pd
from app.extensions import db
from app.repositories.file_repo import FileRepository
from app.repositories.field_repo import FieldRepository
from app.repositories.record_repo import RecordRepository
from app.utils import normalize_header

logger = logging.getLogger(__name__)

MASTER_COLUMNS = {'name', 'email', 'phone', 'company', 'city', 'state', 'country'}

class ExcelService:
    @staticmethod
    def ingest_file(file_id, file_path):
        """
        Synchronously parses and ingests an Excel file into the database.
        Runs under application context.
        """
        logger.info(f"Starting ingestion for file ID {file_id} from {file_path}")
        FileRepository.update_status(file_id, 'processing')
        
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found at: {file_path}")
                
            # 1. Header Extraction
            # Read first row only to extract headers
            df_headers = pd.read_excel(file_path, nrows=0)
            headers = df_headers.columns.tolist()
            
            if not headers:
                raise ValueError("Excel file contains no columns or is empty")
                
            # 2. Mapping & Classification
            header_mapping = {}
            
            for header in headers:
                norm = normalize_header(header)
                if not norm:
                    # Skip columns that normalize to nothing (e.g. empty headers or special chars only)
                    logger.warning(f"Skipping empty or special-character-only column header: '{header}'")
                    continue
                
                # Check 1: Direct Master Column match
                if norm in MASTER_COLUMNS:
                    header_mapping[header] = {
                        'type': 'master',
                        'target': norm
                    }
                    continue
                
                # Check 2: Match aliases (e.g. "Mobile No" -> "phone")
                alias = FieldRepository.get_alias_by_normalized(norm)
                if alias:
                    if alias.target_type == 'master':
                        header_mapping[header] = {
                            'type': 'master',
                            'target': alias.target_identifier
                        }
                    else:  # custom
                        header_mapping[header] = {
                            'type': 'custom',
                            'target': str(alias.target_identifier)
                        }
                        FieldRepository.increment_field_usage(int(alias.target_identifier))
                    continue
                
                # Check 3: Check Field Registry
                registry_field = FieldRepository.get_field_by_normalized_name(norm)
                if registry_field:
                    header_mapping[header] = {
                        'type': 'custom',
                        'target': str(registry_field.id)
                    }
                    FieldRepository.increment_field_usage(registry_field.id)
                    continue
                
                # Check 4: New custom field creation
                new_field = FieldRepository.create_field(
                    field_name=header,
                    normalized_name=norm,
                    data_type='VARCHAR'
                )
                header_mapping[header] = {
                    'type': 'custom',
                    'target': str(new_field.id)
                }
            
            # 3. Read Rows & Batch Insert
            df = pd.read_excel(file_path)
            total_rows = len(df)
            
            records_to_insert = []
            batch_size = 1000
            
            for _, row in df.iterrows():
                record_dict = {
                    'file_id': file_id,
                    'name': None,
                    'email': None,
                    'phone': None,
                    'company': None,
                    'city': None,
                    'state': None,
                    'country': None,
                    'custom_fields': {}
                }
                
                for header, val in row.items():
                    if header not in header_mapping:
                        continue
                    
                    # Clean pandas nan/nat values
                    if pd.isnull(val) or str(val).strip().lower() in ('nan', 'nat', 'null'):
                        cleaned_val = None
                    else:
                        cleaned_val = val
                        
                    if cleaned_val is None:
                        continue
                        
                    mapping = header_mapping[header]
                    if mapping['type'] == 'master':
                        record_dict[mapping['target']] = str(cleaned_val)
                    else:  # custom
                        # custom fields in JSON: {"<registry_id>": "<value>"}
                        record_dict['custom_fields'][mapping['target']] = str(cleaned_val)
                
                # If custom fields dict is empty, store as None/null in DB
                if not record_dict['custom_fields']:
                    record_dict['custom_fields'] = None
                
                records_to_insert.append(record_dict)
                
                # Perform bulk insertion in chunks
                if len(records_to_insert) >= batch_size:
                    RecordRepository.bulk_insert(records_to_insert)
                    records_to_insert = []
                    
            # Insert residual records
            if records_to_insert:
                RecordRepository.bulk_insert(records_to_insert)
                
            # Update file status to completed
            FileRepository.update_status(file_id, 'completed', total_rows=total_rows)
            logger.info(f"Successfully processed file {file_id}. Row count: {total_rows}")
            
        except Exception as e:
            logger.error(f"Error processing file {file_id}: {str(e)}", exc_info=True)
            FileRepository.update_status(file_id, 'failed')
            raise e
