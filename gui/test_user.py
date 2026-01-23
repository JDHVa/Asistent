#!/usr/bin/env python3
"""
Script para inicializar/verificar la base de datos - VERSIÓN SIMPLIFICADA
"""
import sys
import os
import sqlite3

# Añadir directorio actual al path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

def init_database():
    """Inicializar y verificar la base de datos"""
    try:
        from database_manager import get_database
        
        print("🔧 Inicializando base de datos...")
        
        # Forzar la creación de la base de datos
        db = get_database()
        
        # Verificar conexión
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        
        # Listar tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print("\n📊 Tablas en la base de datos:")
        if tables:
            for table in tables:
                print(f"  ✅ {table[0]}")
        else:
            print("  ❌ No hay tablas en la base de datos")
            return False
        
        # Crear usuario de prueba
        from user_manager import get_user_manager
        user_manager = get_user_manager()
        
        test_user_id = user_manager.create_or_get_user("test_user", "Usuario de Prueba")
        
        if test_user_id:
            print(f"\n✅ Usuario de prueba creado: test_user")
        
        conn.close()
        print("\n" + "="*60)
        print("✅ Base de datos verificada correctamente")
        print("="*60 + "\n")
        return True
        
    except Exception as e:
        print(f"❌ Error crítico inicializando base de datos: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Limpiar base de datos anterior (si existe)
    try:
        if os.path.exists("data/asistente_personal.db"):
            print("🗑️ Eliminando base de datos anterior...")
            os.remove("data/asistente_personal.db")
    except:
        pass
    
    if init_database():
        sys.exit(0)
    else:
        sys.exit(1)