import sqlite3
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

class DatabaseManager:
    """Gestor de base de datos SQLite con todo en inglés"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            db_dir = os.path.join(current_dir, "..", "data", "database")
            os.makedirs(db_dir, exist_ok=True)
            db_path = os.path.join(db_dir, "assistant.db")
        
        self.db_path = db_path
        self.connection = None
        self.current_user_id = None
        self.setup_database()
    
    def connect(self):
        """Conectar a la base de datos"""
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row  # Para acceder por nombre de columna
        return self.connection
    
    def close(self):
        """Cerrar conexión"""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def setup_database(self):
        """Crear tablas si no existen - TODO EN INGLÉS"""
        conn = self.connect()
        cursor = conn.cursor()
        
        # Tabla de usuarios
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT UNIQUE NOT NULL,
                name TEXT,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                settings TEXT DEFAULT '{}'
            )
        ''')
        
        # Tabla de tareas - EN INGLÉS
            # Para la tabla tasks
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                title TEXT NOT NULL,
                description TEXT,
                priority TEXT CHECK(priority IN ('alta', 'media', 'baja', 'high', 'medium', 'low')),
                category TEXT,
                due_date TEXT,
                due_time TEXT,
                completed INTEGER DEFAULT 0,
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # Tabla de eventos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                location TEXT,
                description TEXT,
                date TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                color TEXT DEFAULT '#4285f4',
                recurrence TEXT DEFAULT 'No repetir',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Para la tabla reminders
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                title TEXT NOT NULL,
                description TEXT,
                date TEXT,
                time TEXT,
                date_time TEXT,
                priority TEXT CHECK(priority IN ('alta', 'media', 'baja', 'high', 'medium', 'low')),
                recurrence TEXT,
                active INTEGER DEFAULT 1,
                completed INTEGER DEFAULT 0,
                sound INTEGER DEFAULT 1,
                popup INTEGER DEFAULT 1,
                auto_snooze INTEGER DEFAULT 0,
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # Tabla de conversaciones
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                role TEXT CHECK(role IN ('user', 'assistant')) NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Tabla de configuraciones
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id TEXT PRIMARY KEY,
                voice_enabled BOOLEAN DEFAULT 1,
                auto_start BOOLEAN DEFAULT 1,
                theme TEXT DEFAULT 'dark',
                language TEXT DEFAULT 'es',
                notification_sound BOOLEAN DEFAULT 1,
                data_retention_days INTEGER DEFAULT 365,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        conn.commit()
        self.close()
        print(f"✅ Base de datos inicializada (inglés): {self.db_path}")

    # ===== MÉTODOS DE USUARIO =====
    def delete_reminder(self, reminder_id: int, user_id: str = None) -> bool:
        """Eliminar un recordatorio"""
        if user_id is None:
            user_id = self.current_user_id
        
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                DELETE FROM reminders 
                WHERE id = ? AND user_id = ?
            ''', (reminder_id, user_id))
            
            conn.commit()
            return cursor.rowcount > 0
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Error eliminando recordatorio: {e}")
            return False
        finally:
            self.close()
    
    def create_user(self, user_id: str, name: str = None, email: str = None) -> str:
        """Crear un nuevo usuario con ID único"""
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO users (user_id, name, email, last_login)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, name, email))
            
            # Crear configuración por defecto
            cursor.execute('''
                INSERT OR IGNORE INTO user_settings (user_id)
                VALUES (?)
            ''', (user_id,))
            
            conn.commit()
            
            # Actualizar usuario existente si ya existe
            if cursor.rowcount == 0:
                cursor.execute('''
                    UPDATE users 
                    SET name = COALESCE(?, name),
                        email = COALESCE(?, email),
                        last_login = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                ''', (name, email, user_id))
                conn.commit()
            
            self.current_user_id = user_id
            print(f"✅ Usuario {user_id} configurado/actualizado")
            return user_id
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Error creando usuario: {e}")
            return None
        finally:
            self.close()
    
    def set_current_user(self, user_id: str) -> bool:
        """Establecer usuario actual"""
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
            user = cursor.fetchone()
            
            if user:
                self.current_user_id = user_id
                
                # Actualizar último login
                cursor.execute('''
                    UPDATE users 
                    SET last_login = CURRENT_TIMESTAMP 
                    WHERE user_id = ?
                ''', (user_id,))
                conn.commit()
                
                print(f"✅ Usuario actual establecido: {user_id}")
                return True
            else:
                print(f"⚠️ Usuario no encontrado: {user_id}")
                return False
                
        except Exception as e:
            print(f"❌ Error estableciendo usuario: {e}")
            return False
        finally:
            self.close()
    
    def get_user_info(self, user_id: str = None) -> Optional[Dict]:
        """Obtener información del usuario"""
        if user_id is None:
            user_id = self.current_user_id
        
        if not user_id:
            return None
        
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT u.*, us.* 
                FROM users u
                LEFT JOIN user_settings us ON u.user_id = us.user_id
                WHERE u.user_id = ?
            ''', (user_id,))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
            
        except Exception as e:
            print(f"❌ Error obteniendo información del usuario: {e}")
            return None
        finally:
            self.close()
    
    def update_user_settings(self, settings: Dict, user_id: str = None) -> bool:
        """Actualizar configuración del usuario"""
        if user_id is None:
            user_id = self.current_user_id
        
        if not user_id:
            return False
        
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            for key, value in settings.items():
                cursor.execute(f'''
                    UPDATE user_settings 
                    SET {key} = ?
                    WHERE user_id = ?
                ''', (value, user_id))
            
            conn.commit()
            return True
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Error actualizando configuración: {e}")
            return False
        finally:
            self.close()
    
    def get_all_users(self) -> List[Dict]:
        """Obtener todos los usuarios (para administración)"""
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT u.*, us.voice_enabled, us.theme, us.language
                FROM users u
                LEFT JOIN user_settings us ON u.user_id = us.user_id
                ORDER BY u.last_login DESC
            ''')
            
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            print(f"❌ Error obteniendo usuarios: {e}")
            return []
        finally:
            self.close()
    
    # ===== MÉTODOS DE TAREAS =====
    
    def save_task(self, task_data: Dict, user_id: str = None) -> int:
        """Guardar una tarea (crear o actualizar) - SIN CONVERSIONES"""
        if user_id is None:
            user_id = self.current_user_id
        
        if not user_id:
            raise ValueError("No hay usuario activo")
        
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            # Asegurar prioridad en inglés
            priority = task_data.get('priority', 'medium').lower()
            if priority not in ['high', 'medium', 'low']:
                # Mapeo automático si viene en español
                priority_map = {
                    'alta': 'high',
                    'media': 'medium', 
                    'baja': 'low'
                }
                priority = priority_map.get(priority, 'medium')
            
            print(f"DEBUG: Guardando tarea con prioridad: {priority}")
            
            task_id = task_data.get('id')
            
            if task_id:  # Actualizar
                cursor.execute('''
                    UPDATE tasks SET
                        title = ?,
                        description = ?,
                        priority = ?,
                        category = ?,
                        due_date = ?,
                        due_time = ?,
                        completed = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND user_id = ?
                ''', (
                    task_data['title'],
                    task_data.get('description', ''),
                    priority,
                    task_data.get('category', ''),
                    task_data.get('due_date'),
                    task_data.get('due_time'),
                    1 if task_data.get('completed', False) else 0,
                    task_id,
                    user_id
                ))
            else:  # Crear nueva
                cursor.execute('''
                    INSERT INTO tasks (
                        user_id, title, description, priority, 
                        category, due_date, due_time, completed
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id,
                    task_data['title'],
                    task_data.get('description', ''),
                    priority,
                    task_data.get('category', ''),
                    task_data.get('due_date'),
                    task_data.get('due_time'),
                    1 if task_data.get('completed', False) else 0
                ))
                task_id = cursor.lastrowid
            
            conn.commit()
            return task_id
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Error guardando tarea: {e}")
            import traceback
            traceback.print_exc()
            return -1
        finally:
            self.close()
    

    def get_tasks(self, user_id: str = None, filters: Dict = None) -> List[Dict]:
        """Obtener tareas del usuario"""
        if user_id is None:
            user_id = self.current_user_id
        
        if not user_id:
            return []
        
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            query = '''
                SELECT * FROM tasks 
                WHERE user_id = ?
            '''
            params = [user_id]
            
            # Aplicar filtros
            if filters:
                conditions = []
                
                if filters.get('completed') is not None:
                    conditions.append("completed = ?")
                    params.append(1 if filters['completed'] else 0)
                
                if filters.get('priority'):
                    conditions.append("priority = ?")
                    params.append(filters['priority'])
                
                if filters.get('category'):
                    conditions.append("category = ?")
                    params.append(filters['category'])
                
                if filters.get('due_date'):
                    conditions.append("due_date = ?")
                    params.append(filters['due_date'])
                
                if conditions:
                    query += " AND " + " AND ".join(conditions)
            
            # Ordenar
            if filters and filters.get('sort_by'):
                sort_field = filters['sort_by']
                order = "DESC" if filters.get('sort_desc', False) else "ASC"
                query += f" ORDER BY {sort_field} {order}"
            else:
                query += " ORDER BY due_date ASC, priority DESC"
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            print(f"❌ Error obteniendo tareas: {e}")
            return []
        finally:
            self.close()
    
    def delete_task(self, task_id: int, user_id: str = None) -> bool:
        """Eliminar una tarea"""
        if user_id is None:
            user_id = self.current_user_id
        
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                DELETE FROM tasks 
                WHERE id = ? AND user_id = ?
            ''', (task_id, user_id))
            
            conn.commit()
            return cursor.rowcount > 0
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Error eliminando tarea: {e}")
            return False
        finally:
            self.close()
    
    def get_tasks_summary(self, user_id: str = None) -> Dict:
        """Obtener resumen de tareas"""
        tasks = self.get_tasks(user_id)
        
        total = len(tasks)
        completed = sum(1 for t in tasks if t['completed'])
        pending = total - completed
        
        # Contar por prioridad
        high_priority = sum(1 for t in tasks if t['priority'] == 'high' and not t['completed'])
        
        # Tareas próximas (para hoy o mañana)
        today = datetime.now().strftime("%Y-%m-%d")
        upcoming = [t for t in tasks if t['due_date'] and t['due_date'] >= today and not t['completed']]
        
        return {
            'total': total,
            'completed': completed,
            'pending': pending,
            'high_priority': high_priority,
            'upcoming': len(upcoming)
        }
    
    # ===== MÉTODOS DE EVENTOS =====
    
    def save_event(self, event_data: Dict, user_id: str = None) -> int:
        """Guardar un evento"""
        if user_id is None:
            user_id = self.current_user_id
        
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            event_id = event_data.get('id')
            
            if event_id:  # Actualizar
                cursor.execute('''
                    UPDATE events SET
                        title = ?,
                        location = ?,
                        description = ?,
                        date = ?,
                        start_time = ?,
                        end_time = ?,
                        color = ?,
                        recurrence = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND user_id = ?
                ''', (
                    event_data['title'],
                    event_data.get('location', ''),
                    event_data.get('description', ''),
                    event_data['date'],
                    event_data['start_time'],
                    event_data['end_time'],
                    event_data.get('color', '#4285f4'),
                    event_data.get('recurrence', 'No repetir'),
                    event_id,
                    user_id
                ))
            else:  # Crear nuevo
                cursor.execute('''
                    INSERT INTO events (
                        user_id, title, location, description,
                        date, start_time, end_time, color, recurrence
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id,
                    event_data['title'],
                    event_data.get('location', ''),
                    event_data.get('description', ''),
                    event_data['date'],
                    event_data['start_time'],
                    event_data['end_time'],
                    event_data.get('color', '#4285f4'),
                    event_data.get('recurrence', 'No repetir')
                ))
                event_id = cursor.lastrowid
            
            conn.commit()
            return event_id
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Error guardando evento: {e}")
            return -1
        finally:
            self.close()
    
    def get_events(self, user_id: str = None, filters: Dict = None) -> List[Dict]:
        """Obtener eventos del usuario"""
        if user_id is None:
            user_id = self.current_user_id
        
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            query = '''
                SELECT * FROM events 
                WHERE user_id = ?
            '''
            params = [user_id]
            
            if filters:
                if filters.get('date'):
                    query += " AND date = ?"
                    params.append(filters['date'])
                
                if filters.get('start_date') and filters.get('end_date'):
                    query += " AND date BETWEEN ? AND ?"
                    params.extend([filters['start_date'], filters['end_date']])
                
                if filters.get('search'):
                    query += " AND (title LIKE ? OR description LIKE ? OR location LIKE ?)"
                    search_term = f"%{filters['search']}%"
                    params.extend([search_term, search_term, search_term])
            
            query += " ORDER BY date ASC, start_time ASC"
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            print(f"❌ Error obteniendo eventos: {e}")
            return []
        finally:
            self.close()
    
    def get_events_summary(self, user_id: str = None) -> Dict:
        """Obtener resumen de eventos"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        events = self.get_events(user_id)
        total = len(events)
        
        # Eventos de hoy
        today_events = [e for e in events if e['date'] == today]
        
        # Eventos de esta semana
        week_events = self.get_events(user_id, {
            'start_date': today,
            'end_date': (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        })
        
        return {
            'total': total,
            'today': len(today_events),
            'this_week': len(week_events)
        }
    
    # ===== MÉTODOS DE RECORDATORIOS =====
    
    def save_reminder(self, reminder_data: Dict, user_id: str = None) -> int:
        """Guardar un recordatorio - SIN CONVERSIONES"""
        if user_id is None:
            user_id = self.current_user_id
        
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            # Asegurar prioridad en inglés
            priority = reminder_data.get('priority', 'medium').lower()
            if priority not in ['high', 'medium', 'low']:
                # Mapeo automático si viene en español
                priority_map = {
                    'alta': 'high',
                    'media': 'medium', 
                    'baja': 'low'
                }
                priority = priority_map.get(priority, 'medium')
            
            print(f"DEBUG: Guardando recordatorio con prioridad: {priority}")
            
            reminder_id = reminder_data.get('id')
            
            if reminder_id:  # Actualizar
                cursor.execute('''
                    UPDATE reminders SET
                        title = ?,
                        description = ?,
                        date_time = ?,
                        date = ?,
                        time = ?,
                        priority = ?,
                        recurrence = ?,
                        active = ?,
                        completed = ?,
                        sound = ?,
                        popup = ?,
                        auto_snooze = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND user_id = ?
                ''', (
                    reminder_data['title'],
                    reminder_data.get('description', ''),
                    reminder_data.get('date_time', ''),
                    reminder_data.get('date', ''),
                    reminder_data.get('time', ''),
                    priority,
                    reminder_data.get('recurrence', 'none'),
                    1 if reminder_data.get('active', True) else 0,
                    1 if reminder_data.get('completed', False) else 0,
                    1 if reminder_data.get('sound', True) else 0,
                    1 if reminder_data.get('popup', True) else 0,
                    1 if reminder_data.get('auto_snooze', False) else 0,
                    reminder_id,
                    user_id
                ))
            else:  # Crear nuevo
                cursor.execute('''
                    INSERT INTO reminders (
                        user_id, title, description, date_time,
                        date, time, priority, recurrence,
                        active, completed, sound, popup, auto_snooze
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id,
                    reminder_data['title'],
                    reminder_data.get('description', ''),
                    reminder_data.get('date_time', ''),
                    reminder_data.get('date', ''),
                    reminder_data.get('time', ''),
                    priority,
                    reminder_data.get('recurrence', 'none'),
                    1 if reminder_data.get('active', True) else 0,
                    1 if reminder_data.get('completed', False) else 0,
                    1 if reminder_data.get('sound', True) else 0,
                    1 if reminder_data.get('popup', True) else 0,
                    1 if reminder_data.get('auto_snooze', False) else 0
                ))
                reminder_id = cursor.lastrowid
            
            conn.commit()
            return reminder_id
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Error guardando recordatorio: {e}")
            import traceback
            traceback.print_exc()
            return -1
        finally:
            self.close()
              
    def get_reminders(self, user_id: str = None, filters: Dict = None) -> List[Dict]:
        """Obtener recordatorios del usuario"""
        if user_id is None:
            user_id = self.current_user_id
        
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            query = '''
                SELECT * FROM reminders 
                WHERE user_id = ?
            '''
            params = [user_id]
            
            if filters:
                conditions = []
                
                if filters.get('active') is not None:
                    conditions.append("active = ?")
                    params.append(1 if filters['active'] else 0)
                
                if filters.get('completed') is not None:
                    conditions.append("completed = ?")
                    params.append(1 if filters['completed'] else 0)
                
                if filters.get('priority'):
                    conditions.append("priority = ?")
                    params.append(filters['priority'])
                
                if filters.get('date'):
                    conditions.append("date = ?")
                    params.append(filters['date'])
                
                if filters.get('upcoming'):
                    conditions.append("date >= ?")
                    params.append(datetime.now().strftime("%Y-%m-%d"))
                
                if conditions:
                    query += " AND " + " AND ".join(conditions)
            
            query += " ORDER BY date ASC, time ASC"
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            print(f"❌ Error obteniendo recordatorios: {e}")
            return []
        finally:
            self.close()
    
    def get_active_reminders(self, user_id: str = None) -> List[Dict]:
        """Obtener recordatorios activos para notificaciones"""
        if user_id is None:
            user_id = self.current_user_id
        
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            cursor.execute('''
                SELECT * FROM reminders 
                WHERE user_id = ? 
                AND active = 1 
                AND completed = 0
                AND (date || ' ' || time) <= ?
                ORDER BY date ASC, time ASC
            ''', (user_id, current_datetime))
            
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            print(f"❌ Error obteniendo recordatorios activos: {e}")
            return []
        finally:
            self.close()
    
    # ===== MÉTODOS DE CONVERSACIONES =====
    
    def save_message(self, role: str, content: str, user_id: str = None) -> bool:
        """Guardar un mensaje en la conversación"""
        if user_id is None:
            user_id = self.current_user_id
        
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO conversations (user_id, role, content)
                VALUES (?, ?, ?)
            ''', (user_id, role, content))
            
            conn.commit()
            return True
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Error guardando mensaje: {e}")
            return False
        finally:
            self.close()
    
    def get_conversation_history(self, user_id: str = None, limit: int = 50) -> List[Dict]:
        """Obtener historial de conversación"""
        if user_id is None:
            user_id = self.current_user_id
        
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT role, content, timestamp 
                FROM conversations 
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (user_id, limit))
            
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            print(f"❌ Error obteniendo historial: {e}")
            return []
        finally:
            self.close()
    
    def clear_conversation(self, user_id: str = None) -> bool:
        """Limpiar historial de conversación"""
        if user_id is None:
            user_id = self.current_user_id
        
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                DELETE FROM conversations 
                WHERE user_id = ?
            ''', (user_id,))
            
            conn.commit()
            return True
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Error limpiando conversación: {e}")
            return False
        finally:
            self.close()
    
    # ===== MÉTODOS DE BACKUP Y RESTAURACIÓN =====
    
    def export_user_data(self, user_id: str = None) -> Dict:
        """Exportar todos los datos del usuario"""
        if user_id is None:
            user_id = self.current_user_id
        
        return {
            'user_info': self.get_user_info(user_id),
            'tasks': self.get_tasks(user_id),
            'events': self.get_events(user_id),
            'reminders': self.get_reminders(user_id),
            'conversation_history': self.get_conversation_history(user_id),
            'export_date': datetime.now().isoformat(),
            'user_id': user_id
        }
    
    def import_user_data(self, data: Dict, user_id: str = None) -> bool:
        """Importar datos de un usuario"""
        if user_id is None:
            user_id = self.current_user_id
        
        try:
            # Limpiar datos existentes (opcional)
            # self.clear_user_data(user_id)
            
            # Importar tareas
            for task in data.get('tasks', []):
                task_copy = task.copy()
                task_copy.pop('id', None)
                self.save_task(task_copy, user_id)
            
            # Importar eventos
            for event in data.get('events', []):
                event_copy = event.copy()
                event_copy.pop('id', None)
                self.save_event(event_copy, user_id)
            
            # Importar recordatorios
            for reminder in data.get('reminders', []):
                reminder_copy = reminder.copy()
                reminder_copy.pop('id', None)
                self.save_reminder(reminder_copy, user_id)
            
            return True
            
        except Exception as e:
            print(f"❌ Error importando datos: {e}")
            return False
    
    def clear_user_data(self, user_id: str = None) -> bool:
        """Eliminar todos los datos del usuario"""
        if user_id is None:
            user_id = self.current_user_id
        
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            # Eliminar en orden correcto (por restricciones de claves foráneas)
            tables = ['conversations', 'reminders', 'events', 'tasks', 'user_settings']
            
            for table in tables:
                cursor.execute(f'DELETE FROM {table} WHERE user_id = ?', (user_id,))
            
            # No eliminamos el usuario de la tabla users para mantener el registro
            conn.commit()
            return True
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Error limpiando datos: {e}")
            return False
        finally:
            self.close()

# Singleton para acceso global
_database_instance = None

def get_database() -> DatabaseManager:
    """Obtener instancia única de la base de datos"""
    global _database_instance
    if _database_instance is None:
        _database_instance = DatabaseManager()
    return _database_instance

def set_current_user(user_id: str) -> bool:
    """Establecer usuario actual en la base de datos"""
    db = get_database()
    
    # Si el usuario no existe, crearlo automáticamente
    user_info = db.get_user_info(user_id)
    if not user_info:
        db.create_user(user_id, f"Usuario_{user_id[:8]}")
    
    return db.set_current_user(user_id)

def get_current_user_id() -> Optional[str]:
    """Obtener ID del usuario actual"""
    db = get_database()
    return db.current_user_id