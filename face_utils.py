"""
app/facial_recognition/face_utils.py
Utilidades para procesamiento y visualización de rostros.
"""
import cv2
import numpy as np
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class FaceUtils:
    """
    Clase con utilidades para procesamiento de rostros.
    """
    
    @staticmethod
    def draw_face_boxes(frame, face_locations, names=None, confidences=None):
        """
        Dibuja cuadros y etiquetas alrededor de los rostros.
        
        Args:
            frame: Imagen donde dibujar
            face_locations: Lista de bounding boxes [(x1, y1, x2, y2), ...]
            names: Lista de nombres para cada rostro
            confidences: Lista de confianzas para cada rostro
        
        Returns:
            Frame con los cuadros dibujados
        """
        frame_copy = frame.copy()
        
        for i, (x1, y1, x2, y2) in enumerate(face_locations):
            # Determinar color (verde si reconocido, rojo si desconocido)
            if names and i < len(names):
                is_recognized = names[i] != "Desconocido" if names else False
                color = (0, 255, 0) if is_recognized else (0, 0, 255)
            else:
                color = (0, 255, 255)  # Amarillo para solo detección
            
            # Dibujar rectángulo alrededor del rostro
            cv2.rectangle(frame_copy, (x1, y1), (x2, y2), color, 2)
            
            # Preparar texto para etiqueta
            label_parts = []
            
            if names and i < len(names):
                label_parts.append(names[i])
            
            if confidences and i < len(confidences):
                label_parts.append(f"{confidences[i]:.1%}")
            
            if label_parts:
                label = " | ".join(label_parts)
                
                # Calcular tamaño del texto
                (text_width, text_height), baseline = cv2.getTextSize(
                    label, cv2.FONT_HERSHEY_DUPLEX, 0.6, 1
                )
                
                # Dibujar fondo para el texto
                cv2.rectangle(
                    frame_copy,
                    (x1, y1 - text_height - 10),
                    (x1 + text_width + 10, y1),
                    color,
                    cv2.FILLED
                )
                
                # Dibujar texto
                cv2.putText(
                    frame_copy,
                    label,
                    (x1 + 5, y1 - 5),
                    cv2.FONT_HERSHEY_DUPLEX,
                    0.6,
                    (255, 255, 255),
                    1
                )
        
        return frame_copy
    
    @staticmethod
    def draw_landmarks(frame, landmarks, color=(0, 255, 255)):
        """
        Dibuja landmarks faciales en el frame.
        
        Args:
            frame: Imagen donde dibujar
            landmarks: Lista de puntos (x, y) o MediaPipe landmarks
            color: Color para los puntos
        
        Returns:
            Frame con landmarks dibujados
        """
        frame_copy = frame.copy()
        
        try:
            # Si son landmarks de MediaPipe
            if hasattr(landmarks[0], 'x'):
                for landmark in landmarks:
                    h, w = frame.shape[:2]
                    x = int(landmark.x * w)
                    y = int(landmark.y * h)
                    cv2.circle(frame_copy, (x, y), 1, color, -1)
            
            # Si son puntos (x, y) normales
            elif isinstance(landmarks[0], (tuple, list)) and len(landmarks[0]) >= 2:
                for (x, y) in landmarks:
                    cv2.circle(frame_copy, (int(x), int(y)), 2, color, -1)
        
        except Exception as e:
            logger.warning(f"⚠️ Error dibujando landmarks: {e}")
        
        return frame_copy
    
    @staticmethod
    def extract_face_regions(frame, face_locations, padding=20):
        """
        Extrae regiones de rostros del frame con padding.
        
        Args:
            frame: Frame original
            face_locations: Lista de bounding boxes
            padding: Padding adicional alrededor del rostro
        
        Returns:
            Lista de imágenes de rostros recortadas
        """
        face_images = []
        h, w = frame.shape[:2]
        
        for (x1, y1, x2, y2) in face_locations:
            # Aplicar padding
            x1_pad = max(0, x1 - padding)
            y1_pad = max(0, y1 - padding)
            x2_pad = min(w, x2 + padding)
            y2_pad = min(h, y2 + padding)
            
            # Extraer región
            face_region = frame[y1_pad:y2_pad, x1_pad:x2_pad]
            
            if face_region.size > 0:
                face_images.append(face_region)
        
        return face_images
    
    @staticmethod
    def preprocess_face(face_image, target_size=(160, 160)):
        """
        Preprocesa una imagen de rostro para reconocimiento.
        
        Args:
            face_image: Imagen del rostro
            target_size: Tamaño objetivo para redimensionar
        
        Returns:
            Imagen preprocesada
        """
        try:
            # Convertir a escala de grises si es color
            if len(face_image.shape) == 3:
                face_gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
            else:
                face_gray = face_image
            
            # Ecualizar histograma para mejorar contraste
            face_eq = cv2.equalizeHist(face_gray)
            
            # Redimensionar
            face_resized = cv2.resize(face_eq, target_size)
            
            # Normalizar
            face_normalized = face_resized.astype(np.float32) / 255.0
            
            return face_normalized
            
        except Exception as e:
            logger.error(f"❌ Error preprocesando rostro: {e}")
            return None
    
    @staticmethod
    def calculate_face_quality(face_image):
        """
        Calcula una métrica de calidad para una imagen de rostro.
        
        Args:
            face_image: Imagen del rostro
        
        Returns:
            Tuple: (puntuación 0-100, problemas_detectados)
        """
        problems = []
        score = 100
        
        try:
            h, w = face_image.shape[:2]
            
            # 1. Verificar tamaño
            min_size = 50
            if h < min_size or w < min_size:
                problems.append("Rostro muy pequeño")
                score -= 40
            
            # 2. Verificar relación de aspecto (debe ser aproximadamente cuadrada)
            aspect_ratio = w / h if h > 0 else 0
            if aspect_ratio < 0.7 or aspect_ratio > 1.3:
                problems.append("Rostro muy estirado/comprimido")
                score -= 20
            
            # 3. Verificar iluminación
            if len(face_image.shape) == 3:
                gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
            else:
                gray = face_image
            
            brightness = np.mean(gray)
            
            if brightness < 50:
                problems.append("Muy oscuro")
                score -= 30
            elif brightness > 200:
                problems.append("Muy brillante")
                score -= 20
            elif brightness < 100:
                problems.append("Oscuro")
                score -= 10
            elif brightness > 150:
                problems.append("Brillante")
                score -= 5
            
            # 4. Verificar contraste
            contrast = np.std(gray)
            if contrast < 20:
                problems.append("Bajo contraste")
                score -= 15
            
            # 5. Verificar desenfoque
            blur = cv2.Laplacian(gray, cv2.CV_64F).var()
            if blur < 50:
                problems.append("Imagen borrosa")
                score -= 25
            
            # Asegurar que la puntuación no sea negativa
            score = max(0, min(100, score))
            
            return score, problems
            
        except Exception as e:
            logger.error(f"❌ Error calculando calidad: {e}")
            return 0, ["Error en cálculo de calidad"]
    
    @staticmethod
    def enhance_face_image(face_image):
        """
        Mejora la calidad de una imagen de rostro.
        
        Args:
            face_image: Imagen del rostro
        
        Returns:
            Imagen mejorada
        """
        try:
            if len(face_image.shape) == 3:
                # Convertir a escala de grises
                gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
            else:
                gray = face_image.copy()
            
            # 1. Ecualización de histograma CLAHE (mejor que equalizeHist)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            
            # 2. Suavizado ligero para reducir ruido
            enhanced = cv2.medianBlur(enhanced, 3)
            
            # 3. Enfoque ligero
            kernel = np.array([[-1, -1, -1],
                               [-1,  9, -1],
                               [-1, -1, -1]])
            enhanced = cv2.filter2D(enhanced, -1, kernel)
            
            # Convertir de vuelta a BGR si la entrada era color
            if len(face_image.shape) == 3:
                enhanced = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
            
            return enhanced
            
        except Exception as e:
            logger.error(f"❌ Error mejorando imagen: {e}")
            return face_image
    
    @staticmethod
    def align_face(face_image, landmarks=None):
        """
        Alinea un rostro basado en landmarks o detección de ojos.
        
        Args:
            face_image: Imagen del rostro
            landmarks: Landmarks faciales (opcional)
        
        Returns:
            Rostro alineado
        """
        try:
            if landmarks is None:
                # Detectar ojos usando Haar Cascade
                eye_cascade = cv2.CascadeClassifier(
                    cv2.data.haarcascades + 'haarcascade_eye.xml'
                )
                
                eyes = eye_cascade.detectMultiScale(face_image, 1.1, 4)
                
                if len(eyes) >= 2:
                    # Tomar los dos ojos con mayor área
                    eyes = sorted(eyes, key=lambda e: e[2]*e[3], reverse=True)[:2]
                    
                    # Calcular centro de los ojos
                    eye_centers = []
                    for (ex, ey, ew, eh) in eyes:
                        eye_centers.append((ex + ew//2, ey + eh//2))
                    
                    # Calcular ángulo de inclinación
                    left_eye, right_eye = eye_centers[:2]
                    dy = right_eye[1] - left_eye[1]
                    dx = right_eye[0] - left_eye[0]
                    angle = np.degrees(np.arctan2(dy, dx))
                    
                    # Rotar imagen
                    h, w = face_image.shape[:2]
                    center = (w//2, h//2)
                    rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
                    aligned = cv2.warpAffine(face_image, rotation_matrix, (w, h))
                    
                    return aligned
            
            return face_image
            
        except Exception as e:
            logger.warning(f"⚠️ Error alineando rostro: {e}")
            return face_image
    
    @staticmethod
    def create_face_mosaic(face_images, cols=4, max_size=200):
        """
        Crea un mosaico con múltiples imágenes de rostros.
        
        Args:
            face_images: Lista de imágenes de rostros
            cols: Número de columnas en el mosaico
            max_size: Tamaño máximo de cada rostro en el mosaico
        
        Returns:
            Imagen mosaico
        """
        if not face_images:
            return None
        
        # Calcular número de filas
        rows = (len(face_images) + cols - 1) // cols
        
        # Crear mosaico vacío
        mosaic_h = rows * max_size
        mosaic_w = cols * max_size
        
        if len(face_images[0].shape) == 3:
            mosaic = np.zeros((mosaic_h, mosaic_w, 3), dtype=np.uint8)
        else:
            mosaic = np.zeros((mosaic_h, mosaic_w), dtype=np.uint8)
        
        # Colocar cada rostro en el mosaico
        for idx, face_img in enumerate(face_images):
            row = idx // cols
            col = idx % cols
            
            # Redimensionar rostro
            face_resized = cv2.resize(face_img, (max_size, max_size))
            
            # Calcular posición
            y1 = row * max_size
            y2 = y1 + max_size
            x1 = col * max_size
            x2 = x1 + max_size
            
            # Colocar en mosaico
            if len(face_resized.shape) == len(mosaic.shape):
                mosaic[y1:y2, x1:x2] = face_resized
            elif len(face_resized.shape) == 2 and len(mosaic.shape) == 3:
                mosaic[y1:y2, x1:x2] = cv2.cvtColor(face_resized, cv2.COLOR_GRAY2BGR)
        
        # Dibujar líneas de separación
        for i in range(1, cols):
            x = i * max_size
            cv2.line(mosaic, (x, 0), (x, mosaic_h), (100, 100, 100), 1)
        
        for i in range(1, rows):
            y = i * max_size
            cv2.line(mosaic, (0, y), (mosaic_w, y), (100, 100, 100), 1)
        
        return mosaic
    
    @staticmethod
    def estimate_age_gender(face_image):
        """
        Estimación básica de edad y género (placeholder - se puede mejorar con modelos).
        
        Args:
            face_image: Imagen del rostro
        
        Returns:
            Tuple: (edad_estimada, género_estimado, confianza)
        """
        # NOTA: Esta es una implementación simple. Para producción,
        # se recomienda usar modelos preentrenados como:
        # - AgeNet
        # - GenderNet
        # - DeepFace
        
        try:
            h, w = face_image.shape[:2]
            
            # Características simples para demo
            # En una implementación real, usarías un modelo entrenado
            
            # Estimación basada en proporciones faciales (muy básica)
            eye_region_ratio = 0.3  # Placeholder
            
            if eye_region_ratio > 0.35:
                gender = "Femenino"
                gender_confidence = 0.6
            else:
                gender = "Masculino"
                gender_confidence = 0.6
            
            # Estimación de edad muy básica
            skin_smoothness = np.std(cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY))
            
            if skin_smoothness < 25:
                age = "Adulto mayor"
            elif skin_smoothness < 35:
                age = "Adulto"
            else:
                age = "Joven"
            
            age_confidence = 0.5  # Baja confianza en este método simple
            
            return age, gender, (age_confidence + gender_confidence) / 2
            
        except Exception as e:
            logger.warning(f"⚠️ Error estimando edad/género: {e}")
            return "Desconocido", "Desconocido", 0.0
    
    @staticmethod
    def detect_emotion(face_image):
        """
        Detección básica de emociones (placeholder - se puede mejorar con modelos).
        
        Args:
            face_image: Imagen del rostro
        
        Returns:
            Tuple: (emoción, confianza)
        """
        # NOTA: Esta es una implementación simple. Para producción,
        # se recomienda usar modelos como:
        # - FER (Facial Expression Recognition)
        # - DeepFace
        # - Modelos de MediaPipe
        
        try:
            # Análisis simple de características
            gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
            
            # Placeholder - en realidad necesitarías landmarks faciales
            # y un modelo entrenado
            
            # Para demo, devolvemos una emoción aleatoria
            emotions = ["Neutral", "Feliz", "Triste", "Enojado", "Sorprendido"]
            emotion = "Neutral"  # Por defecto
            
            # Intenta detectar sonrisa (muy básico)
            smile_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_smile.xml'
            )
            
            smiles = smile_cascade.detectMultiScale(
                gray, scaleFactor=1.8, minNeighbors=20, minSize=(25, 25)
            )
            
            if len(smiles) > 0:
                emotion = "Feliz"
                confidence = 0.7
            else:
                confidence = 0.5
            
            return emotion, confidence
            
        except Exception as e:
            logger.warning(f"⚠️ Error detectando emoción: {e}")
            return "Desconocido", 0.0


# ========== FUNCIONES DE CONVENIENCIA ==========

def draw_emotion_overlay(frame, face_location, emotion, confidence):
    """
    Dibuja información de emoción sobre un rostro.
    
    Args:
        frame: Frame donde dibujar
        face_location: Bounding box del rostro
        emotion: Emoción detectada
        confidence: Confianza de la detección
    
    Returns:
        Frame con overlay de emoción
    """
    x1, y1, x2, y2 = face_location
    
    # Mapeo de emociones a colores
    emotion_colors = {
        "Feliz": (0, 255, 0),      # Verde
        "Triste": (255, 0, 0),     # Azul
        "Enojado": (0, 0, 255),    # Rojo
        "Sorprendido": (255, 255, 0),  # Cyan
        "Neutral": (200, 200, 200),    # Gris
        "Desconocido": (100, 100, 100) # Gris oscuro
    }
    
    color = emotion_colors.get(emotion, (200, 200, 200))
    
    # Dibujar texto de emoción
    text = f"{emotion} ({confidence:.0%})"
    cv2.putText(frame, text, (x1, y2 + 25),
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    
    # Dibujar barra de confianza
    bar_width = 100
    bar_height = 10
    bar_x = x1
    bar_y = y2 + 45
    
    # Fondo de la barra
    cv2.rectangle(frame, (bar_x, bar_y),
                 (bar_x + bar_width, bar_y + bar_height),
                 (100, 100, 100), -1)
    
    # Barra de confianza
    conf_width = int(bar_width * confidence)
    cv2.rectangle(frame, (bar_x, bar_y),
                 (bar_x + conf_width, bar_y + bar_height),
                 color, -1)
    
    # Borde de la barra
    cv2.rectangle(frame, (bar_x, bar_y),
                 (bar_x + bar_width, bar_y + bar_height),
                 (255, 255, 255), 1)
    
    return frame


def create_face_summary(face_image, name="Desconocido"):
    """
    Crea un resumen visual de un rostro con información.
    
    Args:
        face_image: Imagen del rostro
        name: Nombre del rostro
    
    Returns:
        Imagen de resumen
    """
    utils = FaceUtils()
    
    # Crear imagen de resumen
    summary_h = 300
    summary_w = 400
    
    summary = np.zeros((summary_h, summary_w, 3), dtype=np.uint8)
    
    # Redimensionar rostro para el resumen
    face_resized = cv2.resize(face_image, (150, 150))
    
    # Colocar rostro
    summary[20:170, 20:170] = face_resized
    
    # Calcular calidad
    quality_score, problems = utils.calculate_face_quality(face_image)
    
    # Dibujar información
    cv2.putText(summary, f"Nombre: {name}", (200, 40),
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    cv2.putText(summary, f"Calidad: {quality_score}/100", (200, 70),
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    # Barra de calidad
    cv2.rectangle(summary, (200, 85), (350, 95), (100, 100, 100), -1)
    cv2.rectangle(summary, (200, 85), (200 + int(quality_score * 1.5), 95),
                 (0, 255, 0), -1)
    
    # Problemas detectados
    y_offset = 120
    for i, problem in enumerate(problems[:3]):  # Máximo 3 problemas
        cv2.putText(summary, f"• {problem}", (200, y_offset + i * 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 100, 255), 1)
    
    # Estimación de edad/género (si está disponible)
    age, gender, _ = utils.estimate_age_gender(face_image)
    cv2.putText(summary, f"Edad: {age}", (20, 200),
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    cv2.putText(summary, f"Género: {gender}", (20, 225),
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    # Detección de emoción
    emotion, emotion_conf = utils.detect_emotion(face_image)
    cv2.putText(summary, f"Emoción: {emotion}", (20, 250),
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    cv2.putText(summary, f"Confianza: {emotion_conf:.0%}", (20, 275),
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    # Borde
    cv2.rectangle(summary, (0, 0), (summary_w-1, summary_h-1),
                 (200, 200, 200), 2)
    
    return summary


# ========== PRUEBA DEL MÓDULO ==========

if __name__ == "__main__":
    print("🧪 PRUEBA DE FACE_UTILS")
    print("=" * 50)
    
    # Crear una imagen de prueba
    test_image = np.zeros((200, 200, 3), dtype=np.uint8)
    test_image[50:150, 50:150] = [255, 255, 255]  # Cuadrado blanco
    
    utils = FaceUtils()
    
    print("1. Probando cálculo de calidad...")
    score, problems = utils.calculate_face_quality(test_image)
    print(f"   Puntuación: {score}/100")
    print(f"   Problemas: {problems}")
    
    print("\n2. Probando mejora de imagen...")
    enhanced = utils.enhance_face_image(test_image)
    print(f"   Imagen mejorada: {enhanced.shape}")
    
    print("\n3. Probando preprocesamiento...")
    processed = utils.preprocess_face(test_image)
    print(f"   Imagen preprocesada: {processed.shape if processed is not None else 'None'}")
    
    print("\n4. Probando dibujo de cuadros...")
    face_locations = [(30, 30, 70, 70), (100, 100, 150, 150)]
    names = ["Usuario1", "Desconocido"]
    confidences = [0.85, 0.45]
    
    drawn = utils.draw_face_boxes(test_image, face_locations, names, confidences)
    print(f"   Imagen con cuadros dibujada")
    
    print("\n✅ Pruebas completadas")