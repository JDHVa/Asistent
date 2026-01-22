import os
import cv2
import pickle
import numpy as np
from datetime import datetime
import json
from pathlib import Path
import logging
import warnings

# Suprimir advertencias
warnings.filterwarnings('ignore')

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FaceSystem:
    """
    Sistema de reconocimiento facial robusto usando MediaPipe.
    """
    
    def __init__(self, registros_path="data/known_faces", cache_path="data/cache"):
        """
        Inicializa el sistema facial.
        """
        # Configurar rutas
        self.base_path = Path(registros_path)
        self.cache_path = Path(cache_path)
        self.encodings_cache = self.cache_path / "face_embeddings.pkl"
        
        # Crear directorios
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.cache_path.mkdir(parents=True, exist_ok=True)
        
        # Inicializar MediaPipe de forma segura
        self._initialize_mediapipe()
        
        # Base de datos
        self.known_embeddings = []  # Lista de embeddings faciales
        self.known_names = []       # Lista de nombres
        
        # Parámetros
        self.min_face_size = 100
        self.confidence_threshold = 0.14
        
        # Cargar base de datos
        self.load_database()
        
        logger.info(f"📊 Sistema facial inicializado. Usuarios: {len(self.known_names)}")
    
    def _initialize_mediapipe(self):
        """Inicializa MediaPipe de forma segura."""
        try:
            import mediapipe as mp
            self.mp = mp
            
            # SOLUCIÓN: Inicializar con configuración SIMPLE y CONSISTENTE
            # IMPORTANTE: Usar exactamente la misma configuración siempre
            
            # 1. FaceDetection - SIN parámetros complicados
            self.face_detection = mp.solutions.face_detection.FaceDetection(
                min_detection_confidence=0.5
            )
            
            # 2. FaceMesh - CONFIGURACIÓN FIJA (sin refine_landmarks para consistencia)
            # Nota: Si quieres refine_landmarks, úsalo siempre igual
            self.face_mesh = mp.solutions.face_mesh.FaceMesh(
                static_image_mode=True,
                max_num_faces=1,
                refine_landmarks=False,  # ← IMPORTANTE: Mantener igual siempre
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
            
            self.face_detection_available = True
            logger.info("✅ MediaPipe inicializado con configuración consistente")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando MediaPipe: {e}")
            self.face_detection_available = False
            self.face_detection = None
            self.face_mesh = None
    
    def load_database(self):
        """Carga la base de datos de rostros."""
        logger.info("📂 Cargando base de datos...")
        
        # Intentar desde caché
        if self._load_from_cache():
            logger.info(f"✅ Base cargada: {len(self.known_names)} usuarios")
            return True
        
        # Desde imágenes
        return self._load_from_images()
    
    def _load_from_cache(self):
        """Carga desde caché con manejo de dimensiones."""
        try:
            if self.encodings_cache.exists():
                with open(self.encodings_cache, 'rb') as f:
                    cache_data = pickle.load(f)
                
                if 'embeddings' in cache_data and 'names' in cache_data:
                    self.known_embeddings = cache_data['embeddings']
                    self.known_names = cache_data['names']
                    
                    # SOLUCIÓN: Normalizar dimensiones
                    self._normalize_embeddings()
                    
                    return True
                    
        except Exception as e:
            logger.warning(f"⚠️ Error cargando caché: {e}")
        
        return False
    
    def _normalize_embeddings(self):
        """Normaliza todos los embeddings a la misma dimensión."""
        if not self.known_embeddings:
            return
        
        # Determinar dimensión objetivo (la más común)
        dimensions = [e.shape[0] for e in self.known_embeddings]
        from collections import Counter
        most_common_dim = Counter(dimensions).most_common(1)[0][0]
        
        logger.info(f"🔧 Normalizando embeddings a dimensión: {most_common_dim}")
        
        # Normalizar cada embedding
        normalized_embeddings = []
        for i, embedding in enumerate(self.known_embeddings):
            if embedding.shape[0] != most_common_dim:
                # Ajustar dimensión
                normalized = self._resize_embedding(embedding, most_common_dim)
                normalized_embeddings.append(normalized)
                logger.debug(f"  Embedding {i} ajustado: {embedding.shape[0]} → {most_common_dim}")
            else:
                normalized_embeddings.append(embedding)
        
        self.known_embeddings = normalized_embeddings
    
    def _resize_embedding(self, embedding, target_dim):
        """Redimensiona un embedding a la dimensión objetivo."""
        current_dim = embedding.shape[0]
        
        if current_dim == target_dim:
            return embedding
        
        if current_dim > target_dim:
            # Recortar si es más grande
            return embedding[:target_dim]
        else:
            # Rellenar con ceros si es más pequeño
            padding = np.zeros(target_dim - current_dim, dtype=embedding.dtype)
            return np.concatenate([embedding, padding])
    
    def _load_from_images(self):
        """Carga desde imágenes."""
        valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp')
        loaded_count = 0
        
        for file_path in self.base_path.iterdir():
            if file_path.suffix.lower() in valid_extensions:
                try:
                    image = cv2.imread(str(file_path))
                    if image is None:
                        continue
                    
                    # Extraer embedding
                    embedding = self._extract_face_embedding(image)
                    
                    if embedding is not None:
                        name = file_path.stem
                        self.known_embeddings.append(embedding)
                        self.known_names.append(name)
                        loaded_count += 1
                        
                except Exception as e:
                    logger.error(f"❌ Error procesando {file_path.name}: {e}")
        
        # Normalizar dimensiones
        self._normalize_embeddings()
        
        # Guardar caché
        if loaded_count > 0:
            self._save_to_cache()
        
        logger.info(f"📊 Usuarios cargados: {loaded_count}")
        return loaded_count > 0
    
    def _extract_face_embedding(self, image):
        """Extrae embedding facial consistente."""
        if not self.face_detection_available or self.face_mesh is None:
            return None
        
        try:
            # Convertir BGR a RGB
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Procesar con FaceMesh
            results = self.face_mesh.process(rgb_image)
            
            if results.multi_face_landmarks:
                face_landmarks = results.multi_face_landmarks[0]
                
                # SOLUCIÓN: Usar solo los primeros 1404 valores (468 landmarks × 3)
                # Esto asegura consistencia incluso con refine_landmarks
                embedding = []
                max_points = 468  # Número estándar de landmarks sin refinamiento
                
                for i, landmark in enumerate(face_landmarks.landmark):
                    if i >= max_points:
                        break  # Limitar a 468 puntos
                    embedding.extend([landmark.x, landmark.y, landmark.z])
                
                # Rellenar si hay menos puntos
                while len(embedding) < (max_points * 3):
                    embedding.extend([0.0, 0.0, 0.0])
                
                # Tomar exactamente 1404 valores
                embedding = np.array(embedding[:1404], dtype=np.float32)
                
                # Normalizar el embedding
                embedding = self._normalize_embedding_vector(embedding)
                
                return embedding
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo embedding: {e}")
            return None
    
    def _normalize_embedding_vector(self, embedding):
        """Normaliza el vector de embedding para mejor comparación."""
        # Normalizar por L2
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        
        return embedding
    
    def _save_to_cache(self):
        """Guarda en caché."""
        try:
            cache_data = {
                'embeddings': self.known_embeddings,
                'names': self.known_names,
                'timestamp': datetime.now().isoformat(),
                'version': '2.0',
                'embedding_dim': 1404  # Especificar dimensión
            }
            
            with open(self.encodings_cache, 'wb') as f:
                pickle.dump(cache_data, f)
            
            logger.info(f"💾 Cache guardada: {len(self.known_names)} usuarios")
            
        except Exception as e:
            logger.error(f"❌ Error guardando caché: {e}")
    
    # ========== API PÚBLICA ==========
    
    def register_face(self, image, name):
        """Registra un nuevo rostro."""
        try:
            # Validar nombre
            safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '_', '-')).strip()
            if not safe_name or len(safe_name) < 2:
                return False, "❌ Nombre inválido"
            
            if safe_name in self.known_names:
                return False, f"❌ '{safe_name}' ya existe"
            
            # Extraer embedding
            embedding = self._extract_face_embedding(image)
            if embedding is None:
                return False, "❌ No se detectó rostro"
            
            # Guardar imagen
            image_path = self.base_path / f"{safe_name}.jpg"
            cv2.imwrite(str(image_path), image)
            
            # Agregar a base de datos
            self.known_embeddings.append(embedding)
            self.known_names.append(safe_name)
            
            # Guardar caché
            self._save_to_cache()
            
            # Guardar metadatos
            self._save_metadata(safe_name, image_path)
            
            return True, f"✅ '{safe_name}' registrado"
            
        except Exception as e:
            logger.error(f"❌ Error registrando: {e}")
            return False, f"❌ Error: {str(e)}"
    
    def _save_metadata(self, name, image_path):
        """Guarda metadatos."""
        try:
            metadata_path = self.base_path / f"{name}.json"
            metadata = {
                "name": name,
                "registered": datetime.now().isoformat(),
                "image": str(image_path.name),
                "access_count": 0
            }
            
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
                
        except Exception as e:
            logger.warning(f"⚠️ Error guardando metadatos: {e}")
    
    def recognize_face(self, face_image):
        """Reconoce un rostro de forma segura."""
        try:
            if len(self.known_embeddings) == 0:
                return "Desconocido", 0.0
            
            # Extraer embedding
            query_embedding = self._extract_face_embedding(face_image)
            if query_embedding is None:
                return "Desconocido", 0.0
            
            # Asegurar dimensión
            query_embedding = self._resize_embedding(query_embedding, 1404)
            query_embedding = self._normalize_embedding_vector(query_embedding)
            
            # Calcular similitudes
            best_match = None
            best_similarity = -1
            
            for known_embedding, known_name in zip(self.known_embeddings, self.known_names):
                # Asegurar dimensiones iguales
                known_embedding = self._resize_embedding(known_embedding, 1404)
                known_embedding = self._normalize_embedding_vector(known_embedding)
                
                # Calcular similitud del coseno (más robusto)
                similarity = np.dot(query_embedding, known_embedding)
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = known_name
            
            if best_match is None:
                return "Desconocido", 0.0
            
            # Convertir similitud a confianza (0.0-1.0)
            confidence = (best_similarity + 1) / 2  # Escalar de [-1,1] a [0,1]
            
            if confidence >= self.confidence_threshold:
                return best_match, confidence
            else:
                return "Desconocido", confidence
            
        except Exception as e:
            logger.error(f"❌ Error reconociendo: {e}")
            return "Desconocido", 0.0
    
    def detect_faces(self, frame):
        """Detecta rostros en un frame."""
        if not self.face_detection_available or self.face_detection is None:
            return self._detect_faces_opencv(frame)
        
        try:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_detection.process(rgb_frame)
            
            face_locations = []
            
            if results.detections:
                for detection in results.detections:
                    bbox = detection.location_data.relative_bounding_box
                    h, w, _ = frame.shape
                    
                    x = int(bbox.xmin * w)
                    y = int(bbox.ymin * h)
                    width = int(bbox.width * w)
                    height = int(bbox.height * h)
                    
                    # Asegurar dentro del frame
                    x = max(0, x)
                    y = max(0, y)
                    width = min(w - x, width)
                    height = min(h - y, height)
                    
                    if width > 0 and height > 0:
                        face_locations.append((x, y, x + width, y + height))
            
            return face_locations
            
        except Exception as e:
            logger.error(f"❌ Error detectando: {e}")
            return self._detect_faces_opencv(frame)
    
    def _detect_faces_opencv(self, frame):
        """Detección con OpenCV (fallback)."""
        try:
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            face_cascade = cv2.CascadeClassifier(cascade_path)
            
            if face_cascade.empty():
                return []
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            
            face_locations = []
            for (x, y, w, h) in faces:
                face_locations.append((x, y, x + w, y + h))
            
            return face_locations
            
        except Exception as e:
            logger.error(f"❌ Error OpenCV: {e}")
            return []
    
    def validate_image_for_registration(self, image):
        """Valida imagen para registro."""
        try:
            if image is None or image.size == 0:
                return False, "❌ Imagen vacía"
            
            h, w = image.shape[:2]
            if h < 100 or w < 100:
                return False, f"❌ Muy pequeña ({w}x{h})"
            
            face_locations = self.detect_faces(image)
            
            if len(face_locations) == 0:
                return False, "❌ No se detectó rostro"
            
            if len(face_locations) > 1:
                return False, "❌ Múltiples rostros"
            
            # Verificar tamaño del rostro
            x1, y1, x2, y2 = face_locations[0]
            face_width = x2 - x1
            face_height = y2 - y1
            
            if face_width < self.min_face_size or face_height < self.min_face_size:
                return False, f"❌ Rostro pequeño ({face_width}x{face_height})"
            
            # Verificar iluminación
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            brightness = np.mean(gray)
            
            if brightness < 50:
                return False, "❌ Muy oscura"
            elif brightness > 200:
                return False, "❌ Muy brillante"
            
            return True, "✅ Imagen válida"
            
        except Exception as e:
            logger.error(f"❌ Error validando: {e}")
            return False, f"❌ Error: {str(e)}"
    
    def get_user_count(self):
        return len(self.known_names)
    
    def get_user_list(self):
        return self.known_names.copy()
    
    def delete_user(self, name):
        """Elimina usuario."""
        try:
            if name not in self.known_names:
                return False, f"❌ '{name}' no encontrado"
            
            idx = self.known_names.index(name)
            self.known_names.pop(idx)
            self.known_embeddings.pop(idx)
            
            # Eliminar archivos
            for ext in ['.jpg', '.jpeg', '.png', '.bmp', '.json']:
                file_path = self.base_path / f"{name}{ext}"
                if file_path.exists():
                    file_path.unlink()
            
            # Actualizar caché
            self._save_to_cache()
            
            return True, f"✅ '{name}' eliminado"
            
        except Exception as e:
            logger.error(f"❌ Error eliminando: {e}")
            return False, f"❌ Error: {str(e)}"


# ========== FUNCIÓN DE PRUEBA ==========

def test_system():
    """Prueba el sistema."""
    print("🧪 Probando FaceSystem...")
    
    try:
        system = FaceSystem()
        
        print(f"✅ Sistema inicializado. Usuarios: {system.get_user_count()}")
        
        if system.get_user_count() > 0:
            print(f"   Usuarios: {', '.join(system.get_user_list())}")
        
        # Verificar caché
        if system.encodings_cache.exists():
            print(f"📁 Cache existe: {system.encodings_cache}")
            
            with open(system.encodings_cache, 'rb') as f:
                data = pickle.load(f)
                print(f"   Dimensión embedding: {data.get('embedding_dim', 'desconocida')}")
                print(f"   Versión: {data.get('version', 'antigua')}")
        
        # Probar cámara
        print("\n📷 Probando cámara...")
        cap = cv2.VideoCapture(0)
        
        if cap.isOpened():
            print("✅ Cámara disponible")
            cap.release()
        else:
            print("⚠️ Cámara no disponible")
        
        return system
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    system = test_system()
    if system:
        print("\n🎯 Sistema funcionando")
    else:
        print("\n❌ Error en el sistema")