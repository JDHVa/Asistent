"""
Gestor de base de datos SQLite para el Asistente Personal.
Maneja todas las operaciones de base de datos para usuarios, tareas, recordatorios, eventos, notas, etc.
"""
import sqlite3
import os
from datetime import datetime
import json
from typing import Dict, List, Optional, Any
import logging

# Configurar logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Gestor centralizado de base de datos para el Asistente Personal"""
    
    _instance = None
    _database_initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        # Usar ruta absoluta para la base de datos
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)  # Subir un nivel si estamos en gui/
        data_dir = os.path.join(parent_dir, "data")
        
        self.db_path = os.path.join(data_dir, "asistente_personal.db")
        self.current_user = None
        
        print(f"📁 Ruta de base de datos: {self.db_path}")
        self._create_directories()
        self._init_database()
        self._initialized = True
        
    def _create_directories(self):
        """Crear directorios necesarios"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        logger.info(f"✅ Directorio creado: {os.path.dirname(self.db_path)}")
    
    def _init_database(self):
        """Inicializar la base de datos con todas las tablas"""
        try:
            logger.info(f"🔄 Inicializando base de datos en: {self.db_path}")
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Tabla de usuarios
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE,
                    created_at TEXT,
                    last_login TEXT,
                    settings TEXT DEFAULT '{}'
                )
            ''')
            
            # Tabla de tareas (SIN campo priority)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    title TEXT NOT NULL,
                    description TEXT,
                    category TEXT,
                    due_date TEXT,
                    due_time TEXT,
                    completed INTEGER DEFAULT 0,
                    created_at TEXT,
                    updated_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
            
            # Tabla de recordatorios (SIN campo priority)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    title TEXT NOT NULL,
                    description TEXT,
                    date TEXT,
                    time TEXT,
                    date_time TEXT,
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
            
            # Tabla de eventos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    title TEXT NOT NULL,
                    description TEXT,
                    start_date TEXT,
                    end_date TEXT,
                    start_time TEXT,
                    end_time TEXT,
                    location TEXT,
                    category TEXT,
                    all_day INTEGER DEFAULT 0,
                    created_at TEXT,
                    updated_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
            
            # Tabla de notas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    title TEXT NOT NULL,
                    content TEXT,
                    category TEXT,
                    color TEXT DEFAULT '#FFFFFF',
                    tags TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
            
            # Tabla de conversaciones (para chat)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    title TEXT,
                    messages TEXT,  -- JSON con mensajes
                    created_at TEXT,
                    updated_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
            
            # Índices para mejor rendimiento
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_completed ON tasks(completed)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date)')
            
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_reminders_user_id ON reminders(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_reminders_active ON reminders(active)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_reminders_date ON reminders(date)')
            
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_user_id ON events(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_start_date ON events(start_date)')
            
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_notes_user_id ON notes(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id)')
            
            conn.commit()
            conn.close()
            
            logger.info("✅ Base de datos inicializada correctamente")
            DatabaseManager._database_initialized = True
            
            # Verificar tablas creadas
            self._verify_tables()
            
        except Exception as e:
            logger.error(f"❌ Error inicializando base de datos: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _verify_tables(self):
        """Verificar que las tablas se han creado correctamente"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            print("📊 Tablas en la base de datos:")
            for table in tables:
                print(f"  - {table[0]}")
            
            conn.close()
        except Exception as e:
            logger.error(f"❌ Error verificando tablas: {e}")
    
    def set_current_user(self, user_id: str):
        """Establecer el usuario actual"""
        self.current_user = user_id
        logger.debug(f"Usuario actual establecido: {user_id}")
    
    # ===== OPERACIONES DE USUARIOS =====
    
    def create_user(self, user_data: Dict) -> bool:
        """Crear un nuevo usuario"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO users (id, name, email, created_at, last_login, settings)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                user_data.get('id'),
                user_data.get('name'),
                user_data.get('email'),
                user_data.get('created_at', datetime.now().isoformat()),
                datetime.now().isoformat(),
                json.dumps(user_data.get('settings', {}))
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Usuario creado/actualizado: {user_data.get('name')}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creando usuario: {e}")
            return False
    
    def get_user(self, user_id: str) -> Optional[Dict]:
        """Obtener usuario por ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            row = cursor.fetchone()
            
            conn.close()
            
            if row:
                return {
                    'id': row['id'],
                    'name': row['name'],
                    'email': row['email'],
                    'created_at': row['created_at'],
                    'last_login': row['last_login'],
                    'settings': json.loads(row['settings']) if row['settings'] else {}
                }
            return None
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo usuario: {e}")
            return None
    
    def update_user_last_login(self, user_id: str):
        """Actualizar último login del usuario"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users SET last_login = ? WHERE id = ?
            ''', (datetime.now().isoformat(), user_id))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"Último login actualizado para usuario: {user_id}")
            
        except Exception as e:
            logger.error(f"❌ Error actualizando último login: {e}")
    
    def update_user_settings(self, user_id: str, settings: Dict):
        """Actualizar configuración del usuario"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users SET settings = ? WHERE id = ?
            ''', (json.dumps(settings), user_id))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"Configuración actualizada para usuario: {user_id}")
            
        except Exception as e:
            logger.error(f"❌ Error actualizando configuración: {e}")
    
    # ===== OPERACIONES DE TAREAS =====
    
    def save_task(self, task_data: Dict) -> int:
        """Guardar tarea en base de datos (crear o actualizar)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if 'id' in task_data and task_data['id']:
                # Actualizar tarea existente
                cursor.execute('''
                    UPDATE tasks 
                    SET title = ?, description = ?, category = ?, 
                        due_date = ?, due_time = ?, completed = ?,
                        updated_at = ?
                    WHERE id = ? AND user_id = ?
                ''', (
                    task_data.get('title', ''),
                    task_data.get('description', ''),
                    task_data.get('category', ''),
                    task_data.get('due_date', ''),
                    task_data.get('due_time', ''),
                    1 if task_data.get('completed', False) else 0,
                    datetime.now().isoformat(),
                    task_data['id'],
                    self.current_user
                ))
                task_id = task_data['id']
                logger.debug(f"✅ Tarea actualizada: {task_id}")
            else:
                # Insertar nueva tarea
                cursor.execute('''
                    INSERT INTO tasks 
                    (user_id, title, description, category, due_date, due_time, completed, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    self.current_user,
                    task_data.get('title', ''),
                    task_data.get('description', ''),
                    task_data.get('category', ''),
                    task_data.get('due_date', ''),
                    task_data.get('due_time', ''),
                    1 if task_data.get('completed', False) else 0,
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
                task_id = cursor.lastrowid
                logger.debug(f"✅ Nueva tarea guardada: {task_id}")
            
            conn.commit()
            conn.close()
            return task_id
            
        except Exception as e:
            logger.error(f"❌ Error guardando tarea: {e}")
            import traceback
            traceback.print_exc()
            return -1
    
    def get_tasks(self, filters: Dict = None) -> List[Dict]:
        """Obtener todas las tareas del usuario actual con filtros opcionales"""
        try:
            if not self.current_user:
                logger.warning("⚠️ No hay usuario establecido")
                return []
                
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = 'SELECT * FROM tasks WHERE user_id = ?'
            params = [self.current_user]
            
            if filters:
                conditions = []
                
                if filters.get('completed') is not None:
                    conditions.append('completed = ?')
                    params.append(1 if filters['completed'] else 0)
                
                if filters.get('category'):
                    conditions.append('category = ?')
                    params.append(filters['category'])
                
                if filters.get('due_date'):
                    conditions.append('due_date = ?')
                    params.append(filters['due_date'])
                
                if conditions:
                    query += ' AND ' + ' AND '.join(conditions)
            
            # Ordenar por fecha de vencimiento
            query += ' ORDER BY due_date ASC, due_time ASC'
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            tasks = []
            for row in rows:
                tasks.append({
                    'id': row['id'],
                    'title': row['title'],
                    'description': row['description'],
                    'category': row['category'],
                    'due_date': row['due_date'],
                    'due_time': row['due_time'],
                    'completed': bool(row['completed']),
                    'created_at': row['created_at']
                })
            
            conn.close()
            logger.debug(f"✅ Tareas obtenidas: {len(tasks)}")
            return tasks
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo tareas: {e}")
            return []
    
    def get_task(self, task_id: int) -> Optional[Dict]:
        """Obtener una tarea específica por ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM tasks WHERE id = ? AND user_id = ?
            ''', (task_id, self.current_user))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'id': row['id'],
                    'title': row['title'],
                    'description': row['description'],
                    'category': row['category'],
                    'due_date': row['due_date'],
                    'due_time': row['due_time'],
                    'completed': bool(row['completed']),
                    'created_at': row['created_at']
                }
            return None
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo tarea: {e}")
            return None
    
    def delete_task(self, task_id: int) -> bool:
        """Eliminar una tarea"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM tasks WHERE id = ? AND user_id = ?
            ''', (task_id, self.current_user))
            
            conn.commit()
            deleted = cursor.rowcount > 0
            conn.close()
            
            logger.debug(f"✅ Tarea eliminada: {task_id}" if deleted else f"⚠️ Tarea no encontrada: {task_id}")
            return deleted
            
        except Exception as e:
            logger.error(f"❌ Error eliminando tarea: {e}")
            return False
    
    def get_tasks_summary(self) -> Dict:
        """Obtener resumen estadístico de tareas"""
        try:
            if not self.current_user:
                return {'total': 0, 'completed': 0, 'pending': 0, 'overdue': 0}
                
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total de tareas
            cursor.execute('SELECT COUNT(*) FROM tasks WHERE user_id = ?', (self.current_user,))
            total = cursor.fetchone()[0]
            
            # Tareas completadas
            cursor.execute('SELECT COUNT(*) FROM tasks WHERE user_id = ? AND completed = 1', (self.current_user,))
            completed = cursor.fetchone()[0]
            
            # Tareas pendientes
            cursor.execute('SELECT COUNT(*) FROM tasks WHERE user_id = ? AND completed = 0', (self.current_user,))
            pending = cursor.fetchone()[0]
            
            # Tareas atrasadas (pendientes con fecha pasada)
            cursor.execute('''
                SELECT COUNT(*) FROM tasks 
                WHERE user_id = ? AND completed = 0 
                AND due_date < date('now')
            ''', (self.current_user,))
            overdue = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total': total,
                'completed': completed,
                'pending': pending,
                'overdue': overdue
            }
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo resumen de tareas: {e}")
            return {'total': 0, 'completed': 0, 'pending': 0, 'overdue': 0}
    
    # ===== OPERACIONES DE RECORDATORIOS =====
    
    def save_reminder(self, reminder_data: Dict) -> int:
        """Guardar recordatorio en base de datos (crear o actualizar)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if 'id' in reminder_data and reminder_data['id']:
                # Actualizar recordatorio existente
                cursor.execute('''
                    UPDATE reminders 
                    SET title = ?, description = ?, date = ?, time = ?, date_time = ?,
                        recurrence = ?, active = ?, completed = ?, sound = ?, popup = ?,
                        auto_snooze = ?, updated_at = ?
                    WHERE id = ? AND user_id = ?
                ''', (
                    reminder_data.get('title', ''),
                    reminder_data.get('description', ''),
                    reminder_data.get('date', ''),
                    reminder_data.get('time', ''),
                    reminder_data.get('date_time', ''),
                    reminder_data.get('recurrence', ''),
                    1 if reminder_data.get('active', True) else 0,
                    1 if reminder_data.get('completed', False) else 0,
                    1 if reminder_data.get('sound', True) else 0,
                    1 if reminder_data.get('popup', True) else 0,
                    1 if reminder_data.get('auto_snooze', False) else 0,
                    datetime.now().isoformat(),
                    reminder_data['id'],
                    self.current_user
                ))
                reminder_id = reminder_data['id']
                logger.debug(f"✅ Recordatorio actualizado: {reminder_id}")
            else:
                # Insertar nuevo recordatorio
                cursor.execute('''
                    INSERT INTO reminders 
                    (user_id, title, description, date, time, date_time, recurrence, 
                     active, completed, sound, popup, auto_snooze, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    self.current_user,
                    reminder_data.get('title', ''),
                    reminder_data.get('description', ''),
                    reminder_data.get('date', ''),
                    reminder_data.get('time', ''),
                    reminder_data.get('date_time', ''),
                    reminder_data.get('recurrence', ''),
                    1 if reminder_data.get('active', True) else 0,
                    1 if reminder_data.get('completed', False) else 0,
                    1 if reminder_data.get('sound', True) else 0,
                    1 if reminder_data.get('popup', True) else 0,
                    1 if reminder_data.get('auto_snooze', False) else 0,
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
                reminder_id = cursor.lastrowid
                logger.debug(f"✅ Nuevo recordatorio guardado: {reminder_id}")
            
            conn.commit()
            conn.close()
            return reminder_id
            
        except Exception as e:
            logger.error(f"❌ Error guardando recordatorio: {e}")
            import traceback
            traceback.print_exc()
            return -1
    
    def get_reminders(self, filters: Dict = None) -> List[Dict]:
        """Obtener todos los recordatorios del usuario actual"""
        try:
            if not self.current_user:
                return []
                
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = 'SELECT * FROM reminders WHERE user_id = ?'
            params = [self.current_user]
            
            if filters:
                conditions = []
                
                if filters.get('active') is not None:
                    conditions.append('active = ?')
                    params.append(1 if filters['active'] else 0)
                
                if filters.get('completed') is not None:
                    conditions.append('completed = ?')
                    params.append(1 if filters['completed'] else 0)
                
                if filters.get('date'):
                    conditions.append('date = ?')
                    params.append(filters['date'])
                
                if conditions:
                    query += ' AND ' + ' AND '.join(conditions)
            
            # Ordenar por fecha y hora
            query += ' ORDER BY date ASC, time ASC'
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            reminders = []
            for row in rows:
                reminders.append({
                    'id': row['id'],
                    'title': row['title'],
                    'description': row['description'],
                    'date': row['date'],
                    'time': row['time'],
                    'date_time': row['date_time'],
                    'recurrence': row['recurrence'],
                    'active': bool(row['active']),
                    'completed': bool(row['completed']),
                    'sound': bool(row['sound']),
                    'popup': bool(row['popup']),
                    'auto_snooze': bool(row['auto_snooze']),
                    'created_at': row['created_at']
                })
            
            conn.close()
            logger.debug(f"✅ Recordatorios obtenidos: {len(reminders)}")
            return reminders
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo recordatorios: {e}")
            return []
    
    def delete_reminder(self, reminder_id: int) -> bool:
        """Eliminar un recordatorio"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM reminders WHERE id = ? AND user_id = ?
            ''', (reminder_id, self.current_user))
            
            conn.commit()
            deleted = cursor.rowcount > 0
            conn.close()
            
            logger.debug(f"✅ Recordatorio eliminado: {reminder_id}" if deleted else f"⚠️ Recordatorio no encontrado: {reminder_id}")
            return deleted
            
        except Exception as e:
            logger.error(f"❌ Error eliminando recordatorio: {e}")
            return False
    
    # ===== OPERACIONES DE CONVERSACIONES (CHAT) =====
    
    def get_conversation_history(self, limit: int = 50) -> List[Dict]:
        """Obtener historial de conversaciones del usuario actual"""
        try:
            if not self.current_user:
                return []
                
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, title, created_at FROM conversations 
                WHERE user_id = ?
                ORDER BY created_at DESC LIMIT ?
            ''', (self.current_user, limit))
            
            rows = cursor.fetchall()
            
            conversations = []
            for row in rows:
                conversations.append({
                    'id': row['id'],
                    'title': row['title'],
                    'created_at': row['created_at']
                })
            
            conn.close()
            logger.debug(f"✅ Historial de conversaciones obtenido: {len(conversations)}")
            return conversations
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo historial de conversaciones: {e}")
            return []
    
    def save_conversation(self, title: str, messages: List[Dict]) -> int:
        """Guardar una conversación"""
        try:
            if not self.current_user:
                return -1
                
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO conversations (user_id, title, messages, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                self.current_user,
                title,
                json.dumps(messages),
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            
            conv_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.debug(f"✅ Conversación guardada: {conv_id}")
            return conv_id
            
        except Exception as e:
            logger.error(f"❌ Error guardando conversación: {e}")
            return -1
    
    def get_conversation(self, conv_id: int) -> Optional[Dict]:
        """Obtener una conversación específica"""
        try:
            if not self.current_user:
                return None
                
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM conversations WHERE id = ? AND user_id = ?
            ''', (conv_id, self.current_user))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'id': row['id'],
                    'title': row['title'],
                    'messages': json.loads(row['messages']) if row['messages'] else [],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                }
            return None
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo conversación: {e}")
            return None
    
    # ===== MÉTODOS DE CONEXIÓN INTERNA =====
    
    def _get_connection(self):
        """Obtener conexión a la base de datos (para uso interno)"""
        return sqlite3.connect(self.db_path)
    # ===== OPERACIONES DE EVENTOS =====
    
    def save_event(self, event_data: Dict) -> int:
        """Guardar evento en base de datos"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if 'id' in event_data and event_data['id']:
                # Actualizar evento existente
                cursor.execute('''
                    UPDATE events 
                    SET title = ?, description = ?, start_date = ?, end_date = ?,
                        start_time = ?, end_time = ?, location = ?, category = ?,
                        all_day = ?, updated_at = ?
                    WHERE id = ? AND user_id = ?
                ''', (
                    event_data.get('title', ''),
                    event_data.get('description', ''),
                    event_data.get('start_date', ''),
                    event_data.get('end_date', ''),
                    event_data.get('start_time', ''),
                    event_data.get('end_time', ''),
                    event_data.get('location', ''),
                    event_data.get('category', ''),
                    1 if event_data.get('all_day', False) else 0,
                    datetime.now().isoformat(),
                    event_data['id'],
                    self.current_user
                ))
                event_id = event_data['id']
            else:
                # Insertar nuevo evento
                cursor.execute('''
                    INSERT INTO events 
                    (user_id, title, description, start_date, end_date, 
                     start_time, end_time, location, category, all_day, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    self.current_user,
                    event_data.get('title', ''),
                    event_data.get('description', ''),
                    event_data.get('start_date', ''),
                    event_data.get('end_date', ''),
                    event_data.get('start_time', ''),
                    event_data.get('end_time', ''),
                    event_data.get('location', ''),
                    event_data.get('category', ''),
                    1 if event_data.get('all_day', False) else 0,
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
                event_id = cursor.lastrowid
            
            conn.commit()
            conn.close()
            return event_id
            
        except Exception as e:
            logger.error(f"❌ Error guardando evento: {e}")
            return -1
    
    def get_events(self, start_date: str = None, end_date: str = None) -> List[Dict]:
        """Obtener eventos del usuario actual"""
        try:
            if not self.current_user:
                logger.warning("⚠️ No hay usuario establecido para obtener eventos")
                return []
                
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = 'SELECT * FROM events WHERE user_id = ?'
            params = [self.current_user]
            
            if start_date and end_date:
                query += ' AND (start_date BETWEEN ? AND ? OR end_date BETWEEN ? AND ?)'
                params.extend([start_date, end_date, start_date, end_date])
            elif start_date:
                query += ' AND start_date >= ?'
                params.append(start_date)
            
            query += ' ORDER BY start_date ASC, start_time ASC'
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            events = []
            for row in rows:
                events.append({
                    'id': row['id'],
                    'title': row['title'],
                    'description': row['description'],
                    'start_date': row['start_date'],
                    'end_date': row['end_date'],
                    'start_time': row['start_time'],
                    'end_time': row['end_time'],
                    'location': row['location'],
                    'category': row['category'],
                    'all_day': bool(row['all_day']),
                    'created_at': row['created_at']
                })
            
            conn.close()
            logger.debug(f"✅ Eventos obtenidos: {len(events)}")
            return events
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo eventos: {e}")
            return []
    
    def get_event(self, event_id: int) -> Optional[Dict]:
        """Obtener un evento específico por ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM events WHERE id = ? AND user_id = ?
            ''', (event_id, self.current_user))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'id': row['id'],
                    'title': row['title'],
                    'description': row['description'],
                    'start_date': row['start_date'],
                    'end_date': row['end_date'],
                    'start_time': row['start_time'],
                    'end_time': row['end_time'],
                    'location': row['location'],
                    'category': row['category'],
                    'all_day': bool(row['all_day']),
                    'created_at': row['created_at']
                }
            return None
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo evento: {e}")
            return None
    
    def delete_event(self, event_id: int) -> bool:
        """Eliminar un evento"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM events WHERE id = ? AND user_id = ?
            ''', (event_id, self.current_user))
            
            conn.commit()
            deleted = cursor.rowcount > 0
            conn.close()
            
            logger.debug(f"✅ Evento eliminado: {event_id}" if deleted else f"⚠️ Evento no encontrado: {event_id}")
            return deleted
            
        except Exception as e:
            logger.error(f"❌ Error eliminando evento: {e}")
            return False
    
    def get_upcoming_events(self, days_ahead: int = 7) -> List[Dict]:
        """Obtener eventos próximos en los próximos N días"""
        try:
            if not self.current_user:
                return []
                
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Calcular fecha de hoy
            from datetime import datetime, timedelta
            today = datetime.now().strftime('%Y-%m-%d')
            future_date = (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
            
            cursor.execute('''
                SELECT * FROM events 
                WHERE user_id = ? 
                AND start_date >= ?
                AND start_date <= ?
                ORDER BY start_date ASC, start_time ASC
                LIMIT 20
            ''', (self.current_user, today, future_date))
            
            rows = cursor.fetchall()
            
            events = []
            for row in rows:
                events.append({
                    'id': row['id'],
                    'title': row['title'],
                    'start_date': row['start_date'],
                    'start_time': row['start_time'],
                    'end_date': row['end_date'],
                    'end_time': row['end_time'],
                    'location': row['location'],
                    'category': row['category']
                })
            
            conn.close()
            logger.debug(f"✅ Eventos próximos obtenidos: {len(events)}")
            return events
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo eventos próximos: {e}")
            return []
# Función para obtener instancia única del gestor de base de datos
def get_database():
    """Obtener instancia única del gestor de base de datos"""
    return DatabaseManager()