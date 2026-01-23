"""
Gestor de usuarios simplificado para el Asistente Personal.
"""
import json
from datetime import datetime
from database_manager import get_database

class UserManager:
    """Gestor de usuarios simplificado"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(UserManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.db = get_database()
        self.current_user = None
        self.current_user_data = None
        self._initialized = True
    
    def create_or_get_user(self, user_id, username=None):
        """Crear o obtener usuario existente"""
        try:
            if not username:
                username = user_id.replace('user_', '').replace('_', ' ').title()
            
            # Crear datos de usuario
            user_data = {
                'id': user_id,
                'name': username,
                'email': None,
                'created_at': datetime.now().isoformat(),
                'last_login': datetime.now().isoformat(),
                'settings': {}
            }
            
            # Guardar en base de datos
            success = self.db.create_user(user_data)
            
            if success:
                self.current_user = user_id
                self.current_user_data = user_data
                self.db.set_current_user(user_id)
                print(f"✅ Usuario creado/establecido: {username}")
                return user_id
            else:
                print(f"❌ Error creando usuario: {username}")
                return None
                
        except Exception as e:
            print(f"❌ Error en create_or_get_user: {e}")
            # Fallback simple
            self.current_user = user_id
            self.current_user_data = {
                'id': user_id,
                'name': username or 'Usuario',
                'email': None,
                'created_at': datetime.now().isoformat()
            }
            return user_id
    
    def get_current_user(self):
        """Obtener datos del usuario actual"""
        return self.current_user_data
    
    def auto_login(self):
        """Auto-login simplificado"""
        try:
            # Usuario por defecto
            default_id = "default_user"
            default_name = "Usuario"
            print(f"⚠️ Creando usuario por defecto: {default_name}")
            return self.create_or_get_user(default_id, default_name)
                
        except Exception as e:
            print(f"❌ Error en auto_login: {e}")
            # Usuario de emergencia
            return self.create_or_get_user("emergency_user", "Invitado")

def get_user_manager():
    """Obtener instancia única del gestor de usuarios"""
    return UserManager()

def get_current_user_info():
    """Obtener información del usuario actual"""
    manager = get_user_manager()
    user_data = manager.get_current_user()
    
    if user_data:
        return {
            'name': user_data.get('name', 'Usuario'),
            'user_id': user_data.get('id', 'unknown')
        }
    else:
        return {"name": "Invitado", "user_id": "guest_0000"}