# recreate_database_spanish.py
import os
import sqlite3
import shutil

def recreate_database():
    """Recrear completamente la base de datos con restricciones en español"""
    
    # Ruta de la base de datos
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_dir = os.path.join(current_dir, "..", "data", "database")
    db_path = os.path.join(db_dir, "assistant.db")
    
    # Si existe, hacer backup
    if os.path.exists(db_path):
        backup_path = db_path + ".backup"
        shutil.copy2(db_path, backup_path)
        print(f"✅ Backup creado en: {backup_path}")
        os.remove(db_path)
        print("🗑️ Base de datos antigua eliminada")
    
    # Crear directorio si no existe
    os.makedirs(db_dir, exist_ok=True)
    
    # Conectar y crear tablas con español
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔄 Creando base de datos con restricciones en español...")
    
    # Tabla de usuarios
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE NOT NULL,
            name TEXT,
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            settings TEXT DEFAULT '{}'
        )
    ''')
    
    # Tabla de tareas CON ESPAÑOL
    cursor.execute('''
        CREATE TABLE tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            priority TEXT CHECK(priority IN ('alta', 'media', 'baja')) DEFAULT 'media',
            category TEXT,
            due_date TEXT,
            due_time TEXT,
            completed BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    
    # Tabla de eventos
    cursor.execute('''
        CREATE TABLE events (
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
    
    # Tabla de recordatorios CON ESPAÑOL
    cursor.execute('''
        CREATE TABLE reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            date_time TEXT,
            date TEXT,
            time TEXT,
            priority TEXT CHECK(priority IN ('alta', 'media', 'baja')) DEFAULT 'media',
            recurrence TEXT DEFAULT 'ninguna',
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
        CREATE TABLE conversations (
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
        CREATE TABLE user_settings (
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
    
    # Insertar usuario de prueba
    cursor.execute('''
        INSERT INTO users (user_id, name, email, last_login)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
    ''', ('090fd624fefeeda8', 'Juan Pérez', 'juan@email.com'))
    
    cursor.execute('''
        INSERT INTO user_settings (user_id)
        VALUES (?)
    ''', ('090fd624fefeeda8',))
    
    conn.commit()
    conn.close()
    
    print(f"✅ Base de datos creada en: {db_path}")
    print("✅ Restricciones en español: 'alta', 'media', 'baja'")
    print("✅ Usuario de prueba 'Juan Pérez' creado")
    
    # Verificar que funciona
    test_database(db_path)

def test_database(db_path):
    """Probar que la base de datos funciona con español"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n🧪 Probando inserción con español...")
    
    # Probar inserción con español
    test_data = (
        '090fd624fefeeda8',          # user_id
        'Tarea de prueba',           # title
        'Descripción en español',    # description
        'alta',                      # priority EN ESPAÑOL
        'Trabajo',                   # category
        '2024-01-01',                # due_date
        '12:00',                     # due_time
        0                            # completed
    )
    
    try:
        cursor.execute('''
            INSERT INTO tasks (user_id, title, description, priority, category, due_date, due_time, completed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', test_data)
        
        print("✅ Inserción EXITOSA con prioridad 'alta' (español)")
        
        # Verificar restricciones
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='tasks'")
        create_sql = cursor.fetchone()[0]
        if "'alta'" in create_sql and "'media'" in create_sql and "'baja'" in create_sql:
            print("✅ Restricciones CHECK en español verificadas")
        else:
            print("⚠️ Las restricciones no están en español")
        
        conn.commit()
        
    except Exception as e:
        print(f"❌ Error en inserción: {e}")
    
    conn.close()

if __name__ == "__main__":
    recreate_database()