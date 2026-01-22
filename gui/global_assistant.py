# global_assistant.py
import sys
import os
import json
import threading
import queue
import time
from datetime import datetime
from PySide6.QtCore import QObject, Signal, QTimer, QThread
from PySide6.QtWidgets import QApplication
import speech_recognition as sr
import pyttsx3
import google.generativeai as genai
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class GlobalDataManager:
    """Gestor de datos global para el asistente"""
    
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        self.ensure_data_directory()
        self.callbacks = {
            'get_tasks': None,
            'get_events': None,
            'get_reminders': None,
            'get_current_panel': None
        }
    
    def ensure_data_directory(self):
        """Asegurar que existe el directorio de datos"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def register_callbacks(self, callbacks):
        """Registrar callbacks para obtener datos de los paneles"""
        self.callbacks.update(callbacks)
    
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
    
    def get_context_data(self):
        """Obtener datos de contexto desde los paneles"""
        context = {
            "current_time": self.get_current_time_info(),
            "current_panel": "Desconocido"
        }
        
        # Obtener datos mediante callbacks si están disponibles
        try:
            if self.callbacks['get_current_panel']:
                context["current_panel"] = self.callbacks['get_current_panel']()
            
            if self.callbacks['get_tasks']:
                tasks = self.callbacks['get_tasks']()
                context["tasks"] = tasks
                context["pending_tasks"] = [t for t in tasks if not t.get('completed', False)][:3]
            
            if self.callbacks['get_events']:
                events = self.callbacks['get_events']()
                today = datetime.now().strftime("%Y-%m-%d")
                context["today_events"] = [e for e in events if e.get('date', '') == today][:3]
            
            if self.callbacks['get_reminders']:
                reminders = self.callbacks['get_reminders']()
                context["urgent_reminders"] = [
                    r for r in reminders 
                    if r.get('active', False) and not r.get('completed', False)
                ][:3]
                
        except Exception as e:
            print(f"⚠️ Error obteniendo contexto: {e}")
        
        return context

class GlobalGeminiAI:
    """IA para el asistente global"""
    
    def __init__(self, data_manager, user_name="Usuario"):  # ← Añadir parámetro con valor por defecto
        self.api_key = os.getenv("GEMINI_API_KEY", "AIzaSyAm9tYSXoKQfqIBGb_5bWJXcu6r0-Oridk")
        self.model = None
        self.data_manager = data_manager
        self.user_name = user_name  # ← Guardar nombre del usuario
        self.initialize()
    
    def initialize(self):
        """Inicializar Gemini AI"""
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            print("✅ Gemini AI global inicializado")
            return True
        except Exception as e:
            print(f"❌ Error inicializando Gemini global: {e}")
            return False
    
    def generate_response(self, user_query):
        """Generar respuesta con contexto global - MODIFICADO para usar nombre"""
        if not self.model:
            return f"Lo siento {self.user_name}, no puedo conectarme con la IA en este momento."
        
        try:
            # Obtener contexto global
            context_data = self.data_manager.get_context_data()
            
            # Formatear contexto para el prompt
            context_text = f"""CONTEXTO DE {self.user_name.upper()}:
                Hora actual: {context_data['current_time']['time']}
                Fecha: {context_data['current_time']['date']} ({context_data['current_time']['day_name']})
                Panel actual: {context_data['current_panel']}

            """
            
            # Añadir información de tareas si existe
            if 'pending_tasks' in context_data:
                context_text += f"TAREAS PENDIENTES ({len(context_data['pending_tasks'])}):\n"
                for i, task in enumerate(context_data['pending_tasks'], 1):
                    context_text += f"{i}. {task.get('title', 'Sin título')}\n"
            
            # Añadir eventos de hoy si existe
            if 'today_events' in context_data:
                context_text += f"\nEVENTOS DE HOY ({len(context_data['today_events'])}):\n"
                for i, event in enumerate(context_data['today_events'], 1):
                    context_text += f"{i}. {event.get('title', 'Sin título')} a las {event.get('start_time', '?')}\n"
            
            # Añadir recordatorios urgentes si existe
            if 'urgent_reminders' in context_data:
                context_text += f"\nRECORDATORIOS URGENTES ({len(context_data['urgent_reminders'])}):\n"
                for i, reminder in enumerate(context_data['urgent_reminders'], 1):
                    context_text += f"{i}. {reminder.get('title', 'Sin título')}\n"
            
            # Crear prompt PERSONALIZADO
            system_prompt = f"""Eres "Asistente", un asistente virtual personal que está integrado en una aplicación de gestión para {self.user_name}.

            {context_text}

            INSTRUCCIONES IMPORTANTES:
            1. Eres útil, amigable y hablas en español de manera natural
            2. SIEMPRE te refieres al usuario por su nombre: {self.user_name}
            3. Ejemplos de cómo dirigirte:
            - "Claro, {self.user_name}"
            - "Sí, {self.user_name}, te explico..."
            - "{self.user_name}, según lo que veo..."
            - "Por supuesto, {self.user_name}"
            - "{self.user_name}, tengo esa información para ti"
            4. Usa el contexto para responder preguntas sobre tareas, eventos y recordatorios
            5. Sé conciso pero informativo
            6. Si no hay información en el contexto, di que no hay nada programado
            7. Siempre responde en español y en un tono natural como si estuvieras hablando
            8. El usuario te activa diciendo "asistente" seguido de una pregunta
            9. NUNCA olvides usar el nombre del usuario ({self.user_name}) en tus respuestas

            FORMATO DE RESPUESTA:
            - Respuesta hablada natural
            - Incluye información relevante del contexto cuando sea apropiado
            - Usa el nombre {self.user_name} al menos una vez en cada respuesta
            - Sé breve y directo"""
            
            full_prompt = f"{system_prompt}\n\n{self.user_name}: {user_query}\n\nAsistente:"
            
            response = self.model.generate_content(
                full_prompt,
                generation_config={
                    "temperature": 0.7,
                    "top_p": 0.8,
                    "top_k": 40,
                    "max_output_tokens": 300,
                }
            )
            
            return response.text
            
        except Exception as e:
            error_msg = f"Lo siento {self.user_name}, hubo un error al procesar tu solicitud."
            print(f"❌ Error Gemini global: {e}")
            return error_msg

class GlobalVoiceAssistant(QObject):
    """Asistente de voz global que funciona en toda la aplicación"""
    
    # Señales
    command_received = Signal(str)      # Comando de voz recibido
    response_ready = Signal(str)        # Respuesta lista para mostrar/hablar
    status_changed = Signal(str)        # Cambio de estado
    error_occurred = Signal(str)        # Error
    
    def __init__(self, user_name="Usuario"):  # ← Añadir parámetro con valor por defecto
        super().__init__()
        
        # Guardar nombre del usuario
        self.user_name = user_name
        
        # Inicializar componentes
        self.data_manager = GlobalDataManager()
        self.gemini = GlobalGeminiAI(self.data_manager, user_name)  # ← Pasar el nombre
        
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
        
        # Iniciar escucha en hilo separado
        self.listening_thread = None
        self.running = True
        self.start_listening_thread()
        
        print(f"✅ Asistente global inicializado para: {user_name}")
    
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
            
            # Configurar velocidad y volumen
            self.tts_engine.setProperty('rate', 150)
            self.tts_engine.setProperty('volume', 0.9)
            
            print("✅ TTS global configurado")
            
        except Exception as e:
            print(f"❌ Error configurando TTS global: {e}")
    
    def setup_speech_recognition(self):
        """Configurar reconocimiento de voz"""
        try:
            self.recognizer = sr.Recognizer()
            
            # Intentar usar micrófono disponible
            try:
                self.microphone = sr.Microphone(device_index=0)
                print("✅ Micrófono global configurado")
            except:
                self.microphone = sr.Microphone()
                
        except Exception as e:
            print(f"❌ Error configurando reconocimiento de voz global: {e}")
            self.error_occurred.emit(f"Error de micrófono: {e}")
    
    def speak(self, text):
        """Hablar texto (no bloqueante)"""
        if not self.tts_engine:
            return
        
        def speak_thread():
            try:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            except Exception as e:
                print(f"❌ Error en hilo de TTS global: {e}")
        
        thread = threading.Thread(target=speak_thread, daemon=True)
        thread.start()
    
    def start_listening_thread(self):
        """Iniciar hilo de escucha continua"""
        def listen_loop():
            print("🔊 Asistente global escuchando...")
            
            while self.running:
                try:
                    with self.microphone as source:
                        # Ajustar para ruido ambiental
                        self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                        
                        try:
                            # Escuchar con timeout corto
                            audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=3)
                            
                            # Reconocer audio
                            text = self.recognizer.recognize_google(audio, language='es-ES')
                            text = text.lower()
                            
                            # Verificar palabra clave
                            if self.keyword in text:
                                print(f"✅ Palabra clave detectada: {text}")
                                self.command_queue.put(text)
                                self.command_received.emit(text)
                                
                        except sr.WaitTimeoutError:
                            pass
                        except sr.UnknownValueError:
                            pass
                        except Exception as e:
                            if "exceptions must derive from BaseException" not in str(e):
                                print(f"⚠️ Error en reconocimiento: {e}")
                    
                except Exception as e:
                    print(f"⚠️ Error en bucle de escucha: {e}")
                    time.sleep(0.5)
        
        self.listening_thread = threading.Thread(target=listen_loop, daemon=True)
        self.listening_thread.start()
    
    def process_commands(self):
        """Procesar comandos en cola"""
        if not self.command_queue.empty():
            command = self.command_queue.get()
            self.process_command(command)
    
    def process_command(self, command):
        """Procesar un comando específico"""
        try:
            # Extraer la consulta después de "asistente"
            if self.keyword in command:
                query = command.replace(self.keyword, "").strip()
                
                if not query:
                    response = "¿Sí? ¿En qué puedo ayudarte?"
                else:
                    # Obtener respuesta de Gemini
                    response = self.gemini.generate_response(query)
                
                # Emitir respuesta
                self.response_ready.emit(response)
                
                # Hablar la respuesta
                self.speak(response)
                
                print(f"🤖 Asistente global: {response[:50]}...")
                
        except Exception as e:
            error_msg = f"Error procesando comando: {e}"
            print(error_msg)
            self.error_occurred.emit(error_msg)
    
    def register_callbacks(self, callbacks):
        """Registrar callbacks para obtener datos de la aplicación"""
        self.data_manager.register_callbacks(callbacks)
    
    def stop(self):
        """Detener el asistente"""
        self.running = False
        if self.listening_thread:
            self.listening_thread.join(timeout=1)

# Instancia global única
global_assistant = None

def get_global_assistant(user_name="Usuario"):  # ← Añadir parámetro
    """Obtener la instancia global del asistente (singleton)"""
    global global_assistant
    if global_assistant is None:
        global_assistant = GlobalVoiceAssistant(user_name)  # ← Pasar el nombre
    else:
        # Si ya existe, podemos actualizar el nombre si es diferente
        global_assistant.user_name = user_name
        global_assistant.gemini.user_name = user_name
    return global_assistant