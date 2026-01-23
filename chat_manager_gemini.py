import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import hashlib
import time

logger = logging.getLogger(__name__)

class GeminiChatManager:
    """Gestor de chat usando Google Gemini."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.api_key = self.config.get('api_key', '')
        self.model_name = self.config.get('model', 'gemini-pro')
        self.temperature = self.config.get('temperature', 0.7)
        self.max_tokens = self.config.get('max_tokens', 1000)
        
        # Inicializar Gemini
        self.gemini_available = False
        self.model = None
        
        # Configurar Gemini si hay API key
        if self.api_key:
            try:
                import google.generativeai as genai
                
                # Configurar API
                genai.configure(api_key=self.api_key)
                
                # Configurar modelo
                generation_config = {
                    "temperature": self.temperature,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": self.max_tokens,
                }
                
                safety_settings = [
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                ]
                
                # Crear modelo
                self.model = genai.GenerativeModel(
                    model_name=self.model_name,
                    generation_config=generation_config,
                    safety_settings=safety_settings
                )
                
                self.gemini_available = True
                print(f"✅ Gemini inicializado: {self.model_name}")
                
            except ImportError:
                print("❌ Error: No se pudo importar google.generativeai")
                print("   Instálalo con: pip install google-generativeai")
            except Exception as e:
                print(f"❌ Error configurando Gemini: {e}")
        else:
            print("⚠️ No hay API key de Gemini. Usando modo simulación.")
        
        # Historial de conversaciones
        self.conversations = {}
        self.current_conversation_id = None
        
        # Crear directorio para conversaciones
        os.makedirs("data/conversations", exist_ok=True)
        
        print(f"✅ Chat Manager inicializado. Gemini: {self.gemini_available}")
    
    def create_conversation(self, title: Optional[str] = None) -> str:
        """Crea una nueva conversación."""
        conv_id = hashlib.md5(f"{datetime.now().timestamp()}{title}".encode()).hexdigest()[:8]
        
        if not title:
            title = f"Conversación {len(self.conversations) + 1}"
        
        conversation = {
            'id': conv_id,
            'title': title,
            'messages': [],
            'model': self.model_name,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'metadata': {}
        }
        
        self.conversations[conv_id] = conversation
        self.current_conversation_id = conv_id
        
        # Guardar automáticamente
        self._save_conversation(conversation)
        
        print(f"✅ Conversación creada: {title} ({conv_id})")
        return conv_id
    
    def send_message(self, message: str, conversation_id: Optional[str] = None) -> str:
        """Envía un mensaje y obtiene respuesta."""
        # Validar mensaje
        if not message or not message.strip():
            return "Por favor, escribe un mensaje."
        
        # Obtener o crear conversación
        if conversation_id and conversation_id in self.conversations:
            self.current_conversation_id = conversation_id
        elif not self.current_conversation_id:
            self.current_conversation_id = self.create_conversation()
        
        conversation = self.conversations[self.current_conversation_id]
        
        # Agregar mensaje del usuario
        user_msg = {
            'role': 'user',
            'content': message,
            'timestamp': datetime.now().isoformat()
        }
        conversation['messages'].append(user_msg)
        
        try:
            if self.gemini_available and self.model:
                # Preparar historial para Gemini (últimos 10 mensajes)
                chat_history = []
                for msg in conversation['messages'][-10:]:
                    role = "user" if msg['role'] == 'user' else "model"
                    chat_history.append({
                        'role': role,
                        'parts': [msg['content']]
                    })
                
                # Iniciar chat con historial
                chat = self.model.start_chat(history=chat_history)
                
                # Enviar mensaje a Gemini
                print(f"🔍 Enviando a Gemini: {message[:50]}...")
                response = chat.send_message(message)
                response_text = response.text
                
                print(f"✅ Respuesta recibida ({len(response_text)} caracteres)")
                
            else:
                # Modo simulación
                response_text = self._get_simulated_response(message)
                print(f"⚠️ Modo simulación: {response_text[:50]}...")
            
            # Agregar respuesta del asistente
            assistant_msg = {
                'role': 'assistant',
                'content': response_text,
                'timestamp': datetime.now().isoformat()
            }
            conversation['messages'].append(assistant_msg)
            
            # Actualizar timestamp
            conversation['updated_at'] = datetime.now().isoformat()
            
            # Guardar
            self._save_conversation(conversation)
            
            return response_text
            
        except Exception as e:
            error_msg = f"Lo siento, hubo un error: {str(e)[:100]}"
            print(f"❌ Error en Gemini: {e}")
            
            # Agregar mensaje de error
            assistant_msg = {
                'role': 'assistant',
                'content': error_msg,
                'timestamp': datetime.now().isoformat()
            }
            conversation['messages'].append(assistant_msg)
            
            return error_msg
    
    def _get_simulated_response(self, message: str) -> str:
        """Respuesta simulada cuando no hay Gemini disponible."""
        message_lower = message.lower()
        
        # Respuestas por palabra clave
        responses = {
            'hola': "¡Hola! Soy tu asistente personal. Estoy usando el modo simulación porque no tengo configurada la API de Gemini. ¿En qué puedo ayudarte?",
            'cómo estás': "¡Estoy funcionando bien! Aunque estoy en modo simulación, puedo ayudarte con muchas cosas.",
            'qué puedes hacer': "Puedo: 1) Chatear contigo, 2) Leer respuestas en voz alta, 3) Guardar conversaciones. Configura la API de Gemini para respuestas más inteligentes.",
            'gemini': "Para usar Gemini AI, necesitas una API key. Obtén una en: https://makersuite.google.com/app/apikey y agrégalo al archivo .env como GEMINI_API_KEY=tu_key",
            'gracias': "¡De nada! ¿Hay algo más en lo que pueda ayudarte?",
            'adiós': "¡Hasta luego! Recuerda que puedes configurar Gemini para respuestas más avanzadas.",
            'python': "¡Python es genial! Puedo ayudarte con conceptos de Python, aunque esté en modo simulación.",
            'código': "Puedo ayudarte con código. ¿Qué lenguaje te interesa? En modo simulación mis respuestas son limitadas.",
        }
        
        # Buscar palabras clave
        for keyword, response in responses.items():
            if keyword in message_lower:
                return response
        
        # Respuesta general
        general_responses = [
            "Entiendo tu mensaje. Estoy en modo simulación. Configura Gemini API para respuestas más precisas.",
            "Interesante pregunta. Mis capacidades son limitadas en modo simulación.",
            "Puedo procesar tu solicitud, pero para mejores resultados configura la API de Gemini.",
            "Como asistente en modo desarrollo, puedo guardar conversaciones y hablar, pero mis respuestas son básicas.",
            "¡Vaya! En modo simulación mis respuestas son predefinidas. Configura Gemini para IA real."
        ]
        
        import random
        return random.choice(general_responses)
    
    def _save_conversation(self, conversation: Dict):
        """Guarda una conversación en archivo."""
        try:
            file_path = f"data/conversations/{conversation['id']}.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(conversation, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ Error guardando conversación: {e}")
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict]:
        """Obtiene una conversación por ID."""
        return self.conversations.get(conversation_id)
    
    def get_all_conversations(self) -> List[Dict]:
        """Obtiene todas las conversaciones."""
        return list(self.conversations.values())

# Función de prueba
def test_gemini():
    """Prueba simple de Gemini."""
    print("🧪 Probando Gemini Chat Manager...")
    
    # Configuración de prueba
    config = {
        'api_key': os.getenv('GEMINI_API_KEY', ''),
        'model': 'gemini-pro',
        'temperature': 0.7
    }
    
    manager = GeminiChatManager(config)
    
    # Crear conversación
    conv_id = manager.create_conversation("Prueba inicial")
    
    # Enviar mensaje
    response = manager.send_message("Hola, ¿cómo estás?", conv_id)
    print(f"Respuesta: {response}")
    
    print("✅ Prueba completada")

if __name__ == "__main__":
    test_gemini()