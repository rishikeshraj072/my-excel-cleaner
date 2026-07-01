from app.extensions import db
from app.models.file import UploadedFile

class FileRepository:
    @staticmethod
    def create(user_id, filename, original_filename):
        uploaded_file = UploadedFile(
            user_id=user_id,
            filename=filename,
            original_filename=original_filename,
            status='pending'
        )
        db.session.add(uploaded_file)
        db.session.commit()
        return uploaded_file

    @staticmethod
    def get_by_id(file_id):
        return UploadedFile.query.get(file_id)

    @staticmethod
    def update_status(file_id, status, total_rows=None):
        uploaded_file = UploadedFile.query.get(file_id)
        if uploaded_file:
            uploaded_file.status = status
            if total_rows is not None:
                uploaded_file.total_rows = total_rows
            db.session.commit()
        return uploaded_file

    @staticmethod
    def get_all():
        return UploadedFile.query.order_by(UploadedFile.uploaded_at.desc()).all()
