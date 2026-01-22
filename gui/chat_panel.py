"""
Panel de chat interactivo con el asistente IA - VERSIÓN COMPLETA
Integración de Gemini AI y funcionalidades de voz
"""
# Plantilla completa de imports para PySide6 widgets
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
import os
import sys
import io
from pathlib import Path
from dotenv import load_dotenv
import threading
from assistant_managers import gemini_manager, voice_manager

# Intento de importar bibliotecas de voz con manejo de errores
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️ Google Generative AI no está disponible. Instala: pip install google-generativeai")

try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
    print("⚠️ Speech Recognition no está disponible. Instala: pip install SpeechRecognition")

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    print("⚠️ pyttsx3 no está disponible. Instala: pip install pyttsx3")

# Cargar variables de entorno
load_dotenv()

class MessageWidget(QFrame):
    """Widget para mostrar un mensaje en el chat"""
    def __init__(self, message, is_user, timestamp=None, parent=None):
        super().__init__(parent)
        self.message = message
        self.is_user = is_user
        self.setup_ui(timestamp)
        
    def setup_ui(self, timestamp):
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setLineWidth(1)
        
        # Layout principal
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 10, 15, 10)
        main_layout.setSpacing(5)
        
        # Cabecera del mensaje
        header_layout = QHBoxLayout()
        
        # Icono según tipo de mensaje
        icon_label = QLabel("👤" if self.is_user else "🤖")
        icon_label.setStyleSheet("font-size: 16px;")
        
        # Información del remitente
        sender_label = QLabel("Tú" if self.is_user else "Asistente")
        sender_font = QFont()
        sender_font.setBold(True)
        sender_font.setPointSize(11)
        sender_label.setFont(sender_font)
        
        # Tiempo
        if not timestamp:
            timestamp = QDateTime.currentDateTime().toString("hh:mm")
        time_label = QLabel(timestamp)
        time_label.setStyleSheet("color: #80868b; font-size: 10px;")
        
        header_layout.addWidget(icon_label)
        header_layout.addWidget(sender_label)
        header_layout.addStretch()
        header_layout.addWidget(time_label)
        
        # Contenido del mensaje
        content_label = QLabel(self.message)
        content_label.setWordWrap(True)
        content_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        content_label.setStyleSheet("""
            QLabel {
                color: #202124;
                font-size: 13px;
                line-height: 1.4;
                padding: 5px;
            }
        """)
        
        main_layout.addLayout(header_layout)
        main_layout.addWidget(content_label)
        
        self.setLayout(main_layout)
        
        # Estilo según tipo de mensaje
        if self.is_user:
            self.setStyleSheet("""
                QFrame {
                    background-color: #e3f2fd;
                    border: 1px solid #bbdefb;
                    border-radius: 10px;
                    border-top-right-radius: 0;
                    margin-left: 60px;
                    margin-right: 10px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: #f5f5f5;
                    border: 1px solid #e0e0e0;
                    border-radius: 10px;
                    border-top-left-radius: 0;
                    margin-left: 10px;
                    margin-right: 60px;
                }
            """)


class ChatPanel(QWidget):
    """Panel principal del chat con todas las funcionalidades"""
    
    # Señales
    message_sent = Signal(str)
    conversation_cleared = Signal()
    
class ChatPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.conversation_history = []
        self.current_conversation = []
        self.thinking = False
            
        # Usar gestores centralizados
        from assistant_managers import gemini_manager, voice_manager
        self.gemini_manager = gemini_manager
        self.voice_manager = voice_manager
            
        # Verificar disponibilidad de voz (usando los nuevos atributos)
        self.voice_enabled = self.voice_manager.tts_available  # <-- CAMBIO AQUÍ
            
        self.setup_ui()
        self.load_conversation_history()
        self.start_new_conversation()
        
    def setup_ui(self):
        """Configurar la interfaz completa del chat"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Barra de herramientas superior
        toolbar = self.create_toolbar()
        main_layout.addWidget(toolbar)
        
        # Splitter para historial y chat actual
        splitter = QSplitter(Qt.Horizontal)
        
        # Panel izquierdo: Historial de conversaciones
        history_panel = self.create_history_panel()
        
        # Panel derecho: Chat actual
        chat_panel = self.create_chat_panel()
        
        splitter.addWidget(history_panel)
        splitter.addWidget(chat_panel)
        splitter.setSizes([250, 750])
        
        main_layout.addWidget(splitter, 1)
        
    def create_toolbar(self):
        """Crear barra de herramientas superior"""
        toolbar = QFrame()
        toolbar.setFixedHeight(50)
        toolbar.setStyleSheet("""
            QFrame {
                background-color: #2b2d30;
                border-bottom: 1px solid #3c4043;
            }
        """)
        
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(15, 0, 15, 0)
        
        # Model selector
        model_label = QLabel("Modelo:")
        model_label.setStyleSheet("color: #9aa0a6;")
        
        self.model_combo = QComboBox()
        model_options = ["Gemini Flash", "Gemini Pro"]
        
        if not self.gemini_manager.model:
            model_options.append("Modo Simulado")
            self.model_combo.addItems(model_options)
            self.model_combo.setCurrentText("Modo Simulado")
        else:
            self.model_combo.addItems(model_options)
            self.model_combo.setCurrentIndex(0)
        
        # Checkbox para voz (solo si TTS está disponible)
        if self.voice_manager.tts_available:  # <-- CAMBIO AQUÍ
            self.voice_checkbox = QCheckBox("🔊 Voz")
            self.voice_checkbox.setChecked(self.voice_enabled)
            self.voice_checkbox.setStyleSheet("color: #9aa0a6;")
            self.voice_checkbox.stateChanged.connect(self.toggle_voice)
            layout.addWidget(self.voice_checkbox)
        else:
            voice_label = QLabel("🔇 Voz no disponible")
            voice_label.setStyleSheet("color: #ea4335;")
            layout.addWidget(voice_label)
        
        # Estado de Gemini
        gemini_status = "✅" if self.gemini_manager.model else "❌"
        gemini_text = "Gemini" if self.gemini_manager.model else "Gemini (no disp.)"
        self.gemini_status_label = QLabel(f"{gemini_status} {gemini_text}")
        self.gemini_status_label.setStyleSheet("color: #34a853;" if self.gemini_manager.model else "color: #ea4335;")
        
        layout.addWidget(model_label)
        layout.addWidget(self.model_combo)
        layout.addSpacing(20)
        layout.addWidget(self.gemini_status_label)
        layout.addStretch()
        
        # Botón nueva conversación
        new_chat_btn = QPushButton("➕ Nueva Conversación")
        new_chat_btn.clicked.connect(self.start_new_conversation)
        
        # Botón guardar conversación
        save_btn = QPushButton("💾 Guardar")
        save_btn.clicked.connect(self.save_conversation)
        
        layout.addWidget(new_chat_btn)
        layout.addWidget(save_btn)
        
        return toolbar

    def toggle_voice(self, state):
        """Activar/desactivar voz"""
        self.voice_enabled = (state == Qt.Checked)
        if self.voice_enabled:
            print("🔊 Voz activada")
        else:
            print("🔇 Voz desactivada")
    
    def create_history_panel(self):
        """Crear panel de historial de conversaciones"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #202124;
                border-right: 1px solid #3c4043;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Título
        title = QLabel("📚 Historial")
        title.setStyleSheet("""
            QLabel {
                color: #e8eaed;
                font-size: 16px;
                font-weight: bold;
                padding: 15px;
                border-bottom: 1px solid #3c4043;
            }
        """)
        
        # Lista de conversaciones
        self.history_list = QListWidget()
        self.history_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                color: #e8eaed;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 10px 15px;
                border-bottom: 1px solid #2d2e31;
            }
            QListWidget::item:hover {
                background-color: #2d2e31;
            }
            QListWidget::item:selected {
                background-color: #4285f4;
                color: white;
            }
        """)
        self.history_list.itemClicked.connect(self.load_conversation)
        
        layout.addWidget(title)
        layout.addWidget(self.history_list, 1)
        
        return panel
    
    def create_chat_panel(self):
        """Crear panel principal del chat"""
        panel = QWidget()
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Área de mensajes
        self.messages_scroll = QScrollArea()
        self.messages_scroll.setWidgetResizable(True)
        self.messages_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.messages_scroll.setStyleSheet("""
            QScrollArea {
                background-color: #1a1a1a;
                border: none;
            }
        """)
        
        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setAlignment(Qt.AlignTop)
        self.messages_layout.setContentsMargins(20, 20, 20, 20)
        self.messages_layout.setSpacing(10)
        
        self.messages_scroll.setWidget(self.messages_container)
        
        # Barra de entrada
        input_panel = self.create_input_panel()
        
        layout.addWidget(self.messages_scroll, 1)
        layout.addWidget(input_panel)
        
        return panel
    
    def create_input_panel(self):
        """Crear panel de entrada de mensajes"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #202124;
                border-top: 1px solid #3c4043;
                padding: 15px;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setSpacing(10)
        
        # Barra de acciones
        actions_layout = QHBoxLayout()
        
        # Botones de formato
        format_btns = ["B", "I", "U", "📎", "📷"]
        for btn_text in format_btns:
            btn = QPushButton(btn_text)
            btn.setFixedSize(30, 30)
            btn.setObjectName("secondary")
            actions_layout.addWidget(btn)
        
        # Botón de voz (solo si está disponible)
        if self.voice_manager.microphone_available:  # <-- CAMBIO AQUÍ
            self.voice_btn = QPushButton("🎤")
            self.voice_btn.setFixedSize(30, 30)
            self.voice_btn.setToolTip("Hablar mensaje (mantén presionado)")
            self.voice_btn.setCheckable(True)
            self.voice_btn.pressed.connect(self.start_voice_recognition)
            self.voice_btn.released.connect(self.stop_voice_recognition)
            actions_layout.addWidget(self.voice_btn)
        else:
            # Mostrar botón deshabilitado si no hay micrófono
            self.voice_btn = QPushButton("🎤")
            self.voice_btn.setFixedSize(30, 30)
            self.voice_btn.setToolTip("Micrófono no disponible")
            self.voice_btn.setEnabled(False)
            self.voice_btn.setStyleSheet("opacity: 0.5;")
            actions_layout.addWidget(self.voice_btn)
        
        actions_layout.addStretch()
        
        # Contador de caracteres
        self.char_count = QLabel("0/4000")
        self.char_count.setStyleSheet("color: #9aa0a6; font-size: 11px;")
        actions_layout.addWidget(self.char_count)
        
        # Área de texto
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("Escribe tu mensaje aquí... (Ctrl+Enter para enviar)")
        self.message_input.setMaximumHeight(100)
        self.message_input.setAcceptRichText(False)
        self.message_input.textChanged.connect(self.update_char_count)
        
        self.message_input.setStyleSheet("""
            QTextEdit {
                background-color: #292a2d;
                color: #e8eaed;
                border: 1px solid #3c4043;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                selection-background-color: #4285f4;
            }
            QTextEdit:focus {
                border: 2px solid #4285f4;
            }
        """)
        
        # Barra inferior con botón enviar
        bottom_layout = QHBoxLayout()
        
        # Modo de entrada
        self.input_mode = QComboBox()
        self.input_mode.addItems(["Texto", "Voz", "Comando"])
        
        # Botón enviar
        self.send_btn = QPushButton("Enviar (Ctrl+Enter)")
        self.send_btn.setFixedWidth(150)
        self.send_btn.clicked.connect(self.send_message)
        
        bottom_layout.addWidget(self.input_mode)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.send_btn)
        
        layout.addLayout(actions_layout)
        layout.addWidget(self.message_input)
        layout.addLayout(bottom_layout)
        
        # Conectar Ctrl+Enter
        self.message_input.keyPressEvent = self.handle_key_press
        
        return panel
    
    def handle_key_press(self, event):
        """Manejar teclas especiales"""
        if event.key() == Qt.Key_Return and event.modifiers() == Qt.ControlModifier:
            self.send_message()
        else:
            QTextEdit.keyPressEvent(self.message_input, event)
    
    def update_char_count(self):
        """Actualizar contador de caracteres"""
        text = self.message_input.toPlainText()
        count = len(text)
        self.char_count.setText(f"{count}/4000")
        
        # Cambiar color si se excede
        if count > 4000:
            self.char_count.setStyleSheet("color: #ea4335; font-size: 11px;")
        else:
            self.char_count.setStyleSheet("color: #9aa0a6; font-size: 11px;")
    
    def send_message(self):
        """Enviar mensaje"""
        message = self.message_input.toPlainText().strip()
        if not message or self.thinking:
            return
        
        # Agregar mensaje del usuario
        self.add_message(message, is_user=True)
        self.message_input.clear()
        
        # Mostrar indicador de "pensando"
        self.show_thinking_indicator()
        
        # Guardar en historial
        self.current_conversation.append({
            "role": "user",
            "content": message,
            "timestamp": QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        })
        
        # Usar el modelo seleccionado
        selected_model = self.model_combo.currentText()
        
        if ("Gemini" in selected_model) and self.gemini_manager.model:
            # Usar Gemini AI
            QTimer.singleShot(100, lambda: self.process_with_gemini(message))
        else:
            # Usar simulación
            QTimer.singleShot(1500, self.simulate_ai_response)
    
    def process_with_gemini(self, message):
        """Procesar mensaje con Gemini AI"""
        try:
            # Prompt del sistema para contexto
            system_prompt = """Eres un asistente virtual personal útil y amigable. 
            Responde en español de manera clara y concisa. 
            Si el usuario pregunta sobre programación, tareas, recordatorios o cualquier otra cosa, 
            proporciona respuestas útiles y prácticas y lo mas importante, responde brevemente."""
            
            # Obtener respuesta de Gemini
            response = self.gemini_manager.send_message(message, system_prompt)
            
            self.hide_thinking_indicator()
            self.add_message(response, is_user=False)
            
            # Guardar respuesta en historial
            self.current_conversation.append({
                "role": "assistant",
                "content": response,
                "timestamp": QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
            })
            
            # Reproducir voz si está habilitado
            if self.voice_enabled and self.voice_manager and self.voice_manager.tts_engine:
                self.voice_manager.speak(response)
                
        except Exception as e:
            self.hide_thinking_indicator()
            error_msg = f"❌ Error con Gemini AI: {str(e)[:100]}"
            self.add_message(error_msg, is_user=False)
            
    def simulate_ai_response(self):
        """Simular respuesta de IA (solo si Gemini no está disponible)"""
        self.hide_thinking_indicator()
        
        # Respuestas de ejemplo
        responses = [
            "¡Hola! Soy tu asistente personal. Puedo ayudarte con una variedad de tareas como programación, análisis de datos, redacción, y más. ¿En qué puedo asistirte hoy?",
            "Entiendo tu consulta. Permíteme analizarla y proporcionarte la mejor respuesta posible basada en la información disponible.",
            "Interesante pregunta. Déjame procesar esa información y te daré una respuesta detallada en un momento.",
            "He recibido tu mensaje. Estoy trabajando en una respuesta útil y precisa para ti.",
            "Gracias por tu pregunta. Como asistente de IA, puedo ayudarte con conceptos, explicaciones, sugerencias y análisis. ¿Hay algo específico en lo que te gustaría que profundice?"
        ]
        
        import random
        response = random.choice(responses)
        self.add_message(response, is_user=False)
        
        # Guardar en historial
        self.current_conversation.append({
            "role": "assistant",
            "content": response,
            "timestamp": QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        })
        
        # Reproducir voz si está habilitado
        if self.voice_enabled and self.voice_manager and self.voice_manager.tts_engine:
            self.voice_manager.speak(response)
    
    def add_message(self, text, is_user=True):
        """Agregar mensaje al chat"""
        timestamp = QDateTime.currentDateTime().toString("hh:mm")
        message_widget = MessageWidget(text, is_user, timestamp)
        
        self.messages_layout.addWidget(message_widget)
        
        # Desplazar hacia abajo
        QTimer.singleShot(100, self.scroll_to_bottom)
    
    def scroll_to_bottom(self):
        """Desplazar al final del chat"""
        scrollbar = self.messages_scroll.verticalScrollBar()
        if scrollbar:
            scrollbar.setValue(scrollbar.maximum())
    
    def show_thinking_indicator(self):
        """Mostrar indicador de 'pensando'"""
        self.thinking = True
        self.send_btn.setEnabled(False)
        self.send_btn.setText("Pensando...")
        
        # Agregar widget de pensando
        thinking_widget = QFrame()
        thinking_widget.setStyleSheet("""
            QFrame {
                background-color: #2d2e31;
                border: 1px solid #3c4043;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        
        thinking_layout = QHBoxLayout(thinking_widget)
        
        dots = QLabel("🤖 El asistente está pensando...")
        dots.setStyleSheet("color: #9aa0a6; font-style: italic;")
        
        thinking_layout.addWidget(dots)
        thinking_layout.addStretch()
        
        self.thinking_indicator = thinking_widget
        self.messages_layout.addWidget(thinking_widget)
    
    def hide_thinking_indicator(self):
        """Ocultar indicador de 'pensando'"""
        self.thinking = False
        self.send_btn.setEnabled(True)
        self.send_btn.setText("Enviar (Ctrl+Enter)")
        
        if hasattr(self, 'thinking_indicator'):
            self.thinking_indicator.deleteLater()
    
    def start_new_conversation(self):
        """Iniciar nueva conversación"""
        # Limpiar mensajes actuales
        while self.messages_layout.count():
            item = self.messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Reiniciar conversación actual
        self.current_conversation = []
        
        # Limpiar historial de Gemini
        if self.gemini_manager:
            self.gemini_manager.clear_history()
        
        # Agregar mensaje de bienvenida
        if self.gemini_manager.model:
            welcome_msg = "¡Hola! Soy tu asistente personal con Gemini AI. ¿En qué puedo ayudarte hoy?"
        else:
            welcome_msg = "¡Hola! Soy tu asistente personal. ¿En qué puedo ayudarte hoy?"
            
        self.add_message(welcome_msg, is_user=False)
        
        # Guardar en historial
        self.current_conversation.append({
            "role": "assistant",
            "content": welcome_msg,
            "timestamp": QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        })
        
        # Actualizar historial
        self.update_history_list()
    
    def start_voice_recognition(self):
        """Iniciar reconocimiento de voz"""
        if not self.voice_manager.available:
            QMessageBox.warning(self, "Voz no disponible", 
                              "El sistema de reconocimiento de voz no está disponible.\n\n"
                              "Instala las dependencias necesarias:\n"
                              "pip install SpeechRecognition pyttsx3")
            return
        
        # Cambiar apariencia del botón para indicar que está escuchando
        self.voice_btn.setText("🎤...")
        self.voice_btn.setStyleSheet("background-color: #ea4335; color: white;")
        
        # En un hilo separado para no bloquear la interfaz
        self.voice_thread = threading.Thread(target=self.process_voice_input, daemon=True)
        self.voice_thread.start()
    
    def stop_voice_recognition(self):
        """Detener reconocimiento de voz"""
        self.voice_btn.setText("🎤")
        self.voice_btn.setStyleSheet("")
    
    def process_voice_input(self):
        """Procesar entrada de voz en segundo plano"""
        try:
            # Reconocer voz - CAMBIA ESTA LÍNEA
            # recognized_text = self.voice_manager.recognize_speech()  # ← VIEJO
            recognized_text = self.voice_manager.listen()  # ← NUEVO
            
            # Actualizar interfaz en el hilo principal
            if recognized_text and not recognized_text.startswith("❌") and not recognized_text.startswith("⏱️"):
                # Usar un timer para actualizar en el hilo principal
                QTimer.singleShot(0, lambda: self.message_input.setPlainText(recognized_text))
            elif recognized_text:
                # Mostrar error en el chat
                QTimer.singleShot(0, lambda: self.add_message(f"❌ Voz: {recognized_text}", is_user=False))
                
        except Exception as e:
            error_msg = f"Error en reconocimiento de voz: {str(e)}"
            print(error_msg)
            QTimer.singleShot(0, lambda: self.add_message(f"❌ {error_msg}", is_user=False))

    def load_conversation_history(self):
        """Cargar historial de conversaciones"""
        # Por ahora, datos de ejemplo
        self.conversation_history = [
            {"id": 1, "title": "Planificación de proyecto", "date": "2024-02-15", "preview": "Discusión sobre el nuevo proyecto..."},
            {"id": 2, "title": "Ayuda con código Python", "date": "2024-02-14", "preview": "Problemas con funciones asíncronas..."},
            {"id": 3, "title": "Revisión de documentos", "date": "2024-02-13", "preview": "Revisión de contrato y términos..."},
        ]
        
        self.update_history_list()
    
    def update_history_list(self):
        """Actualizar lista de historial"""
        self.history_list.clear()
        
        for conv in self.conversation_history:
            item_text = f"{conv['title']}\n<small>{conv['date']} - {conv['preview'][:30]}...</small>"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, conv['id'])
            self.history_list.addItem(item)
    
    def load_conversation(self, item):
        """Cargar conversación seleccionada"""
        conv_id = item.data(Qt.UserRole)
        
        # Por ahora, solo simulación
        QMessageBox.information(self, "Cargar Conversación", 
                              f"Esta función cargaría la conversación ID: {conv_id}")
    
    def save_conversation(self):
        """Guardar conversación actual"""
        if not self.current_conversation:
            QMessageBox.warning(self, "Sin conversación", "No hay conversación para guardar.")
            return
        
        # Simular guardado
        title = f"Conversación {QDateTime.currentDateTime().toString('dd-MM-yyyy hh:mm')}"
        self.conversation_history.insert(0, {
            "id": len(self.conversation_history) + 1,
            "title": title,
            "date": QDateTime.currentDateTime().toString("yyyy-MM-dd"),
            "preview": self.current_conversation[0]['content'][:50] + "..."
        })
        
        self.update_history_list()
        QMessageBox.information(self, "Guardado", "Conversación guardada exitosamente.")

# Para probar el panel individualmente
if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    
    app = QApplication([])
    app.setStyle("Fusion")
    
    # Estilo oscuro
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
    
    window = ChatPanel()
    window.setWindowTitle("Chat Panel - Asistente Virtual")
    window.resize(1200, 800)
    window.show()
    
    sys.exit(app.exec())