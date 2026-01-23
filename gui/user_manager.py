"""
Gestor de usuarios para el Asistente Personal.
"""
import json
import os
import hashlib
from datetime import datetime
from database_manager import get_database  # Solo importar get_database

class UserManager:
    """Gestor de usuarios centralizado"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(UserManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.db = get_database()  # Obtener instancia de base de datos
        self.current_user = None
        self.current_user_data = None
        self._initialized = True
    
    def create_or_get_user(self, user_id, username=None):
        """Crear o obtener usuario existente"""
        try:
            if not username:
                # Extraer nombre del ID si no se proporciona
                username = user_id.replace('user_', '').replace('_', ' ').title()
            
            # Primero verificar si el usuario ya existe
            existing_user = self.db.get_user(user_id)
            
            if existing_user:
                # Usuario existe, establecer como actual
                self.current_user = user_id
                self.current_user_data = existing_user
                self.db.set_current_user(user_id)  # Usar método de DatabaseManager
                print(f"✅ Usuario existente cargado: {username}")
                return user_id
            else:
                # Crear nuevo usuario
                user_data = {
                    'id': user_id,
                    'name': username,
                    'email': None,
                    'created_at': datetime.now().isoformat(),
                    'last_login': datetime.now().isoformat(),
                    'settings': {}
                }
                
                if self.db.create_user(user_data):
                    self.current_user = user_id
                    self.current_user_data = user_data
                    self.db.set_current_user(user_id)  # Usar método de DatabaseManager
                    print(f"✅ Nuevo usuario creado: {username}")
                    return user_id
                else:
                    print(f"❌ Error creando usuario: {username}")
                    return None
                    
        except Exception as e:
            print(f"❌ Error en create_or_get_user: {e}")
            # Fallback: crear usuario con datos mínimos
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
        """Auto-login (comportamiento por defecto)"""
        try:
            # Verificar si hay algún usuario en la base de datos
            conn = self.db._get_connection()  # Método interno para obtener conexión
            cursor = conn.cursor()
            cursor.execute('SELECT id, name FROM users LIMIT 1')
            row = cursor.fetchone()
            conn.close()
            
            if row:
                user_id, username = row
                print(f"✅ Usuario encontrado en BD: {username}")
                return self.create_or_get_user(user_id, username)
            else:
                # Crear usuario por defecto
                default_id = "default_user"
                default_name = "Usuario"
                print(f"⚠️ Creando usuario por defecto: {default_name}")
                return self.create_or_get_user(default_id, default_name)
                
        except Exception as e:
            print(f"❌ Error en auto_login: {e}")
            # Usuario de emergencia
            return self.create_or_get_user("emergency_user", "Invitado")
    
    def logout(self):
        """Cerrar sesión del usuario actual"""
        self.current_user = None
        self.current_user_data = None
        print("✅ Sesión cerrada")

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
            'user_id': user_data.get('id', 'unknown'),
            'email': user_data.get('email'),
            'created_at': user_data.get('created_at')
        }
    else:
        return {"name": "Invitado", "user_id": "guest_0000"}