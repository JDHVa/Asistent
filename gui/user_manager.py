# user_manager.py
import os
import json
import hashlib
import uuid
from typing import Optional, Dict, List
from datetime import datetime
from database_manager import get_database, set_current_user, get_current_user_id

class UserManager:
    """Gestor de identidades de usuario"""
    
    def __init__(self):
        self.db = get_database()
        self.current_user = None
        self.users_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 
            "..", "data", "users.json"
        )
        os.makedirs(os.path.dirname(self.users_file), exist_ok=True)
    
    def auto_login(self) -> str:
        """Auto-login basado en el último usuario o crear uno invitado por defecto"""
        last_user = self.load_last_user()
        
        if last_user and self.set_current_user(last_user):
            print(f"✅ Auto-login exitoso para usuario: {last_user}")
            return last_user
        else:
            # Crear usuario invitado por defecto si no hay último usuario
            return self.create_guest_user()
    
    def create_guest_user(self) -> str:
        """Crear un usuario invitado por defecto"""
        # ID fijo para usuario invitado
        guest_id = "guest_0000"
        
        # Verificar si ya existe
        user_info = self.db.get_user_info(guest_id)
        if not user_info:
            # Crear usuario invitado
            self.db.create_user(guest_id, "Invitado", None)
            print(f"✅ Usuario invitado creado: {guest_id}")
        
        # Establecer como usuario actual
        self.set_current_user(guest_id)
        return guest_id
    
    def create_or_get_user(self, user_id: str, name: str = None, email: str = None) -> str:
        """Crear usuario si no existe, o obtener el existente"""
        user_info = self.db.get_user_info(user_id)
        
        if not user_info:
            # Crear nuevo usuario
            return self.db.create_user(user_id, name, email)
        else:
            # Usuario ya existe, establecer como actual
            self.set_current_user(user_id)
            return user_id
    
    def switch_to_guest(self) -> str:
        """Cambiar al usuario invitado"""
        return self.create_guest_user()
    
    def generate_user_id(self, seed: str = None) -> str:
        """Generar un ID único para el usuario"""
        if seed:
            # Usar el seed (ej: nombre de usuario) para generar ID consistente
            return hashlib.sha256(seed.encode()).hexdigest()[:16]
        else:
            # Generar ID aleatorio único
            return str(uuid.uuid4())[:16]
    
    def create_user(self, name: str, email: str = None) -> str:
        """Crear un nuevo usuario"""
        # Generar ID único basado en el nombre
        user_id = self.generate_user_id(name)
        
        # Crear en la base de datos
        self.db.create_user(user_id, name, email)
        
        # Cargar como usuario actual
        self.set_current_user(user_id)
        
        print(f"✅ Usuario creado: {name} (ID: {user_id})")
        return user_id
    
    def set_current_user(self, user_id: str) -> bool:
        """Establecer usuario actual"""
        success = set_current_user(user_id)
        if success:
            self.current_user = user_id
            self.save_last_user(user_id)
        return success
    
    def get_current_user(self) -> Optional[Dict]:
        """Obtener información del usuario actual"""
        if not self.current_user:
            return None
        return self.db.get_user_info(self.current_user)
    
    def save_last_user(self, user_id: str):
        """Guardar el último usuario activo"""
        try:
            data = {'last_user': user_id}
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(data, f)
        except Exception as e:
            print(f"⚠️ Error guardando último usuario: {e}")
    
    def load_last_user(self) -> Optional[str]:
        """Cargar el último usuario activo"""
        try:
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('last_user')
        except Exception as e:
            print(f"⚠️ Error cargando último usuario: {e}")
        return None
    
    def auto_login(self) -> str:
        """Auto-login basado en el último usuario o crear uno por defecto"""
        last_user = self.load_last_user()
        
        if last_user and self.set_current_user(last_user):
            print(f"✅ Auto-login exitoso para usuario: {last_user}")
            return last_user
        else:
            # Crear usuario por defecto
            default_user_id = self.create_user("Usuario Principal")
            return default_user_id
    
    def list_users(self) -> List[Dict]:
        """Listar todos los usuarios"""
        return self.db.get_all_users()
    
    def switch_user(self, user_id: str) -> bool:
        """Cambiar a otro usuario"""
        return self.set_current_user(user_id)
    
    def delete_user(self, user_id: str) -> bool:
        """Eliminar un usuario (y todos sus datos)"""
        try:
            # Verificar que no estamos eliminando al usuario actual
            if user_id == self.current_user:
                print("⚠️ No se puede eliminar el usuario actual")
                return False
            
            # Eliminar datos de la base de datos
            success = self.db.clear_user_data(user_id)
            
            if success:
                print(f"✅ Datos del usuario {user_id} eliminados")
            return success
            
        except Exception as e:
            print(f"❌ Error eliminando usuario: {e}")
            return False
    
    def update_user_profile(self, name: str = None, email: str = None, 
                           settings: Dict = None) -> bool:
        """Actualizar perfil del usuario actual"""
        if not self.current_user:
            return False
        
        conn = self.db.connect()
        cursor = conn.cursor()
        
        try:
            updates = []
            params = []
            
            if name:
                updates.append("name = ?")
                params.append(name)
            
            if email:
                updates.append("email = ?")
                params.append(email)
            
            if updates:
                query = f"UPDATE users SET {', '.join(updates)} WHERE user_id = ?"
                params.append(self.current_user)
                cursor.execute(query, params)
            
            if settings:
                self.db.update_user_settings(settings, self.current_user)
            
            conn.commit()
            return True
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Error actualizando perfil: {e}")
            return False
        finally:
            self.db.close()

# Singleton global
_user_manager = None

def get_user_manager() -> UserManager:
    """Obtener instancia global del gestor de usuarios"""
    global _user_manager
    if _user_manager is None:
        _user_manager = UserManager()
    return _user_manager

def get_current_user_info() -> Optional[Dict]:
    """Obtener información del usuario actual"""
    manager = get_user_manager()
    return manager.get_current_user()