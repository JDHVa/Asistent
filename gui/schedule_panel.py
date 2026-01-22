"""
Panel completo de horario y calendario con eventos recurrentes.
"""
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
import json
from datetime import datetime, timedelta
from database_manager import get_database

from export_data import export_tasks, export_events, export_reminders
class EventWidget(QWidget):
    """Widget para mostrar un evento en la lista"""
    
    event_updated = Signal(dict)
    event_deleted = Signal(int)
    
    def __init__(self, event_data, parent=None):
        super().__init__(parent)
        self.event_data = event_data
        self.setup_ui()
        
    def setup_ui(self):
        self.setFixedHeight(70)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # Color indicador
        color_indicator = QFrame()
        color_indicator.setFixedWidth(6)
        color_indicator.setStyleSheet(f"""
            QFrame {{
                background-color: {self.event_data.get('color', '#4285f4')};
                border-radius: 3px;
            }}
        """)
        
        # Información del evento
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        # Título
        title_label = QLabel(self.event_data.get('title', 'Sin título'))
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(11)
        title_label.setFont(title_font)
        
        # Detalles
        details_layout = QHBoxLayout()
        
        # Hora
        start_time = self.event_data.get('start_time', '')
        end_time = self.event_data.get('end_time', '')
        time_text = f"🕒 {start_time}" + (f" - {end_time}" if end_time else "")
        
        time_label = QLabel(time_text)
        time_label.setStyleSheet("color: #4285f4; font-size: 10px;")
        
        # Recurrencia
        recurrence = self.event_data.get('recurrence', 'ninguna')
        if recurrence != 'ninguna':
            recur_label = QLabel(f"🔁 {recurrence}")
            recur_label.setStyleSheet("color: #34a853; font-size: 10px;")
            details_layout.addWidget(recur_label)
        
        details_layout.addWidget(time_label)
        details_layout.addStretch()
        
        # Ubicación/descripción
        location = self.event_data.get('location', '')
        if location:
            loc_label = QLabel(f"📍 {location}")
            loc_label.setStyleSheet("color: #9aa0a6; font-size: 9px;")
            info_layout.addWidget(loc_label)
        
        info_layout.addWidget(title_label)
        info_layout.addLayout(details_layout)
        
        # Botones de acción
        action_layout = QVBoxLayout()
        action_layout.setSpacing(2)
        
        edit_btn = QPushButton("✏️")
        edit_btn.setFixedSize(24, 24)
        edit_btn.setToolTip("Editar evento")
        edit_btn.clicked.connect(self.edit_event)
        
        delete_btn = QPushButton("🗑️")
        delete_btn.setFixedSize(24, 24)
        delete_btn.setToolTip("Eliminar evento")
        delete_btn.clicked.connect(self.delete_event)
        
        action_layout.addWidget(edit_btn)
        action_layout.addWidget(delete_btn)
        
        layout.addWidget(color_indicator)
        layout.addLayout(info_layout, 1)
        layout.addLayout(action_layout)
        
        # Estilo
        self.setStyleSheet("""
            QWidget {
                background-color: #292a2d;
                border: 1px solid #3c4043;
                border-radius: 8px;
            }
            QWidget:hover {
                background-color: #2d2e31;
                border-color: #4285f4;
            }
        """)
        
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
        edit_btn.setStyleSheet(btn_style)
        delete_btn.setStyleSheet(btn_style.replace("#4285f4", "#ea4335"))
    
    def edit_event(self):
        """Editar evento"""
        QMessageBox.information(self, "Editar Evento", 
                              f"Editar: {self.event_data.get('title')}")
    
    def delete_event(self):
        """Eliminar evento"""
        reply = QMessageBox.question(
            self, "Eliminar Evento",
            f"¿Eliminar evento '{self.event_data.get('title')}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.event_deleted.emit(self.event_data.get('id'))

class SchedulePanel(QWidget):
    """Panel completo de horario y calendario"""
    
class SchedulePanel(QWidget):
    """Panel completo de horario y calendario"""
    
    def __init__(self, user_id=None, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.db = get_database()
        
        # Establecer usuario actual si se proporciona
        if user_id:
            self.db.set_current_user(user_id)
        
        self.events = []
        self.next_id = 1
        self.current_view = 'month'  # 'month', 'week', 'day'
        
        self.setup_ui()
        self.load_events()
        
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
        
        # Panel izquierdo: Calendario y formulario
        left_panel = self.create_left_panel()
        
        # Panel derecho: Vista de eventos
        right_panel = self.create_right_panel()
        
        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(right_panel)
        main_splitter.setSizes([400, 600])
        
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
        title = QLabel("📅 Calendario y Horario")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #e8eaed;")
        
        # Selector de vista
        view_layout = QHBoxLayout()
        view_layout.setSpacing(5)
        
        view_btns = [
            ("📅 Mes", "month"),
            ("📆 Semana", "week"), 
            ("📝 Día", "day"),
            ("📋 Lista", "list")
        ]
        
        for btn_text, view_type in view_btns:
            btn = QPushButton(btn_text)
            btn.setCheckable(True)
            btn.setChecked(view_type == 'month')
            btn.clicked.connect(lambda checked, vt=view_type: self.change_view(vt))
            view_layout.addWidget(btn)
        
        # Fecha actual
        self.date_label = QLabel()
        self.update_date_label()
        
        # Navegación
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(5)
        
        prev_btn = QPushButton("◀")
        prev_btn.setFixedSize(30, 30)
        prev_btn.clicked.connect(self.navigate_prev)
        
        today_btn = QPushButton("Hoy")
        today_btn.clicked.connect(self.go_to_today)
        
        next_btn = QPushButton("▶")
        next_btn.setFixedSize(30, 30)
        next_btn.clicked.connect(self.navigate_next)
        
        nav_layout.addWidget(prev_btn)
        nav_layout.addWidget(today_btn)
        nav_layout.addWidget(next_btn)
        
        layout.addWidget(title)
        layout.addStretch()
        layout.addLayout(view_layout)
        layout.addStretch()
        layout.addWidget(self.date_label)
        layout.addLayout(nav_layout)
                # Botón IA
        self.ai_btn = QPushButton("🤖 IA")
        self.ai_btn.setToolTip("Analizar horario con IA")
        self.ai_btn.setFixedSize(40, 30)
        self.ai_btn.clicked.connect(self.analyze_with_ai)
        nav_layout.addWidget(self.ai_btn)
        
        return header
    def analyze_with_ai(self):
        """Analizar horario con IA"""
        from assistant_managers import gemini_manager, voice_manager
        
        if not gemini_manager.model:
            QMessageBox.warning(self, "IA no disponible", 
                              "Gemini AI no está configurado. Verifica tu API key.")
            return
        
        # Obtener eventos del día seleccionado
        selected_date = self.calendar.selectedDate().toString("yyyy-MM-dd")
        day_events = [e for e in self.events if e['date'] == selected_date]
        
        current_time = QTime.currentTime().toString("hh:mm")
        current_date = QDate.currentDate().toString("dd/MM/yyyy")
        
        # Mostrar indicador de procesamiento
        QMessageBox.information(self, "Analizando", 
                              "🤖 IA está analizando tu horario...")
        
        # Obtener análisis
        analysis = gemini_manager.analyze_schedule(day_events, f"{current_date} {current_time}")
        
        # Mostrar resultado
        dialog = QDialog(self)
        dialog.setWindowTitle("🤖 Análisis de IA")
        dialog.setMinimumSize(500, 400)
        
        layout = QVBoxLayout(dialog)
        
        # Texto del análisis
        text_edit = QTextEdit()
        text_edit.setPlainText(analysis)
        text_edit.setReadOnly(True)
        text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #202124;
                color: #e8eaed;
                border: 1px solid #3c4043;
                border-radius: 8px;
                padding: 10px;
                font-size: 13px;
            }
        """)
        
        # Botones
        button_layout = QHBoxLayout()
        
        speak_btn = QPushButton("🔊 Escuchar")
        speak_btn.clicked.connect(lambda: voice_manager.speak(analysis))
        
        copy_btn = QPushButton("📋 Copiar")
        copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(analysis))
        
        close_btn = QPushButton("Cerrar")
        close_btn.clicked.connect(dialog.accept)
        
        button_layout.addWidget(speak_btn)
        button_layout.addWidget(copy_btn)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        
        layout.addWidget(text_edit, 1)
        layout.addLayout(button_layout)
        
        dialog.exec()
        
        # Hablar automáticamente si hay eventos
        if day_events and voice_manager.available:
            voice_manager.speak(analysis)
    
    def create_left_panel(self):
        """Crear panel izquierdo (calendario y formulario)"""
        panel = QWidget()
        
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)
        
        # Calendario
        calendar_group = QGroupBox("📅 Calendario")
        calendar_group.setStyleSheet("""
            QGroupBox {
                color: #9aa0a6;
                border: 1px solid #3c4043;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                font-weight: bold;
            }
        """)
        
        calendar_layout = QVBoxLayout(calendar_group)
        
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.setStyleSheet("""
            QCalendarWidget {
                background-color: #1e1e1e;
                color: #e8eaed;
                border: 1px solid #3c4043;
                border-radius: 6px;
            }
            QCalendarWidget QToolButton {
                color: #e8eaed;
                font-weight: bold;
            }
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background-color: #2d2e31;
            }
            QCalendarWidget QSpinBox {
                background-color: #202124;
                color: #e8eaed;
                border: 1px solid #3c4043;
            }
            QCalendarWidget QAbstractItemView:enabled {
                background-color: #1e1e1e;
                color: #e8eaed;
                selection-background-color: #4285f4;
                selection-color: white;
            }
        """)
        self.calendar.selectionChanged.connect(self.on_date_selected)
        
        calendar_layout.addWidget(self.calendar)
        
        # Eventos del día seleccionado
        daily_events_label = QLabel("📝 Eventos del día:")
        daily_events_label.setStyleSheet("color: #e8eaed; font-weight: bold; margin-top: 10px;")
        
        self.daily_events_list = QListWidget()
        self.daily_events_list.setStyleSheet("""
            QListWidget {
                background-color: #202124;
                border: 1px solid #3c4043;
                border-radius: 6px;
                color: #e8eaed;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #2d2e31;
            }
        """)
        
        calendar_layout.addWidget(daily_events_label)
        calendar_layout.addWidget(self.daily_events_list, 1)
        
        # Formulario de nuevo evento
        form_group = QGroupBox("➕ Nuevo Evento")
        form_group.setStyleSheet(calendar_group.styleSheet())
        
        form_layout = QVBoxLayout(form_group)
        form_layout.setSpacing(10)
        
        # Campos del formulario
        self.event_title = QLineEdit()
        self.event_title.setPlaceholderText("Título del evento *")
        
        self.event_location = QLineEdit()
        self.event_location.setPlaceholderText("Ubicación (opcional)")
        
        self.event_description = QTextEdit()
        self.event_description.setPlaceholderText("Descripción...")
        self.event_description.setMaximumHeight(60)
        
        # Fecha y hora
        datetime_layout = QHBoxLayout()
        
        date_col = QVBoxLayout()
        date_col.addWidget(QLabel("Fecha:"))
        self.event_date = QDateEdit()
        self.event_date.setDate(QDate.currentDate())
        self.event_date.setCalendarPopup(True)
        date_col.addWidget(self.event_date)
        
        time_col = QVBoxLayout()
        time_col.addWidget(QLabel("Hora inicio:"))
        self.event_start_time = QTimeEdit()
        self.event_start_time.setTime(QTime(9, 0))
        time_col.addWidget(self.event_start_time)
        
        time_col.addWidget(QLabel("Hora fin:"))
        self.event_end_time = QTimeEdit()
        self.event_end_time.setTime(QTime(10, 0))
        time_col.addWidget(self.event_end_time)
        
        datetime_layout.addLayout(date_col)
        datetime_layout.addLayout(time_col)
        
        # Configuración adicional
        config_layout = QHBoxLayout()
        
        # Color
        color_col = QVBoxLayout()
        color_col.addWidget(QLabel("Color:"))
        self.event_color = QComboBox()
        self.event_color.addItems(["Azul", "Verde", "Rojo", "Amarillo", "Morado", "Naranja"])
        color_col.addWidget(self.event_color)
        
        # Recurrencia
        recur_col = QVBoxLayout()
        recur_col.addWidget(QLabel("Repetir:"))
        self.event_recurrence = QComboBox()
        self.event_recurrence.addItems(["No repetir", "Diario", "Semanal", "Mensual", "Anual"])
        recur_col.addWidget(self.event_recurrence)
        
        config_layout.addLayout(color_col)
        config_layout.addLayout(recur_col)
        
        # Botón agregar
        add_btn = QPushButton("➕ Agregar Evento")
        add_btn.clicked.connect(self.add_event)
        
        form_layout.addWidget(self.event_title)
        form_layout.addWidget(self.event_location)
        form_layout.addWidget(self.event_description)
        form_layout.addLayout(datetime_layout)
        form_layout.addLayout(config_layout)
        form_layout.addWidget(add_btn)
        
        layout.addWidget(calendar_group, 2)
        layout.addWidget(form_group, 1)
        
        # Estilos de inputs
        input_style = """
            QLineEdit, QTextEdit, QComboBox, QDateEdit, QTimeEdit {
                background-color: #202124;
                color: #e8eaed;
                border: 1px solid #3c4043;
                border-radius: 6px;
                padding: 8px;
                font-size: 14px;
            }
        """
        
        inputs = [self.event_title, self.event_location, self.event_description,
                 self.event_date, self.event_start_time, self.event_end_time,
                 self.event_color, self.event_recurrence]
        for inp in inputs:
            inp.setStyleSheet(input_style)
        
        return panel
    
    def create_right_panel(self):
        """Crear panel derecho (vista de eventos)"""
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
        
        # Vista semanal
        week_view = self.create_week_view()
        
        # Vista mensual
        month_view = self.create_month_view()
        
        # Vista de lista
        list_view = self.create_list_view()
        
        self.view_tabs.addTab(week_view, "📆 Semana")
        self.view_tabs.addTab(month_view, "📅 Mes")
        self.view_tabs.addTab(list_view, "📋 Lista")
        
        layout.addWidget(self.view_tabs, 1)
        
        # Estadísticas
        stats_frame = QFrame()
        stats_frame.setStyleSheet("""
            QFrame {
                background-color: #292a2d;
                border: 1px solid #3c4043;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        
        stats_layout = QHBoxLayout(stats_frame)
        
        stats = [
            ("📊 Total", "0", "#4285f4"),
            ("🎯 Hoy", "0", "#34a853"),
            ("🚀 Esta semana", "0", "#fbbc04"),
            ("⏳ Próximos", "0", "#ea4335")
        ]
        
        for label, value, color in stats:
            stat = self.create_stat_widget(label, value, color)
            stats_layout.addWidget(stat)
        
        stats_layout.addStretch()
        
        # Botón exportar
        export_btn = QPushButton("📤 Exportar Calendario")
        export_btn.setObjectName("secondary")
        
        stats_layout.addWidget(export_btn)
        
        layout.addWidget(stats_frame)
        
        return panel
    
    def create_week_view(self):
        """Crear vista semanal"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Crear tabla de horario semanal
        week_table = QTreeWidget()
        week_table.setHeaderLabels(["Hora", "Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"])
        week_table.setStyleSheet("""
            QTreeWidget {
                background-color: #1e1e1e;
                color: #e8eaed;
                border: 1px solid #3c4043;
                font-size: 12px;
            }
            QHeaderView::section {
                background-color: #2d2e31;
                color: #9aa0a6;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        
        # Añadir horas
        for hour in range(8, 20):
            item = QTreeWidgetItem([f"{hour:02d}:00"])
            week_table.addTopLevelItem(item)
        
        week_table.header().setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addWidget(week_table)
        return widget
    
    def create_month_view(self):
        """Crear vista mensual"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        info = QLabel("Vista mensual del calendario\n\nAquí se mostrarían los eventos organizados por día del mes.")
        info.setStyleSheet("color: #9aa0a6; font-size: 14px;")
        info.setAlignment(Qt.AlignCenter)
        info.setWordWrap(True)
        
        layout.addWidget(info)
        return widget
    
    def create_list_view(self):
        """Crear vista de lista de eventos"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Lista de todos los eventos
        self.events_list = QListWidget()
        self.events_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
            }
            QListWidget::item {
                margin: 5px 0px;
            }
        """)
        self.events_list.setSpacing(5)
        
        layout.addWidget(self.events_list, 1)
        
        # Filtros
        filter_frame = QFrame()
        filter_layout = QHBoxLayout(filter_frame)
        
        filter_label = QLabel("Filtrar:")
        
        self.event_filter = QComboBox()
        self.event_filter.addItems(["Todos", "Hoy", "Esta semana", "Este mes", "Pasados", "Futuros"])
        self.event_filter.currentTextChanged.connect(self.filter_events)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar eventos...")
        
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.event_filter)
        filter_layout.addWidget(self.search_input, 1)
        
        layout.addWidget(filter_frame)
        
        return widget
    
    def create_stat_widget(self, label, value, color):
        """Crear widget de estadística"""
        widget = QFrame()
        widget.setStyleSheet(f"""
            QFrame {{
                background-color: {color}20;
                border: 1px solid {color}40;
                border-radius: 8px;
                padding: 5px 10px;
            }}
        """)
        
        layout = QVBoxLayout(widget)
        layout.setSpacing(2)
        
        value_label = QLabel(value)
        value_label.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: bold;")
        value_label.setAlignment(Qt.AlignCenter)
        
        label_label = QLabel(label)
        label_label.setStyleSheet("color: #9aa0a6; font-size: 10px;")
        label_label.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(value_label)
        layout.addWidget(label_label)
        
        # Guardar referencia
        if label == "📊 Total":
            self.total_stat = value_label
        elif label == "🎯 Hoy":
            self.today_stat = value_label
        elif label == "🚀 Esta semana":
            self.week_stat = value_label
        elif label == "⏳ Próximos":
            self.upcoming_stat = value_label
        
        return widget
    
    def add_event(self):
        """Agregar nuevo evento"""
        title = self.event_title.text().strip()
        if not title:
            QMessageBox.warning(self, "Advertencia", "Ingresa un título para el evento.")
            return
        
        event_data = {
            'id': self.next_id,
            'title': title,
            'location': self.event_location.text().strip(),
            'description': self.event_description.toPlainText().strip(),
            'date': self.event_date.date().toString("yyyy-MM-dd"),
            'start_time': self.event_start_time.time().toString("hh:mm"),
            'end_time': self.event_end_time.time().toString("hh:mm"),
            'color': self.get_color_code(self.event_color.currentText()),
            'recurrence': self.event_recurrence.currentText(),
            'created_at': QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        }
        
        # Crear widget de evento
        event_widget = EventWidget(event_data)
        event_widget.event_updated.connect(self.update_event)
        event_widget.event_deleted.connect(self.delete_event)
        
        # Agregar a lista principal
        list_item = QListWidgetItem()
        list_item.setSizeHint(QSize(0, 70))
        self.events_list.addItem(list_item)
        self.events_list.setItemWidget(list_item, event_widget)
        
        # Guardar evento
        event_data['widget'] = event_widget
        event_data['list_item'] = list_item
        self.events.append(event_data)
        self.next_id += 1
        
        # Limpiar formulario
        self.event_title.clear()
        self.event_location.clear()
        self.event_description.clear()
        self.event_date.setDate(QDate.currentDate())
        self.event_start_time.setTime(QTime(9, 0))
        self.event_end_time.setTime(QTime(10, 0))
        
        # Actualizar vistas
        self.update_stats()
        self.update_daily_events()
        
        QMessageBox.information(self, "Éxito", "Evento agregado correctamente.")
    
    def get_color_code(self, color_name):
        """Obtener código hexadecimal del color"""
        colors = {
            "Azul": "#4285f4",
            "Verde": "#34a853",
            "Rojo": "#ea4335",
            "Amarillo": "#fbbc04",
            "Morado": "#a142f4",
            "Naranja": "#ff6d01"
        }
        return colors.get(color_name, "#4285f4")
    
    def update_event(self, event_data):
        """Actualizar evento"""
        for i, event in enumerate(self.events):
            if event['id'] == event_data['id']:
                self.events[i] = event_data
                break
        
        self.update_stats()
        self.update_daily_events()
    
    def delete_event(self, event_id):
        """Eliminar evento"""
        for i, event in enumerate(self.events):
            if event['id'] == event_id:
                # Remover de lista
                row = self.events_list.row(event['list_item'])
                self.events_list.takeItem(row)
                
                # Eliminar de lista
                del self.events[i]
                break
        
        self.update_stats()
        self.update_daily_events()
    
    def update_stats(self):
        """Actualizar estadísticas"""
        total = len(self.events)
        
        # Eventos de hoy
        today = QDate.currentDate().toString("yyyy-MM-dd")
        today_count = sum(1 for e in self.events if e['date'] == today)
        
        # Eventos de esta semana
        week_count = self.count_events_this_week()
        
        # Eventos próximos (futuros)
        upcoming = self.count_upcoming_events()
        
        # Actualizar labels
        self.total_stat.setText(str(total))
        self.today_stat.setText(str(today_count))
        self.week_stat.setText(str(week_count))
        self.upcoming_stat.setText(str(upcoming))
    
    def count_events_this_week(self):
        """Contar eventos de esta semana"""
        today = QDate.currentDate()
        start_of_week = today.addDays(-today.dayOfWeek() + 1)
        end_of_week = start_of_week.addDays(6)
        
        count = 0
        start_str = start_of_week.toString("yyyy-MM-dd")
        end_str = end_of_week.toString("yyyy-MM-dd")
        
        for event in self.events:
            if start_str <= event['date'] <= end_str:
                count += 1
        
        return count
    
    def count_upcoming_events(self):
        """Contar eventos futuros"""
        today = QDate.currentDate().toString("yyyy-MM-dd")
        count = 0
        
        for event in self.events:
            if event['date'] > today:
                count += 1
        
        return count
    
    def update_daily_events(self):
        """Actualizar eventos del día seleccionado"""
        self.daily_events_list.clear()
        
        selected_date = self.calendar.selectedDate().toString("yyyy-MM-dd")
        
        for event in self.events:
            if event['date'] == selected_date:
                item_text = f"{event['start_time']} - {event['title']}"
                if event['location']:
                    item_text += f" ({event['location']})"
                
                item = QListWidgetItem(item_text)
                self.daily_events_list.addItem(item)
    
    def on_date_selected(self):
        """Manejador de selección de fecha"""
        self.update_daily_events()
    
    def update_date_label(self):
        """Actualizar etiqueta de fecha"""
        current_date = QDate.currentDate()
        self.date_label.setText(current_date.toString("dddd, d 'de' MMMM 'de' yyyy"))
    
    def change_view(self, view_type):
        """Cambiar vista"""
        self.current_view = view_type
        
        # Cambiar pestaña
        tab_index = {"month": 1, "week": 0, "list": 2}.get(view_type, 0)
        self.view_tabs.setCurrentIndex(tab_index)
        
        print(f"Vista cambiada a: {view_type}")
    
    def navigate_prev(self):
        """Navegar a período anterior"""
        print("Navegar anterior")
    
    def navigate_next(self):
        """Navegar a período siguiente"""
        print("Navegar siguiente")
    
    def go_to_today(self):
        """Ir a hoy"""
        self.calendar.setSelectedDate(QDate.currentDate())
        self.update_date_label()
        print("Ir a hoy")
    
    def filter_events(self, filter_text):
        """Filtrar eventos"""
        print(f"Filtrar por: {filter_text}")
    def display_events(self):
        """Mostrar eventos en la lista"""
        self.events_list.clear()
        
        for event in self.events:
            # Crear widget de evento
            event_widget = EventWidget(event)
            event_widget.event_updated.connect(self.update_event)
            event_widget.event_deleted.connect(self.delete_event)
            
            # Agregar a la lista
            list_item = QListWidgetItem()
            list_item.setSizeHint(QSize(0, 70))
            self.events_list.addItem(list_item)
            self.events_list.setItemWidget(list_item, event_widget)

    # En schedule_panel.py, modificar load_events:

    def load_events(self):
        """Cargar eventos desde la base de datos"""
        try:
            if self.user_id:
                # Asegurar que db existe
                if not hasattr(self, 'db') or not self.db:
                    self.db = get_database()
                    if self.user_id:
                        self.db.set_current_user(self.user_id)
                
                self.events = self.db.get_events()
                
                # Asegurar que display_events existe
                if hasattr(self, 'display_events'):
                    self.display_events()
                else:
                    # Si no existe, crear uno básico
                    self.display_events = self.create_display_events_fallback()
                    self.display_events()
                
                if hasattr(self, 'update_stats'):
                    self.update_stats()
                if hasattr(self, 'update_daily_events'):
                    self.update_daily_events()
                    
            else:
                self.load_sample_events()
                
        except Exception as e:
            print(f"❌ Error cargando eventos desde BD: {e}")
            self.events = []
            self.load_sample_events()
    
    def load_sample_events(self):
        """Cargar eventos de ejemplo"""
        sample_events = [
            {
                'title': 'Reunión de equipo',
                'location': 'Sala de conferencias A',
                'date': QDate.currentDate().toString("yyyy-MM-dd"),
                'start_time': '10:00',
                'end_time': '11:00',
                'color': '#4285f4',
                'recurrence': 'Semanal'
            },
            {
                'title': 'Almuerzo con cliente',
                'location': 'Restaurante La Scala',
                'date': QDate.currentDate().toString("yyyy-MM-dd"),
                'start_time': '13:00',
                'end_time': '14:30',
                'color': '#34a853',
                'recurrence': 'No repetir'
            },
            {
                'title': 'Gimnasio',
                'location': 'Club Deportivo',
                'date': QDate.currentDate().addDays(1).toString("yyyy-MM-dd"),
                'start_time': '18:00',
                'end_time': '19:00',
                'color': '#ea4335',
                'recurrence': 'Diario'
            },
            {
                'title': 'Entrega de proyecto',
                'location': 'Oficina',
                'date': QDate.currentDate().addDays(3).toString("yyyy-MM-dd"),
                'start_time': '17:00',
                'end_time': '18:00',
                'color': '#fbbc04',
                'recurrence': 'No repetir'
            }
        ]
        
        for event_data in sample_events:
            event = {
                'id': self.next_id,
                **event_data,
                'description': 'Evento de ejemplo',
                'created_at': QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
            }
            
            event_widget = EventWidget(event)
            event_widget.event_updated.connect(self.update_event)
            event_widget.event_deleted.connect(self.delete_event)
            
            list_item = QListWidgetItem()
            list_item.setSizeHint(QSize(0, 70))
            self.events_list.addItem(list_item)
            self.events_list.setItemWidget(list_item, event_widget)
            
            event['widget'] = event_widget
            event['list_item'] = list_item
            self.events.append(event)
            self.next_id += 1
        
        self.update_stats()
        self.update_daily_events()