#!/usr/bin/env python3
"""
Script para inicializar/verificar la base de datos
"""
import sys
import os

# Añadir directorio actual al path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

def init_database():
    """Inicializar y verificar la base de datos"""
    try:
        from database_manager import get_database
        
        print("🔧 Inicializando base de datos...")
        db = get_database()
        
        # Verificar que la base de datos se creó correctamente
        import sqlite3
        conn = sqlite3.connect("data/asistente_personal.db")
        cursor = conn.cursor()
        
        # Listar tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print("📊 Tablas en la base de datos:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Verificar estructura de tablas
        table_checks = {
            'users': ['id', 'name', 'email', 'created_at', 'last_login', 'settings'],
            'tasks': ['id', 'user_id', 'title', 'description', 'category', 'due_date', 'due_time', 'completed'],
            'reminders': ['id', 'user_id', 'title', 'description', 'date', 'time', 'date_time', 'recurrence', 'active', 'completed']
        }
        
        for table_name, expected_columns in table_checks.items():
            if table_name in [t[0] for t in tables]:
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns = [col[1] for col in cursor.fetchall()]
                
                missing = [col for col in expected_columns if col not in columns]
                if missing:
                    print(f"⚠️ Tabla '{table_name}' le faltan columnas: {missing}")
                else:
                    print(f"✅ Tabla '{table_name}' OK")
            else:
                print(f"❌ Tabla '{table_name}' NO EXISTE")
        
        conn.close()
        print("✅ Base de datos verificada correctamente")
        
        # Crear usuario de prueba si no existe
        from user_manager import get_user_manager
        user_manager = get_user_manager()
        test_user_id = user_manager.create_or_get_user("test_user", "Usuario de Prueba")
        
        if test_user_id:
            print(f"✅ Usuario de prueba creado: test_user")
        
        return True
        
    except Exception as e:
        print(f"❌ Error crítico inicializando base de datos: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if init_database():
        print("\n" + "="*60)
        print("✅ Base de datos lista para usar")
        print("="*60 + "\n")
        sys.exit(0)
    else:
        print("\n" + "="*60)
        print("❌ Error inicializando base de datos")
        print("="*60 + "\n")
        sys.exit(1)