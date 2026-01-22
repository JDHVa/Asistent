"""
Asistente de voz continuo - Integrado con la aplicación principal
Escucha constantemente y responde usando Gemini AI
"""
import sys
import os
import json
import threading
import time
import queue
from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QApplication, QWidget, QMainWindow, QDialog, QLabel, QPushButton,  # Agregar QApplication aquí
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
import google.generativeai as genai
from dotenv import load_dotenv
import speech_recognition as sr
import pyttsx3

# Cargar variables de entorno
load_dotenv()

class ListeningThread(QThread):
    """Hilo para escuchar continuamente"""
    heard_text = Signal(str)
    listening_state = Signal(bool)
    error_occurred = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.running = True
        self.keyword = "asistente"
        self.recognizer = None
        self.microphone = None
        self.setup_recognizer()
    
    def setup_recognizer(self):
        """Configurar reconocimiento de voz"""
        try:
            self.recognizer = sr.Recognizer()
            
            # Listar micrófonos disponibles
            print("🎤 Buscando micrófonos...")
            try:
                mics = sr.Microphone.list_microphone_names()
                print(f"Micrófonos encontrados: {len(mics)}")
                for i, mic in enumerate(mics[:3]):  # Mostrar solo los primeros 3
                    print(f"  {i}: {mic}")
                
                # Usar el primer micrófono disponible
                self.microphone = sr.Microphone(device_index=0)
                print(f"✅ Usando micrófono: {mics[0]}")
            except:
                # Si no se pueden listar, intentar con micrófono por defecto
                print("⚠️ Usando micrófono por defecto")
                self.microphone = sr.Microphone()
                
        except Exception as e:
            print(f"❌ Error al configurar micrófono: {e}")
            self.error_occurred.emit(f"Error de micrófono: {e}")
    
    def run(self):
        """Bucle principal de escucha"""
        if not self.recognizer or not self.microphone:
            self.error_occurred.emit("No se pudo inicializar el micrófono")
            return
        
        print("🔊 Asistente escuchando... Di 'Asistente' para activar")
        
        while self.running:
            try:
                # Indicar que está escuchando
                self.listening_state.emit(True)
                
                with self.microphone as source:
                    # Ajustar para ruido ambiental
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    
                    # Escuchar con timeout corto para respuesta rápida
                    try:
                        audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=3)
                        
                        # Procesar audio
                        text = self.recognizer.recognize_google(audio, language='es-ES')
                        text = text.lower()
                        
                        print(f"🎤 Escuché: {text}")
                        
                        # Verificar si contiene la palabra clave
                        if self.keyword in text:
                            print(f"✅ Palabra clave detectada: '{self.keyword}'")
                            # Emitir el texto completo
                            self.heard_text.emit(text)
                            
                    except sr.WaitTimeoutError:
                        # Timeout normal, continuar escuchando
                        pass
                    except sr.UnknownValueError:
                        # No se entendió el audio, continuar
                        pass
                    except sr.RequestError as e:
                        print(f"⚠️ Error de conexión con Google Speech: {e}")
                
            except Exception as e:
                print(f"⚠️ Error en escucha: {e}")
                time.sleep(0.1)  # Pequeña pausa para no saturar
            
            finally:
                self.listening_state.emit(False)
    
    def stop(self):
        """Detener el hilo"""
        self.running = False
        self.wait()

class DataManager:
    """Gestor para acceder a los datos de la aplicación principal"""
    
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        self.ensure_data_directory()
    
    def ensure_data_directory(self):
        """Asegurar que existe el directorio de datos"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def load_tasks(self):
        """Cargar tareas desde archivo JSON"""
        tasks_file = os.path.join(self.data_dir, "tasks.json")
        if os.path.exists(tasks_file):
            try:
                with open(tasks_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"❌ Error cargando tareas: {e}")
                return []
        return []
    
    def load_events(self):
        """Cargar eventos desde archivo JSON"""
        events_file = os.path.join(self.data_dir, "events.json")
        if os.path.exists(events_file):
            try:
                with open(events_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"❌ Error cargando eventos: {e}")
                return []
        return []
    
    def load_reminders(self):
        """Cargar recordatorios desde archivo JSON"""
        reminders_file = os.path.join(self.data_dir, "reminders.json")
        if os.path.exists(reminders_file):
            try:
                with open(reminders_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"❌ Error cargando recordatorios: {e}")
                return []
        return []
    
    def get_current_time_info(self):
        """Obtener información de tiempo actual"""
        now = datetime.now()
        return {
            "date": now.strftime("%d/%m/%Y"),
            "time": now.strftime("%H:%M"),
            "day_name": now.strftime("%A"),
            "hour": now.hour,
            "minute": now.minute
        }
    
    def get_upcoming_tasks(self, limit=5):
        """Obtener próximas tareas pendientes"""
        tasks = self.load_tasks()
        pending_tasks = [t for t in tasks if not t.get('completed', False)]
        
        # Ordenar por fecha (si tienen)
        pending_tasks.sort(key=lambda x: x.get('due_date', '9999-99-99'))
        return pending_tasks[:limit]
    
    def get_today_events(self):
        """Obtener eventos de hoy"""
        events = self.load_events()
        today = datetime.now().strftime("%Y-%m-%d")
        
        today_events = []
        for event in events:
            event_date = event.get('date', '')
            if event_date == today:
                today_events.append(event)
        
        return today_events
    
    def get_urgent_reminders(self):
        """Obtener recordatorios urgentes"""
        reminders = self.load_reminders()
        now = datetime.now()
        
        urgent = []
        for reminder in reminders:
            if reminder.get('active', False) and not reminder.get('completed', False):
                # Verificar si es urgente (hoy o prioridad alta)
                reminder_date = reminder.get('date', '')
                reminder_time = reminder.get('time', '00:00')
                
                if reminder_date == now.strftime("%Y-%m-%d"):
                    urgent.append(reminder)
                elif reminder.get('priority', '') == 'alta':
                    urgent.append(reminder)
        
        return urgent

class GeminiAI:
    """Clase para interactuar con Gemini"""
    
    def __init__(self, data_manager):
        self.api_key = os.getenv("GEMINI_API_KEY", "AIzaSyAm9tYSXoKQfqIBGb_5bWJXcu6r0-Oridk")
        self.model = None
        self.data_manager = data_manager
        self.initialize()
    
    def initialize(self):
        """Inicializar Gemini AI"""
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            print("✅ Gemini AI inicializado")
            return True
        except Exception as e:
            print(f"❌ Error inicializando Gemini: {e}")
            return False
    
    def get_context_data(self):
        """Obtener datos de contexto para el asistente"""
        try:
            context = {
                "current_time": self.data_manager.get_current_time_info(),
                "upcoming_tasks": self.data_manager.get_upcoming_tasks(3),
                "today_events": self.data_manager.get_today_events(),
                "urgent_reminders": self.data_manager.get_urgent_reminders(),
                "total_tasks": len(self.data_manager.load_tasks()),
                "total_events": len(self.data_manager.load_events()),
                "day_name": datetime.now().strftime("%A")
            }
            
            # Formatear para el prompt
            context_text = f"""CONTEXTO DEL USUARIO:
Hora actual: {context['current_time']['time']}
Fecha: {context['current_time']['date']} ({context['day_name']})

TAREAS PRÓXIMAS ({len(context['upcoming_tasks'])}):
"""
            
            for i, task in enumerate(context['upcoming_tasks'], 1):
                priority = task.get('priority', 'media').capitalize()
                due_date = task.get('due_date', 'Sin fecha')
                context_text += f"{i}. {task.get('title', 'Sin título')} - Prioridad: {priority} - Para: {due_date}\n"
            
            context_text += f"\nEVENTOS DE HOY ({len(context['today_events'])}):\n"
            for i, event in enumerate(context['today_events'], 1):
                time_range = f"{event.get('start_time', '?')}-{event.get('end_time', '?')}"
                context_text += f"{i}. {event.get('title', 'Sin título')} a las {time_range}"
                if event.get('location'):
                    context_text += f" en {event.get('location')}"
                context_text += "\n"
            
            context_text += f"\nRECORDATORIOS URGENTES ({len(context['urgent_reminders'])}):\n"
            for i, reminder in enumerate(context['urgent_reminders'], 1):
                context_text += f"{i}. {reminder.get('title', 'Sin título')} - {reminder.get('date_time', 'Sin hora')}\n"
            
            return context_text
        except Exception as e:
            print(f"❌ Error obteniendo contexto: {e}")
            return "CONTEXTO: No se pudieron cargar los datos del usuario."
    
    def generate_response(self, user_query):
        """Generar respuesta con contexto de la aplicación"""
        if not self.model:
            return "Lo siento, no puedo conectarme con la IA en este momento."
        
        try:
            # Obtener datos de contexto
            context_data = self.get_context_data()
            
            # Crear prompt con contexto
            system_prompt = f"""Eres "Asistente", un asistente virtual personal integrado con una aplicación de gestión de tareas, eventos y recordatorios.
            
{context_data}

INSTRUCCIONES:
1. Eres útil, amigable y hablas en español de manera natural
2. Usa los datos del contexto para responder preguntas sobre tareas, eventos y recordatorios
3. Si el usuario pregunta sobre su día, agenda o próximas actividades, usa la información del contexto
4. Sé conciso pero informativo
5. Si no hay información relevante en el contexto, di que no hay nada programado o pregunta si quiere agregar algo
6. IMPORTANTE: Siempre responde en español y en un tono natural como si estuvieras hablando

FORMATO DE RESPUESTA:
- Respuesta hablada natural
- Incluye información relevante del contexto cuando sea apropiado
- No menciones explícitamente que estás usando datos del contexto"""
            
            full_prompt = f"{system_prompt}\n\nUsuario: {user_query}\n\nAsistente:"
            
            response = self.model.generate_content(
                full_prompt,
                generation_config={
                    "temperature": 0.7,
                    "top_p": 0.8,
                    "top_k": 40,
                    "max_output_tokens": 500,
                }
            )
            
            return response.text
            
        except Exception as e:
            error_msg = f"Lo siento, hubo un error al procesar tu solicitud: {str(e)[:100]}"
            print(f"❌ Error Gemini: {e}")
            return error_msg

class VoiceAssistantWindow(QMainWindow):
    """Ventana principal del asistente de voz"""
    
    def __init__(self):
        super().__init__()
        
        # Inicializar gestores
        self.data_manager = DataManager()
        self.gemini = GeminiAI(self.data_manager)
        
        # Configurar voz
        self.tts_engine = None
        self.setup_tts()
        
        # Configurar escucha
        self.listening_thread = None
        self.command_queue = queue.Queue()
        
        # Interfaz
        self.setup_ui()
        
        # Iniciar hilo de escucha
        self.start_listening()
        
        # Timer para procesar comandos
        self.command_timer = QTimer()
        self.command_timer.timeout.connect(self.process_commands)
        self.command_timer.start(100)  # Revisar cada 100ms
    
    def setup_tts(self):
        """Configurar texto a voz"""
        try:
            self.tts_engine = pyttsx3.init()
            
            # Configurar voz en español
            voices = self.tts_engine.getProperty('voices')
            spanish_voice = None
            
            for voice in voices:
                if 'spanish' in voice.name.lower() or 'español' in voice.name.lower():
                    spanish_voice = voice.id
                    break
            
            if spanish_voice:
                self.tts_engine.setProperty('voice', spanish_voice)
                print(f"✅ Voz configurada")
            
            # Configurar velocidad y volumen
            self.tts_engine.setProperty('rate', 150)
            self.tts_engine.setProperty('volume', 0.9)
            
            print("✅ TTS configurado")
            
        except Exception as e:
            print(f"❌ Error configurando TTS: {e}")
    
    def speak(self, text):
        """Hablar texto"""
        if not self.tts_engine:
            return
        
        # Limpiar texto
        clean_text = text.replace('*', '').replace('`', '').replace('#', '')
        
        # Usar hilo para no bloquear
        def speak_thread():
            try:
                self.tts_engine.say(clean_text)
                self.tts_engine.runAndWait()
            except Exception as e:
                print(f"❌ Error en hilo de TTS: {e}")
        
        thread = threading.Thread(target=speak_thread, daemon=True)
        thread.start()
    
    def setup_ui(self):
        """Configurar interfaz"""
        self.setWindowTitle("🎤 Asistente de Voz")
        self.setGeometry(100, 100, 600, 500)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Título
        title = QLabel("🎤 Asistente de Voz Continuo")
        title.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 22px;
                font-weight: bold;
                padding: 10px;
                background-color: #4285f4;
                border-radius: 10px;
            }
        """)
        title.setAlignment(Qt.AlignCenter)
        
        # Estado
        self.status_label = QLabel("🟢 Escuchando... Di 'Asistente'")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #34a853;
                font-size: 16px;
                padding: 15px;
                background-color: rgba(52, 168, 83, 0.2);
                border-radius: 10px;
                border: 2px solid #34a853;
            }
        """)
        self.status_label.setAlignment(Qt.AlignCenter)
        
        # Indicador de actividad
        self.activity_indicator = QLabel("●")
        self.activity_indicator.setStyleSheet("""
            QLabel {
                color: #ea4335;
                font-size: 30px;
                font-weight: bold;
            }
        """)
        self.activity_indicator.setAlignment(Qt.AlignCenter)
        self.activity_indicator.setVisible(False)
        
        # Área de log
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setPlaceholderText("Aquí aparecerán las conversaciones...")
        self.log_area.setStyleSheet("""
            QTextEdit {
                background-color: #2d2e31;
                color: #e8eaed;
                border: 1px solid #3c4043;
                border-radius: 10px;
                padding: 15px;
                font-size: 13px;
            }
        """)
        
        # Panel de información
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background-color: #292a2d;
                border: 1px solid #3c4043;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        
        info_layout = QVBoxLayout(info_frame)
        
        info_title = QLabel("📊 Información del Sistema")
        info_title.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 14px;")
        
        self.info_label = QLabel("Cargando información...")
        self.info_label.setStyleSheet("color: #9aa0a6; font-size: 12px;")
        self.info_label.setWordWrap(True)
        
        info_layout.addWidget(info_title)
        info_layout.addWidget(self.info_label)
        
        # Botones
        button_layout = QHBoxLayout()
        
        self.toggle_btn = QPushButton("⏸️ Pausar")
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.clicked.connect(self.toggle_listening)
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #4285f4;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3367d6;
            }
        """)
        
        test_btn = QPushButton("🎤 Probar")
        test_btn.clicked.connect(self.test_microphone)
        
        refresh_btn = QPushButton("🔄 Actualizar")
        refresh_btn.clicked.connect(self.update_info)
        
        clear_btn = QPushButton("🗑️ Limpiar")
        clear_btn.clicked.connect(self.clear_log)
        
        button_layout.addWidget(self.toggle_btn)
        button_layout.addWidget(test_btn)
        button_layout.addWidget(refresh_btn)
        button_layout.addWidget(clear_btn)
        
        layout.addWidget(title)
        layout.addWidget(self.status_label)
        layout.addWidget(self.activity_indicator)
        layout.addWidget(self.log_area, 2)
        layout.addWidget(info_frame)
        layout.addLayout(button_layout)
        
        # Actualizar información inicial
        self.update_info()
    
    def start_listening(self):
        """Iniciar hilo de escucha"""
        self.listening_thread = ListeningThread()
        self.listening_thread.heard_text.connect(self.handle_voice_input)
        self.listening_thread.listening_state.connect(self.update_activity_indicator)
        self.listening_thread.error_occurred.connect(self.show_error)
        self.listening_thread.start()
        
        self.add_to_log("✅ Escucha iniciada - Di 'Asistente' para activar")
    
    def handle_voice_input(self, text):
        """Manejar entrada de voz"""
        self.command_queue.put(text)
        self.add_to_log(f"🎤 Detectado: {text}")
    
    def process_commands(self):
        """Procesar comandos en cola"""
        if not self.command_queue.empty():
            command = self.command_queue.get()
            self.process_command(command)
    
    def process_command(self, command):
        """Procesar un comando específico"""
        try:
            # Extraer el comando después de "asistente"
            if "asistente" in command:
                # Remover la palabra clave y limpiar
                query = command.replace("asistente", "").strip()
                
                if not query:
                    response = "¿Sí? ¿En qué puedo ayudarte?"
                    self.speak(response)
                    self.add_to_log(f"🤖 Asistente: {response}")
                else:
                    # Actualizar estado
                    self.status_label.setText("🤖 Procesando...")
                    
                    # Obtener respuesta de Gemini
                    response = self.gemini.generate_response(query)
                    
                    # Hablar respuesta
                    self.speak(response)
                    
                    # Agregar al log
                    self.add_to_log(f"🤖 Asistente: {response}")
                    
                    # Actualizar información del sistema
                    self.update_info()
                
                # Restaurar estado normal
                QTimer.singleShot(2000, lambda: self.status_label.setText("🟢 Escuchando... Di 'Asistente'"))
                
        except Exception as e:
            error_msg = f"Error procesando comando: {e}"
            print(error_msg)
            self.add_to_log(f"❌ Error: {error_msg}")
    
    def update_activity_indicator(self, is_listening):
        """Actualizar indicador de actividad"""
        self.activity_indicator.setVisible(is_listening)
    
    def toggle_listening(self, paused):
        """Pausar/reanudar escucha"""
        if paused:
            if self.listening_thread:
                self.listening_thread.running = False
            self.status_label.setText("⏸️ Escucha pausada")
            self.status_label.setStyleSheet("""
                QLabel {
                    color: #fbbc04;
                    font-size: 16px;
                    padding: 15px;
                    background-color: rgba(251, 188, 4, 0.2);
                    border-radius: 10px;
                    border: 2px solid #fbbc04;
                }
            """)
            self.toggle_btn.setText("▶️ Reanudar")
            self.add_to_log("⏸️ Escucha pausada")
        else:
            if self.listening_thread:
                self.listening_thread.running = True
            self.status_label.setText("🟢 Escuchando... Di 'Asistente'")
            self.status_label.setStyleSheet("""
                QLabel {
                    color: #34a853;
                    font-size: 16px;
                    padding: 15px;
                    background-color: rgba(52, 168, 83, 0.2);
                    border-radius: 10px;
                    border: 2px solid #34a853;
                }
            """)
            self.toggle_btn.setText("⏸️ Pausar")
            self.add_to_log("▶️ Escucha reanudada")
    
    def add_to_log(self, text):
        """Agregar texto al log"""
        timestamp = QDateTime.currentDateTime().toString("hh:mm:ss")
        log_text = f"[{timestamp}] {text}"
        
        # Agregar al área de texto
        self.log_area.append(log_text)
        
        # Desplazar hacia abajo
        self.log_area.verticalScrollBar().setValue(
            self.log_area.verticalScrollBar().maximum()
        )
    
    def clear_log(self):
        """Limpiar el área de log"""
        self.log_area.clear()
        self.add_to_log("🗑️ Log limpiado")
    
    def test_microphone(self):
        """Probar el micrófono"""
        try:
            self.add_to_log("🔊 Probando micrófono... Habla algo")
            
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                audio = recognizer.listen(source, timeout=3)
                text = recognizer.recognize_google(audio, language='es-ES')
                
                self.add_to_log(f"✅ Reconocido: {text}")
                self.speak(f"Te escuché decir: {text}")
                
        except sr.WaitTimeoutError:
            self.add_to_log("❌ No se detectó voz")
        except Exception as e:
            self.add_to_log(f"❌ Error: {e}")
    
    def update_info(self):
        """Actualizar información del sistema"""
        try:
            tasks = self.data_manager.get_upcoming_tasks(3)
            events = self.data_manager.get_today_events()
            reminders = self.data_manager.get_urgent_reminders()
            time_info = self.data_manager.get_current_time_info()
            
            info_text = f"""
            🕒 Hora: {time_info['time']} | 📅 Fecha: {time_info['date']}
            📋 Tareas próximas: {len(tasks)} | 📅 Eventos hoy: {len(events)}
            🔔 Recordatorios urgentes: {len(reminders)}
            
            Ejemplos de comandos:
            • "Asistente, ¿qué tengo que hacer hoy?"
            • "Asistente, dime mi próxima tarea"
            • "Asistente, ¿qué eventos tengo?"
            • "Asistente, ¿hay algo urgente?"
            • "Asistente, dime la hora"
            """
            
            self.info_label.setText(info_text)
            
        except Exception as e:
            self.info_label.setText(f"Error cargando información: {e}")
    
    def show_error(self, error_msg):
        """Mostrar error"""
        self.add_to_log(f"❌ {error_msg}")
        QMessageBox.warning(self, "Error", error_msg)
    
    def closeEvent(self, event):
        """Manejar cierre de ventana"""
        if self.listening_thread:
            self.listening_thread.stop()
        
        reply = QMessageBox.question(
            self, 'Cerrar Asistente',
            '¿Seguro que quieres cerrar el asistente de voz?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()

def main():
    """Función principal"""
    app = QApplication(sys.argv)
    app.setApplicationName("Asistente de Voz")
    app.setOrganizationName("Asistente Personal")
    
    # Estilo oscuro
    app.setStyle("Fusion")
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
    dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
    dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))
    app.setPalette(dark_palette)
    
    window = VoiceAssistantWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()