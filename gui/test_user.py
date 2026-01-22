# test_database_spanish.py
import sqlite3
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(current_dir, "..", "data", "database", "assistant.db")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Verificar restricciones de tareas
cursor.execute("PRAGMA table_info(tasks)")
columns = cursor.fetchall()
print("📋 Columnas de la tabla 'tasks':")
for col in columns:
    if col[1] == 'priority':
        print(f"  - {col[1]}: {col[2]} (restricción)")
        # Verificar restricción CHECK
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='tasks'")
        create_sql = cursor.fetchone()[0]
        print(f"  - SQL: {create_sql[create_sql.find('CHECK'):create_sql.find(') DEFAULT')+1] if 'CHECK' in create_sql else 'No CHECK'}")
        
# Probar insert con español
test_data = {
    'user_id': 'test_user',
    'title': 'Tarea de prueba',
    'description': 'Descripción',
    'priority': 'alta',  # Español
    'category': 'Trabajo',
    'due_date': '2024-01-01',
    'due_time': '12:00',
    'completed': 0
}

try:
    cursor.execute('''
        INSERT INTO tasks (user_id, title, description, priority, category, due_date, due_time, completed)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', tuple(test_data.values()))
    print("✅ Inserción con español funcionó!")
    conn.commit()
except Exception as e:
    print(f"❌ Error: {e}")

conn.close()