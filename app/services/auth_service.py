from werkzeug.security import generate_password_hash, check_password_hash
from app.repositories.user_repo import UserRepository

class AuthService:
    @staticmethod
    def register(username, email, password):
        if not username or not email or not password:
            raise ValueError("All fields are required")
            
        # Check if username exists
        if UserRepository.get_by_username(username):
            raise ValueError("Username is already taken")
            
        # Check if email exists
        if UserRepository.get_by_email(email):
            raise ValueError("Email is already registered")
            
        password_hash = generate_password_hash(password)
        return UserRepository.create(username, email, password_hash)

    @staticmethod
    def authenticate(username_or_email, password):
        if not username_or_email or not password:
            return None
            
        # Try finding by username first, then email
        user = UserRepository.get_by_username(username_or_email)
        if not user:
            user = UserRepository.get_by_email(username_or_email)
            
        if user and check_password_hash(user.password_hash, password):
            return user
        return None

    @staticmethod
    def get_user(user_id):
        return UserRepository.get_by_id(user_id)
