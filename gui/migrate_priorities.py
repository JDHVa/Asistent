# recreate_database.py
import os
import sqlite3
import shutil
from datetime import datetime

def recreate_database():
    """Recrear la base de datos con constraints en inglés"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_dir = os.path.join(current_dir, "data", "database")
    db_path = os.path.join(db_dir, "assistant.db")
    backup_path = os.path.join(db_dir, f"assistant_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
    
    # Si existe la base de datos, hacer backup
    if os.path.exists(db_path):
        print(f"📦 Haciendo backup de la base de datos existente: {backup_path}")
        shutil.copy2(db_path, backup_path)
    
    # Eliminar la base de datos existente
    if os.path.exists(db_path):
        os.remove(db_path)
        print("🗑️  Base de datos eliminada")
    
    # Reconectar para crear tablas nuevas
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Tabla de usuarios (sin cambios)
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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            priority TEXT CHECK(priority IN ('high', 'medium', 'low')) DEFAULT 'medium',
            category TEXT,
            due_date TEXT,
            due_time TEXT,
            completed BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    
    # Tabla de eventos (sin cambios)
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
    
    # Tabla de recordatorios - EN INGLÉS
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            date_time TEXT,
            date TEXT,
            time TEXT,
            priority TEXT CHECK(priority IN ('high', 'medium', 'low')) DEFAULT 'medium',
            recurrence TEXT DEFAULT 'none',
            active BOOLEAN DEFAULT 1,
            completed BOOLEAN DEFAULT 0,
            sound BOOLEAN DEFAULT 1,
            popup BOOLEAN DEFAULT 1,
            auto_snooze BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
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
    conn.close()
    
    print("✅ Base de datos recreada con constraints en inglés")
    print(f"📁 Ubicación: {db_path}")
    print("⚠️  Los datos existentes se perdieron (pero hay backup)")

if __name__ == "__main__":
    recreate_database()