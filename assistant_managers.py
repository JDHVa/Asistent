"""
Gestores centralizados para Gemini AI y voz - VERSIÓN COMPATIBLE
"""
import os
import threading
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Intentar importar bibliotecas con manejo de errores
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️ Google Generative AI no disponible. Instala: pip install google-generativeai")

try:
    # Intentar importar speech_recognition sin forzar pyaudio
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
    print("⚠️ SpeechRecognition no disponible")

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    print("⚠️ pyttsx3 no disponible")

class GeminiManager:
    """Gestor para interactuar con Gemini AI"""
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "AIzaSyAm9tYSXoKQfqIBGb_5bWJXcu6r0-Oridk")
        self.model = None
        self.conversation_history = []
        self.initialize_gemini()
        
    def initialize_gemini(self):
        """Inicializar Gemini AI"""
        try:
            if not GEMINI_AVAILABLE:
                print("⚠️ google.generativeai no está instalado")
                return False
                
            if not self.api_key:
                print("⚠️ No se encontró API key para Gemini")
                return False
                
            genai.configure(api_key=self.api_key)
            
            # Usar modelos disponibles
            try:
                # Intentar con el modelo más reciente primero
                self.model = genai.GenerativeModel('gemini-2.5-flash')
                print("✅ Modelo Gemini 'gemini-2.5-flash' inicializado")
                return True
            except Exception as e:
                print(f"⚠️ Error con flash: {e}")
                try:
                    self.model = genai.GenerativeModel('gemini-pro')
                    print("✅ Modelo Gemini 'gemini-pro' inicializado")
                    return True
                except Exception as e2:
                    print(f"❌ Error con pro: {e2}")
                    return False
                    
        except Exception as e:
            print(f"❌ Error crítico al inicializar Gemini: {e}")
            return False
    
    def send_message(self, message, system_prompt=None):
        """Enviar mensaje a Gemini y obtener respuesta"""
        if not self.model:
            return "❌ Error: Gemini AI no está configurado."
        
        try:
            # Agregar contexto del sistema si se proporciona
            if system_prompt:
                full_prompt = f"{system_prompt}\n\nUsuario: {message}"
            else:
                full_prompt = message
            
            # Configurar parámetros
            generation_config = {
                "temperature": 0.7,
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 1024,
            }
            
            # Enviar mensaje con historial
            chat = self.model.start_chat(history=self.conversation_history)
            response = chat.send_message(
                full_prompt,
                generation_config=generation_config
            )
            
            # Guardar en historial
            self.conversation_history.append({"role": "user", "parts": [full_prompt]})
            self.conversation_history.append({"role": "model", "parts": [response.text]})
            
            # Limitar historial
            if len(self.conversation_history) > 10:
                self.conversation_history = self.conversation_history[-10:]
            
            return response.text
            
        except Exception as e:
            error_msg = f"❌ Error con Gemini AI: {str(e)}"
            print(error_msg)
            return error_msg
    
    def analyze_schedule(self, events, current_time=None):
        """Analizar horario y dar recomendaciones"""
        if not events:
            return "No tienes eventos programados para hoy. ¡Es un buen día para planificar algo nuevo!"
        
        # Formatear eventos
        events_text = ""
        for i, event in enumerate(events, 1):
            events_text += f"{i}. {event['title']} - {event['start_time']} a {event['end_time']}"
            if event.get('location'):
                events_text += f" en {event['location']}"
            events_text += "\n"
        
        prompt = f"""Analiza este horario y da recomendaciones útiles:

Eventos del día:
{events_text}

Hora actual: {current_time if current_time else 'No especificada'}

Como asistente personal responde brevemente , proporciona:
1. Un resumen amigable del día
2. Sugerencias para optimizar el tiempo
3. Recordatorios importantes
4. Un mensaje motivacional breve

Responde en español, de manera natural y positiva."""
        
        return self.send_message(prompt, "Eres un asistente personal organizado y motivador.")
    
    def analyze_tasks(self, tasks):
        """Analizar tareas pendientes"""
        pending_tasks = [t for t in tasks if not t['completed']]
        completed_tasks = [t for t in tasks if t['completed']]
        
        if not pending_tasks:
            return "¡Excelente! No tienes tareas pendientes. ¡Buen trabajo!"
        
        tasks_text = ""
        for i, task in enumerate(pending_tasks[:5], 1):
            priority_icon = "🔥" if task['priority'] == 'high' else "⚠️" if task['priority'] == 'medium' else "📌"
            tasks_text += f"{i}. {priority_icon} {task['title']}"
            if task.get('due_date'):
                tasks_text += f" (para el {task['due_date']})"
            tasks_text += "\n"
        
        prompt = f"""Analiza estas tareas pendientes:

Tareas pendientes ({len(pending_tasks)}):
{tasks_text}

Tareas completadas: {len(completed_tasks)}

Como asistente de productividad responde brevemente, proporciona:
1. Priorización de tareas
2. Sugerencias para ser más eficiente
3. Motivación para completar las tareas
4. Consejos para evitar la procrastinación

Responde en español, de manera práctica y alentadora."""
        
        return self.send_message(prompt, "Eres un coach de productividad experto.")
    
    def clear_history(self):
        """Limpiar historial de conversación"""
        self.conversation_history = []

class VoiceManager:
    """Gestor para funcionalidades de voz - Versión compatible"""
    
    def __init__(self):
        self.recognizer = None
        self.microphone = None
        self.tts_engine = None
        self.microphone_available = False
        self.tts_available = False
        self.initialize_voice()
        
    def initialize_voice(self):
        """Inicializar componentes de voz con manejo robusto de errores"""
        # Inicializar TTS (siempre intentar)
        self.initialize_tts()
        
        # Inicializar reconocimiento de voz (opcional)
        self.initialize_speech_recognition()
        
        print(f"✅ Estado de voz - TTS: {'✅' if self.tts_available else '❌'}, Micrófono: {'✅' if self.microphone_available else '❌'}")
    
    def initialize_tts(self):
        """Inicializar texto a voz"""
        try:
            if not TTS_AVAILABLE:
                print("⚠️ pyttsx3 no está disponible")
                return
            
            self.tts_engine = pyttsx3.init()
            
            # Configurar propiedades
            try:
                # Buscar voces en español
                voices = self.tts_engine.getProperty('voices')
                for voice in voices:
                    if 'spanish' in voice.name.lower() or 'español' in voice.name.lower():
                        self.tts_engine.setProperty('voice', voice.id)
                        print(f"✅ Voz configurada: {voice.name}")
                        break
            except:
                print("⚠️ Usando voz por defecto")
            
            # Configurar velocidad y volumen
            self.tts_engine.setProperty('rate', 150)
            self.tts_engine.setProperty('volume', 0.9)
            
            self.tts_available = True
            print("✅ TTS inicializado correctamente")
            
        except Exception as e:
            print(f"❌ Error al inicializar TTS: {e}")
            self.tts_available = False
    
    def initialize_speech_recognition(self):
        """Inicializar reconocimiento de voz"""
        try:
            if not SPEECH_RECOGNITION_AVAILABLE:
                print("⚠️ SpeechRecognition no disponible")
                return
            
            self.recognizer = sr.Recognizer()
            
            # Intentar detectar micrófono SIN usar distutils
            try:
                # Listar micrófonos disponibles
                print("🔍 Buscando micrófonos...")
                
                # Método alternativo sin depender de pyaudio
                import sys
                if sys.platform == 'win32':
                    # En Windows, intentar con un índice específico
                    try:
                        self.microphone = sr.Microphone(device_index=0)
                        self.microphone_available = True
                        print("✅ Micrófono detectado (Windows)")
                    except:
                        print("⚠️ No se pudo acceder al micrófono en Windows")
                else:
                    # En Linux/Mac, intentar de otra forma
                    try:
                        self.microphone = sr.Microphone()
                        self.microphone_available = True
                        print("✅ Micrófono detectado")
                    except Exception as mic_error:
                        print(f"⚠️ Error con micrófono: {mic_error}")
                        
            except Exception as e:
                print(f"⚠️ No se pudo inicializar micrófono: {e}")
                print("💡 Solución: Instala pyaudio o usa entrada de texto")
                
        except Exception as e:
            print(f"❌ Error al inicializar reconocimiento de voz: {e}")
    
    def speak(self, text):
        """Convertir texto a voz"""
        if not self.tts_available or not self.tts_engine:
            print("⚠️ TTS no disponible para hablar")
            return False
        
        try:
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
            return True
            
        except Exception as e:
            print(f"❌ Error al hablar: {e}")
            return False
    
    def listen(self):
        """Escuchar voz del usuario"""
        if not self.microphone_available or not self.recognizer or not self.microphone:
            return "❌ Micrófono no disponible"
        
        try:
            with self.microphone as source:
                print("🎤 Escuchando... (habla ahora)")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            print("🔍 Procesando...")
            text = self.recognizer.recognize_google(audio, language='es-ES')
            print(f"✅ Reconocido: {text}")
            return text
            
        except sr.WaitTimeoutError:
            return "⏱️ Tiempo agotado"
        except sr.UnknownValueError:
            return "❌ No se entendió el audio"
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def recognize_speech(self):
        """Alias para compatibilidad"""
        return self.listen()
    
    def is_microphone_available(self):
        """Verificar si el micrófono está disponible"""
        return self.microphone_available
    
    def is_tts_available(self):
        """Verificar si TTS está disponible"""
        return self.tts_available

# Instancias globales
gemini_manager = GeminiManager()
voice_manager = VoiceManager()