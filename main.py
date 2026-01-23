#!/usr/bin/env python3
"""
Archivo principal que:
1. Ejecuta la autenticación facial usando face_auth.py (funcional)
2. Obtiene el nombre del usuario reconocido
3. Inicia la aplicación PySide6 con el user_id correspondiente
"""

import sys
import os
from PySide6.QtWidgets import QApplication, QMessageBox
import time

# Configurar paths
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.extend([
    current_dir,
    os.path.join(current_dir, "gui"),
    os.path.join(current_dir, "intento1")
])

def main():
    print("\n" + "=" * 60)
    print("ASISTENTE PERSONAL - SISTEMA DE RECONOCIMIENTO FACIAL")
    print("=" * 60)
    
    print("\n🔐 INICIANDO SISTEMA DE AUTENTICACIÓN...")
    
    # 1. Ejecutar autenticación facial usando face_auth.py
    try:
        # Importar el sistema facial
        from face_auth import run_authentication_flow, FaceAuthenticator
        from face_system import FaceSystem
        
        # Verificar si hay usuarios registrados
        face_system = FaceSystem()
        user_count = face_system.get_user_count()
        
        if user_count == 0:
            print("\n⚠️ No hay usuarios registrados en el sistema facial.")
            print("   ¿Deseas registrar un nuevo usuario? (s/n): ", end="")
            choice = input().strip().lower()
            
            if choice == 's':
                print("\n📝 REGISTRO DE NUEVO USUARIO")
                print("-" * 40)
                username = input("Nombre del nuevo usuario: ").strip()
                
                if username:
                    authenticator = FaceAuthenticator(face_system)
                    success, message = authenticator.register_new_user(username)
                    print(f"\n{message}")
                    
                    if not success:
                        print("⚠️ Continuando en modo invitado...")
                        username = "Invitado"
                        user_id = "guest_0000"
                        use_face_auth = False
                    else:
                        use_face_auth = True
                        user_id = f"user_{username.lower().replace(' ', '_')}"
                else:
                    print("❌ Nombre inválido. Continuando en modo invitado...")
                    username = "Invitado"
                    user_id = "guest_0000"
                    use_face_auth = False
            else:
                print("⚠️ Continuando en modo invitado...")
                username = "Invitado"
                user_id = "guest_0000"
                use_face_auth = False
        else:
            print(f"✅ Sistema facial listo. Usuarios registrados: {user_count}")
            print("\n🔍 Iniciando reconocimiento facial...")
            print("   Por favor, colócate frente a la cámara")
            print("   Tienes 30 segundos para reconocerte")
            print("   Presiona 'q' en la ventana para cancelar\n")
            
            # Ejecutar el flujo de autenticación
            time.sleep(2)  # Dar tiempo para leer el mensaje
            
            success, username, confidence = run_authentication_flow(face_system)
            
            if success:
                print(f"\n✅ ¡AUTENTICACIÓN EXITOSA!")
                print(f"   Bienvenido/a: {username}")
                print(f"   Confianza: {confidence:.2%}")
                real_username = username  # ← Guardar el nombre REAL
                user_id = f"user_{username.lower().replace(' ', '_')}"
                use_face_auth = True
            else:
                print("\n❌ AUTENTICACIÓN FALLIDA")
                print("\nOpciones:")
                print("1. Reintentar autenticación")
                print("2. Continuar como invitado")
                print("3. Salir")
                
                choice = input("\nSelecciona opción (1-3): ").strip()
                
                if choice == "1":
                    # Intentar de nuevo
                    success, username, confidence = run_authentication_flow(face_system)
                    if success:
                        user_id = f"user_{username.lower().replace(' ', '_')}"
                        use_face_auth = True
                    else:
                        print("⚠️ Continuando en modo invitado...")
                        username = "Invitado"
                        user_id = "guest_0000"
                        use_face_auth = False
                elif choice == "2":
                    print("⚠️ Continuando en modo invitado...")
                    username = "Invitado"
                    user_id = "guest_0000"
                    use_face_auth = False
                else:
                    print("👋 Saliendo...")
                    return
        
    except ImportError as e:
        print(f"⚠️ Error importando módulos faciales: {e}")
        print("⚠️ Continuando en modo desarrollo...")
        username = "Desarrollo"
        user_id = "dev_001"
        use_face_auth = False
    except Exception as e:
        print(f"❌ Error en autenticación: {e}")
        print("⚠️ Continuando en modo desarrollo...")
        username = "Desarrollo"
        user_id = "dev_001"
        use_face_auth = False
    
    # 2. Iniciar aplicación Qt
    # Después de la autenticación facial, antes de crear MainWindow:
    print(f"\n🚀 INICIANDO APLICACIÓN PARA: {username}")
    print(f"   ID de usuario: {user_id}")
    print(f"   Autenticación facial: {'✅' if use_face_auth else '❌'}")

    # ✅ AÑADIR ESTO: Crear/establecer usuario antes de iniciar la app
    try:
        from user_manager import get_user_manager
        user_manager = get_user_manager()
        
        # Crear el usuario si no existe, o obtenerlo
        actual_user_id = user_manager.create_or_get_user(user_id, username)
        print(f"✅ Usuario preparado en sistema: {actual_user_id}")
        
    except Exception as e:
        print(f"⚠️ Error preparando usuario: {e}")
    
    app = QApplication(sys.argv)
    
    try:
        from gui.main_window import MainWindow
        from gui.global_assistant import get_global_assistant
        global_assistant = get_global_assistant(username)

        # Configurar tema oscuro
        app.setStyle("Fusion")
        from PySide6.QtGui import QPalette, QColor
        from PySide6.QtCore import Qt
        
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.WindowText, Qt.white)
        dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
        dark_palette.setColor(QPalette.ToolTipText, Qt.white)
        dark_palette.setColor(QPalette.Text, Qt.white)
        dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ButtonText, Qt.white)
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.HighlightedText, Qt.black)
        app.setPalette(dark_palette)
        
        # Iniciar ventana principal
        print("🎬 Cargando interfaz principal...")
        
        # Intentar crear MainWindow con user_id
        try:
            # Opción 1: Si MainWindow acepta user_id como parámetro
            window = MainWindow(user_id=user_id)
            print("✅ Ventana principal creada con user_id como parámetro")
        except TypeError as e:
            # Opción 2: Si MainWindow no acepta parámetros
            print(f"⚠️ MainWindow no acepta parámetros: {e}")
            print("⚠️ Creando ventana y ajustando user_id después...")
            
            window = MainWindow()
            
            # Intentar ajustar user_id después de la creación
            if hasattr(window, 'user_id'):
                window.user_id = user_id
                print(f"✅ user_id establecido a: {user_id}")
            
            if hasattr(window, 'user_data'):
                window.user_data = {
                    "name": username,
                    "user_id": user_id,
                    "use_face_auth": use_face_auth
                }
                print(f"✅ user_data establecido para: {username}")
            
            # Actualizar etiqueta de usuario si existe
            if hasattr(window, 'user_label'):
                window.user_label.setText(f"👤 {username}")
                print("✅ Etiqueta de usuario actualizada")
        
        window.show()
        
        print("\n" + "=" * 60)
        print("✅ APLICACIÓN INICIADA CORRECTAMENTE")
        print("=" * 60)
        print(f"👤 Usuario: {username}")
        print(f"🔑 ID: {user_id}")
        print(f"🔐 Autenticación facial: {'Activada' if use_face_auth else 'Desactivada'}")
        print("\n💡 Presiona Ctrl+C en esta terminal para salir")
        print("=" * 60)
        
        sys.exit(app.exec())
        
    except ImportError as e:
        print(f"❌ Error importando MainWindow: {e}")
        QMessageBox.critical(
            None,
            "Error de importación",
            f"No se pudo cargar la ventana principal:\n{str(e)}"
        )
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        QMessageBox.critical(
            None,
            "Error",
            f"No se pudo iniciar la aplicación:\n{str(e)}"
        )

if __name__ == "__main__":
    main()