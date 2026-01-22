# update_database.py
import sqlite3
import os

def update_database_constraints():
    """Actualizar restricciones de la base de datos a español"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(current_dir, "..", "data", "database", "assistant.db")
    
    if not os.path.exists(db_path):
        print("❌ Base de datos no encontrada")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔄 Actualizando restricciones de base de datos...")
    
    # 1. Hacer backup de tablas
    tables_to_update = ['tasks', 'reminders']
    
    for table in tables_to_update:
        try:
            # Renombrar tabla existente
            cursor.execute(f"ALTER TABLE {table} RENAME TO {table}_old")
            print(f"✅ Tabla {table} renombrada a {table}_old")
            
            # Obtener estructura de la tabla vieja
            cursor.execute(f"PRAGMA table_info({table}_old)")
            columns = cursor.fetchall()
            
            # Crear nueva tabla con restricciones en español
            if table == 'tasks':
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
            elif table == 'reminders':
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
            
            # Convertir prioridades de inglés a español
            priority_conversion = {
                'high': 'alta',
                'medium': 'media',
                'low': 'baja'
            }
            
            # Obtener datos de la tabla vieja
            cursor.execute(f"SELECT * FROM {table}_old")
            rows = cursor.fetchall()
            
            # Insertar datos en nueva tabla con prioridades convertidas
            for row in rows:
                # Convertir prioridad si existe
                row_data = list(row)
                if len(row_data) > 4:  # Asumiendo que priority está en índice 4
                    old_priority = row_data[4]
                    if old_priority in priority_conversion:
                        row_data[4] = priority_conversion[old_priority]
                
                placeholders = ','.join(['?'] * len(row_data))
                cursor.execute(f"INSERT INTO {table} VALUES ({placeholders})", row_data)
            
            # Eliminar tabla vieja
            cursor.execute(f"DROP TABLE {table}_old")
            
            print(f"✅ Tabla {table} actualizada correctamente")
            
        except Exception as e:
            print(f"❌ Error actualizando tabla {table}: {e}")
            conn.rollback()
            # Intentar restaurar tabla original
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
                cursor.execute(f"ALTER TABLE {table}_old RENAME TO {table}")
            except:
                pass
            break
    
    conn.commit()
    conn.close()
    print("🎉 Base de datos actualizada exitosamente!")

if __name__ == "__main__":
    update_database_constraints()