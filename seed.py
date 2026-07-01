import logging
from sqlalchemy import create_engine, text
from app import create_app
from app.extensions import db
from app.config import Config
from app.models.user import User
from app.models.field import FieldRegistry, FieldAlias
from app.services.auth_service import AuthService
from app.services.registry_service import RegistryService
from app.utils import normalize_header

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_database_if_not_exists():
    db_uri = Config.SQLALCHEMY_DATABASE_URI
    if "mysql" not in db_uri:
        logger.info("Not using MySQL. Skipping database creation step.")
        return
        
    try:
        # Separate DB name from URI
        # mysql+pymysql://user:pass@host:port/dbname[?params]
        parts = db_uri.rsplit('/', 1)
        base_uri = parts[0]
        db_name = parts[1]
        if '?' in db_name:
            db_name = db_name.split('?')[0]
            
        logger.info(f"Connecting to MySQL server at {base_uri} to verify database '{db_name}'...")
        temp_engine = create_engine(base_uri)
        with temp_engine.connect() as conn:
            # MySQL 8 command to create database
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"))
            conn.commit()
        logger.info(f"Database '{db_name}' verified/created successfully.")
        temp_engine.dispose()
    except Exception as e:
        logger.warning(f"Could not automatically create database. Reason: {e}")
        logger.warning("Continuing assuming database exists and user has correct privileges...")

def seed_data():
    app = create_app()
    with app.app_context():
        logger.info("Creating database tables...")
        db.create_all()
        
        # 1. Seed Admin User
        admin_email = "admin@example.com"
        existing_user = User.query.filter_by(email=admin_email).first()
        if not existing_user:
            logger.info("Seeding default admin user...")
            AuthService.register(
                username="admin",
                email=admin_email,
                password="adminpassword"
            )
            logger.info("Admin user created (User: admin / Password: adminpassword)")
        else:
            logger.info("Admin user already exists.")
            
        # 2. Seed Default Custom Fields in Registry
        default_fields = [
            {"name": "Passport Number", "type": "VARCHAR"},
            {"name": "Blood Group", "type": "VARCHAR"},
            {"name": "National ID", "type": "VARCHAR"},
            {"name": "Birth Date", "type": "VARCHAR"}
        ]
        
        registered_fields = {}
        for f in default_fields:
            norm = normalize_header(f["name"])
            existing = FieldRegistry.query.filter_by(normalized_name=norm).first()
            if not existing:
                logger.info(f"Seeding custom field: {f['name']}")
                field = FieldRegistry(
                    field_name=f["name"],
                    normalized_name=norm,
                    data_type=f["type"],
                    usage_count=0
                )
                db.session.add(field)
                db.session.flush() # populated id
                registered_fields[norm] = field.id
            else:
                registered_fields[norm] = existing.id
        db.session.commit()

        # 3. Seed Default Field Aliases
        # Structure: (Alias String, Target Type, Target Identifier)
        default_aliases = [
            # Master columns mappings
            ("Full Name", "master", "name"),
            ("Name", "master", "name"),
            ("Email Address", "master", "email"),
            ("E-mail", "master", "email"),
            ("Contact Number", "master", "phone"),
            ("Mobile No", "master", "phone"),
            ("Mobile Number", "master", "phone"),
            ("Company Name", "master", "company"),
            ("Organization", "master", "company"),
            ("State Name", "master", "state"),
            ("Country Name", "master", "country"),
            # Custom columns mappings (resolved dynamically)
            ("Passport No", "custom", "passport_number"),
            ("Passport", "custom", "passport_number"),
            ("Blood Type", "custom", "blood_group"),
            ("Date of Birth", "custom", "birth_date"),
            ("DOB", "custom", "birth_date")
        ]
        
        for alias, t_type, t_id in default_aliases:
            norm = normalize_header(alias)
            existing = FieldAlias.query.filter_by(normalized_alias=norm).first()
            if not existing:
                # If target is custom, resolve custom normalized name to ID string
                resolved_id = t_id
                if t_type == "custom":
                    resolved_id = str(registered_fields.get(t_id))
                    if resolved_id == 'None':
                        # Skip if custom field wasn't successfully seeded
                        continue
                
                logger.info(f"Seeding alias mapping: '{alias}' -> {t_type} ({resolved_id})")
                new_alias = FieldAlias(
                    alias=alias,
                    normalized_alias=norm,
                    target_type=t_type,
                    target_identifier=resolved_id
                )
                db.session.add(new_alias)
        
        db.session.commit()
        logger.info("Seeding process completed successfully!")

if __name__ == "__main__":
    create_database_if_not_exists()
    seed_data()
