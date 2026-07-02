import os
import uuid
import threading
from flask import Blueprint, current_app, request, jsonify, session
from werkzeug.utils import secure_filename
from app.routes.auth import login_required
from app.repositories.file_repo import FileRepository
from app.repositories.field_repo import FieldRepository
from app.repositories.record_repo import RecordRepository
from app.services.excel_service import ExcelService
from app.services.registry_service import RegistryService

api_bp = Blueprint('api', __name__)

@api_bp.route('/api/custom-fields', methods=['GET'])
@login_required
def get_custom_fields():
    fields = RegistryService.get_active_fields()
    # If client requests only searchable fields
    searchable_only = request.args.get('searchable_only', 'false').lower() == 'true'
    if searchable_only:
        fields = [f for f in fields if f.searchable]
    return jsonify([f.to_dict() for f in fields])

@api_bp.route('/api/records', methods=['GET'])
@login_required
def get_records():
    # Extract master relational filters
    master_filters = {
        'name': request.args.get('name', '').strip(),
        'email': request.args.get('email', '').strip(),
        'phone': request.args.get('phone', '').strip(),
        'company': request.args.get('company', '').strip(),
        'city': request.args.get('city', '').strip(),
        'state': request.args.get('state', '').strip(),
        'country': request.args.get('country', '').strip()
    }
    
    custom_field_id = request.args.get('custom_field_id', '').strip()
    custom_field_value = request.args.get('custom_field_value', '').strip()
    
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 25))
    except ValueError:
        page = 1
        per_page = 25
        
    results = RecordRepository.search_records(
        master_filters=master_filters,
        custom_field_id=custom_field_id if custom_field_id else None,
        custom_field_value=custom_field_value if custom_field_value else None,
        page=page,
        per_page=per_page
    )
    
    # Serialize items
    records_list = [item.to_dict() for item in results['items']]
    
    return jsonify({
        "records": records_list,
        "total": results['total'],
        "page": results['page'],
        "pages": results['pages'],
        "per_page": results['per_page']
    })

@api_bp.route('/api/records/<int:record_id>/custom', methods=['GET'])
@login_required
def get_record_custom_fields(record_id):
    record = RecordRepository.get_by_id(record_id)
    if not record:
        return jsonify({"error": "Record not found"}), 404
        
    custom_data = record.custom_fields or {}
    resolved_data = {}
    
    # Resolve numeric registry IDs to human-readable field names
    for key_id_str, val in custom_data.items():
        try:
            field = FieldRepository.get_field_by_id(int(key_id_str))
            if field:
                resolved_data[field.field_name] = val
            else:
                resolved_data[f"Unregistered Field #{key_id_str}"] = val
        except (ValueError, TypeError):
            resolved_data[key_id_str] = val
            
    return jsonify(resolved_data)

@api_bp.route('/api/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in request"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected for upload"}), 400
        
    # Check file extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ('.xlsx', '.xls'):
        return jsonify({"error": "Only Excel files (.xlsx, .xls) are allowed"}), 400
        
    try:
        # Save file securely with UUID to prevent overlaps
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        # Log database row for upload history
        uploaded_file = FileRepository.create(
            user_id=session['user_id'],
            filename=unique_filename,
            original_filename=file.filename
        )
        
        # Convert ORM object to dict before starting thread to prevent concurrent read collisions
        file_dict = uploaded_file.to_dict()
        file_id = uploaded_file.id
        flask_app = current_app._get_current_object()
        
        # Execute parsing pipeline in a background thread to prevent gateway timeout
        def process_upload():
            with flask_app.app_context():
                try:
                    ExcelService.ingest_file(file_id, file_path)
                except Exception:
                    # Exception logging and status transition handled inside ExcelService
                    pass
                finally:
                    # Clean up thread-local database session and return connection to pool
                    from app.extensions import db
                    db.session.remove()
                    
        thread = threading.Thread(target=process_upload)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "message": "Upload successful! Ingestion pipeline started.",
            "file": file_dict
        }), 202
        
    except Exception as e:
        return jsonify({"error": f"Failed to upload file: {str(e)}"}), 500

@api_bp.route('/api/aliases', methods=['POST'])
@login_required
def create_alias():
    alias = request.form.get('alias', '').strip()
    target_type = request.form.get('target_type', '').strip()
    target_identifier = request.form.get('target_identifier', '').strip()
    
    try:
        new_alias = RegistryService.add_alias(alias, target_type, target_identifier)
        return jsonify({
            "message": "Alias mapped successfully!",
            "alias": new_alias.to_dict()
        }), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@api_bp.route('/api/aliases/<int:alias_id>/delete', methods=['POST'])
@login_required
def delete_alias(alias_id):
    success = RegistryService.delete_alias(alias_id)
    if success:
        return jsonify({"message": "Alias mapping deleted"}), 200
    return jsonify({"error": "Alias mapping not found"}), 404

@api_bp.route('/api/fields/<int:field_id>/status', methods=['POST'])
@login_required
def update_field_status(field_id):
    data = request.json or {}
    
    is_active = data.get('is_active')
    searchable = data.get('searchable')
    filterable = data.get('filterable')
    
    updated_field = RegistryService.update_field(
        field_id,
        is_active=is_active,
        searchable=searchable,
        filterable=filterable
    )
    
    if updated_field:
        return jsonify({
            "message": "Field status updated successfully",
            "field": updated_field.to_dict()
        }), 200
    return jsonify({"error": "Custom field not found in registry"}), 404

@api_bp.route('/api/clean', methods=['POST'])
@login_required
def clean_records():
    from app.services.cleaner_service import CleanerService
    
    data = request.json or {}
    rules = data.get('rules', [])
    
    if not rules:
        return jsonify({"error": "No data cleaning rules specified"}), 400
        
    try:
        results = CleanerService.clean_pipeline(rules)
        return jsonify({
            "message": "Cleaning pipeline executed successfully",
            "total_deleted": results["total_deleted"],
            "details": results["details"]
        }), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Internal error executing clean rules: {str(e)}"}), 500
