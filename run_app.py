#!/usr/bin/env python3
"""
Archivo principal que integra reconocimiento facial con la aplicación.
Flujo:
1. Primero ejecuta autenticación facial
2. Si es exitosa, obtiene el user_id del usuario reconocido
3. Inicia MainWindow con el user_id correspondiente
"""
import sys
import os
from PySide6.QtWidgets import QApplication, QMessageBox, QSplashScreen
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap

# Añadir directorios al path CORRECTAMENTE
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
sys.path.append(os.path.join(current_dir, "gui"))
sys.path.append(os.path.join(current_dir, "intento1"))

print(f"📁 Directorio actual: {current_dir}")
print(f"📁 Paths añadidos: {sys.path[-3:]}")

# Intentar importar módulos de reconocimiento facial
try:
    from face_auth import FaceAuthenticator, run_authentication_flow
    from face_system import FaceSystem
    FACE_AUTH_AVAILABLE = True
    print("✅ Módulos de reconocimiento facial cargados")
except ImportError as e:
    print(f"❌ No se pudo cargar módulos de reconocimiento facial: {e}")
    FACE_AUTH_AVAILABLE = False
    # Intentar desde intento1
    try:
        from intento1.face_auth import FaceAuthenticator, run_authentication_flow
        from intento1.face_system import FaceSystem
        FACE_AUTH_AVAILABLE = True
        print("✅ Módulos de reconocimiento facial cargados desde intento1/")
    except ImportError as e2:
        print(f"❌ Error definitivo: {e2}")
        FACE_AUTH_AVAILABLE = False

# Intentar importar gestor de usuarios
try:
    from user_manager import get_user_manager
    USER_MANAGER_AVAILABLE = True
    print("✅ Gestor de usuarios disponible")
except ImportError as e:
    print(f"⚠️ No se pudo cargar gestor de usuarios: {e}")
    # Intentar desde gui
    try:
        from gui.user_manager import get_user_manager
        USER_MANAGER_AVAILABLE = True
        print("✅ Gestor de usuarios cargado desde gui/")
    except ImportError as e2:
        print(f"❌ Error definitivo: {e2}")
        USER_MANAGER_AVAILABLE = False

# Importar ventana principal
try:
    from gui.main_window import MainWindow
    MAIN_WINDOW_AVAILABLE = True
    print("✅ Ventana principal disponible")
except ImportError as e:
    print(f"❌ No se pudo cargar ventana principal: {e}")
    MAIN_WINDOW_AVAILABLE = False

# Intentar importar auth_dialog
try:
    from auth_dialog import AuthDialog
    AUTH_DIALOG_AVAILABLE = True
    print("✅ Diálogo de autenticación disponible")
except ImportError as e:
    print(f"⚠️ No se pudo cargar auth_dialog: {e}")
    # Intentar desde intento1
    try:
        from intento1.auth_dialog import AuthDialog
        AUTH_DIALOG_AVAILABLE = True
        print("✅ Diálogo de autenticación cargado desde intento1/")
    except ImportError as e2:
        print(f"❌ Error definitivo: {e2}")
        AUTH_DIALOG_AVAILABLE = False

class FacialAuthApp:
    """Aplicación principal con autenticación facial"""
    
    def __init__(self):
        self.face_system = None
        self.authenticator = None
        self.user_manager = None
        self.current_user_id = None
        self.current_username = None
        
    def setup_auth_system(self):
        """Configurar sistema de autenticación facial"""
        if not FACE_AUTH_AVAILABLE:
            print("❌ Sistema de reconocimiento facial no disponible")
            return False
        
        try:
            self.face_system = FaceSystem()
            self.authenticator = FaceAuthenticator(self.face_system)
            
            # Verificar si hay usuarios registrados
            if self.face_system.get_user_count() == 0:
                print("⚠️ No hay usuarios registrados en el sistema facial")
                return self.register_first_user()
            
            print(f"✅ Sistema facial inicializado. Usuarios: {self.face_system.get_user_count()}")
            return True
            
        except Exception as e:
            print(f"❌ Error configurando sistema facial: {e}")
            return False
    
    def register_first_user(self):
        """Registrar el primer usuario si no hay ninguno"""
        try:
            print("\n" + "=" * 60)
            print("REGISTRO DE PRIMER USUARIO")
            print("=" * 60)
            print("No hay usuarios registrados en el sistema facial.")
            print("Necesitas registrar al menos un usuario para continuar.")
            
            username = input("\nNombre del nuevo usuario: ").strip()
            if not username:
                print("❌ Nombre inválido")
                return False
            
            # Registrar usuario en sistema facial
            print(f"\nRegistrando usuario: {username}")
            print("Por favor, colócate frente a la cámara...")
            
            success, message = self.authenticator.register_new_user(username)
            if success:
                print(f"✅ {message}")
                
                # Intentar registrar también en user_manager si está disponible
                if USER_MANAGER_AVAILABLE:
                    try:
                        self.user_manager = get_user_manager()
                        # Crear usuario en la base de datos
                        user_id = self.user_manager.create_user(
                            username=username,
                            email=f"{username.lower()}@asistente.com",
                            password="facial_auth",  # Contraseña por defecto
                            use_facial_auth=True
                        )
                        if user_id:
                            print(f"✅ Usuario creado en base de datos con ID: {user_id}")
                    except Exception as e:
                        print(f"⚠️ No se pudo crear usuario en base de datos: {e}")
                
                return True
            else:
                print(f"❌ Error en registro: {message}")
                return False
                
        except Exception as e:
            print(f"❌ Error registrando usuario: {e}")
            return False
    
    def authenticate_user(self, timeout=30):
        """Autenticar usuario mediante reconocimiento facial"""
        if not self.authenticator:
            print("❌ Sistema de autenticación no inicializado")
            return False, None, None
        
        try:
            print("\n" + "=" * 60)
            print("AUTENTICACIÓN FACIAL")
            print("=" * 60)
            print("Por favor, colócate frente a la cámara...")
            print(f"Tienes {timeout} segundos para autenticarte.")
            print("Presiona 'q' en la ventana para cancelar.")
            
            success, username, confidence = self.authenticator.authenticate_user(timeout)
            
            if success:
                print(f"\n✅ ¡Autenticación exitosa!")
                print(f"   Usuario: {username}")
                print(f"   Confianza: {confidence:.2%}")
                self.current_username = username
                return True, username, confidence
            else:
                print("\n❌ Autenticación fallida")
                if username and username != "Desconocido":
                    print(f"   Mejor coincidencia: {username} ({confidence:.2%})")
                return False, None, None
                
        except Exception as e:
            print(f"❌ Error en autenticación: {e}")
            return False, None, None
    
    def get_user_id_from_username(self, username):
        """Obtener user_id a partir del nombre de usuario reconocido"""
        if not USER_MANAGER_AVAILABLE:
            print("⚠️ Gestor de usuarios no disponible. Usando modo invitado.")
            return f"user_{username.lower().replace(' ', '_')}"
        
        try:
            self.user_manager = get_user_manager()
            
            # Buscar usuario por nombre
            user_data = self.user_manager.find_user_by_username(username)
            
            if user_data:
                print(f"✅ Usuario encontrado en base de datos: {user_data}")
                return user_data.get('user_id')
            else:
                # Si no existe, crear usuario
                print(f"⚠️ Usuario '{username}' no encontrado en base de datos. Creando...")
                
                user_id = self.user_manager.create_user(
                    username=username,
                    email=f"{username.lower().replace(' ', '_')}@asistente.com",
                    password="facial_auth",
                    use_facial_auth=True
                )
                
                if user_id:
                    print(f"✅ Nuevo usuario creado con ID: {user_id}")
                    return user_id
                else:
                    print("❌ No se pudo crear usuario. Usando modo invitado.")
                    return f"user_{username.lower().replace(' ', '_')}"
                    
        except Exception as e:
            print(f"❌ Error obteniendo user_id: {e}")
            return f"user_{username.lower().replace(' ', '_')}"
    
    def run_with_auth_dialog(self):
        """Ejecutar con diálogo de autenticación Qt"""
        from auth_dialog import AuthDialog
        
        app = QApplication(sys.argv)
        
        # Mostrar splash screen
        splash_pix = QPixmap(400, 300)
        splash_pix.fill(Qt.darkGray)
        splash = QSplashScreen(splash_pix)
        splash.showMessage("Iniciando sistema de reconocimiento facial...", 
                          Qt.AlignBottom | Qt.AlignCenter, Qt.white)
        splash.show()
        
        QTimer.singleShot(2000, splash.close)  # Mostrar por 2 segundos
        
        # Inicializar sistema facial
        self.setup_auth_system()
        
        # Crear diálogo de autenticación
        auth_dialog = AuthDialog(self.face_system)
        
        def on_auth_success(user_data):
            """Manejador de autenticación exitosa"""
            print(f"✅ Autenticación exitosa desde diálogo: {user_data}")
            username = user_data.get('name')
            self.current_username = username
            
            # Obtener user_id
            user_id = self.get_user_id_from_username(username)
            self.current_user_id = user_id
            
            # Cerrar diálogo y abrir ventana principal
            auth_dialog.accept()
            
            # Iniciar ventana principal
            self.start_main_window(app, user_id)
        
        def on_auth_failed(error_msg):
            """Manejador de autenticación fallida"""
            print(f"❌ Autenticación fallida: {error_msg}")
            
            # Preguntar si desea continuar en modo invitado
            reply = QMessageBox.question(
                None,
                "Autenticación Fallida",
                "No se pudo autenticar. ¿Desea continuar en modo invitado?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                auth_dialog.accept()
                self.start_main_window(app, "guest_0000")
            else:
                auth_dialog.reject()
                sys.exit()
        
        def on_auth_skipped():
            """Manejador para saltar autenticación"""
            print("⚠️ Autenticación saltada (modo desarrollo)")
            auth_dialog.accept()
            self.start_main_window(app, "demo_001")
        
        # Conectar señales
        auth_dialog.auth_successful.connect(on_auth_success)
        auth_dialog.auth_failed.connect(on_auth_failed)
        auth_dialog.auth_skipped.connect(on_auth_skipped)
        
        # Mostrar diálogo de autenticación
        auth_dialog.exec()
        
        sys.exit(app.exec())
    
    def start_main_window(self, app, user_id):
        """Iniciar ventana principal con user_id específico"""
        try:
            # Modificar el main_window para que use nuestro user_id
            window = MainWindow()
            
            # Sobreescribir el user_id si MainWindow lo permite
            # (esto depende de cómo esté implementado MainWindow)
            # Si MainWindow no acepta parámetros, necesitaríamos modificarlo
            
            # Opción 1: Si MainWindow acepta user_id en constructor
            try:
                window = MainWindow(user_id=user_id)
            except TypeError:
                # Opción 2: Si no acepta parámetros, modificar atributos después
                window.user_id = user_id
                window.user_data = {
                    "name": self.current_username or "Usuario",
                    "user_id": user_id
                }
                # Actualizar etiqueta en barra de estado
                if hasattr(window, 'user_label'):
                    window.user_label.setText(f"👤 {self.current_username or 'Usuario'}")
            
            window.show()
            
        except Exception as e:
            print(f"❌ Error iniciando ventana principal: {e}")
            QMessageBox.critical(
                None,
                "Error",
                f"No se pudo iniciar la aplicación:\n{str(e)}"
            )
            sys.exit(1)
    
    def run_cli_mode(self):
        """Ejecutar en modo línea de comandos (sin interfaz Qt)"""
        print("\n" + "=" * 60)
        print("MODO CONSOLA - AUTENTICACIÓN FACIAL")
        print("=" * 60)
        
        # Configurar sistema
        if not self.setup_auth_system():
            print("❌ No se pudo inicializar el sistema facial")
            return
        
        # Autenticar usuario
        success, username, confidence = self.authenticate_user(timeout=30)
        
        if not success:
            print("\n❌ No se pudo autenticar al usuario.")
            response = input("¿Continuar en modo invitado? (s/n): ").strip().lower()
            if response == 's':
                user_id = "guest_0000"
                username = "Invitado"
            else:
                return
        
        # Obtener user_id
        user_id = self.get_user_id_from_username(username)
        
        print(f"\n✅ Iniciando aplicación para usuario:")
        print(f"   Nombre: {username}")
        print(f"   ID: {user_id}")
        
        # Iniciar aplicación Qt
        app = QApplication(sys.argv)
        
        # Configurar paleta oscura
        app.setStyle("Fusion")
        from PySide6.QtGui import QPalette, QColor
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.WindowText, Qt.white)
        app.setPalette(dark_palette)
        
        # Iniciar ventana principal
        self.current_user_id = user_id
        self.current_username = username
        self.start_main_window(app, user_id)
        
        sys.exit(app.exec())


def main():
    """Función principal"""
    print("\n" + "=" * 60)
    print("ASISTENTE PERSONAL - SISTEMA DE RECONOCIMIENTO FACIAL")
    print("=" * 60)
    
    # Verificar dependencias
    if not MAIN_WINDOW_AVAILABLE:
        print("❌ No se pudo cargar la ventana principal")
        return
    
    # Crear instancia de la aplicación
    app = FacialAuthApp()
    
    # Elegir modo de ejecución
    print("\nModos de ejecución disponibles:")
    print("1. Modo gráfico completo (recomendado)")
    print("2. Modo consola")
    
    try:
        choice = input("\nSelecciona modo (1-2, Enter para modo gráfico): ").strip()
        
        if choice == "2":
            app.run_cli_mode()
        else:
            app.run_with_auth_dialog()
            
    except KeyboardInterrupt:
        print("\n\n❌ Aplicación interrumpida por el usuario")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()