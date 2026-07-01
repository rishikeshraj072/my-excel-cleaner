import os
import pandas as pd
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.file import UploadedFile
from app.models.field import FieldRegistry, FieldAlias
from app.models.record import MasterRecord
from app.repositories.file_repo import FileRepository
from app.repositories.record_repo import RecordRepository
from app.services.excel_service import ExcelService
from app.services.auth_service import AuthService
from app.utils import normalize_header

MOCK_EXCEL_PATH = "mock_data.xlsx"

def create_mock_excel():
    print(f"Creating mock Excel file at: {MOCK_EXCEL_PATH}...")
    
    data = {
        "Name": ["Alice Smith", "Bob Jones", "Charlie Brown", "Diana Prince", "Evan Wright"],
        "Email Address": ["alice@example.com", "bob@example.com", "charlie@example.com", "diana@example.com", "evan@example.com"],
        "Mobile No": ["123-456-7890", "987-654-3210", "555-555-5555", "777-888-9999", "111-222-3333"],
        "Company": ["Google", "Apple", "Netflix", "Amazon", "Meta"],
        "City": ["Mountain View", "Cupertino", "Los Gatos", "Seattle", "Menlo Park"],
        "State": ["CA", "CA", "CA", "WA", "CA"],
        "Country": ["USA", "USA", "USA", "USA", "USA"],
        # Custom properties (already mapped in default aliases or registry)
        "Passport Number": ["P123456", "P234567", "P345678", "P456789", "P567890"],
        "Blood Group": ["O+", "A-", "B+", "AB-", "O-"],
        # Completely new column that should trigger auto-registration
        "Emergency Contact Name": ["John Smith", "Mary Jones", "Sally Brown", "Steve Prince", "Helen Wright"]
    }
    
    df = pd.DataFrame(data)
    df.to_excel(MOCK_EXCEL_PATH, index=False)
    print("Mock Excel file created successfully.")

def run_verification():
    app = create_app()
    with app.app_context():
        # Ensure database tables exist
        print("Ensuring tables are initialized...")
        db.create_all()
        
        # Clear records for test idempotency
        print("Clearing test database records...")
        MasterRecord.query.delete()
        UploadedFile.query.delete()
        db.session.commit()
        
        # 1. Ensure we have at least one user
        user = User.query.first()
        if not user:
            print("Creating test admin user...")
            user = AuthService.register("verify_admin", "verify@example.com", "verifypassword")
        
        # 2. Log file record in uploaded_files
        print("Creating mock upload history entry...")
        uploaded_file = FileRepository.create(
            user_id=user.id,
            filename=MOCK_EXCEL_PATH,
            original_filename="mock_data.xlsx"
        )
        
        # 3. Trigger Ingestion Service
        print("Running Ingestion Pipeline...")
        ExcelService.ingest_file(uploaded_file.id, MOCK_EXCEL_PATH)
        
        # Verify file is completed
        refreshed_file = FileRepository.get_by_id(uploaded_file.id)
        print(f"Ingestion status: {refreshed_file.status}, Row count: {refreshed_file.total_rows}")
        assert refreshed_file.status == 'completed', "Ingestion status should be 'completed'"
        assert refreshed_file.total_rows == 5, "Total row count should be 5"
        
        # 4. Verify Auto-Registration
        print("Verifying auto-registration of 'Emergency Contact Name'...")
        emergency_field = FieldRegistry.query.filter_by(
            normalized_name=normalize_header("Emergency Contact Name")
        ).first()
        assert emergency_field is not None, "Emergency Contact Name field should have been auto-registered"
        print(f"Auto-registered field details: ID #{emergency_field.id}, Name: {emergency_field.field_name}, Usage Count: {emergency_field.usage_count}")
        
        # 5. Query verification
        print("\n--- Verifying Unified Search Engine ---")
        
        # Query 1: Master Relational Filter (City = Seattle)
        print("\nQuery 1: Relational Filter (City = 'Seattle')")
        r1 = RecordRepository.search_records(master_filters={'city': 'Seattle'})
        print(f"Found {r1['total']} records:")
        for item in r1['items']:
            print(f"- {item.name} | {item.company} | {item.city} | Custom JSON: {item.custom_fields}")
        assert r1['total'] == 1, "Should find exactly 1 record in Seattle"
        assert r1['items'][0].name == "Diana Prince"
        
        # Query 2: Custom JSON Filter (Blood Group = 'O-')
        blood_group_field = FieldRegistry.query.filter_by(
            normalized_name=normalize_header("Blood Group")
        ).first()
        assert blood_group_field is not None, "Blood Group field should exist in registry"
        
        print(f"\nQuery 2: Custom JSON Filter (Blood Group [ID: #{blood_group_field.id}] = 'O-')")
        r2 = RecordRepository.search_records(
            custom_field_id=blood_group_field.id,
            custom_field_value="O-"
        )
        print(f"Found {r2['total']} records:")
        for item in r2['items']:
            print(f"- {item.name} | {item.company} | Custom JSON: {item.custom_fields}")
        assert r2['total'] == 1, "Should find exactly 1 record with Blood Group O-"
        assert r2['items'][0].name == "Evan Wright"
        
        # Query 3: Auto-Registered Custom JSON Filter (Emergency Contact Name = 'Sally Brown')
        print(f"\nQuery 3: Auto-Registered JSON Filter (Emergency Contact Name [ID: #{emergency_field.id}] = 'Sally Brown')")
        r3 = RecordRepository.search_records(
            custom_field_id=emergency_field.id,
            custom_field_value="Sally Brown"
        )
        print(f"Found {r3['total']} records:")
        for item in r3['items']:
            print(f"- {item.name} | {item.company} | Custom JSON: {item.custom_fields}")
        assert r3['total'] == 1, "Should find exactly 1 record with Emergency Contact Name Sally Brown"
        assert r3['items'][0].name == "Charlie Brown"
        
        print("\nIngestion and query validation passed successfully!")

if __name__ == "__main__":
    create_mock_excel()
    try:
        run_verification()
    finally:
        # Cleanup mock excel file
        if os.path.exists(MOCK_EXCEL_PATH):
            os.remove(MOCK_EXCEL_PATH)
            print(f"Cleaned up {MOCK_EXCEL_PATH}")
