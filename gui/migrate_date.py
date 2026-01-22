# migrate_data.py
import json
import os
from database_manager import get_database
from datetime import datetime

def migrate_json_to_sqlite(user_id="default"):
    """Migrar datos de archivos JSON a la base de datos SQLite"""
    db = get_database()
    
    # Establecer usuario
    db.create_user(user_id, "Migrated User")
    db.set_current_user(user_id)
    
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    
    # Migrar tareas
    tasks_file = os.path.join(data_dir, "tasks.json")
    if os.path.exists(tasks_file):
        with open(tasks_file, 'r', encoding='utf-8') as f:
            tasks = json.load(f)
            for task in tasks:
                db.save_task(task)
        print(f"✅ Migradas {len(tasks)} tareas")
    
    # Migrar eventos
    events_file = os.path.join(data_dir, "events.json")
    if os.path.exists(events_file):
        with open(events_file, 'r', encoding='utf-8') as f:
            events = json.load(f)
            for event in events:
                db.save_event(event)
        print(f"✅ Migrados {len(events)} eventos")
    
    # Migrar recordatorios
    reminders_file = os.path.join(data_dir, "reminders.json")
    if os.path.exists(reminders_file):
        with open(reminders_file, 'r', encoding='utf-8') as f:
            reminders = json.load(f)
            for reminder in reminders:
                db.save_reminder(reminder)
        print(f"✅ Migrados {len(reminders)} recordatorios")
    
    print("🚀 Migración completada exitosamente!")

if __name__ == "__main__":
    migrate_json_to_sqlite()