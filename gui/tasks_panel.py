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
from export_data import export_tasks, export_events, export_reminders
class TaskWidget(QWidget):
    """Widget para mostrar una tarea individual"""
    
    task_updated = Signal(dict)  # Cuando la tarea se actualiza
    task_deleted = Signal(int)   # Cuando se elimina (id)
    
    def __init__(self, task_data, parent=None):
        super().__init__(parent)
        self.task_data = task_data
        self.setup_ui()
        
    def setup_ui(self):
        """Configurar la interfaz de la tarea"""
        self.setFixedHeight(90)
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(12, 8, 12, 8)
        main_layout.setSpacing(10)
        
        # Checkbox de completado
        self.completed_cb = QCheckBox()
        self.completed_cb.setChecked(self.task_data.get('completed', False))
        self.completed_cb.stateChanged.connect(self.toggle_completed)
        
        # Información de la tarea
        info_layout = QVBoxLayout()
        info_layout.setSpacing(3)
        
        # Título
        self.title_label = QLabel(self.task_data.get('title', 'Sin título'))
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        
        # Descripción
        desc = self.task_data.get('description', '')
        if desc:
            self.desc_label = QLabel(desc)
            self.desc_label.setStyleSheet("color: #9aa0a6; font-size: 11px;")
            self.desc_label.setWordWrap(True)
            info_layout.addWidget(self.desc_label)
        
        # Detalles (fecha y prioridad)
        details_layout = QHBoxLayout()
        
        # Prioridad
        priority = self.task_data.get('priority', 'medium')
        priority_colors = {
            'high': ('🔥 Alta', '#ea4335'),
            'medium': ('⚠️ Media', '#fbbc04'),
            'low': ('📌 Baja', '#34a853')
        }
        priority_text, priority_color = priority_colors.get(priority, ('⚠️ Media', '#fbbc04'))
        
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
        
        # Fecha
        due_date = self.task_data.get('due_date')
        if due_date:
            date_label = QLabel(f"📅 {due_date}")
            date_label.setStyleSheet("color: #4285f4; font-size: 10px;")
            details_layout.addWidget(date_label)
        
        # Categoría
        category = self.task_data.get('category', '')
        if category:
            category_label = QLabel(f"🏷️ {category}")
            category_label.setStyleSheet("color: #a142f4; font-size: 10px;")
            details_layout.addWidget(category_label)
        
        details_layout.addWidget(priority_label)
        details_layout.addStretch()
        
        info_layout.addWidget(self.title_label)
        info_layout.addLayout(details_layout)
        
        # Botones de acción
        action_layout = QVBoxLayout()
        action_layout.setSpacing(4)
        
        edit_btn = QPushButton("✏️")
        edit_btn.setFixedSize(28, 28)
        edit_btn.setToolTip("Editar tarea")
        edit_btn.clicked.connect(self.edit_task)
        
        delete_btn = QPushButton("🗑️")
        delete_btn.setFixedSize(28, 28)
        delete_btn.setToolTip("Eliminar tarea")
        delete_btn.clicked.connect(self.delete_task)
        
        action_layout.addWidget(edit_btn)
        action_layout.addWidget(delete_btn)
        
        main_layout.addWidget(self.completed_cb)
        main_layout.addLayout(info_layout, 1)
        main_layout.addLayout(action_layout)
        
        # Estilo inicial
        self.update_style()
        
        # Estilo de los botones
        btn_style = """
            QPushButton {
                background-color: #2d2e31;
                border: 1px solid #3c4043;
                border-radius: 6px;
                color: #9aa0a6;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #35363a;
                border-color: #4285f4;
            }
        """
        edit_btn.setStyleSheet(btn_style)
        delete_btn.setStyleSheet(btn_style.replace("#4285f4", "#ea4335"))
    
    def update_style(self):
        """Actualizar estilo según estado"""
        if self.task_data.get('completed', False):
            self.title_label.setStyleSheet("color: #9aa0a6; text-decoration: line-through;")
            self.setStyleSheet("""
                TaskWidget {
                    background-color: #2d2e31;
                    border: 1px solid #3c4043;
                    border-radius: 8px;
                    opacity: 0.7;
                }
            """)
        else:
            self.title_label.setStyleSheet("color: #e8eaed;")
            self.setStyleSheet("""
                TaskWidget {
                    background-color: #292a2d;
                    border: 2px solid #3c4043;
                    border-radius: 8px;
                }
                TaskWidget:hover {
                    background-color: #2d2e31;
                    border-color: #4285f4;
                }
            """)
    
    def toggle_completed(self, state):
        """Cambiar estado de completado"""
        self.task_data['completed'] = (state == Qt.Checked)
        self.update_style()
        self.task_updated.emit(self.task_data)
    
    def edit_task(self):
        """Editar la tarea"""
        # Por ahora, solo notificación
        QMessageBox.information(self, "Editar Tarea", 
                              f"Editar tarea: {self.task_data.get('title')}")
    
    def delete_task(self):
        """Eliminar la tarea"""
        reply = QMessageBox.question(
            self, "Eliminar Tarea",
            f"¿Estás seguro de que quieres eliminar la tarea '{self.task_data.get('title')}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.task_deleted.emit(self.task_data.get('id'))

class TasksPanel(QWidget):
    """Panel principal de gestión de tareas con todas las funcionalidades"""
    
    def __init__(self):
        super().__init__()
        self.tasks = []
        self.next_id = 1
        self.setup_ui()
        self.load_sample_tasks()
        
    def setup_ui(self):
        """Configurar la interfaz completa de tareas"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # Encabezado con estadísticas
        header = self.create_header()
        main_layout.addWidget(header)
        
        # Panel de filtros y búsqueda
        filters_panel = self.create_filters_panel()
        main_layout.addWidget(filters_panel)
        
        # Panel principal con splitter
        main_splitter = QSplitter(Qt.Horizontal)
        
        # Panel izquierdo: Formulario y vista rápida
        left_panel = self.create_left_panel()
        
        # Panel derecho: Lista de tareas
        right_panel = self.create_right_panel()
        
        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(right_panel)
        main_splitter.setSizes([350, 650])
        
        main_layout.addWidget(main_splitter, 1)
        
    def create_header(self):
        """Crear encabezado con estadísticas"""
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
        title = QLabel("✅ Gestión de Tareas")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #e8eaed;")
        
        # Estadísticas
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(20)
        
        stats_data = [
            ("📊 Total", "0", "#4285f4"),
            ("✅ Completadas", "0", "#34a853"),
            ("⏳ Pendientes", "0", "#fbbc04"),
            ("🔥 Urgentes", "0", "#ea4335")
        ]
        
        for label_text, value, color in stats_data:
            stat_widget = self.create_stat_widget(label_text, value, color)
            stats_layout.addWidget(stat_widget)
        
        stats_layout.addStretch()
        
        # Botón agregar rápido
        quick_add_btn = QPushButton("➕ Agregar Rápido")
        quick_add_btn.clicked.connect(self.quick_add_task)
        
        layout.addWidget(title)
        layout.addLayout(stats_layout, 1)
        layout.addWidget(quick_add_btn)
        # Botón IA
        ai_btn = QPushButton("🤖 IA")
        ai_btn.clicked.connect(self.analyze_tasks_with_ai)
        layout.addWidget(ai_btn)
        
        return header
    
    def analyze_tasks_with_ai(self):
        """Analizar tareas con IA"""
        from assistant_managers import gemini_manager, voice_manager
        
        if not gemini_manager.model:
            QMessageBox.warning(self, "IA no disponible", 
                              "Gemini AI no está configurado.")
            return
        
        # Obtener análisis de Gemini
        analysis = gemini_manager.analyze_tasks(self.tasks)
        
        # Mostrar resultado
        QMessageBox.information(self, "🤖 Análisis de IA", analysis)
        
        # Hablar resultado
        if voice_manager.available:
            voice_manager.speak(analysis)
    def create_stat_widget(self, label, value, color):
        """Crear widget de estadística"""
        widget = QFrame()
        widget.setStyleSheet(f"""
            QFrame {{
                background-color: {color}20;
                border: 1px solid {color}40;
                border-radius: 8px;
                padding: 8px 12px;
            }}
        """)
        
        layout = QVBoxLayout(widget)
        layout.setSpacing(2)
        
        value_label = QLabel(value)
        value_font = QFont()
        value_font.setPointSize(16)
        value_font.setBold(True)
        value_label.setFont(value_font)
        value_label.setStyleSheet(f"color: {color};")
        value_label.setAlignment(Qt.AlignCenter)
        
        label_label = QLabel(label)
        label_label.setStyleSheet("color: #9aa0a6; font-size: 11px;")
        label_label.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(value_label)
        layout.addWidget(label_label)
        
        # Guardar referencia para actualizar
        if label == "📊 Total":
            self.total_stat = value_label
        elif label == "✅ Completadas":
            self.completed_stat = value_label
        elif label == "⏳ Pendientes":
            self.pending_stat = value_label
        elif label == "🔥 Urgentes":
            self.urgent_stat = value_label
        
        return widget
    
    def create_filters_panel(self):
        """Crear panel de filtros y búsqueda"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #292a2d;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        
        layout = QHBoxLayout(panel)
        
        # Búsqueda
        search_layout = QHBoxLayout()
        search_label = QLabel("🔍")
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar tareas...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #202124;
                color: #e8eaed;
                border: 1px solid #3c4043;
                border-radius: 6px;
                padding: 8px 12px;
                min-width: 200px;
            }
            QLineEdit:focus {
                border: 2px solid #4285f4;
            }
        """)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        
        # Filtros
        filters_layout = QHBoxLayout()
        
        # Filtro por estado
        self.status_filter = QComboBox()
        self.status_filter.addItems(["Todas", "Pendientes", "Completadas", "Atrasadas"])
        
        # Filtro por prioridad
        self.priority_filter = QComboBox()
        self.priority_filter.addItems(["Todas", "Alta", "Media", "Baja"])
        
        # Filtro por categoría
        self.category_filter = QComboBox()
        self.category_filter.addItems(["Todas", "Trabajo", "Personal", "Estudio", "Salud"])
        
        # Ordenar por
        self.sort_by = QComboBox()
        self.sort_by.addItems(["Fecha", "Prioridad", "Nombre", "Categoría"])
        
        filters_layout.addWidget(QLabel("Estado:"))
        filters_layout.addWidget(self.status_filter)
        filters_layout.addWidget(QLabel("Prioridad:"))
        filters_layout.addWidget(self.priority_filter)
        filters_layout.addWidget(QLabel("Categoría:"))
        filters_layout.addWidget(self.category_filter)
        filters_layout.addWidget(QLabel("Ordenar:"))
        filters_layout.addWidget(self.sort_by)
        
        layout.addLayout(search_layout)
        layout.addStretch()
        layout.addLayout(filters_layout)
        
        return panel
    
    def create_left_panel(self):
        """Crear panel izquierdo (formulario y vista rápida)"""
        panel = QWidget()
        
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)
        
        # Formulario de nueva tarea
        form_group = QGroupBox("➕ Nueva Tarea")
        form_group.setStyleSheet("""
            QGroupBox {
                color: #9aa0a6;
                border: 1px solid #3c4043;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
            }
        """)
        
        form_layout = QVBoxLayout(form_group)
        form_layout.setSpacing(10)
        
        # Campos del formulario
        self.task_title = QLineEdit()
        self.task_title.setPlaceholderText("Título de la tarea *")
        
        self.task_desc = QTextEdit()
        self.task_desc.setPlaceholderText("Descripción (opcional)")
        self.task_desc.setMaximumHeight(80)
        
        # Configuración en grid
        grid_layout = QHBoxLayout()
        
        # Columna 1
        col1 = QVBoxLayout()
        col1.addWidget(QLabel("Prioridad:"))
        self.task_priority = QComboBox()
        self.task_priority.addItems(["Alta", "Media", "Baja"])
        col1.addWidget(self.task_priority)
        
        col1.addWidget(QLabel("Categoría:"))
        self.task_category = QComboBox()
        self.task_category.addItems(["Trabajo", "Personal", "Estudio", "Salud", "Otros"])
        col1.addWidget(self.task_category)
        
        # Columna 2
        col2 = QVBoxLayout()
        col2.addWidget(QLabel("Fecha límite:"))
        self.task_due_date = QDateEdit()
        self.task_due_date.setDate(QDate.currentDate().addDays(1))
        self.task_due_date.setCalendarPopup(True)
        col2.addWidget(self.task_due_date)
        
        col2.addWidget(QLabel("Hora:"))
        self.task_due_time = QTimeEdit()
        self.task_due_time.setTime(QTime(17, 0))
        col2.addWidget(self.task_due_time)
        
        grid_layout.addLayout(col1)
        grid_layout.addLayout(col2)
        
        # Botón agregar
        add_btn = QPushButton("➕ Agregar Tarea")
        add_btn.clicked.connect(self.add_task)
        
        form_layout.addWidget(self.task_title)
        form_layout.addWidget(self.task_desc)
        form_layout.addLayout(grid_layout)
        form_layout.addWidget(add_btn)
        
        # Vista rápida de próximas tareas
        quick_view_group = QGroupBox("📅 Próximas Tareas")
        quick_view_group.setStyleSheet(form_group.styleSheet())
        
        quick_layout = QVBoxLayout(quick_view_group)
        
        self.quick_tasks_list = QListWidget()
        self.quick_tasks_list.setStyleSheet("""
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
            QListWidget::item:selected {
                background-color: #4285f4;
                color: white;
            }
        """)
        
        quick_layout.addWidget(self.quick_tasks_list)
        
        layout.addWidget(form_group)
        layout.addWidget(quick_view_group, 1)
        
        # Aplicar estilos a los inputs
        input_style = """
            QLineEdit, QTextEdit, QComboBox, QDateEdit, QTimeEdit {
                background-color: #202124;
                color: #e8eaed;
                border: 1px solid #3c4043;
                border-radius: 6px;
                padding: 8px;
                font-size: 14px;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus, 
            QDateEdit:focus, QTimeEdit:focus {
                border: 2px solid #4285f4;
            }
        """
        
        inputs = [self.task_title, self.task_desc, self.task_priority, 
                 self.task_category, self.task_due_date, self.task_due_time]
        for inp in inputs:
            inp.setStyleSheet(input_style)
        
        return panel
    
    def create_right_panel(self):
        """Crear panel derecho (lista principal de tareas)"""
        panel = QWidget()
        
        layout = QVBoxLayout(panel)
        layout.setSpacing(10)
        
        # Cabecera de la lista
        list_header = QHBoxLayout()
        
        list_title = QLabel("📋 Todas las Tareas")
        list_title.setStyleSheet("color: #e8eaed; font-weight: bold; font-size: 16px;")
        
        # Botones de acción masiva
        action_layout = QHBoxLayout()
        action_layout.setSpacing(5)
        
        mark_all_btn = QPushButton("✅ Marcar Todas")
        mark_all_btn.setObjectName("secondary")
        
        delete_completed_btn = QPushButton("🗑️ Limpiar Completadas")
        delete_completed_btn.setObjectName("danger")
        delete_completed_btn.clicked.connect(self.delete_completed_tasks)
        
        export_btn = QPushButton("📤 Exportar")
        export_btn.setObjectName("secondary")
        
        action_layout.addWidget(mark_all_btn)
        action_layout.addWidget(delete_completed_btn)
        action_layout.addWidget(export_btn)
        
        list_header.addWidget(list_title)
        list_header.addStretch()
        list_header.addLayout(action_layout)
        
        # Lista de tareas
        self.tasks_list = QListWidget()
        self.tasks_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
            }
            QListWidget::item {
                border: none;
                margin: 5px 0px;
            }
        """)
        self.tasks_list.setSpacing(5)
        
        layout.addLayout(list_header)
        layout.addWidget(self.tasks_list, 1)
        
        return panel
    
    def add_task(self):
        """Agregar una nueva tarea desde el formulario"""
        title = self.task_title.text().strip()
        if not title:
            QMessageBox.warning(self, "Advertencia", "Por favor, ingresa un título para la tarea.")
            return
        
        task_data = {
            'id': self.next_id,
            'title': title,
            'description': self.task_desc.toPlainText().strip(),
            'priority': self.task_priority.currentText().lower(),
            'category': self.task_category.currentText(),
            'due_date': self.task_due_date.date().toString("dd/MM/yyyy"),
            'due_time': self.task_due_time.time().toString("hh:mm"),
            'completed': False,
            'created_at': QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        }
        
        # Crear widget de tarea
        task_widget = TaskWidget(task_data)
        task_widget.task_updated.connect(self.update_task)
        task_widget.task_deleted.connect(self.delete_task)
        
        # Agregar a la lista
        list_item = QListWidgetItem()
        list_item.setSizeHint(QSize(0, 90))
        self.tasks_list.addItem(list_item)
        self.tasks_list.setItemWidget(list_item, task_widget)
        
        # Guardar tarea
        task_data['widget'] = task_widget
        task_data['list_item'] = list_item
        self.tasks.append(task_data)
        self.next_id += 1
        
        # Limpiar formulario
        self.task_title.clear()
        self.task_desc.clear()
        self.task_due_date.setDate(QDate.currentDate().addDays(1))
        self.task_due_time.setTime(QTime(17, 0))
        
        # Actualizar estadísticas y vistas
        self.update_stats()
        self.update_quick_view()
        
        QMessageBox.information(self, "Éxito", "Tarea agregada correctamente.")
    
    def quick_add_task(self):
        """Agregar tarea rápidamente"""
        title, ok = QInputDialog.getText(self, "Agregar Tarea Rápida", 
                                       "Ingresa el título de la tarea:")
        if ok and title:
            task_data = {
                'id': self.next_id,
                'title': title,
                'description': '',
                'priority': 'medium',
                'category': 'Personal',
                'due_date': QDate.currentDate().toString("dd/MM/yyyy"),
                'due_time': '17:00',
                'completed': False,
                'created_at': QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
            }
            
            task_widget = TaskWidget(task_data)
            task_widget.task_updated.connect(self.update_task)
            task_widget.task_deleted.connect(self.delete_task)
            
            list_item = QListWidgetItem()
            list_item.setSizeHint(QSize(0, 90))
            self.tasks_list.addItem(list_item)
            self.tasks_list.setItemWidget(list_item, task_widget)
            
            task_data['widget'] = task_widget
            task_data['list_item'] = list_item
            self.tasks.append(task_data)
            self.next_id += 1
            
            self.update_stats()
            self.update_quick_view()
    
    def update_task(self, task_data):
        """Actualizar una tarea existente"""
        for i, task in enumerate(self.tasks):
            if task['id'] == task_data['id']:
                self.tasks[i] = task_data
                break
        
        self.update_stats()
        self.update_quick_view()
    
    def delete_task(self, task_id):
        """Eliminar una tarea específica"""
        for i, task in enumerate(self.tasks):
            if task['id'] == task_id:
                # Remover de la lista
                row = self.tasks_list.row(task['list_item'])
                self.tasks_list.takeItem(row)
                
                # Eliminar de la lista
                del self.tasks[i]
                break
        
        self.update_stats()
        self.update_quick_view()
    
    def delete_completed_tasks(self):
        """Eliminar todas las tareas completadas"""
        completed_tasks = [t for t in self.tasks if t['completed']]
        
        if not completed_tasks:
            QMessageBox.information(self, "Información", "No hay tareas completadas para eliminar.")
            return
        
        reply = QMessageBox.question(
            self, "Eliminar Tareas Completadas",
            f"¿Estás seguro de que quieres eliminar {len(completed_tasks)} tarea(s) completada(s)?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            for task in completed_tasks:
                row = self.tasks_list.row(task['list_item'])
                self.tasks_list.takeItem(row)
            
            self.tasks = [t for t in self.tasks if not t['completed']]
            self.update_stats()
            self.update_quick_view()
            
            QMessageBox.information(self, "Éxito", 
                                  f"Se eliminaron {len(completed_tasks)} tareas completadas.")
    
    def update_stats(self):
        """Actualizar todas las estadísticas"""
        total = len(self.tasks)
        completed = sum(1 for t in self.tasks if t['completed'])
        pending = total - completed
        
        # Contar urgentes (alta prioridad y no completadas)
        urgent = sum(1 for t in self.tasks if t['priority'] == 'high' and not t['completed'])
        
        # Actualizar labels
        self.total_stat.setText(str(total))
        self.completed_stat.setText(str(completed))
        self.pending_stat.setText(str(pending))
        self.urgent_stat.setText(str(urgent))
    
    def update_quick_view(self):
        """Actualizar vista rápida de próximas tareas"""
        self.quick_tasks_list.clear()
        
        # Filtrar tareas no completadas y ordenar por fecha
        pending_tasks = [t for t in self.tasks if not t['completed']]
        pending_tasks.sort(key=lambda x: x['due_date'])
        
        # Mostrar solo las próximas 5
        for task in pending_tasks[:5]:
            item_text = f"{task['title']}\n"
            item_text += f"  📅 {task['due_date']} • {task['priority'].capitalize()}"
            
            item = QListWidgetItem(item_text)
            self.quick_tasks_list.addItem(item)
    
    def load_sample_tasks(self):
        """Cargar tareas de ejemplo"""
        sample_tasks = [
            {
                'title': 'Completar informe mensual',
                'description': 'Revisar datos y generar gráficos para la presentación del equipo',
                'priority': 'high',
                'category': 'Trabajo',
                'due_date': QDate.currentDate().addDays(2).toString("dd/MM/yyyy"),
                'due_time': '18:00',
                'completed': False
            },
            {
                'title': 'Ir al supermercado',
                'description': 'Comprar leche, huevos, pan, frutas y verduras',
                'priority': 'medium',
                'category': 'Personal',
                'due_date': QDate.currentDate().toString("dd/MM/yyyy"),
                'due_time': '19:00',
                'completed': True
            },
            {
                'title': 'Estudiar para el examen final',
                'description': 'Repasar capítulos 5-8 del libro de texto y hacer ejercicios',
                'priority': 'high',
                'category': 'Estudio',
                'due_date': QDate.currentDate().addDays(5).toString("dd/MM/yyyy"),
                'due_time': '20:00',
                'completed': False
            },
            {
                'title': 'Llamar al médico para cita',
                'description': 'Pedir cita para revisión anual y chequeo general',
                'priority': 'low',
                'category': 'Salud',
                'due_date': QDate.currentDate().addDays(3).toString("dd/MM/yyyy"),
                'due_time': '10:00',
                'completed': False
            },
            {
                'title': 'Preparar presentación para reunión',
                'description': 'Crear slides y preparar discurso para la reunión del jueves',
                'priority': 'medium',
                'category': 'Trabajo',
                'due_date': QDate.currentDate().addDays(1).toString("dd/MM/yyyy"),
                'due_time': '15:00',
                'completed': False
            }
        ]
        
        for task_data in sample_tasks:
            task = {
                'id': self.next_id,
                **task_data,
                'created_at': QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
            }
            
            task_widget = TaskWidget(task)
            task_widget.task_updated.connect(self.update_task)
            task_widget.task_deleted.connect(self.delete_task)
            
            list_item = QListWidgetItem()
            list_item.setSizeHint(QSize(0, 90))
            self.tasks_list.addItem(list_item)
            self.tasks_list.setItemWidget(list_item, task_widget)
            
            task['widget'] = task_widget
            task['list_item'] = list_item
            self.tasks.append(task)
            self.next_id += 1
        
        self.update_stats()
        self.update_quick_view()