import os
import threading
from dotenv import load_dotenv

load_dotenv()

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Google Generative AI no disponible. Instala: pip install google-generativeai")

try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
    print("SpeechRecognition no disponible")

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    print("pyttsx3 no disponible")

class GeminiManager:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "AIzaSyD4Mx8LrJZXq24DHdxHjNV-suN8zeO_ggE")
        self.model = None
        self.conversation_history = []
        self.initialize_gemini()
        
    def initialize_gemini(self):
        try:
            if not GEMINI_AVAILABLE:
                return False
                
            if not self.api_key:
                return False
                
            genai.configure(api_key=self.api_key)
            
            try:
                self.model = genai.GenerativeModel('gemini-2.5-flash')
                print("✅ Modelo Gemini 'gemini-2.5-flash' inicializado")
                return True
            except Exception:
                try:
                    self.model = genai.GenerativeModel('gemini-pro')
                    print("✅ Modelo Gemini 'gemini-pro' inicializado")
                    return True
                except Exception:
                    return False
                    
        except Exception:
            return False
    
    def send_message(self, message, system_prompt=None):
        if not self.model:
            return "Error: Gemini AI no está configurado."
        
        try:
            if system_prompt:
                full_prompt = f"{system_prompt}\n\nUsuario: {message}"
            else:
                full_prompt = message
            
            generation_config = {
                "temperature": 0.7,
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 1024,
            }
            
            chat = self.model.start_chat(history=self.conversation_history)
            response = chat.send_message(
                full_prompt,
                generation_config=generation_config
            )
            
            self.conversation_history.append({"role": "user", "parts": [full_prompt]})
            self.conversation_history.append({"role": "model", "parts": [response.text]})
            
            if len(self.conversation_history) > 10:
                self.conversation_history = self.conversation_history[-10:]
            
            return response.text
            
        except Exception as e:
            return f"Error con Gemini AI: {str(e)}"
    
    def analyze_schedule(self, events, current_time=None):
        if not events:
            return "No tienes eventos programados."
        
        events_text = ""
        for i, event in enumerate(events, 1):
            events_text += f"{i}. {event['title']} - {event['start_time']} a {event['end_time']}"
            if event.get('location'):
                events_text += f" en {event['location']}"
            events_text += "\n"
        
        prompt = f"""Analiza este horario:
{events_text}
Hora actual: {current_time if current_time else 'No especificada'}
Responde en español de manera natural."""
        
        return self.send_message(prompt, "Eres un asistente personal organizado.")
    
    def analyze_tasks(self, tasks):
        pending_tasks = [t for t in tasks if not t['completed']]
        completed_tasks = [t for t in tasks if t['completed']]
        
        if not pending_tasks:
            return "¡Excelente! No tienes tareas pendientes."
        
        tasks_text = ""
        for i, task in enumerate(pending_tasks[:5], 1):
            tasks_text += f"{i}. {task['title']}"
            if task.get('due_date'):
                tasks_text += f" (para el {task['due_date']})"
            tasks_text += "\n"
        
        prompt = f"""Analiza estas tareas:
{tasks_text}
Completadas: {len(completed_tasks)}
Responde en español de manera práctica."""
        
        return self.send_message(prompt, "Eres un coach de productividad.")
    
    def clear_history(self):
        self.conversation_history = []

class VoiceManager:
    def __init__(self):
        self.recognizer = None
        self.microphone = None
        self.tts_engine = None
        self.microphone_available = False
        self.tts_available = False
        self.initialize_voice()
        
    def initialize_voice(self):
        self.initialize_tts()
        self.initialize_speech_recognition()
        print(f"✅ Estado de voz - TTS: {'✅' if self.tts_available else 'Error'}, Micrófono: {'✅' if self.microphone_available else 'Error'}")
    
    def initialize_tts(self):
        try:
            if not TTS_AVAILABLE:
                return
            
            self.tts_engine = pyttsx3.init()
            
            try:
                voices = self.tts_engine.getProperty('voices')
                for voice in voices:
                    if 'spanish' in voice.name.lower() or 'español' in voice.name.lower():
                        self.tts_engine.setProperty('voice', voice.id)
                        print(f"✅ Voz configurada: {voice.name}")
                        break
            except:
                pass
            
            self.tts_engine.setProperty('rate', 150)
            self.tts_engine.setProperty('volume', 0.9)
            self.tts_available = True
            print("✅ TTS inicializado correctamente")
            
        except Exception:
            self.tts_available = False
    
    def initialize_speech_recognition(self):
        try:
            if not SPEECH_RECOGNITION_AVAILABLE:
                return
            
            self.recognizer = sr.Recognizer()
            
            import sys
            if sys.platform == 'win32':
                try:
                    self.microphone = sr.Microphone(device_index=0)
                    self.microphone_available = True
                    print("✅ Micrófono detectado (Windows)")
                except:
                    pass
            else:
                try:
                    self.microphone = sr.Microphone()
                    self.microphone_available = True
                    print("✅ Micrófono detectado")
                except Exception:
                    pass
                        
        except Exception:
            pass
    
    def speak(self, text):
        if not self.tts_available or not self.tts_engine:
            return False
        
        try:
            clean_text = text.replace('*', '').replace('`', '').replace('#', '')
            
            def speak_thread():
                try:
                    self.tts_engine.say(clean_text)
                    self.tts_engine.runAndWait()
                except Exception:
                    pass
            
            thread = threading.Thread(target=speak_thread, daemon=True)
            thread.start()
            return True
            
        except Exception:
            return False
    
    def listen(self):
        if not self.microphone_available or not self.recognizer or not self.microphone:
            return "Micrófono no disponible"
        
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            text = self.recognizer.recognize_google(audio, language='es-ES')
            print(f"✅ Reconocido: {text}")
            return text
            
        except sr.WaitTimeoutError:
            return "Tiempo agotado"
        except sr.UnknownValueError:
            return "No se entendió el audio"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def recognize_speech(self):
        return self.listen()
    
    def is_microphone_available(self):
        return self.microphone_available
    
    def is_tts_available(self):
        return self.tts_available

gemini_manager = GeminiManager()
voice_manager = VoiceManager()