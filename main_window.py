"""
Ventana principal del Asistente Personal con PySide6.
Incluye 4 pestañas: Chat, Tareas, Horario, Recordatorios.
"""
from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, 
    QHBoxLayout, QLabel, QFrame, QPushButton, QSystemTrayIcon,
    QMenu, QApplication, QStatusBar, QToolBar, QMessageBox
)
from PySide6.QtCore import Qt, QSize, Signal, QTimer
from PySide6.QtGui import QIcon, QAction, QFont, QPalette, QColor
import os
import sys

from global_assistant import get_global_assistant

# Añadir directorio actual al path para imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

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
    from chat_panel import ChatPanel
    from tasks_panel import TasksPanel
    from schedule_panel import SchedulePanel
    from reminders_panel import RemindersPanel
    PANELS_AVAILABLE = True
    
except ImportError as e:
    print(f"❌ Error importando módulos: {e}")
    PANELS_AVAILABLE = False
    
    # Crear placeholders si fallan los imports
    class ChatPanel(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            label = QLabel("Panel de Chat (Error de carga)")
            label.setAlignment(Qt.AlignCenter)
            layout = QVBoxLayout()
            layout.addWidget(label)
            self.setLayout(layout)
    
    TasksPanel = SchedulePanel = RemindersPanel = ChatPanel

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
    """Ventana principal de la aplicación"""
    
    def __init__(self, user_data=None):
        super().__init__()
        self.user_data = user_data or {}
        print(f"🔧 Creando pestañas para: {self.user_data.get('name', 'Invitado')}")
        
        self.global_assistant = get_global_assistant()
        
        # Configurar callbacks para que el asistente acceda a los datos
        self.setup_assistant_callbacks()
        
        # Conectar señales del asistente
        self.setup_assistant_connections()
        
        self.setup_window()
        self.setup_ui()
        self.setup_tray_icon()
        self.apply_styles()
        print("✅ Asistente global integrado en MainWindow")

    def setup_assistant_callbacks(self):
        """Configurar callbacks para que el asistente acceda a los datos"""
        callbacks = {
            'get_current_panel': self.get_current_panel,
            'get_tasks': self.get_current_tasks,
            'get_events': self.get_current_events,
            'get_reminders': self.get_current_reminders
        }
        
        self.global_assistant.register_callbacks(callbacks)

    def setup_assistant_connections(self):
        """Conectar señales del asistente global"""
        self.global_assistant.command_received.connect(self.on_assistant_command)
        self.global_assistant.response_ready.connect(self.on_assistant_response)
        self.global_assistant.error_occurred.connect(self.on_assistant_error)
    def get_current_panel(self):
        """Obtener el panel actual"""
        tab_names = ["Chat", "Tareas", "Horario", "Recordatorios"]
        current_index = self.tab_widget.currentIndex()
        if 0 <= current_index < len(tab_names):
            return tab_names[current_index]
        return "Desconocido"
    
    def get_current_tasks(self):
        """Obtener tareas del panel de tareas"""
        try:
            if hasattr(self, 'tasks_panel'):
                return self.tasks_panel.tasks
        except Exception as e:
            print(f"⚠️ Error obteniendo tareas: {e}")
        return []
    
    def get_current_events(self):
        """Obtener eventos del panel de horario"""
        try:
            if hasattr(self, 'schedule_panel'):
                return self.schedule_panel.events
        except Exception as e:
            print(f"⚠️ Error obteniendo eventos: {e}")
        return []
    
    def get_current_reminders(self):
        """Obtener recordatorios del panel de recordatorios"""
        try:
            if hasattr(self, 'reminders_panel'):
                return self.reminders_panel.reminders
        except Exception as e:
            print(f"⚠️ Error obteniendo recordatorios: {e}")
        return []
    
    def on_assistant_command(self, command):
        """Manejar comando recibido del asistente"""
        print(f"🎤 Comando recibido: {command}")
        # Mostrar notificación en la barra de estado
        self.statusBar().showMessage(f"🎤 {command[:50]}...", 3000)
    
    def on_assistant_response(self, response):
        """Manejar respuesta del asistente"""
        print(f"🤖 Respuesta: {response}")
        # Mostrar notificación en la barra de estado
        self.statusBar().showMessage(f"🤖 {response[:50]}...", 5000)
        
        # Si estamos en el panel de chat, también mostrar ahí
        if hasattr(self, 'chat_panel'):
            current_tab = self.tab_widget.currentIndex()
            if current_tab == 0:  # Panel de chat
                self.chat_panel.add_message("Asistente", response)
    
    def on_assistant_error(self, error):
        """Manejar error del asistente"""
        print(f"❌ Error del asistente: {error}")
        self.statusBar().showMessage(f"❌ {error}", 5000)
    
    # Añadir este método a la clase MainWindow
    def closeEvent(self, event):
        """Manejar cierre de ventana - también detener el asistente"""
        # Detener el asistente global
        if hasattr(self, 'global_assistant'):
            self.global_assistant.stop()
        
        # Resto del código de cierre...
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
    def setup_window(self):
        """Configuración básica de la ventana"""
        self.setWindowTitle("Asistente Personal")
        self.setMinimumSize(1100, 750)
        
        # Para ventana sin bordes nativos
        self.setWindowFlags(Qt.FramelessWindowHint)
        
        # Para permitir sombras y efectos
        self.setAttribute(Qt.WA_TranslucentBackground)
        
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

    def create_tabs(self):
        """Crear las pestañas principales"""
        print("DEBUG: Creando pestañas...")
        
        # Pestaña 1: Chat
        try:
            # NO pasar gemini_manager si ChatPanel no lo acepta
            self.chat_panel = ChatPanel()
            self.tab_widget.addTab(self.chat_panel, "💬 Chat")
            print("DEBUG: Pestaña Chat creada")
        except Exception as e:
            print(f"ERROR creando ChatPanel: {e}")
            error_widget = QLabel("Error cargando Chat")
            error_widget.setAlignment(Qt.AlignCenter)
            error_widget.setStyleSheet("color: red; font-size: 20px;")
            self.tab_widget.addTab(error_widget, "💬 Chat")
        
        # Pestaña 2: Tareas
        try:
            # NO pasar user_data si TasksPanel no lo acepta
            self.tasks_panel = TasksPanel()
            self.tab_widget.addTab(self.tasks_panel, "✅ Tareas")
            print("DEBUG: Pestaña Tareas creada")
        except Exception as e:
            print(f"ERROR creando TasksPanel: {e}")
            error_widget = QLabel("Error cargando Tareas")
            error_widget.setAlignment(Qt.AlignCenter)
            error_widget.setStyleSheet("color: red; font-size: 20px;")
            self.tab_widget.addTab(error_widget, "✅ Tareas")
        
        # Pestaña 3: Horario
        try:
            # NO pasar user_data si SchedulePanel no lo acepta
            self.schedule_panel = SchedulePanel()
            self.tab_widget.addTab(self.schedule_panel, "📅 Horario")
            print("DEBUG: Pestaña Horario creada")
        except Exception as e:
            print(f"ERROR creando SchedulePanel: {e}")
            error_widget = QLabel("Error cargando Horario")
            error_widget.setAlignment(Qt.AlignCenter)
            error_widget.setStyleSheet("color: red; font-size: 20px;")
            self.tab_widget.addTab(error_widget, "📅 Horario")
        
        # Pestaña 4: Recordatorios
        try:
            # NO pasar user_data si RemindersPanel no lo acepta
            self.reminders_panel = RemindersPanel()
            self.tab_widget.addTab(self.reminders_panel, "⏰ Recordatorios")
            print("DEBUG: Pestaña Recordatorios creada")
        except Exception as e:
            print(f"ERROR creando RemindersPanel: {e}")
            error_widget = QLabel("Error cargando Recordatorios")
            error_widget.setAlignment(Qt.AlignCenter)
            error_widget.setStyleSheet("color: red; font-size: 20px;")
            self.tab_widget.addTab(error_widget, "⏰ Recordatorios")
        
        # Conectar señal de cambio de pestaña
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
    
    def create_tab_icon(self, emoji):
        """Crear icono de pestaña con emoji"""
        label = QLabel(emoji)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 16px;")
        return label
    
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
            self.tray_icon = QSystemTrayIcon(self)
            
            # Intentar crear un icono
            try:
                # Usar un emoji como texto para el icono (solución temporal)
                self.tray_icon.setToolTip("Asistente Personal")
            except:
                pass
            
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
            else:
                # Estilos básicos si no hay styles.py
                basic_styles = """
                /* ===== VENTANA PRINCIPAL ===== */
                QMainWindow {
                    background-color: #202124;
                }
                
                /* ===== BARRA DE TÍTULO PERSONALIZADA ===== */
                #TitleBar {
                    background-color: #2b2d30;
                    border-bottom: 1px solid #3c4043;
                }
                
                #TitleLabel {
                    color: #e8eaed;
                }
                
                /* ===== PESTAÑAS ===== */
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
                """
                self.setStyleSheet(basic_styles)
                
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
            self.move(self.pos() + event.globalPosition().toPoint() - self  .drag_pos)
            self.drag_pos = event.globalPosition().toPoint()
            event.accept()
    
    def closeEvent(self, event):
        """Manejador de cierre de ventana"""
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
        # Aquí puedes guardar configuraciones, tamaño de ventana, etc.
        pass

if __name__ == "__main__":
    # Para pruebas directas
    import sys
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())