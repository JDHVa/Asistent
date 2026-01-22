"""
Gestores centralizados para Gemini AI y voz
"""
import os
import threading
from dotenv import load_dotenv
import google.generativeai as genai

# Cargar variables de entorno
load_dotenv()

# Intentar importar bibliotecas de voz
try:
    import speech_recognition as sr
    import pyttsx3
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False
    print("⚠️ Dependencias de voz no disponibles. Instala: pip install SpeechRecognition pyttsx3")

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
            if not self.api_key:
                print("⚠️ Advertencia: No se encontró API key para Gemini")
                return False
                
            genai.configure(api_key=self.api_key)
            
            # Usar el modelo flash (más rápido)
            model_name = "gemini-2.5-flash"
            try:
                self.model = genai.GenerativeModel(model_name)
                print(f"✅ Modelo Gemini '{model_name}' inicializado correctamente")
                return True
            except Exception as e:
                print(f"⚠️ Error con modelo flash: {e}")
                # Intentar con otro modelo
                try:
                    self.model = genai.GenerativeModel('gemini-pro')
                    print("✅ Modelo Gemini 'gemini-pro' inicializado correctamente")
                    return True
                except Exception as e2:
                    print(f"❌ Error al inicializar Gemini: {e2}")
                    return False
                    
        except Exception as e:
            print(f"❌ Error crítico al inicializar Gemini: {e}")
            return False
    
    def send_message(self, message, system_prompt=None):
        """Enviar mensaje a Gemini y obtener respuesta"""
        if not self.model:
            return "❌ Error: Gemini AI no está configurado correctamente."
        
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
            
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            ]
            
            # Enviar mensaje con historial
            chat = self.model.start_chat(history=self.conversation_history)
            response = chat.send_message(
                full_prompt,
                generation_config=generation_config,
                safety_settings=safety_settings
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

Como asistente personal, proporciona:
1. Un resumen amigable del día
2. Sugerencias para optimizar el tiempo
3. Recordatorios importantes
4. Un mensaje motivacional breve
5. Resumelo de la forma mas breve posible

Responde en español, de manera natural y positiva
"""
        
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

Como asistente de productividad, proporciona:
1. Priorización de tareas
2. Sugerencias para ser más eficiente
3. Motivación para completar las tareas
4. Consejos para evitar la procrastinación
5. Resumelo de la forma mas breve posible

Responde en español, de manera práctica y alentadora."""
        
        return self.send_message(prompt, "Eres un coach de productividad experto.")
    
    def clear_history(self):
        """Limpiar historial de conversación"""
        self.conversation_history = []

class VoiceManager:
    """Gestor para funcionalidades de voz"""
    
    def __init__(self):
        self.recognizer = None
        self.microphone = None
        self.tts_engine = None
        self.available = False
        self.initialize_voice()
        
    def initialize_voice(self):
        """Inicializar componentes de voz"""
        if not VOICE_AVAILABLE:
            print("⚠️ Componentes de voz no disponibles")
            return
            
        try:
            # Inicializar reconocimiento de voz
            self.recognizer = sr.Recognizer()
            
            try:
                self.microphone = sr.Microphone()
            except Exception as e:
                print(f"⚠️ Error con micrófono: {e}")
            
            # Inicializar TTS
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
            self.tts_engine.setProperty('rate', int(os.getenv("VOICE_SPEECH_RATE", "150")))
            self.tts_engine.setProperty('volume', float(os.getenv("VOICE_VOLUME", "0.9")))
            
            self.available = True
            print("✅ Sistema de voz inicializado")
            
        except Exception as e:
            print(f"❌ Error al inicializar voz: {e}")
            self.available = False
    
    def speak(self, text):
        """Hablar texto"""
        if not self.available or not self.tts_engine:
            return False
        
        try:
            clean_text = text.replace('*', '').replace('#', '').replace('```', '')
            
            def speak_thread():
                self.tts_engine.say(clean_text)
                self.tts_engine.runAndWait()
            
            thread = threading.Thread(target=speak_thread, daemon=True)
            thread.start()
            return True
            
        except Exception as e:
            print(f"❌ Error al hablar: {e}")
            return False
    
    def listen(self):
        """Escuchar y transcribir voz"""
        if not self.available or not self.recognizer or not self.microphone:
            return "❌ Voz no disponible"
        
        try:
            with self.microphone as source:
                print("🎤 Escuchando...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                
            print("🔍 Procesando...")
            text = self.recognizer.recognize_google(audio, language='es-ES')
            print(f"✅ Reconocido: {text}")
            return text
            
        except sr.WaitTimeoutError:
            return "⏱️ Tiempo agotado"
        except sr.UnknownValueError:
            return "❌ No se entendió"
        except Exception as e:
            return f"❌ Error: {e}"
    def recognize_speech(self):
        """Reconocer voz del usuario (alias para compatibilidad)"""
        return self.listen()
# Instancia global para compartir entre paneles
gemini_manager = GeminiManager()
voice_manager = VoiceManager()