import os
import cv2
import pickle
import numpy as np
from datetime import datetime
import json
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FaceSystem:
    def __init__(self, registros_path="data/known_faces", cache_path="data/cache"):
        self.base_path = Path(registros_path)
        self.cache_path = Path(cache_path)
        self.encodings_cache = self.cache_path / "face_embeddings.pkl"
        
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.cache_path.mkdir(parents=True, exist_ok=True)
        
        try:
            import mediapipe as mp
            self.mp = mp
            
            self.face_detection = mp.solutions.face_detection.FaceDetection(
                model_selection=1,
                min_detection_confidence=0.5
            )
            
            self.face_mesh = mp.solutions.face_mesh.FaceMesh(
                static_image_mode=True,
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
            
            self.face_detection_available = True
            logger.info("MediaPipe inicializado correctamente")
            
        except ImportError as e:
            logger.error(f"Error al importar MediaPipe: {e}")
            self.face_detection_available = False
            raise ImportError("MediaPipe no está instalado. Ejecuta: pip install mediapipe==0.10.14")
        
        self.known_embeddings = []
        self.known_names = []
        
        self.min_face_size = 100
        self.confidence_threshold = 0.14
        
        self.load_database()
        
        logger.info(f"Sistema facial inicializado. Usuarios registrados: {len(self.known_names)}")

    def load_database(self):
        logger.info("Cargando base de datos de rostros...")
        
        if self._load_from_cache():
            logger.info(f"Base cargada desde caché: {len(self.known_names)} usuarios")
            return True
        
        return self._load_from_images()

    def _load_from_cache(self):
        try:
            if self.encodings_cache.exists():
                with open(self.encodings_cache, 'rb') as f:
                    cache_data = pickle.load(f)
                
                if 'embeddings' in cache_data and 'names' in cache_data:
                    self.known_embeddings = cache_data['embeddings']
                    self.known_names = cache_data['names']
                    return True
                    
        except Exception as e:
            logger.warning(f"Error cargando caché: {e}")
        
        return False

    def _load_from_images(self):
        valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp')
        loaded_count = 0
        
        for file_path in self.base_path.iterdir():
            if file_path.suffix.lower() in valid_extensions:
                try:
                    image = cv2.imread(str(file_path))
                    if image is None:
                        logger.warning(f"No se pudo leer: {file_path.name}")
                        continue
                    
                    embedding = self._extract_face_embedding(image)
                    
                    if embedding is not None:
                        name = file_path.stem
                        self.known_embeddings.append(embedding)
                        self.known_names.append(name)
                        loaded_count += 1
                        logger.info(f"Cargado: {name}")
                    
                except Exception as e:
                    logger.error(f"Error procesando {file_path.name}: {e}")
        
        if loaded_count > 0:
            self._save_to_cache()
        
        logger.info(f"Total usuarios cargados: {loaded_count}")
        return loaded_count > 0

    def _extract_face_embedding(self, image):
        try:
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = self.face_mesh.process(rgb_image)
            
            if results.multi_face_landmarks:
                face_landmarks = results.multi_face_landmarks[0]
                
                embedding = []
                for landmark in face_landmarks.landmark:
                    embedding.extend([landmark.x, landmark.y, landmark.z])
                
                return np.array(embedding, dtype=np.float32)
            
            return None
            
        except Exception as e:
            logger.error(f"Error extrayendo embedding: {e}")
            return None

    def _save_to_cache(self):
        try:
            cache_data = {
                'embeddings': self.known_embeddings,
                'names': self.known_names,
                'timestamp': datetime.now().isoformat(),
                'version': '1.0'
            }
            
            with open(self.encodings_cache, 'wb') as f:
                pickle.dump(cache_data, f)
            
            logger.info(f"Cache guardada: {len(self.known_names)} usuarios")
            return True
            
        except Exception as e:
            logger.error(f"Error guardando caché: {e}")
            return False

    def register_face(self, image, name):
        try:
            safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '_', '-')).strip()
            if not safe_name or len(safe_name) < 2:
                return False, "Nombre inválido. Debe tener al menos 2 caracteres."
            
            if safe_name in self.known_names:
                return False, f"El nombre '{safe_name}' ya está registrado."
            
            embedding = self._extract_face_embedding(image)
            if embedding is None:
                return False, "No se detectó un rostro claro en la imagen."
            
            image_path = self.base_path / f"{safe_name}.jpg"
            cv2.imwrite(str(image_path), image)
            
            self.known_embeddings.append(embedding)
            self.known_names.append(safe_name)
            
            self._save_to_cache()
            self._save_metadata(safe_name, image_path)
            
            return True, f"Usuario '{safe_name}' registrado exitosamente."
            
        except Exception as e:
            logger.error(f"Error registrando rostro: {e}")
            return False, f"Error durante el registro: {str(e)}"

    def _save_metadata(self, name, image_path):
        try:
            metadata_path = self.base_path / f"{name}_metadata.json"
            metadata = {
                "name": name,
                "registered_date": datetime.now().isoformat(),
                "image_path": str(image_path),
                "last_seen": None,
                "access_count": 0
            }
            
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.warning(f"Error guardando metadatos: {e}")

    def recognize_face(self, face_image):
        try:
            if len(self.known_embeddings) == 0:
                return "Desconocido", 0.0
            
            embedding = self._extract_face_embedding(face_image)
            if embedding is None:
                return "Desconocido", 0.0
            
            best_match = None
            best_distance = float('inf')
            
            for known_embedding, known_name in zip(self.known_embeddings, self.known_names):
                distance = np.linalg.norm(embedding - known_embedding)
                
                if distance < best_distance:
                    best_distance = distance
                    best_match = known_name
            
            confidence = 1.0 / (1.0 + best_distance)
            
            if confidence >= self.confidence_threshold:
                return best_match, confidence
            else:
                return "Desconocido", confidence
            
        except Exception as e:
            logger.error(f"Error reconociendo rostro: {e}")
            return "Desconocido", 0.0

    def detect_faces(self, frame):
        if not self.face_detection_available:
            return []
        
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
                    
                    x = max(0, x)
                    y = max(0, y)
                    width = min(w - x, width)
                    height = min(h - y, height)
                    
                    face_locations.append((x, y, x + width, y + height))
            
            return face_locations
            
        except Exception as e:
            logger.error(f"Error detectando rostros: {e}")
            return []

    def get_user_count(self):
        return len(self.known_names)

    def get_user_list(self):
        return self.known_names.copy()

    def delete_user(self, name):
        try:
            if name not in self.known_names:
                return False, f"Usuario '{name}' no encontrado."
            
            idx = self.known_names.index(name)
            
            self.known_names.pop(idx)
            self.known_embeddings.pop(idx)
            
            image_path = self.base_path / f"{name}.jpg"
            metadata_path = self.base_path / f"{name}_metadata.json"
            
            if image_path.exists():
                image_path.unlink()
            
            if metadata_path.exists():
                metadata_path.unlink()
            
            self._save_to_cache()
            
            return True, f"Usuario '{name}' eliminado exitosamente."
            
        except Exception as e:
            logger.error(f"Error eliminando usuario: {e}")
            return False, f"Error eliminando usuario: {str(e)}"

    def validate_image_for_registration(self, image):
        try:
            if image is None or image.size == 0:
                return False, "Imagen vacía o no válida."
            
            h, w = image.shape[:2]
            if h < 100 or w < 100:
                return False, f"Imagen muy pequeña ({w}x{h}). Mínimo 100x100."
            
            face_locations = self.detect_faces(image)
            
            if len(face_locations) == 0:
                return False, "No se detectó ningún rostro."
            
            if len(face_locations) > 1:
                return False, "Se detectaron múltiples rostros. Solo debe haber uno."
            
            x1, y1, x2, y2 = face_locations[0]
            face_width = x2 - x1
            face_height = y2 - y1
            
            if face_width < self.min_face_size or face_height < self.min_face_size:
                return False, f"Rostro muy pequeño ({face_width}x{face_height})."
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            brightness = np.mean(gray)
            
            if brightness < 50:
                return False, "Imagen muy oscura. Mejora la iluminación."
            elif brightness > 200:
                return False, "Imagen muy brillante. Reduce la iluminación."
            
            return True, "Imagen válida para registro."
            
        except Exception as e:
            logger.error(f"Error validando imagen: {e}")
            return False, f"Error validando imagen: {str(e)}"

def test_face_system():
    print("Probando FaceSystem...")
    
    try:
        face_system = FaceSystem()
        
        print(f"Sistema inicializado. Usuarios: {face_system.get_user_count()}")
        
        if face_system.get_user_count() > 0:
            print(f"   Usuarios registrados: {', '.join(face_system.get_user_list())}")
        
        return face_system
        
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    system = test_face_system()
    if system:
        print("FaceSystem está funcionando correctamente.")