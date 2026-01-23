"""
Ventana principal del Asistente Personal con PySide6.
Incluye 4 pestañas: Chat, Tareas, Horario, Recordatorios.
"""
from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, 
    QHBoxLayout, QLabel, QFrame, QPushButton, QSystemTrayIcon,
    QMenu, QApplication, QStatusBar, QToolBar, QMessageBox,
    QInputDialog
)
from PySide6.QtCore import Qt, QSize, Signal, QTimer
from PySide6.QtGui import QIcon, QFont, QPalette, QColor, QAction
import os
import sys

# Añadir directorio actual al path para imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Importar sistema de base de datos y usuarios
try:
    from database_manager import get_database
    from user_manager import get_user_manager, get_current_user_info
    
    # Inicializar base de datos primero
    db = get_database()  # Esto crea e inicializa la base de datos
    DATABASE_AVAILABLE = True
    print("✅ Módulos de base de datos importados correctamente")
    
except ImportError as e:
    print(f"⚠️ No se pudo importar sistema de base de datos: {e}")
    DATABASE_AVAILABLE = False
    
    # Funciones dummy para cuando no hay base de datos
    def get_database():
        return None
    
    def get_user_manager():
        return None
    
    def get_current_user_info():
        return {"name": "Invitado", "user_id": "guest_0000"}
except Exception as e:
    print(f"⚠️ Error inicializando base de datos: {e}")
    DATABASE_AVAILABLE = False

# Importar el asistente global
try:
    from global_assistant import get_global_assistant
    ASSISTANT_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ No se pudo importar asistente global: {e}")
    ASSISTANT_AVAILABLE = False
    def get_global_assistant(user_id=None, user_name="Usuario"):
        return None

# Importar los paneles (con manejo de errores)
try:
    # Intentar importar el módulo styles
    try:
        from styles import get_stylesheet
        STYLES_AVAILABLE = True
    except ImportError:
        print("⚠️ No se encontró styles.py, usando estilos por defecto")
        STYLES_AVAILABLE = False
        def get_stylesheet():
            return ""
    
    # Intentar importar los paneles
    try:
        from chat_panel import ChatPanel
        CHAT_PANEL_AVAILABLE = True
    except ImportError:
        print("⚠️ ChatPanel no disponible")
        CHAT_PANEL_AVAILABLE = False
        
    try:
        from tasks_panel import TasksPanel
        TASKS_PANEL_AVAILABLE = True
    except ImportError:
        print("⚠️ TasksPanel no disponible")
        TASKS_PANEL_AVAILABLE = False
        
    try:
        from schedule_panel import SchedulePanel
        SCHEDULE_PANEL_AVAILABLE = True
    except ImportError:
        print("⚠️ SchedulePanel no disponible")
        SCHEDULE_PANEL_AVAILABLE = False
        
    try:
        from reminders_panel import RemindersPanel
        REMINDERS_PANEL_AVAILABLE = True
    except ImportError:
        print("⚠️ RemindersPanel no disponible")
        REMINDERS_PANEL_AVAILABLE = False
    
    PANELS_AVAILABLE = True
    
except ImportError as e:
    print(f"❌ Error importando módulos: {e}")
    PANELS_AVAILABLE = False
    
    # Crear placeholders si fallan los imports
    class ChatPanel(QWidget):
        def __init__(self, user_id=None, parent=None):
            super().__init__(parent)
            label = QLabel("Panel de Chat (No disponible)")
            label.setAlignment(Qt.AlignCenter)
            layout = QVBoxLayout()
            layout.addWidget(label)
            self.setLayout(layout)
        def get_tasks_for_assistant(self):
            return []
    
    class TasksPanel(QWidget):
        def __init__(self, user_id=None, parent=None):
            super().__init__(parent)
            label = QLabel("Panel de Tareas (No disponible)")
            label.setAlignment(Qt.AlignCenter)
            layout = QVBoxLayout()
            layout.addWidget(label)
            self.setLayout(layout)
        def get_tasks_for_assistant(self):
            return []
        def get_events_for_assistant(self):
            return []
        def get_reminders_for_assistant(self):
            return []
    
    class SchedulePanel(QWidget):
        def __init__(self, user_id=None, parent=None):
            super().__init__(parent)
            label = QLabel("Panel de Horario (No disponible)")
            label.setAlignment(Qt.AlignCenter)
            layout = QVBoxLayout()
            layout.addWidget(label)
            self.setLayout(layout)
        def get_events_for_assistant(self):
            return []
    
    class RemindersPanel(QWidget):
        def __init__(self, user_id=None, parent=None):
            super().__init__(parent)
            label = QLabel("Panel de Recordatorios (No disponible)")
            label.setAlignment(Qt.AlignCenter)
            layout = QVBoxLayout()
            layout.addWidget(label)
            self.setLayout(layout)
        def get_reminders_for_assistant(self):
            return []

class TitleBar(QFrame):
    """Barra de título personalizada CORREGIDA"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent  # Guardar referencia a la ventana principal
        self.setup_ui()
        
    def setup_ui(self):
        """SOLO configurar la barra de título, no toda la ventana"""
        self.setObjectName("TitleBar")
        self.setFixedHeight(50)
        
        layout = QHBoxLayout(self)  # Layout directamente en TitleBar
        layout.setContentsMargins(15, 5, 15, 5)
        
        # Logo y título
        self.logo_label = QLabel("🤖")
        self.logo_label.setStyleSheet("font-size: 20px;")
        
        self.title_label = QLabel("Asistente Personal")
        self.title_label.setObjectName("TitleLabel")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        
        layout.addWidget(self.logo_label)
        layout.addWidget(self.title_label)
        layout.addStretch()
        
        # Botones de control de ventana
        control_layout = QHBoxLayout()
        control_layout.setSpacing(5)
        
        # Botón minimizar
        self.minimize_btn = QPushButton("─")
        self.minimize_btn.setFixedSize(30, 30)
        self.minimize_btn.setToolTip("Minimizar")
        self.minimize_btn.clicked.connect(self.parent_window.showMinimized)
        
        # Botón maximizar/restaurar
        self.maximize_btn = QPushButton("□")
        self.maximize_btn.setFixedSize(30, 30)
        self.maximize_btn.setToolTip("Maximizar")
        self.maximize_btn.clicked.connect(self.toggle_maximize)
        
        # Botón cerrar
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.setToolTip("Cerrar")
        self.close_btn.clicked.connect(self.parent_window.close)
        
        # Estilos de los botones
        button_style = """
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 6px;
                color: #e8eaed;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3c4043;
            }
            QPushButton#close_btn:hover {
                background-color: #ea4335;
                color: white;
            }
        """
        self.minimize_btn.setStyleSheet(button_style)
        self.maximize_btn.setStyleSheet(button_style)
        self.close_btn.setObjectName("close_btn")
        self.close_btn.setStyleSheet(button_style)
        
        control_layout.addWidget(self.minimize_btn)
        control_layout.addWidget(self.maximize_btn)
        control_layout.addWidget(self.close_btn)
        
        layout.addLayout(control_layout)
    
    def toggle_maximize(self):
        if self.parent_window.isMaximized():
            self.parent_window.showNormal()
            self.maximize_btn.setText("□")
        else:
            self.parent_window.showMaximized()
            self.maximize_btn.setText("❐")

class MainWindow(QMainWindow):
    def __init__(self, user_id=None, username=None):
        super().__init__()
        
        print("🚀 Iniciando Asistente Personal...")
        
        # Inicializar gestor de usuarios
        self.user_manager = get_user_manager()
        
        # Manejo de usuario con fallbacks robustos
        try:
            if DATABASE_AVAILABLE:
                if user_id:
                    print(f"🔧 Usuario recibido: {user_id}")
                    
                    # Usar el gestor de usuarios para crear/establecer usuario
                    actual_user_id = self.user_manager.create_or_get_user(user_id, username)
                    self.user_id = actual_user_id
                    
                    # Obtener información actualizada del usuario
                    user_info = self.user_manager.get_current_user()
                    if user_info:
                        self.username = user_info.get('name', username or 'Usuario')
                        self.user_data = dict(user_info)
                        print(f"✅ Usuario cargado desde BD: {self.username}")
                    else:
                        self.username = username or user_id.replace('user_', '').replace('_', ' ').title()
                        self.user_data = {"name": self.username, "user_id": self.user_id}
                        print(f"⚠️ Usuario creado nuevo: {self.username}")
                    
                else:
                    # Auto-login (comportamiento original)
                    self.user_id = self.user_manager.auto_login()
                    user_info = self.user_manager.get_current_user()
                    
                    if user_info:
                        self.user_data = dict(user_info)
                        self.username = self.user_data.get('name', 'Usuario')
                    else:
                        self.username = "Usuario"
                        self.user_data = {"name": self.username, "user_id": self.user_id}
                    
                    print(f"✅ Auto-login completado: {self.username}")
                
            else:
                # Modo sin base de datos
                print("⚠️ Modo sin base de datos activado")
                if user_id:
                    self.user_id = user_id
                    self.username = username if username else user_id.replace('user_', '').replace('_', ' ').title()
                else:
                    self.user_id = "guest_0000"
                    self.username = "Invitado"
                
                self.user_data = {"name": self.username, "user_id": self.user_id}
                print(f"⚠️ Usando usuario temporal: {self.username}")
                
        except Exception as e:
            print(f"❌ Error crítico en inicialización de usuario: {e}")
            # Fallback absoluto
            self.user_id = "emergency_guest"
            self.username = "Invitado"
            self.user_data = {"name": self.username, "user_id": self.user_id}
            print(f"⚠️ Usando usuario de emergencia: {self.username}")
        
        # Inicializar base de datos SIEMPRE (aunque esté en modo fallback)
        try:
            self.db = get_database()
            print("✅ Base de datos inicializada")
            
            # Establecer usuario en la base de datos
            if self.user_id and self.db:
                self.db.set_current_user(self.user_id)
                print(f"✅ Usuario establecido en BD: {self.user_id}")
                
        except Exception as e:
            print(f"❌ Error inicializando base de datos: {e}")
            self.db = None

        print(f"🔧 Iniciando para usuario: {self.username} (ID: {self.user_id})")
        
        # Inicializar asistente global CON EL NOMBRE REAL
        try:
            if ASSISTANT_AVAILABLE:
                from global_assistant import get_global_assistant
                
                # Usar el nombre REAL del usuario, no el ID
                actual_name = self.user_data.get('name', self.username)
                self.assistant = get_global_assistant(self.user_id, actual_name)
                
                if self.assistant:
                    # Conectar señales del asistente
                    self.assistant.response_ready.connect(self.show_assistant_response)
                    self.assistant.error_occurred.connect(self.show_assistant_error)
                    print(f"✅ Asistente global inicializado para: {actual_name}")
                else:
                    print("⚠️ Asistente global no disponible")
                    self.assistant = None
            else:
                self.assistant = None
        except Exception as e:
            print(f"❌ Error inicializando asistente global: {e}")
            self.assistant = None
        
        # Configurar ventana e interfaz
        try:
            self.setup_window()
            self.setup_ui()
            self.setup_tray_icon()
            self.apply_styles()
            print("✅ Interfaz configurada exitosamente")
        except Exception as e:
            print(f"❌ Error crítico configurando interfaz: {e}")
            import traceback
            traceback.print_exc()
            # Aún así mostrar la ventana con error mínimo
            self.setup_minimal_ui()
        
        # Verificación final del estado
        print("\n" + "=" * 60)
        print("📊 RESUMEN DE INICIALIZACIÓN:")
        print(f"👤 Usuario: {self.username}")
        print(f"🔑 ID: {self.user_id}")
        print(f"📁 User Data: {self.user_data}")
        print(f"🗄️  Base de datos: {'✅ Disponible' if self.db else '❌ No disponible'}")
        print(f"🤖 Asistente: {'✅ Inicializado' if self.assistant else '❌ No disponible'}")
        print("=" * 60 + "\n")
    
    def setup_minimal_ui(self):
        """Configurar interfaz mínima en caso de error"""
        self.setWindowTitle("Asistente Personal - Modo de Recuperación")
        self.setMinimumSize(800, 600)
        
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        
        error_label = QLabel("⚠️ La interfaz principal no pudo cargarse completamente.")
        error_label.setStyleSheet("color: #ea4335; font-size: 16px; font-weight: bold;")
        error_label.setAlignment(Qt.AlignCenter)
        
        user_label = QLabel(f"Usuario: {self.username}")
        user_label.setAlignment(Qt.AlignCenter)
        
        layout.addStretch()
        layout.addWidget(error_label)
        layout.addWidget(user_label)
        layout.addStretch()
        
        self.setCentralWidget(central_widget)
    
    def setup_window(self):
        """Configuración básica de la ventana"""
        self.setWindowTitle(f"Asistente Personal - {self.username}")
        self.setMinimumSize(1100, 750)
        
        # Para ventana sin bordes nativos
        self.setWindowFlags(Qt.FramelessWindowHint)
        
        # Para permitir sombras y efectos
        self.setAttribute(Qt.WA_TranslucentBackground)
    
    def setup_assistant_callbacks(self):
        """Configurar callbacks para que el asistente acceda a los datos"""
        if not self.assistant:
            return
        
        # Registrar callbacks para que el asistente obtenga datos de los paneles
        callbacks = {
            'get_tasks': self.get_tasks_for_assistant,
            'get_events': self.get_events_for_assistant,
            'get_reminders': self.get_reminders_for_assistant,
            'get_current_panel': self.get_current_panel_name
        }
        self.assistant.register_callbacks(callbacks)
    
    def get_tasks_for_assistant(self):
        """Obtener tareas para el asistente"""
        try:
            if hasattr(self, 'tasks_panel') and hasattr(self.tasks_panel, 'get_tasks_for_assistant'):
                return self.tasks_panel.get_tasks_for_assistant()
        except Exception as e:
            print(f"⚠️ Error obteniendo tareas para asistente: {e}")
        return []
    
    def get_events_for_assistant(self):
        """Obtener eventos para el asistente"""
        try:
            if hasattr(self, 'schedule_panel') and hasattr(self.schedule_panel, 'get_events_for_assistant'):
                return self.schedule_panel.get_events_for_assistant()
        except Exception as e:
            print(f"⚠️ Error obteniendo eventos para asistente: {e}")
        return []
    
    def get_reminders_for_assistant(self):
        """Obtener recordatorios para el asistente"""
        try:
            if hasattr(self, 'reminders_panel') and hasattr(self.reminders_panel, 'get_reminders_for_assistant'):
                return self.reminders_panel.get_reminders_for_assistant()
        except Exception as e:
            print(f"⚠️ Error obteniendo recordatorios para asistente: {e}")
        return []
    
    def get_current_panel_name(self):
        """Obtener nombre del panel actual"""
        if hasattr(self, 'tab_widget'):
            current_tab = self.tab_widget.currentWidget()
            if current_tab == self.tasks_panel:
                return "Tareas"
            elif current_tab == self.schedule_panel:
                return "Calendario"
            elif current_tab == self.reminders_panel:
                return "Recordatorios"
        return "Principal"
    
    def show_assistant_response(self, response):
        """Mostrar respuesta del asistente"""
        QMessageBox.information(self, "🤖 Asistente", response)
    
    def show_assistant_error(self, error):
        """Mostrar error del asistente"""
        QMessageBox.warning(self, "Error del Asistente", error)
    
    def setup_ui(self):
        """Configurar la interfaz de usuario - CORREGIDO"""
        # Configurar ventana sin bordes nativos
        self.setWindowFlags(Qt.FramelessWindowHint)
        
        # Widget central
        central_widget = QWidget()
        central_widget.setObjectName("CentralWidget")
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Barra de título personalizada
        self.title_bar = TitleBar(self)
        main_layout.addWidget(self.title_bar)
        
        # Contenido principal (pestañas)
        self.content_widget = QWidget()
        self.content_widget.setObjectName("ContentWidget")
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Widget de pestañas
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("MainTabs")
        self.tab_widget.setTabPosition(QTabWidget.North)
        
        # Crear pestañas
        self.create_tabs()
        
        content_layout.addWidget(self.tab_widget)
        main_layout.addWidget(self.content_widget, 1)  # 1 = factor de expansión
        
        # Barra de estado
        self.setup_status_bar()
        
        # Estilo básico si no hay styles.py
        if not STYLES_AVAILABLE:
            central_widget.setStyleSheet("""
                #CentralWidget {
                    background-color: #202124;
                }
                #TitleBar {
                    background-color: #2b2d30;
                    border-bottom: 1px solid #3c4043;
                }
                #TitleLabel {
                    color: #e8eaed;
                    font-weight: bold;
                }
                QTabWidget::pane {
                    border: 1px solid #3c4043;
                    background-color: #292a2d;
                }
                QTabBar::tab {
                    background-color: #35363a;
                    color: #9aa0a6;
                    padding: 10px 20px;
                }
                QTabBar::tab:selected {
                    background-color: #292a2d;
                    color: #e8eaed;
                }
            """)

    def create_tabs(self):
        """Crear las pestañas principales"""
        print("DEBUG: Creando pestañas...")
        
        # Pestaña 1: Chat
        try:
            if CHAT_PANEL_AVAILABLE:
                self.chat_panel = ChatPanel(user_id=self.user_id)
                self.tab_widget.addTab(self.chat_panel, "💬 Chat")
                print("DEBUG: Pestaña Chat creada")
            else:
                raise ImportError("ChatPanel no disponible")
        except Exception as e:
            print(f"ERROR creando ChatPanel: {e}")
            error_widget = QLabel("Panel de Chat no disponible")
            error_widget.setAlignment(Qt.AlignCenter)
            self.tab_widget.addTab(error_widget, "💬 Chat")
        
        # Pestaña 2: Tareas
        try:
            if TASKS_PANEL_AVAILABLE:
                self.tasks_panel = TasksPanel(user_id=self.user_id)
                self.tab_widget.addTab(self.tasks_panel, "✅ Tareas")
                print("DEBUG: Pestaña Tareas creada")
            else:
                raise ImportError("TasksPanel no disponible")
        except Exception as e:
            print(f"ERROR creando TasksPanel: {e}")
            error_widget = QLabel("Panel de Tareas no disponible")
            error_widget.setAlignment(Qt.AlignCenter)
            self.tab_widget.addTab(error_widget, "✅ Tareas")
        
        # Pestaña 3: Horario
        try:
            if SCHEDULE_PANEL_AVAILABLE:
                self.schedule_panel = SchedulePanel(user_id=self.user_id)
                self.tab_widget.addTab(self.schedule_panel, "📅 Horario")
                print("DEBUG: Pestaña Horario creada")
            else:
                raise ImportError("SchedulePanel no disponible")
        except Exception as e:
            print(f"ERROR creando SchedulePanel: {e}")
            error_widget = QLabel("Panel de Horario no disponible")
            error_widget.setAlignment(Qt.AlignCenter)
            self.tab_widget.addTab(error_widget, "📅 Horario")
        
        # Pestaña 4: Recordatorios
        try:
            if REMINDERS_PANEL_AVAILABLE:
                self.reminders_panel = RemindersPanel(user_id=self.user_id)
                self.tab_widget.addTab(self.reminders_panel, "⏰ Recordatorios")
                print("DEBUG: Pestaña Recordatorios creada")
            else:
                raise ImportError("RemindersPanel no disponible")
        except Exception as e:
            print(f"ERROR creando RemindersPanel: {e}")
            error_widget = QLabel("Panel de Recordatorios no disponible")
            error_widget.setAlignment(Qt.AlignCenter)
            self.tab_widget.addTab(error_widget, "⏰ Recordatorios")
        
        # Conectar señal de cambio de pestaña
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        # Configurar callbacks del asistente después de crear los paneles
        self.setup_assistant_callbacks()
    
    def setup_status_bar(self):
        """Configurar la barra de estado"""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        
        # Estado de conexión
        self.connection_status = QLabel("🟢 Conectado")
        self.connection_status.setStyleSheet("color: #34a853; font-weight: bold;")
        
        # Hora actual
        self.time_label = QLabel()
        self.update_time()
        
        # Temporizador para actualizar hora
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.update_time)
        self.time_timer.start(1000)  # Actualizar cada segundo
        
        # Usuario actual
        user_name = self.user_data.get('name', 'Invitado')
        self.user_label = QLabel(f"👤 {user_name}")
        
        status_bar.addPermanentWidget(self.connection_status)
        status_bar.addPermanentWidget(self.user_label, 1)
        status_bar.addPermanentWidget(self.time_label)
    
    def update_time(self):
        """Actualizar la hora en la barra de estado"""
        from datetime import datetime
        current_time = datetime.now().strftime("%H:%M:%S %d/%m/%Y")
        self.time_label.setText(f"🕒 {current_time}")
    
    def setup_tray_icon(self):
        """Configurar el icono en la bandeja del sistema"""
        try:
            # Intentar crear un icono simple
            self.tray_icon = QSystemTrayIcon(self)
            
            # Crear un icono simple desde un emoji (solución temporal)
            from PySide6.QtGui import QPixmap, QPainter, QColor
            pixmap = QPixmap(32, 32)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            painter.setPen(QColor(255, 255, 255))
            painter.setFont(QFont("Arial", 20))
            painter.drawText(pixmap.rect(), Qt.AlignCenter, "🤖")
            painter.end()
            
            self.tray_icon.setIcon(QIcon(pixmap))
            self.tray_icon.setToolTip("Asistente Personal")
            
            # Crear menú para el tray icon
            tray_menu = QMenu()
            
            show_action = QAction("Mostrar", self)
            show_action.triggered.connect(self.show_normal)
            
            hide_action = QAction("Ocultar", self)
            hide_action.triggered.connect(self.hide)
            
            quit_action = QAction("Salir", self)
            quit_action.triggered.connect(QApplication.quit)
            
            tray_menu.addAction(show_action)
            tray_menu.addAction(hide_action)
            tray_menu.addSeparator()
            tray_menu.addAction(quit_action)
            
            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.show()
            
        except Exception as e:
            print(f"⚠️ Error configurando tray icon: {e}")
    
    def show_normal(self):
        """Mostrar ventana normal desde el tray"""
        self.showNormal()
        self.activateWindow()
        self.raise_()
    
    def apply_styles(self):
        """Aplicar estilos a la ventana"""
        try:
            if STYLES_AVAILABLE:
                self.setStyleSheet(get_stylesheet())
        except Exception as e:
            print(f"⚠️ Error aplicando estilos: {e}")
    
    def on_tab_changed(self, index):
        """Manejador de cambio de pestaña"""
        tab_names = ["Chat", "Tareas", "Horario", "Recordatorios"]
        if 0 <= index < len(tab_names):
            self.statusBar().showMessage(f"Modo: {tab_names[index]}", 2000)
    
    # Funciones para mover ventana sin bordes
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and event.position().y() < 50:
            self.drag_pos = event.globalPosition().toPoint()
            event.accept()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and hasattr(self, 'drag_pos'):
            self.move(self.pos() + event.globalPosition().toPoint() - self.drag_pos)
            self.drag_pos = event.globalPosition().toPoint()
            event.accept()
    
    def closeEvent(self, event):
        """Manejador de cierre de ventana"""
        # Detener el asistente global si existe
        if hasattr(self, 'assistant') and self.assistant:
            self.assistant.stop()
        
        reply = QMessageBox.question(
            self, 'Salir',
            "¿Estás seguro de que quieres salir?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Guardar estado de la aplicación
            self.save_state()
            event.accept()
        else:
            event.ignore()
    
    def save_state(self):
        """Guardar estado de la aplicación antes de cerrar"""
        try:
            # Guardar geometría de ventana
            from PySide6.QtCore import QSettings
            settings = QSettings("AsistentePersonal", "MainWindow")
            settings.setValue("geometry", self.saveGeometry())
            settings.setValue("windowState", self.saveState())
            if hasattr(self, 'tab_widget'):
                settings.setValue("currentTab", self.tab_widget.currentIndex())
        except Exception as e:
            print(f"⚠️ Error guardando estado: {e}")

if __name__ == "__main__":
    # Para pruebas directas
    import sys
    app = QApplication(sys.argv)
    
    # Establecer paleta de colores oscura por defecto
    app.setStyle("Fusion")
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.WindowText, Qt.white)
    dark_palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
    dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.white)
    dark_palette.setColor(QPalette.ColorRole.ToolTipText, Qt.white)
    dark_palette.setColor(QPalette.ColorRole.Text, Qt.white)
    dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.ButtonText, Qt.white)
    dark_palette.setColor(QPalette.ColorRole.BrightText, Qt.red)
    dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.ColorRole.HighlightedText, Qt.black)
    app.setPalette(dark_palette)
    
    # Iniciar ventana principal
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())