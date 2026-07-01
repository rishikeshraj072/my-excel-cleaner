from flask import Blueprint, render_template, redirect, url_for, session
from app.routes.auth import login_required
from app.services.registry_service import RegistryService
from app.repositories.file_repo import FileRepository

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    from app.models.record import MasterRecord
    from app.models.field import FieldRegistry
    from app.models.file import UploadedFile
    
    total_records = MasterRecord.query.count()
    total_fields = FieldRegistry.query.filter_by(is_active=True).count()
    total_files = UploadedFile.query.count()
    last_file = UploadedFile.query.order_by(UploadedFile.uploaded_at.desc()).first()
    
    custom_fields = RegistryService.get_active_fields()
    
    return render_template(
        'dashboard.html',
        custom_fields=custom_fields,
        total_records=total_records,
        total_fields=total_fields,
        total_files=total_files,
        last_file=last_file
    )

@main_bp.route('/registry')
@login_required
def registry():
    fields = RegistryService.get_all_fields()
    return render_template('registry.html', fields=fields)

@main_bp.route('/aliases')
@login_required
def aliases():
    # Need existing aliases and active registry fields (to link them)
    aliases_list = RegistryService.get_all_aliases()
    custom_fields = RegistryService.get_active_fields()
    return render_template('aliases.html', aliases=aliases_list, custom_fields=custom_fields)

@main_bp.route('/cleaner')
@login_required
def cleaner():
    custom_fields = RegistryService.get_active_fields()
    return render_template('cleaner.html', custom_fields=custom_fields)

@main_bp.route('/history')
@login_required
def history():
    # Audit trail of uploaded sheets and processing status
    uploads = FileRepository.get_all()
    return render_template('history.html', uploads=uploads)
