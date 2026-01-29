import sys
import os
import json
import threading
import queue
import time
from datetime import datetime, timedelta
from PySide6.QtCore import QObject, Signal, QTimer, QThread
from PySide6.QtWidgets import QApplication
import speech_recognition as sr
import pyttsx3
import google.generativeai as genai
from dotenv import load_dotenv

try:
    from database_manager import get_database
except ImportError:
    pass

load_dotenv()

class GlobalDataManager:
    """Gestor de datos global para el asistente con conexión a BD"""
    
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        self.ensure_data_directory()
        
        self.db = None
        if user_id:
            self.connect_database()
        
        self.callbacks = {
            'get_tasks': None,
            'get_events': None,
            'get_reminders': None,
            'get_current_panel': None
        }
    
    def connect_database(self):
        try:
            self.db = get_database()
            if self.user_id:
                self.db.set_current_user(self.user_id)
            print(f"Base de datos conectada para usuario: {self.user_id}")
            return True
        except Exception as e:
            print(f"Error conectando a BD: {e}")
            return False
    
    def set_user_id(self, user_id):
        self.user_id = user_id
        if self.db:
            self.db.set_current_user(user_id)
    
    def ensure_data_directory(self):
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def register_callbacks(self, callbacks):
        self.callbacks.update(callbacks)
    
    def get_current_time_info(self):
        now = datetime.now()
        return {
            "date": now.strftime("%d/%m/%Y"),
            "time": now.strftime("%H:%M"),
            "day_name": now.strftime("%A"),
            "hour": now.hour,
            "minute": now.minute,
            "weekday": now.weekday(), 
            "is_weekend": now.weekday() >= 5
        }
    
    def get_context_data(self):
        context = {
            "current_time": self.get_current_time_info(),
            "current_panel": "Desconocido",
            "user_id": self.user_id,
            "has_database": self.db is not None
        }
        
        database_data = self.get_database_context()
        context.update(database_data)
        
        try:
            if self.callbacks['get_current_panel']:
                context["current_panel"] = self.callbacks['get_current_panel']()
            
            if self.callbacks['get_tasks']:
                try:
                    tasks = self.callbacks['get_tasks']()
                    if tasks and len(tasks) > 0:
                        context["tasks_from_panel"] = tasks[:5]
                except:
                    pass
            
            if self.callbacks['get_events']:
                try:
                    events = self.callbacks['get_events']()
                    if events and len(events) > 0:
                        context["events_from_panel"] = events[:5]
                except:
                    pass
            
            if self.callbacks['get_reminders']:
                try:
                    reminders = self.callbacks['get_reminders']()
                    if reminders and len(reminders) > 0:
                        context["reminders_from_panel"] = reminders[:5]
                except:
                    pass
                
        except Exception as e:
            print(f"Error obteniendo contexto de callbacks: {e}")
        
        return context
    
    def get_database_context(self):

        database_context = {
            "database_tasks": [],
            "database_events": [],
            "database_reminders": [],
            "database_has_data": False
        }
        
        if not self.db or not self.user_id:
            return database_context
        
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            next_week = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
            
            try:
                tasks = self.db.get_tasks()
                if tasks:
                    pending_tasks = [t for t in tasks if not t.get('completed', False)]
                    overdue_tasks = [t for t in pending_tasks if t.get('due_date', '') < today]
                    
                    database_context["database_tasks"] = {
                        "total": len(tasks),
                        "pending": len(pending_tasks),
                        "completed": len(tasks) - len(pending_tasks),
                        "overdue": len(overdue_tasks),
                        "pending_list": pending_tasks[:5]
                    }
            except Exception as e:
                print(f"Error obteniendo tareas de BD: {e}")
            
            try:
                events = self.db.get_events(today, next_week)
                if events:
                    database_context["database_events"] = {
                        "total": len(events),
                        "today": [e for e in events if e.get('start_date', '') == today],
                        "upcoming": events[:5]
                    }
            except Exception as e:
                print(f"Error obteniendo eventos de BD: {e}")
            
            try:
                reminders = self.db.get_reminders()
                if reminders:
                    active_reminders = [r for r in reminders if r.get('active', True) and not r.get('completed', False)]
                    
                    database_context["database_reminders"] = {
                        "total": len(reminders),
                        "active": len(active_reminders),
                        "active_list": active_reminders[:5]
                    }
            except Exception as e:
                print(f"Error obteniendo recordatorios de BD: {e}")
            
            database_context["database_has_data"] = (
                len(database_context["database_tasks"]) > 0 or
                len(database_context["database_events"]) > 0 or
                len(database_context["database_reminders"]) > 0
            )
            
        except Exception as e:
            print(f"Error general obteniendo contexto de BD: {e}")
        
        return database_context
    
    def get_user_info(self):
        if not self.db or not self.user_id:
            return {"name": "Usuario", "email": None}
        
        try:
            user = self.db.get_user(self.user_id)
            if user:
                return {
                    "name": user.get('name', 'Usuario'),
                    "email": user.get('email'),
                    "created_at": user.get('created_at'),
                    "last_login": user.get('last_login')
                }
        except Exception as e:
            print(f"Error obteniendo info de usuario: {e}")
        
        return {"name": "Usuario", "email": None}

class GlobalGeminiAI:
    
    def __init__(self, data_manager, user_name="Usuario"):
        self.api_key = os.getenv("GEMINI_API_KEY", "YOUR GEMINI APYT KEY")
        self.model = None
        self.data_manager = data_manager
        self.user_name = user_name
        self.initialize()
    
    def initialize(self):
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            print("Gemini AI global inicializado")
            return True
        except Exception as e:
            print(f"Error inicializando Gemini global: {e}")
            return False
    
    def generate_response(self, user_query):
        if not self.model:
            return f"Lo siento {self.user_name}, no puedo conectarme con la IA en este momento."
        
        try:
            context_data = self.data_manager.get_context_data()
            user_info = self.data_manager.get_user_info()
            
            if user_info.get('name') and user_info['name'] != 'Usuario':
                self.user_name = user_info['name']
            
            context_text = f"""CONTEXTO DE {self.user_name.upper()}:
                Hora actual: {context_data['current_time']['time']}
                Fecha: {context_data['current_time']['date']} ({context_data['current_time']['day_name']})
                Panel actual: {context_data['current_panel']}

            """
            
            if isinstance(context_data.get('database_tasks'), dict):
                tasks_info = context_data['database_tasks']
                if tasks_info.get('pending', 0) > 0:
                    context_text += f"TAREAS PENDIENTES ({tasks_info['pending']}):\n"
                    pending_list = tasks_info.get('pending_list', [])
                    for i, task in enumerate(pending_list[:5], 1):
                        title = task.get('title', 'Sin título')
                        due_date = task.get('due_date', 'Sin fecha')
                        category = task.get('category', 'Sin categoría')
                        context_text += f"{i}. {title} ({category}) - Vence: {due_date}\n"
            elif context_data.get('tasks_from_panel'):
                tasks = context_data['tasks_from_panel'][:3]
                context_text += f"TAREAS PENDIENTES ({len(tasks)}):\n"
                for i, task in enumerate(tasks, 1):
                    title = task.get('title', 'Sin título')
                    context_text += f"{i}. {title}\n"
            
            if isinstance(context_data.get('database_events'), dict):
                events_info = context_data['database_events']
                upcoming_events = events_info.get('upcoming', [])
                if upcoming_events:
                    context_text += f"\nEVENTOS PRÓXIMOS ({len(upcoming_events)}):\n"
                    for i, event in enumerate(upcoming_events[:5], 1):
                        title = event.get('title', 'Sin título')
                        date = event.get('start_date', '?')
                        time = event.get('start_time', '?')
                        context_text += f"{i}. {title} - {date} a las {time}\n"
            elif context_data.get('events_from_panel'):
                events = context_data['events_from_panel'][:3]
                context_text += f"\nEVENTOS PRÓXIMOS ({len(events)}):\n"
                for i, event in enumerate(events, 1):
                    title = event.get('title', 'Sin título')
                    context_text += f"{i}. {title}\n"
            
            if isinstance(context_data.get('database_reminders'), dict):
                reminders_info = context_data['database_reminders']
                active_list = reminders_info.get('active_list', [])
                if active_list:
                    context_text += f"\nRECORDATORIOS ACTIVOS ({len(active_list)}):\n"
                    for i, reminder in enumerate(active_list[:5], 1):
                        title = reminder.get('title', 'Sin título')
                        date_time = reminder.get('date_time', '?')
                        context_text += f"{i}. {title} - {date_time}\n"
            elif context_data.get('reminders_from_panel'):
                reminders = context_data['reminders_from_panel'][:3]
                context_text += f"\nRECORDATORIOS ACTIVOS ({len(reminders)}):\n"
                for i, reminder in enumerate(reminders, 1):
                    title = reminder.get('title', 'Sin título')
                    context_text += f"{i}. {title}\n"
            
            if context_text == f"""CONTEXTO DE {self.user_name.upper()}:
                Hora actual: {context_data['current_time']['time']}
                Fecha: {context_data['current_time']['date']} ({context_data['current_time']['day_name']})
                Panel actual: {context_data['current_panel']}

            """:
                context_text += "No hay tareas, eventos o recordatorios programados para hoy.\n"
            
            system_prompt = f"""Eres "Asistente", un asistente virtual personal inteligente integrado en una aplicación de gestión.

            DATOS DEL USUARIO:
            Nombre: {self.user_name}
            Email: {user_info.get('email', 'No disponible')}
            Tiene base de datos: {'Sí' if context_data.get('has_database', False) else 'No'}

            {context_text}

            CAPACIDADES DE BASE DE DATOS:
            1. Puedo acceder a tus tareas, eventos y recordatorios almacenados
            2. Conozco tus fechas límite y compromisos
            3. Puedo hacer análisis de tu productividad
            4. Tengo información actualizada de tu agenda

            INSTRUCCIONES IMPORTANTES:
            1. Usa el nombre {self.user_name} en tus respuestas
            2. Sé útil, amigable y habla en español natural
            3. Usa los datos del contexto para dar respuestas personalizadas
            4. Si hay tareas atrasadas, sugiere priorizarlas
            5. Si hay eventos próximos, recuérdalos amablemente
            6. Ofrece consejos de productividad basados en los datos
            7. Si no hay datos, pregunta si quieres agregar alguno
            8. Mantén un tono positivo y motivacional

            FORMATO DE RESPUESTA:
            - Saludo personalizado usando {self.user_name}
            - Información relevante del contexto
            - Respuesta a la consulta específica
            - Sugerencia o consejo útil
            - Cierre motivacional"""
            
            full_prompt = f"{system_prompt}\n\n{self.user_name}: {user_query}\n\nAsistente:"
            
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
            error_msg = f"Lo siento {self.user_name}, hubo un error al procesar tu solicitud: {str(e)[:100]}"
            print(f"Error Gemini global: {e}")
            import traceback
            traceback.print_exc()
            return error_msg
    
    def analyze_productivity(self):
        if not self.model:
            return "No puedo analizar la productividad en este momento."
        
        context_data = self.data_manager.get_context_data()
        
        prompt = f"""Analiza la productividad de {self.user_name} basándote en estos datos:

        TAREAS:
        - Totales: {context_data.get('database_tasks', {}).get('total', 0)}
        - Pendientes: {context_data.get('database_tasks', {}).get('pending', 0)}
        - Completadas: {context_data.get('database_tasks', {}).get('completed', 0)}
        - Atrasadas: {context_data.get('database_tasks', {}).get('overdue', 0)}

        EVENTOS:
        - Próximos: {len(context_data.get('database_events', {}).get('upcoming', []))}

        RECORDATORIOS:
        - Activos: {context_data.get('database_reminders', {}).get('active', 0)}

        Proporciona un análisis breve con:
        1. Estado general de productividad
        2. Áreas de mejora
        3. Sugerencias específicas
        4. Un mensaje motivacional

        Responde en español de manera amigable."""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error en análisis: {str(e)}"

class GlobalVoiceAssistant(QObject):
    """Asistente de voz global que funciona en toda la aplicación"""
    
    command_received = Signal(str)      
    response_ready = Signal(str)        
    status_changed = Signal(str)       
    error_occurred = Signal(str)    
    database_connected = Signal(bool)  
    
    def __init__(self, user_id=None, user_name="Usuario"):
        super().__init__()
        
        # Guardar información del usuario
        self.user_id = user_id
        self.user_name = user_name
        
        # Inicializar componentes CON BASE DE DATOS
        self.data_manager = GlobalDataManager(user_id)
        self.gemini = GlobalGeminiAI(self.data_manager, user_name)
        
        # Configurar TTS
        self.tts_engine = None
        self.setup_tts()
        
        # Configurar reconocimiento de voz
        self.recognizer = None
        self.microphone = None
        self.setup_speech_recognition()
        
        # Estado
        self.is_listening = False
        self.keyword = "asistente"
        self.command_queue = queue.Queue()
        
        # Timer para procesamiento
        self.timer = QTimer()
        self.timer.timeout.connect(self.process_commands)
        self.timer.start(100)  # Procesar cada 100ms
        
        # Verificar conexión a BD
        if user_id and self.data_manager.db:
            print(f"Asistente global conectado a BD para usuario: {user_id}")
            self.database_connected.emit(True)
        else:
            print("Asistente global funcionando sin base de datos")
            self.database_connected.emit(False)
        
        # Iniciar escucha en hilo separado
        self.listening_thread = None
        self.running = True
        self.start_listening_thread()
        
        print(f"Asistente global inicializado para: {user_name} (ID: {user_id})")
    
    def update_user_info(self, user_id=None, user_name=None):
        if user_id:
            self.user_id = user_id
            self.data_manager.set_user_id(user_id)
            self.database_connected.emit(True)
        
        if user_name:
            self.user_name = user_name
            self.gemini.user_name = user_name
    
    def setup_tts(self):
        try:
            self.tts_engine = pyttsx3.init()
            
            voices = self.tts_engine.getProperty('voices')
            spanish_voice = None
            
            for voice in voices:
                if 'spanish' in voice.name.lower() or 'español' in voice.name.lower():
                    spanish_voice = voice.id
                    break
            
            if spanish_voice:
                self.tts_engine.setProperty('voice', spanish_voice)
            
            self.tts_engine.setProperty('rate', 150)
            self.tts_engine.setProperty('volume', 0.9)
            
            print("TTS global configurado")
            
        except Exception as e:
            print(f"Error configurando TTS global: {e}")
    
    def setup_speech_recognition(self):
        """Configurar reconocimiento de voz"""
        try:
            self.recognizer = sr.Recognizer()
            
            try:
                self.microphone = sr.Microphone(device_index=0)
                print("Micrófono global configurado")
            except:
                self.microphone = sr.Microphone()
                
        except Exception as e:
            print(f"Error configurando reconocimiento de voz global: {e}")
            self.error_occurred.emit(f"Error de micrófono: {e}")
    
    def speak(self, text):
        if not self.tts_engine:
            return
        
        def speak_thread():
            try:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            except Exception as e:
                print(f"Error en hilo de TTS global: {e}")
        
        thread = threading.Thread(target=speak_thread, daemon=True)
        thread.start()
    
    def start_listening_thread(self):
        def listen_loop():
            print("Asistente global escuchando...")
            
            while self.running:
                try:
                    with self.microphone as source:
                        self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                        
                        try:
                            audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=3)
                            
                            text = self.recognizer.recognize_google(audio, language='es-ES')
                            text = text.lower()
                            
                            if self.keyword in text:
                                print(f"Palabra clave detectada: {text}")
                                self.command_queue.put(text)
                                self.command_received.emit(text)
                                
                        except sr.WaitTimeoutError:
                            pass
                        except sr.UnknownValueError:
                            pass
                        except Exception as e:
                            if "exceptions must derive from BaseException" not in str(e):
                                print(f"Error en reconocimiento: {e}")
                    
                except Exception as e:
                    print(f"Error en bucle de escucha: {e}")
                    time.sleep(0.5)
        
        self.listening_thread = threading.Thread(target=listen_loop, daemon=True)
        self.listening_thread.start()
    
    def process_commands(self):
        if not self.command_queue.empty():
            command = self.command_queue.get()
            self.process_command(command)
    
    def process_command(self, command):
        try:
            if self.keyword in command:
                query = command.replace(self.keyword, "").strip()
                
                if not query:
                    response = "¿Sí? ¿En qué puedo ayudarte?"
                else:
                    if "productividad" in query.lower() or "análisis" in query.lower():
                        response = self.gemini.analyze_productivity()
                    elif "tareas" in query.lower() or "pendiente" in query.lower():
                        context = self.data_manager.get_context_data()
                        if context.get('database_tasks', {}).get('pending', 0) > 0:
                            response = f"{self.user_name}, tienes {context['database_tasks']['pending']} tareas pendientes. ¿Quieres que te las liste?"
                        else:
                            response = f"{self.user_name}, no tienes tareas pendientes. ¡Excelente trabajo!"
                    else:
                        response = self.gemini.generate_response(query)
                
                self.response_ready.emit(response)
                
                self.speak(response)
                
                print(f"Asistente global: {response[:50]}...")
                
        except Exception as e:
            error_msg = f"Error procesando comando: {e}"
            print(error_msg)
            self.error_occurred.emit(error_msg)
    
    def register_callbacks(self, callbacks):
        self.data_manager.register_callbacks(callbacks)
    
    def get_database_status(self):
        return self.data_manager.db is not None
    
    def stop(self):
        self.running = False
        if self.listening_thread:
            self.listening_thread.join(timeout=1)

global_assistant = None

def get_global_assistant(user_id=None, user_name="Usuario"):
    global global_assistant
    if global_assistant is None:
        global_assistant = GlobalVoiceAssistant(user_id, user_name)
    else:
        if user_id and global_assistant.user_id != user_id:
            global_assistant.update_user_info(user_id, user_name)
        elif user_name and global_assistant.user_name != user_name:
            global_assistant.update_user_info(None, user_name)

    return global_assistant
