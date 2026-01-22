"""
Script para exportar datos de tu aplicación a JSON para que el asistente los use
"""
import json
import os
from datetime import datetime

def export_tasks(tasks_data):
    """Exportar tareas a JSON"""
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    tasks_file = os.path.join(data_dir, "tasks.json")
    
    # Formatear tareas para exportar
    export_tasks = []
    for task in tasks_data:
        export_tasks.append({
            "id": task.get('id', 0),
            "title": task.get('title', 'Sin título'),
            "description": task.get('description', ''),
            "priority": task.get('priority', 'media'),
            "category": task.get('category', 'General'),
            "due_date": task.get('due_date', ''),
            "due_time": task.get('due_time', ''),
            "completed": task.get('completed', False),
            "created_at": task.get('created_at', '')
        })
    
    with open(tasks_file, 'w', encoding='utf-8') as f:
        json.dump(export_tasks, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Exportadas {len(export_tasks)} tareas")

def export_events(events_data):
    """Exportar eventos a JSON"""
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    events_file = os.path.join(data_dir, "events.json")
    
    # Formatear eventos para exportar
    export_events = []
    for event in events_data:
        export_events.append({
            "id": event.get('id', 0),
            "title": event.get('title', 'Sin título'),
            "description": event.get('description', ''),
            "date": event.get('date', ''),
            "start_time": event.get('start_time', ''),
            "end_time": event.get('end_time', ''),
            "location": event.get('location', ''),
            "color": event.get('color', '#4285f4'),
            "recurrence": event.get('recurrence', 'ninguna'),
            "created_at": event.get('created_at', '')
        })
    
    with open(events_file, 'w', encoding='utf-8') as f:
        json.dump(export_events, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Exportados {len(export_events)} eventos")

def export_reminders(reminders_data):
    """Exportar recordatorios a JSON"""
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    reminders_file = os.path.join(data_dir, "reminders.json")
    
    # Formatear recordatorios para exportar
    export_reminders = []
    for reminder in reminders_data:
        export_reminders.append({
            "id": reminder.get('id', 0),
            "title": reminder.get('title', 'Sin título'),
            "description": reminder.get('description', ''),
            "date_time": reminder.get('date_time', ''),
            "date": reminder.get('date', ''),
            "time": reminder.get('time', ''),
            "priority": reminder.get('priority', 'media'),
            "recurrence": reminder.get('recurrence', 'No repetir'),
            "active": reminder.get('active', True),
            "completed": reminder.get('completed', False),
            "sound": reminder.get('sound', True),
            "popup": reminder.get('popup', True),
            "created_at": reminder.get('created_at', '')
        })
    
    with open(reminders_file, 'w', encoding='utf-8') as f:
        json.dump(export_reminders, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Exportados {len(export_reminders)} recordatorios")

if __name__ == "__main__":
    # Ejemplo de uso desde tu aplicación principal
    # Deberás importar tus datos reales aquí
    
    # Ejemplo con datos de prueba
    sample_tasks = [
        {
            "id": 1,
            "title": "Revisar informe mensual",
            "description": "Revisar y aprobar el informe de ventas",
            "priority": "alta",
            "category": "Trabajo",
            "due_date": datetime.now().strftime("%Y-%m-%d"),
            "due_time": "17:00",
            "completed": False,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    ]
    
    sample_events = [
        {
            "id": 1,
            "title": "Reunión de equipo",
            "description": "Reunión semanal de coordinación",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "start_time": "10:00",
            "end_time": "11:00",
            "location": "Sala de conferencias A",
            "color": "#4285f4",
            "recurrence": "Semanal",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    ]
    
    sample_reminders = [
        {
            "id": 1,
            "title": "Tomar medicamentos",
            "description": "Tomar vitaminas diarias",
            "date_time": f"{datetime.now().strftime('%d/%m/%Y')} 08:00",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": "08:00",
            "priority": "alta",
            "recurrence": "Diario",
            "active": True,
            "completed": False,
            "sound": True,
            "popup": True,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    ]
    
    # Exportar datos
    export_tasks(sample_tasks)
    export_events(sample_events)
    export_reminders(sample_reminders)