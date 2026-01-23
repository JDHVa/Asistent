from PySide6.QtWidgets import (
    QWidget, QMainWindow, QDialog, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QLineEdit, QTextEdit, QPlainTextEdit, QComboBox,
    QCheckBox, QRadioButton, QGroupBox, QTabWidget,
    QListWidget, QListWidgetItem, QTreeWidget, QTreeWidgetItem,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QScrollArea, QScrollBar, QSplitter, QFrame,
    QProgressBar, QSlider, QSpinBox, QDoubleSpinBox,
    QDateEdit, QTimeEdit, QDateTimeEdit, QCalendarWidget,
    QMenu, QMenuBar, QToolBar, QStatusBar, QMessageBox,
    QInputDialog, QFileDialog, QColorDialog, QFontDialog,
    QGraphicsView, QGraphicsScene, QGraphicsItem
)
from PySide6.QtCore import (
    Qt, QSize, QPoint, QRect, QUrl, QDir, QFile,
    QTimer, QDateTime, QDate, QTime, QEvent,
    Signal, Slot, Property, QObject, QThread,
    QSettings, QRegularExpression, QModelIndex
)
from PySide6.QtGui import (
    QIcon, QPixmap, QImage, QPainter, QBrush, QPen,
    QFont, QColor, QPalette, QCursor, QKeySequence,
    QAction, QActionGroup, QStandardItem, QStandardItemModel,
    QLinearGradient, QRadialGradient, QConicalGradient
)
from export_data import export_tasks, export_events, export_reminders
import json
from datetime import datetime, timedelta
from database_manager import get_database


class ReminderWidget(QWidget):
    """Widget para mostrar un recordatorio individual"""
    
    reminder_updated = Signal(dict)
    reminder_deleted = Signal(int)
    
    def __init__(self, reminder_data, parent=None):
        super().__init__(parent)
        self.reminder_data = reminder_data
        self.setup_ui()
        
    def setup_ui(self):
        self.setFixedHeight(80)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)
        
        # Checkbox de activo
        self.active_cb = QCheckBox()
        self.active_cb.setChecked(self.reminder_data.get('active', True))
        self.active_cb.stateChanged.connect(self.toggle_active)
        
        # Información del recordatorio
        info_layout = QVBoxLayout()
        info_layout.setSpacing(3)
        
        # Título
        title_label = QLabel(self.reminder_data.get('title', 'Sin título'))
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_label.setFont(title_font)
        
        # Detalles
        details_layout = QHBoxLayout()
        
        # Fecha y hora
        date_time = self.reminder_data.get('date_time', '')
        time_label = QLabel(f"⏰ {date_time}")
        time_label.setStyleSheet("color: #4285f4; font-size: 10px;")
        
        # Repetición
        recurrence = self.reminder_data.get('recurrence', 'ninguna')
        if recurrence != 'ninguna':
            recur_label = QLabel(f"🔁 {recurrence}")
            recur_label.setStyleSheet("color: #34a853; font-size: 10px;")
            details_layout.addWidget(recur_label)
        
        # Prioridad
        priority = self.reminder_data.get('priority', 'medium')
        priority_colors = {
            'high': ('🔥 High', '#ea4335'),
            'medium': ('⚠️ Medium', '#fbbc04'),
            'low': ('📌 Low', '#34a853')
        }
        priority_text, priority_color = priority_colors.get(priority, ('⚠️ Medium', '#fbbc04'))
        priority_label = QLabel(priority_text)
        priority_label.setStyleSheet(f"""
            QLabel {{
                color: {priority_color};
                font-size: 10px;
                font-weight: bold;
                padding: 2px 8px;
                background-color: {priority_color}20;
                border-radius: 10px;
            }}
        """)
        
        details_layout.addWidget(time_label)
        details_layout.addStretch()
        details_layout.addWidget(priority_label)
        
        # Descripción
        description = self.reminder_data.get('description', '')
        if description:
            desc_label = QLabel(description)
            desc_label.setStyleSheet("color: #9aa0a6; font-size: 11px;")
            desc_label.setWordWrap(True)
            info_layout.addWidget(desc_label)
        
        info_layout.addWidget(title_label)
        info_layout.addLayout(details_layout)
        
        # Botones de acción
        action_layout = QVBoxLayout()
        action_layout.setSpacing(4)
        
        snooze_btn = QPushButton("⏸️")
        snooze_btn.setFixedSize(28, 28)
        snooze_btn.setToolTip("Posponer 5 minutos")
        snooze_btn.clicked.connect(self.snooze_reminder)
        
        edit_btn = QPushButton("✏️")
        edit_btn.setFixedSize(28, 28)
        edit_btn.setToolTip("Editar recordatorio")
        edit_btn.clicked.connect(self.edit_reminder)
        
        delete_btn = QPushButton("🗑️")
        delete_btn.setFixedSize(28, 28)
        delete_btn.setToolTip("Eliminar recordatorio")
        delete_btn.clicked.connect(self.delete_reminder)
        
        action_layout.addWidget(snooze_btn)
        action_layout.addWidget(edit_btn)
        action_layout.addWidget(delete_btn)
        
        layout.addWidget(self.active_cb)
        layout.addLayout(info_layout, 1)
        layout.addLayout(action_layout)
        
        # Estilo inicial
        self.update_style()
        
        # Estilo de botones
        btn_style = """
            QPushButton {
                background-color: #2d2e31;
                border: 1px solid #3c4043;
                border-radius: 4px;
                color: #9aa0a6;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #35363a;
                border-color: #4285f4;
            }
        """
        snooze_btn.setStyleSheet(btn_style)
        edit_btn.setStyleSheet(btn_style)
        delete_btn.setStyleSheet(btn_style.replace("#4285f4", "#ea4335"))
    
    def update_style(self):
        """Actualizar estilo según estado"""
        if self.reminder_data.get('active', True):
            self.setStyleSheet("""
                ReminderWidget {
                    background-color: #292a2d;
                    border: 2px solid #4285f4;
                    border-radius: 8px;
                }
                ReminderWidget:hover {
                    background-color: #2d2e31;
                    border-color: #3367d6;
                }
            """)
        else:
            self.setStyleSheet("""
                ReminderWidget {
                    background-color: #2d2e31;
                    border: 1px solid #3c4043;
                    border-radius: 8px;
                    opacity: 0.6;
                }
            """)
    
    def toggle_active(self, state):
        """Cambiar estado activo"""
        self.reminder_data['active'] = (state == Qt.Checked)
        self.update_style()
        self.reminder_updated.emit(self.reminder_data)
    
    def snooze_reminder(self):
        """Posponer recordatorio"""
        QMessageBox.information(self, "Posponer", 
                              f"Recordatorio '{self.reminder_data.get('title')}' pospuesto 5 minutos.")
    
    def edit_reminder(self):
        """Editar recordatorio"""
        QMessageBox.information(self, "Editar", 
                              f"Editar recordatorio: {self.reminder_data.get('title')}")
    
    def delete_reminder(self):
        """Eliminar recordatorio"""
        reply = QMessageBox.question(
            self, "Eliminar Recordatorio",
            f"¿Eliminar recordatorio '{self.reminder_data.get('title')}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.reminder_deleted.emit(self.reminder_data.get('id'))

class RemindersPanel(QWidget):
    """Panel completo de recordatorios con notificaciones"""
    
class RemindersPanel(QWidget):
    """Panel completo de recordatorios con notificaciones"""
    
    def __init__(self, user_id=None, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.db = get_database()
        
        # Establecer usuario actual si se proporciona
        if user_id:
            self.db.set_current_user(user_id)
        
        self.reminders = []
        self.next_id = 1
        
        self.setup_ui()
        self.load_reminders()  # Cargar desde base de datos
        
        # Timer para verificar recordatorios
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self.check_reminders)
        self.check_timer.start(60000)  # Verificar cada minuto
        
    def setup_ui(self):
        """Configurar interfaz completa"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # Encabezado
        header = self.create_header()
        main_layout.addWidget(header)
        
        # Panel principal con splitter
        main_splitter = QSplitter(Qt.Horizontal)
        
        # Panel izquierdo: Formulario y configuración
        left_panel = self.create_left_panel()
        
        # Panel derecho: Lista de recordatorios
        right_panel = self.create_right_panel()
        
        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(right_panel)
        main_splitter.setSizes([350, 650])
        
        main_layout.addWidget(main_splitter, 1)

        
    def create_header(self):
        """Crear encabezado"""
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background-color: #2d2e31;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        
        layout = QHBoxLayout(header)
        
        # Título
        title = QLabel("⏰ Recordatorios Inteligentes")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #e8eaed;")
        
        # Estado del sistema
        status_layout = QHBoxLayout()
        status_layout.setSpacing(10)
        
        self.system_status = QLabel("🟢 Sistema activo")
        self.system_status.setStyleSheet("""
            QLabel {
                color: #34a853;
                background-color: #34a85320;
                padding: 5px 15px;
                border-radius: 15px;
                font-weight: bold;
            }
        """)
        
        # Próximo recordatorio
        self.next_reminder = QLabel("⏳ Próximo: --:--")
        self.next_reminder.setStyleSheet("""
            QLabel {
                color: #fbbc04;
                background-color: #fbbc0420;
                padding: 5px 15px;
                border-radius: 15px;
            }
        """)
        
        status_layout.addWidget(self.system_status)
        status_layout.addWidget(self.next_reminder)
        
        # Botón rápido
        quick_btn = QPushButton("⏰ Crear Rápido")
        quick_btn.clicked.connect(self.quick_create_reminder)
        
        layout.addWidget(title)
        layout.addLayout(status_layout, 1)
        layout.addWidget(quick_btn)
                # Botón IA
        ai_btn = QPushButton("🤖 IA")
        ai_btn.clicked.connect(self.analyze_reminders_with_ai)
        layout.addWidget(ai_btn)
        
        
        return header
    
    def create_left_panel(self):
        """Crear panel izquierdo"""
        panel = QWidget()
        
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)
        
        # Formulario de nuevo recordatorio
        form_group = QGroupBox("➕ Nuevo Recordatorio")
        form_group.setStyleSheet("""
            QGroupBox {
                color: #9aa0a6;
                border: 1px solid #3c4043;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                font-weight: bold;
            }
        """)
        
        form_layout = QVBoxLayout(form_group)
        form_layout.setSpacing(10)
        
        # Campos del formulario
        self.reminder_title = QLineEdit()
        self.reminder_title.setPlaceholderText("Título del recordatorio *")
        
        self.reminder_desc = QTextEdit()
        self.reminder_desc.setPlaceholderText("Descripción...")
        self.reminder_desc.setMaximumHeight(60)
        
        # Fecha y hora
        datetime_layout = QHBoxLayout()
        
        date_col = QVBoxLayout()
        date_col.addWidget(QLabel("Fecha:"))
        self.reminder_date = QDateEdit()
        self.reminder_date.setDate(QDate.currentDate())
        self.reminder_date.setCalendarPopup(True)
        date_col.addWidget(self.reminder_date)
        
        time_col = QVBoxLayout()
        time_col.addWidget(QLabel("Hora:"))
        self.reminder_time = QTimeEdit()
        self.reminder_time.setTime(QTime.currentTime().addSecs(1800))  # 30 minutos después
        time_col.addWidget(self.reminder_time)
        
        datetime_layout.addLayout(date_col)
        datetime_layout.addLayout(time_col)
        
        # Configuración
        config_layout = QHBoxLayout()
        
        # Prioridad
        priority_col = QVBoxLayout()
        priority_col.addWidget(QLabel("Priority:"))
        self.reminder_priority = QComboBox()
        self.reminder_priority.addItems(["High", "Medium", "Low"])
        priority_col.addWidget(self.reminder_priority)
        
        # Repetición
        recur_col = QVBoxLayout()
        recur_col.addWidget(QLabel("Repetir:"))
        self.reminder_recurrence = QComboBox()
        self.reminder_recurrence.addItems(["No repetir", "Diario", "Semanal", "Mensual", "Anual"])
        recur_col.addWidget(self.reminder_recurrence)
        
        config_layout.addLayout(priority_col)
        config_layout.addLayout(recur_col)
        
        # Opciones adicionales
        options_layout = QVBoxLayout()
        
        self.notify_sound = QCheckBox("Reproducir sonido")
        self.notify_sound.setChecked(True)
        
        self.notify_popup = QCheckBox("Mostrar notificación")
        self.notify_popup.setChecked(True)
        
        self.auto_snooze = QCheckBox("Posponer automáticamente")
        self.auto_snooze.setChecked(False)
        
        options_layout.addWidget(self.notify_sound)
        options_layout.addWidget(self.notify_popup)
        options_layout.addWidget(self.auto_snooze)
        
        # Botón agregar
        add_btn = QPushButton("➕ Agregar Recordatorio")
        add_btn.clicked.connect(self.add_reminder)
        
        form_layout.addWidget(self.reminder_title)
        form_layout.addWidget(self.reminder_desc)
        form_layout.addLayout(datetime_layout)
        form_layout.addLayout(config_layout)
        form_layout.addLayout(options_layout)
        form_layout.addWidget(add_btn)
        
        # Configuración del sistema
        config_group = QGroupBox("⚙️ Configuración del Sistema")
        config_group.setStyleSheet(form_group.styleSheet())
        
        config_system_layout = QVBoxLayout(config_group)
        
        # Intervalo de verificación
        check_layout = QHBoxLayout()
        check_layout.addWidget(QLabel("Verificar cada:"))
        
        self.check_interval = QSpinBox()
        self.check_interval.setRange(1, 60)
        self.check_interval.setValue(5)
        self.check_interval.setSuffix(" min")
        
        check_layout.addWidget(self.check_interval)
        check_layout.addStretch()
        
        # Volumen
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("Volumen:"))
        
        self.volume_slider = QProgressBar()
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(80)
        self.volume_slider.setTextVisible(False)
        
        volume_layout.addWidget(self.volume_slider)
        
        config_system_layout.addLayout(check_layout)
        config_system_layout.addLayout(volume_layout)
        config_system_layout.addStretch()
        
        layout.addWidget(form_group)
        layout.addWidget(config_group, 1)
        
        # Estilos de inputs
        input_style = """
            QLineEdit, QTextEdit, QComboBox, QDateEdit, QTimeEdit, QSpinBox {
                background-color: #202124;
                color: #e8eaed;
                border: 1px solid #3c4043;
                border-radius: 6px;
                padding: 8px;
                font-size: 14px;
            }
            QProgressBar {
                background-color: #202124;
                border: 1px solid #3c4043;
                border-radius: 3px;
                height: 8px;
            }
            QProgressBar::chunk {
                background-color: #4285f4;
                border-radius: 3px;
            }
        """
        
        inputs = [self.reminder_title, self.reminder_desc, self.reminder_date,
                 self.reminder_time, self.reminder_priority, self.reminder_recurrence,
                 self.check_interval]
        for inp in inputs:
            inp.setStyleSheet(input_style)
        
        return panel
    
    def create_right_panel(self):
        """Crear panel derecho"""
        panel = QWidget()
        
        layout = QVBoxLayout(panel)
        layout.setSpacing(10)
        
        # Pestañas para diferentes vistas
        self.view_tabs = QTabWidget()
        self.view_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #3c4043;
                background-color: #202124;
            }
            QTabBar::tab {
                background-color: #35363a;
                color: #9aa0a6;
                padding: 10px 20px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: #292a2d;
                color: #e8eaed;
                border-bottom: 2px solid #4285f4;
            }
        """)
        
        # Vista activos
        active_view = self.create_active_view()
        
        # Vista programados
        scheduled_view = self.create_scheduled_view()
        
        # Vista completados
        completed_view = self.create_completed_view()
        
        self.view_tabs.addTab(active_view, "🔔 Activos")
        self.view_tabs.addTab(scheduled_view, "📅 Programados")
        self.view_tabs.addTab(completed_view, "✅ Completados")
        
        layout.addWidget(self.view_tabs, 1)
        
        # Barra de herramientas
        toolbar = QFrame()
        toolbar.setStyleSheet("""
            QFrame {
                background-color: #292a2d;
                border: 1px solid #3c4043;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        
        toolbar_layout = QHBoxLayout(toolbar)
        
        # Botones de acción masiva
        action_btns = [
            ("⏸️ Posponer Todos", self.snooze_all),
            ("✅ Marcar Todos", self.mark_all_completed),
            ("🗑️ Limpiar Completados", self.clear_completed),
            ("📤 Exportar", self.export_reminders)
        ]
        
        for btn_text, callback in action_btns:
            btn = QPushButton(btn_text)
            btn.clicked.connect(callback)
            toolbar_layout.addWidget(btn)
        
        toolbar_layout.addStretch()
        
        # Estadísticas
        self.stats_label = QLabel("📊 0 activos • 0 programados • 0 completados")
        self.stats_label.setStyleSheet("color: #9aa0a6;")
        
        toolbar_layout.addWidget(self.stats_label)
        
        layout.addWidget(toolbar)
        
        return panel
    def analyze_reminders_with_ai(self):
        """Analizar recordatorios con IA"""
        from assistant_managers import gemini_manager, voice_manager
        
        if not gemini_manager.model:
            QMessageBox.warning(self, "IA no disponible", 
                              "Gemini AI no está configurado.")
            return
        
        # Obtener recordatorios activos
        active_reminders = [r for r in self.reminders if r['active'] and not r['completed']]
        
        if not active_reminders:
            QMessageBox.information(self, "Sin recordatorios", 
                                  "No tienes recordatorios activos.")
            return
        
        # Formatear recordatorios
        reminders_text = "Recordatorios activos:\n\n"
        for i, reminder in enumerate(active_reminders[:5], 1):
            priority_icon = "🔥" if reminder['priority'] == 'alta' else "⚠️" if reminder['priority'] == 'media' else "📌"
            reminders_text += f"{i}. {priority_icon} {reminder['title']} - {reminder['date_time']}\n"
        
        prompt = f"""Analiza estos recordatorios y da recomendaciones:

        {reminders_text}

        Como asistente personal, proporciona:
        1. Recordatorios importantes
        2. Sugerencias para no olvidar nada
        3. Consejos para gestionar el tiempo
        4. Un mensaje motivacional

        Responde en español."""
                
        QMessageBox.information(self, "Analizando", "🤖 IA está analizando tus recordatorios...")
        analysis = gemini_manager.send_message(prompt, "Eres un asistente personal organizado.")
        
        # Mostrar resultado
        QMessageBox.information(self, "Análisis de IA", analysis)
        
        # Hablar resultado
        if voice_manager.available:
            voice_manager.speak(analysis)

    def create_active_view(self):
        """Crear vista de recordatorios activos"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Lista de recordatorios activos
        self.active_list = QListWidget()
        self.active_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
            }
            QListWidget::item {
                margin: 5px 0px;
            }
        """)
        self.active_list.setSpacing(5)
        
        layout.addWidget(self.active_list, 1)
        
        # Info
        info = QLabel("🔔 Recordatorios activos que se mostrarán según programación")
        info.setStyleSheet("color: #9aa0a6; font-size: 12px; padding: 10px;")
        info.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(info)
        
        return widget
    
    def create_scheduled_view(self):
        """Crear vista de recordatorios programados"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Lista de todos los recordatorios
        self.all_reminders_list = QListWidget()
        self.all_reminders_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
            }
            QListWidget::item {
                margin: 5px 0px;
            }
        """)
        self.all_reminders_list.setSpacing(5)
        
        layout.addWidget(self.all_reminders_list, 1)
        
        # Filtros
        filter_frame = QFrame()
        filter_layout = QHBoxLayout(filter_frame)
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Todos", "Hoy", "Mañana", "Esta semana", "Próximos", "Pasados"])
        self.filter_combo.currentTextChanged.connect(self.filter_reminders)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar recordatorios...")
        self.search_input.textChanged.connect(self.filter_reminders)
        
        filter_layout.addWidget(QLabel("Filtrar:"))
        filter_layout.addWidget(self.filter_combo)
        filter_layout.addWidget(self.search_input, 1)
        
        layout.addWidget(filter_frame)
        
        return widget
    
    def create_completed_view(self):
        """Crear vista de recordatorios completados"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Lista de completados
        self.completed_list = QListWidget()
        self.completed_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                color: #9aa0a6;
            }
            QListWidget::item {
                margin: 5px 0px;
                text-decoration: line-through;
            }
        """)
        
        layout.addWidget(self.completed_list, 1)
        
        # Info
        info = QLabel("✅ Recordatorios que ya han sido atendidos o marcados como completados")
        info.setStyleSheet("color: #9aa0a6; font-size: 12px; padding: 10px;")
        info.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(info)
        
        return widget
    
    def add_reminder(self):
        """Agregar nuevo recordatorio"""
        title = self.reminder_title.text().strip()
        if not title:
            QMessageBox.warning(self, "Advertencia", "Ingresa un título para el recordatorio.")
            return
        
        date_time = f"{self.reminder_date.date().toString('dd/MM/yyyy')} {self.reminder_time.time().toString('hh:mm')}"
        
        # Convertir prioridad a español para BD
        priority_text = self.reminder_priority.currentText().lower()
        
        # Mapeo inglés → español

        reminder_data = {
            'title': title,
            'description': self.reminder_desc.toPlainText().strip(),
            'date_time': date_time,
            'date': self.reminder_date.date().toString("yyyy-MM-dd"),
            'time': self.reminder_time.time().toString("hh:mm"),
            'recurrence': self.reminder_recurrence.currentText(),
            'active': True,
            'completed': False,
            'sound': self.notify_sound.isChecked(),
            'popup': self.notify_popup.isChecked(),
            'auto_snooze': self.auto_snooze.isChecked(),
            'created_at': QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss"),
        }
        
        # ✅ GUARDAR EN BASE DE DATOS
        if self.user_id and hasattr(self, 'db') and self.db:
            try:
                reminder_id = self.db.save_reminder(reminder_data)
                if reminder_id > 0:
                    reminder_data['id'] = reminder_id
                    self.display_new_reminder(reminder_data)
                    
                    # Limpiar formulario
                    self.reminder_title.clear()
                    self.reminder_desc.clear()
                    self.reminder_date.setDate(QDate.currentDate())
                    self.reminder_time.setTime(QTime.currentTime().addSecs(1800))
                    
                    QMessageBox.information(self, "Éxito", "Recordatorio agregado correctamente.")
                else:
                    QMessageBox.warning(self, "Error", "No se pudo guardar el recordatorio.")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"No se pudo guardar el recordatorio: {str(e)}")
        else:
            # Modo sin base de datos
            reminder_data['id'] = self.next_id
            self.next_id += 1
            self.display_new_reminder(reminder_data)
            
            # Limpiar formulario
            self.reminder_title.clear()
            self.reminder_desc.clear()
            self.reminder_date.setDate(QDate.currentDate())
            self.reminder_time.setTime(QTime.currentTime().addSecs(1800))
            
            QMessageBox.information(self, "Éxito", "Recordatorio agregado correctamente.")
        
    def quick_create_reminder(self):
        """Crear recordatorio rápido"""
        title, ok = QInputDialog.getText(self, "Recordatorio Rápido", 
                                    "¿Qué quieres recordar?")
        if ok and title:
            # Ya está en español, esto está bien
            reminder_data = {
                'id': self.next_id,
                'title': title,
                'description': '',
                'date_time': QDateTime.currentDateTime().addSecs(300).toString("dd/MM/yyyy hh:mm"),
                'date': QDate.currentDate().toString("yyyy-MM-dd"),
                'time': QTime.currentTime().addSecs(300).toString("hh:mm"),
                'priority': 'media',  # ← En español
                'recurrence': 'No repetir',
                'active': True,
                'completed': False,
                'sound': True,
                'popup': True,
                'auto_snooze': False,
                'created_at': QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss"),
                'priority_display': 'medium'  # Para mostrar en inglés
            }
            
            reminder_widget = ReminderWidget(reminder_data)
            reminder_widget.reminder_updated.connect(self.update_reminder)
            reminder_widget.reminder_deleted.connect(self.delete_reminder)
            
            # Agregar a listas
            list_item = QListWidgetItem()
            list_item.setSizeHint(QSize(0, 80))
            self.all_reminders_list.addItem(list_item)
            self.all_reminders_list.setItemWidget(list_item, reminder_widget)
            
            active_item = QListWidgetItem()
            active_item.setSizeHint(QSize(0, 80))
            self.active_list.addItem(active_item)
            self.active_list.setItemWidget(active_item, reminder_widget)
            
            # Guardar
            reminder_data['widget'] = reminder_widget
            reminder_data['all_list_item'] = list_item
            reminder_data['active_list_item'] = active_item
            self.reminders.append(reminder_data)
            self.next_id += 1
            
            self.update_stats()
            self.update_next_reminder()
    
    def update_reminder(self, reminder_data):
        """Actualizar recordatorio"""
        # ✅ ACTUALIZAR EN BASE DE DATOS
        if self.user_id and hasattr(self, 'db') and self.db:
            try:
                success = self.db.save_reminder(reminder_data)
                if not success:
                    print(f"❌ No se pudo actualizar el recordatorio en BD")
            except Exception as e:
                print(f"❌ Error actualizando recordatorio en BD: {e}")
        
        # Actualizar localmente
        for i, reminder in enumerate(self.reminders):
            if reminder.get('id') == reminder_data.get('id'):
                self.reminders[i] = reminder_data
                break
        
        self.update_stats()
        self.update_next_reminder()
    
    def delete_reminder(self, reminder_id):
        """Eliminar recordatorio"""
        # ✅ ELIMINAR DE BASE DE DATOS
        if self.user_id and hasattr(self, 'db') and self.db:
            try:
                success = self.db.delete_reminder(reminder_id)
                if not success:
                    print(f"❌ No se pudo eliminar el recordatorio de BD")
            except Exception as e:
                print(f"❌ Error eliminando recordatorio de BD: {e}")
        
        # Eliminar localmente
        for i, reminder in enumerate(self.reminders):
            if reminder.get('id') == reminder_id:
                # Remover de listas
                if reminder.get('all_list_item'):
                    row = self.all_reminders_list.row(reminder['all_list_item'])
                    self.all_reminders_list.takeItem(row)
                
                if reminder.get('active_list_item'):
                    row = self.active_list.row(reminder['active_list_item'])
                    self.active_list.takeItem(row)
                
                # Eliminar de lista
                del self.reminders[i]
                break
        
        self.update_stats()
        self.update_next_reminder()
    
    def update_stats(self):
        """Actualizar estadísticas"""
        total = len(self.reminders)
        active = sum(1 for r in self.reminders if r['active'] and not r['completed'])
        completed = sum(1 for r in self.reminders if r['completed'])
        
        self.stats_label.setText(f"📊 {active} activos • {total} programados • {completed} completados")
        
        # Actualizar contadores en pestañas
        self.view_tabs.setTabText(0, f"🔔 Activos ({active})")
        self.view_tabs.setTabText(2, f"✅ Completados ({completed})")
    
    def update_next_reminder(self):
        """Actualizar información del próximo recordatorio"""
        # Encontrar el próximo recordatorio activo
        next_reminder = None
        current_time = QDateTime.currentDateTime()
        
        for reminder in self.reminders:
            if reminder['active'] and not reminder['completed']:
                reminder_time = QDateTime(
                    QDate.fromString(reminder['date'], "yyyy-MM-dd"),
                    QTime.fromString(reminder['time'], "hh:mm")
                )
                
                if reminder_time > current_time:
                    if next_reminder is None or reminder_time < next_reminder['datetime']:
                        next_reminder = {'datetime': reminder_time, 'title': reminder['title']}
        
        if next_reminder:
            time_str = next_reminder['datetime'].toString("hh:mm")
            self.next_reminder.setText(f"⏳ Próximo: {time_str} - {next_reminder['title'][:20]}...")
        else:
            self.next_reminder.setText("⏳ Próximo: --:--")
    
    def filter_reminders(self):
        """Filtrar recordatorios"""
        filter_text = self.filter_combo.currentText()
        search_text = self.search_input.text().lower()
        
        print(f"Filtrando: {filter_text}, Buscando: {search_text}")
    
    def check_reminders(self):
        """Verificar si hay recordatorios que mostrar"""
        current_time = QDateTime.currentDateTime()
        
        for reminder in self.reminders:
            if reminder['active'] and not reminder['completed']:
                reminder_time = QDateTime(
                    QDate.fromString(reminder['date'], "yyyy-MM-dd"),
                    QTime.fromString(reminder['time'], "hh:mm")
                )
                
                # Verificar si es hora (con margen de 1 minuto)
                time_diff = reminder_time.secsTo(current_time)
                if 0 <= time_diff <= 60:  # Dentro del minuto
                    self.show_reminder_notification(reminder)
    
    def show_reminder_notification(self, reminder):
        """Mostrar notificación de recordatorio"""
        print(f"🔔 NOTIFICACIÓN: {reminder['title']} - {reminder['date_time']}")
        
        # Aquí se integraría con el sistema de notificaciones
        # Por ahora, solo imprimir en consola
    
    def snooze_all(self):
        """Posponer todos los recordatorios activos"""
        active_count = sum(1 for r in self.reminders if r['active'] and not r['completed'])
        
        if active_count == 0:
            QMessageBox.information(self, "Información", "No hay recordatorios activos para posponer.")
            return
        
        reply = QMessageBox.question(
            self, "Posponer Todos",
            f"¿Posponer {active_count} recordatorio(s) activo(s) 5 minutos?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            print(f"Posponiendo {active_count} recordatorios...")
    
    def mark_all_completed(self):
        """Marcar todos los recordatorios como completados"""
        active_count = sum(1 for r in self.reminders if r['active'] and not r['completed'])
        
        if active_count == 0:
            QMessageBox.information(self, "Información", "No hay recordatorios activos para marcar.")
            return
        
        reply = QMessageBox.question(
            self, "Marcar Todos",
            f"¿Marcar {active_count} recordatorio(s) activo(s) como completados?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            print(f"Marcando {active_count} recordatorios como completados...")
    
    def clear_completed(self):
        """Limpiar recordatorios completados"""
        completed_count = sum(1 for r in self.reminders if r['completed'])
        
        if completed_count == 0:
            QMessageBox.information(self, "Información", "No hay recordatorios completados para limpiar.")
            return
        
        reply = QMessageBox.question(
            self, "Limpiar Completados",
            f"¿Eliminar {completed_count} recordatorio(s) completado(s)?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            print(f"Eliminando {completed_count} recordatorios completados...")
    
    def export_reminders(self):
        """Exportar recordatorios"""
        QMessageBox.information(self, "Exportar", 
                              "Esta función exportaría los recordatorios a un archivo.")
    
    def load_sample_reminders(self):
        """Cargar recordatorios de ejemplo"""
        sample_reminders = [
            {
                'title': 'Tomar medicamentos',
                'description': 'Tomar vitaminas y suplementos diarios',
                'date': QDate.currentDate().toString("yyyy-MM-dd"),
                'time': '08:00',
                'priority': 'high',  # ← CAMBIADO 'alta' → 'high'
                'recurrence': 'Diario',
                'active': True,
                'completed': False
            },
            {
                'title': 'Reunión semanal de equipo',
                'description': 'Revisión de progreso y planificación',
                'date': QDate.currentDate().addDays(1).toString("yyyy-MM-dd"),
                'time': '10:30',
                'priority': 'medium',  # ← CAMBIADO 'media' → 'medium'
                'recurrence': 'Semanal',
                'active': True,
                'completed': False
            },
            {
                'title': 'Pagar facturas',
                'description': 'Pago de servicios (luz, agua, internet)',
                'date': QDate.currentDate().addDays(3).toString("yyyy-MM-dd"),
                'time': '18:00',
                'priority': 'high',  # ← CAMBIADO 'alta' → 'high'
                'recurrence': 'Mensual',
                'active': True,
                'completed': False
            },
            {
                'title': 'Llamar a mamá',
                'description': 'Llamada familiar semanal',
                'date': QDate.currentDate().addDays(2).toString("yyyy-MM-dd"),
                'time': '20:00',
                'priority': 'low',  # ← CAMBIADO 'baja' → 'low'
                'recurrence': 'Semanal',
                'active': True,
                'completed': True
            }
        ]
    
    def load_reminders(self):
        """Cargar recordatorios desde la base de datos"""
        try:
            if self.user_id:
                self.reminders = self.db.get_reminders()
                self.display_reminders()  # Llamar a display_reminders después de cargar
                self.update_stats()
                self.update_next_reminder()
            else:
                self.load_sample_reminders()
        except Exception as e:
            print(f"❌ Error cargando recordatorios desde BD: {e}")
            self.reminders = []
            self.load_sample_reminders()

    def display_reminders(self):
        """Mostrar recordatorios en las listas"""
        # Limpiar todas las listas primero
        self.active_list.clear()
        self.all_reminders_list.clear()
        self.completed_list.clear()
        
        for reminder in self.reminders:
            # Crear widget de recordatorio
            reminder_widget = ReminderWidget(reminder)
            reminder_widget.reminder_updated.connect(self.update_reminder)
            reminder_widget.reminder_deleted.connect(self.delete_reminder)
            
            # Agregar a la lista principal
            list_item = QListWidgetItem()
            list_item.setSizeHint(QSize(0, 80))
            self.all_reminders_list.addItem(list_item)
            self.all_reminders_list.setItemWidget(list_item, reminder_widget)
            
            # Agregar a lista activa si está activo y no completado
            if reminder.get('active', True) and not reminder.get('completed', False):
                active_item = QListWidgetItem()
                active_item.setSizeHint(QSize(0, 80))
                self.active_list.addItem(active_item)
                self.active_list.setItemWidget(active_item, reminder_widget)
            
            # Agregar a lista completados si está completado
            if reminder.get('completed', False):
                completed_item = QListWidgetItem(reminder.get('title', 'Sin título'))
                self.completed_list.addItem(completed_item)