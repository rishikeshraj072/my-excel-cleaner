from app.repositories.field_repo import FieldRepository
from app.utils import normalize_header

MASTER_COLUMNS = {'name', 'email', 'phone', 'company', 'city', 'state', 'country'}

class RegistryService:
    @staticmethod
    def get_all_fields():
        return FieldRepository.get_all_fields()

    @staticmethod
    def get_active_fields():
        return FieldRepository.get_active_fields()

    @staticmethod
    def get_field(field_id):
        return FieldRepository.get_field_by_id(field_id)

    @staticmethod
    def update_field(field_id, is_active=None, searchable=None, filterable=None):
        return FieldRepository.update_field_status(
            field_id, 
            is_active=is_active, 
            searchable=searchable, 
            filterable=filterable
        )

    @staticmethod
    def get_all_aliases():
        return FieldRepository.get_all_aliases()

    @staticmethod
    def add_alias(alias, target_type, target_identifier):
        if not alias:
            raise ValueError("Alias string cannot be empty")
            
        normalized = normalize_header(alias)
        if not normalized:
            raise ValueError(f"Alias '{alias}' contains no alphanumeric characters after normalization")

        # Check if alias already exists
        existing = FieldRepository.get_alias_by_normalized(normalized)
        if existing:
            raise ValueError(f"Alias variation '{alias}' (normalized: '{normalized}') is already mapped to {existing.target_type} ({existing.target_identifier})")

        # Validate target type & identifier
        if target_type == 'master':
            if target_identifier not in MASTER_COLUMNS:
                raise ValueError(f"Invalid master column target: '{target_identifier}'. Must be one of {MASTER_COLUMNS}")
        elif target_type == 'custom':
            # Check if custom field exists
            field = FieldRepository.get_field_by_id(int(target_identifier))
            if not field:
                raise ValueError(f"Custom field with ID '{target_identifier}' does not exist in registry")
        else:
            raise ValueError("Target type must be 'master' or 'custom'")

        return FieldRepository.create_alias(alias, normalized, target_type, str(target_identifier))

    @staticmethod
    def delete_alias(alias_id):
        return FieldRepository.delete_alias(alias_id)
