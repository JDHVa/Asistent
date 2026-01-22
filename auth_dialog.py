"""
Diálogo de autenticación facial - INTEGRADO CON SISTEMA REAL """
import sys
import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QProgressBar, QMessageBox, QWidget,
    QApplication  # Añadir esta línea
)
from PySide6.QtCore import Qt, Signal, QTimer, QSize
from PySide6.QtGui import QImage, QPixmap, QFont, QColor, QIcon
import cv2
import numpy as np
import logging
# Agrega esto con las otras importaciones al inicio
from datetime import datetime  # <- ESTA LÍNEA
# Configurar logger
logger = logging.getLogger(__name__)

class AuthDialog(QDialog):
    
    # Señales mejoradas
    auth_successful = Signal(dict)  # Emite datos completos del usuario
    auth_failed = Signal(str)       # Emite mensaje de error
    auth_skipped = Signal()         # Modo desarrollo
    
    def __init__(self, face_system=None, parent=None):
        super().__init__(parent)
        self.face_system = face_system
        self.camera_active = False
        self.capture = None
        self.auth_attempts = 0
        self.MAX_ATTEMPTS = 5

        # Estado de autenticación
        self.auth_start_time = None
        self.last_detected_name = None
        self.consecutive_matches = 0
        self.REQUIRED_MATCHES = 3  # Necesita 3 detecciones consecutivas
        self.face_detected = False  # Necesita 3 detecciones consecutivas
        
        self.setup_ui()
        self.setup_camera()
    
    def process_frame_with_realtime_auth(self, frame):
        """Procesar frame con reconocimiento facial real."""
        display_frame = frame.copy()
        user_data = None
        
        # Si no hay sistema facial, usar detección básica
        if not self.face_system:
            return self.fallback_face_detection(display_frame), None
        
        try:
            # Detectar rostros
            face_locations = self.face_system.detect_faces(frame)
            
            if not face_locations:
                self.face_detected = False
                self.update_status("Enfócate en la cámara...", "👤", "#ea4335")
                self.progress_bar.setValue(0)
                self.consecutive_matches = 0
                return display_frame, None
            
            # Tomar el primer rostro
            x1, y1, x2, y2 = face_locations[0]
            face_region = frame[y1:y2, x1:x2]
            
            # Validar tamaño del rostro
            if face_region.shape[0] < 50 or face_region.shape[1] < 50:
                self.update_status("Acércate más a la cámara", "🔍", "#fbbc04")
                return display_frame, None
            
            # Reconocer rostro
            name, confidence = self.face_system.recognize_face(face_region)
            
            # Dibujar resultados
            color = (0, 255, 0) if name != "Desconocido" else (0, 0, 255)
            cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 2)
            
            label = f"{name} ({confidence:.2f})"
            cv2.putText(display_frame, label, (x1, y1-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            
            # Lógica de autenticación
            if name != "Desconocido" and confidence >= 0.6:
                if name == self.last_detected_name:
                    self.consecutive_matches += 1
                else:
                    self.consecutive_matches = 1
                    self.last_detected_name = name
                
                # Actualizar progreso
                progress = min(int((self.consecutive_matches / self.REQUIRED_MATCHES) * 100), 100)
                self.progress_bar.setValue(progress)
                
                # Actualizar estado
                self.update_status(f"Reconociendo: {name}...", "🔍", "#fbbc04")
                
                # Si tenemos suficientes coincidencias consecutivas
                if self.consecutive_matches >= self.REQUIRED_MATCHES:
                    # Preparar datos del usuario
                    user_data = {
                        "authenticated": True,
                        "name": name,
                        "id": f"user_{name.lower().replace(' ', '_')}",
                        "confidence": confidence,
                        "auth_method": "facial_recognition",
                        "auth_timestamp": self.get_current_timestamp(),
                        "metadata": {
                            "face_system": "MediaPipe",
                            "confidence_score": confidence,
                            "last_seen": self.get_current_timestamp()
                        }
                    }
                    
                    self.update_status(f"¡Autenticado como {name}!", "✅", "#34a853")
                    return display_frame, user_data
            else:
                self.consecutive_matches = 0
                self.last_detected_name = None
                self.update_status("Rostro no reconocido", "❓", "#ea4335")
            
            return display_frame, None
            
        except Exception as e:
            logger.error(f"❌ Error en autenticación: {e}")
            self.update_status("Error en reconocimiento", "⚠️", "#ea4335")
            return display_frame, None
    
    def get_current_timestamp(self):
        """Obtener timestamp actual."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def finish_auth(self, user_data):
        """Finalizar autenticación con datos completos."""
        # Cerrar cámara
        if self.capture:
            self.capture.release()
            self.camera_active = False
        
        # Detener timer
        self.camera_timer.stop()
        
        # Emitir señal con datos completos
        self.auth_successful.emit(user_data)
    
    def on_auth_success(self, user_data):
        """Manejador de autenticación exitosa."""
        if not hasattr(self, 'auth_completed'):
            self.auth_completed = True
            
            # Completar barra de progreso
            self.progress_bar.setValue(100)
            
            # Deshabilitar botones
            self.skip_button.setEnabled(False)
            
            # Mostrar mensaje final
            user_name = user_data.get('name', 'Usuario')
            self.update_status(f"¡Bienvenido, {user_name}!", "✅", "#34a853")
            
            # Esperar y finalizar
            QTimer.singleShot(1500, lambda: self.finish_auth(user_data))
        
    def setup_ui(self):
        """Configurar la interfaz del diálogo"""
        self.setWindowTitle("Autenticación Facial - Asistente Personal")
        self.setFixedSize(700, 600)
        
        # Para ventana sin bordes nativos
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        
        # Layout principal
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Barra de título personalizada
        title_bar = QFrame()
        title_bar.setFixedHeight(50)
        title_bar.setStyleSheet("""
            QFrame {
                background-color: #2b2d30;
                border-bottom: 1px solid #3c4043;
            }
        """)
        
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(20, 0, 20, 0)
        
        title_label = QLabel("🔒 Autenticación Facial")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #e8eaed;")
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setToolTip("Cerrar")
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #e8eaed;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ea4335;
                border-radius: 6px;
                color: white;
            }
        """)
        
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(close_btn)
        
        # Contenido
        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: #202124;")
        
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(40, 40, 40, 40)
        content_layout.setSpacing(20)
        
        # Título principal
        main_title = QLabel("Bienvenido al Asistente Personal")
        main_title_font = QFont()
        main_title_font.setPointSize(22)
        main_title_font.setBold(True)
        main_title.setFont(main_title_font)
        main_title.setStyleSheet("color: #e8eaed;")
        main_title.setAlignment(Qt.AlignCenter)
        
        subtitle = QLabel("Por favor, autentícate para continuar")
        subtitle.setStyleSheet("color: #9aa0a6; font-size: 14px;")
        subtitle.setAlignment(Qt.AlignCenter)
        
        # Vista de cámara
        self.camera_frame = QFrame()
        self.camera_frame.setMinimumSize(400, 300)
        self.camera_frame.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border: 3px solid #3c4043;
                border-radius: 12px;
            }
        """)
        
        camera_inner_layout = QVBoxLayout(self.camera_frame)
        camera_inner_layout.setContentsMargins(2, 2, 2, 2)
        
        self.camera_label = QLabel()
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setMinimumSize(396, 296)
        self.camera_label.setStyleSheet("border-radius: 10px;")
        
        camera_inner_layout.addWidget(self.camera_label)
        
        # Indicador de estado
        self.status_frame = QFrame()
        self.status_frame.setFixedHeight(50)
        self.status_frame.setStyleSheet("""
            QFrame {
                background-color: #292a2d;
                border-radius: 8px;
            }
        """)
        
        status_layout = QHBoxLayout(self.status_frame)
        status_layout.setContentsMargins(20, 0, 20, 0)
        
        self.status_icon = QLabel("🔍")
        self.status_icon.setStyleSheet("font-size: 20px;")
        
        self.status_text = QLabel("Iniciando cámara...")
        self.status_text.setStyleSheet("color: #e8eaed; font-size: 14px;")
        
        self.attempts_label = QLabel(f"Intentos: {self.auth_attempts}/{self.MAX_ATTEMPTS}")
        self.attempts_label.setStyleSheet("color: #9aa0a6; font-size: 12px;")
        
        status_layout.addWidget(self.status_icon)
        status_layout.addWidget(self.status_text, 1)
        status_layout.addWidget(self.attempts_label)
        
        # Instrucciones
        instructions = QLabel(
            "• Asegúrate de tener buena iluminación\n"
            "• Mira directamente a la cámara\n"
            "• Mantén una distancia adecuada (50-100 cm)\n"
            "• Evita obstrucciones como lentes oscuros"
        )
        instructions.setStyleSheet("""
            QLabel {
                color: #9aa0a6;
                font-size: 12px;
                padding: 15px;
                background-color: #292a2d;
                border-radius: 8px;
                line-height: 1.5;
            }
        """)
        instructions.setAlignment(Qt.AlignLeft)
        
        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #292a2d;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background-color: #4285f4;
                border-radius: 3px;
            }
        """)
        
        # Botones
        button_layout = QHBoxLayout()
        
        self.skip_button = QPushButton("Modo Desarrollo (Saltar)")
        self.skip_button.setObjectName("secondary")
        self.skip_button.clicked.connect(self.on_skip)
        self.skip_button.setToolTip("Saltar autenticación para desarrollo")
        
        self.retry_button = QPushButton("Reintentar")
        self.retry_button.setObjectName("secondary")
        self.retry_button.clicked.connect(self.restart_camera)
        self.retry_button.hide()
        
        button_layout.addStretch()
        button_layout.addWidget(self.skip_button)
        button_layout.addWidget(self.retry_button)
        button_layout.addStretch()
        
        # Agregar widgets al layout de contenido
        content_layout.addWidget(main_title)
        content_layout.addWidget(subtitle)
        content_layout.addStretch(1)
        content_layout.addWidget(self.camera_frame, 0, Qt.AlignCenter)
        content_layout.addStretch(1)
        content_layout.addWidget(self.status_frame)
        content_layout.addWidget(instructions)
        content_layout.addWidget(self.progress_bar)
        content_layout.addLayout(button_layout)
        
        # Agregar al layout principal
        main_layout.addWidget(title_bar)
        main_layout.addWidget(content_widget)
        
        self.setLayout(main_layout)
        
        # Timer para actualizar la cámara
        self.camera_timer = QTimer()
        self.camera_timer.timeout.connect(self.update_frame)
        
    def setup_camera(self):
        """Inicializar la cámara"""
        try:
            self.capture = cv2.VideoCapture(0)
            if not self.capture.isOpened():
                self.show_error("No se pudo acceder a la cámara")
                return
            
            # Configurar cámara
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            self.camera_active = True
            self.camera_timer.start(30)  # ~30 FPS
            
            self.update_status("Cámara activa. Por favor, mire a la cámara.", "🔍", "#fbbc04")
            
        except Exception as e:
            self.show_error(f"Error al iniciar cámara: {str(e)}")
    
    def update_frame(self):
        """Actualizar frame de la cámara con reconocimiento facial real"""
        if not self.camera_active or not self.capture:
            return
        
        ret, frame = self.capture.read()
        if ret:
            # Voltear horizontalmente para efecto espejo
            frame = cv2.flip(frame, 1)
            
            # Procesar frame para reconocimiento facial
            processed_frame, user_data = self.process_frame_with_realtime_auth(frame)
            
            # Convertir OpenCV a QImage
            rgb_image = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            
            # Escalar manteniendo relación de aspecto
            pixmap = QPixmap.fromImage(qt_image)
            pixmap = pixmap.scaled(
                self.camera_label.size(), 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            
            self.camera_label.setPixmap(pixmap)
            
            # Si se detectó un rostro conocido
            if user_data and user_data.get("authenticated"):
                self.on_auth_success(user_data)
    
    def process_frame_with_realtime_auth(self, frame):
        """Procesar frame con tu sistema de reconocimiento facial real"""
        display_frame = frame.copy()
        user_data = None
        
        try:
            # 1. Detección de rostro usando tu sistema
            if self.face_system:
                # Suponiendo que tu face_system tiene un método detect_and_recognize
                result = self.face_system.detect_and_recognize(frame)
                
                if result and result.get("face_detected"):
                    self.face_detected = True
                    
                    # Dibujar bounding box
                    bbox = result.get("bbox")
                    if bbox:
                        x, y, w, h = bbox
                        color = (0, 255, 0)  # Verde para rostro detectado
                        
                        # Dibujar rectángulo
                        cv2.rectangle(display_frame, (x, y), (x+w, y+h), color, 2)
                        
                        # Etiqueta
                        label = "Rostro Detectado"
                        if result.get("name"):
                            label = f"Rostro: {result.get('name')}"
                            color = (0, 255, 255)  # Amarillo para reconocido
                        
                        cv2.putText(display_frame, label, (x, y-10), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                        
                        # Actualizar progreso si hay rostro
                        if not self.auth_start_time:
                            self.auth_start_time = datetime.now()
                        
                        elapsed = (datetime.now() - self.auth_start_time).total_seconds()
                        progress = min(int((elapsed / 3) * 100), 100)  # 3 segundos para autenticar
                        self.progress_bar.setValue(progress)
                        
                        # Si se reconoce un usuario conocido
                        if result.get("name") and result.get("confidence", 0) > 0.7:
                            user_data = {
                                "authenticated": True,
                                "name": result.get("name"),
                                "id": result.get("user_id", "unknown"),
                                "confidence": result.get("confidence", 0),
                                "metadata": result.get("metadata", {})
                            }
                            self.update_status(f"¡Usuario reconocido: {result['name']}!", "✅", "#34a853")
                        else:
                            self.update_status("Rostro detectado - Verificando...", "🔍", "#fbbc04")
                    
                    # Dibujar puntos faciales si están disponibles
                    landmarks = result.get("landmarks")
                    if landmarks:
                        for (x, y) in landmarks:
                            cv2.circle(display_frame, (int(x), int(y)), 2, (0, 255, 255), -1)
                else:
                    self.face_detected = False
                    self.auth_start_time = None
                    self.progress_bar.setValue(0)
                    self.update_status("Acérquese a la cámara...", "👤", "#ea4335")
            else:
                # Sistema de reconocimiento no disponible - usar detección básica
                self.fallback_face_detection(display_frame)
                
        except Exception as e:
            print(f"Error en procesamiento facial: {e}")
            self.fallback_face_detection(display_frame)
        
        return display_frame, user_data
    
    def fallback_face_detection(self, frame):
        """Detección básica de rostros cuando no hay sistema disponible"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(frame, "Rostro Detectado", (x, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Actualizar UI
            self.update_status("Rostro detectado (modo básico)", "👤", "#fbbc04")
            self.face_detected = True
            
            # Simular progreso
            if not self.auth_start_time:
                self.auth_start_time = datetime.now()
            
            elapsed = (datetime.now() - self.auth_start_time).total_seconds()
            progress = min(int((elapsed / 3) * 100), 100)
            self.progress_bar.setValue(progress)
            
            # Simular autenticación después de 3 segundos
            if elapsed > 3:
                user_data = {
                    "authenticated": True,
                    "name": "Usuario Demo",
                    "id": "demo_001",
                    "confidence": 0.95,
                    "metadata": {"demo": True}
                }
                return user_data
        
        return None
    
    def update_status(self, message, icon="", color="#e8eaed"):
        """Actualizar mensaje de estado"""
        self.status_text.setText(message)
        if icon:
            self.status_icon.setText(icon)
        
        # Actualizar color del texto
        self.status_text.setStyleSheet(f"color: {color}; font-size: 14px;")
    
    def on_auth_success(self, user_data):
        """Manejador de autenticación exitosa"""
        if not hasattr(self, 'auth_completed'):
            self.auth_completed = True
            
            # Detener timers
            self.camera_timer.stop()
            
            # Completar barra de progreso
            self.progress_bar.setValue(100)
            
            # Deshabilitar botones
            self.skip_button.setEnabled(False)
            
            # Mostrar mensaje final
            self.update_status(f"¡Autenticación exitosa! Bienvenido, {user_data['name']}.", "✅", "#34a853")
            
            # Esperar 1.5 segundos y emitir señal
            QTimer.singleShot(1500, lambda: self.finish_auth(user_data))
    
    def finish_auth(self, user_data):
        """Finalizar autenticación"""
        # Cerrar cámara
        if self.capture:
            self.capture.release()
            self.camera_active = False
        
        # Emitir señal
        self.auth_successful.emit(user_data)
    
    def on_skip(self):
        """Manejador para saltar autenticación"""
        reply = QMessageBox.question(
            self, "Modo Desarrollo",
            "¿Estás seguro de que quieres saltar la autenticación?\n\n"
            "Esta opción es solo para desarrollo. En producción, "
            "se requiere autenticación facial.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Detener cámara
            if self.capture:
                self.capture.release()
            
            # Detener timers
            self.camera_timer.stop()
            
            # Emitir señal
            self.auth_skipped.emit()
    
    def show_error(self, message):
        """Mostrar mensaje de error"""
        self.update_status(f"Error: {message}", "❌", "#ea4335")
        self.retry_button.show()
        self.skip_button.setEnabled(True)
        
        # Detener cámara
        if self.capture:
            self.capture.release()
            self.camera_active = False
        self.camera_timer.stop()
    
    def restart_camera(self):
        """Reiniciar la cámara"""
        self.auth_attempts += 1
        self.attempts_label.setText(f"Intentos: {self.auth_attempts}/{self.MAX_ATTEMPTS}")
        
        if self.auth_attempts >= self.MAX_ATTEMPTS:
            self.show_error("Demasiados intentos fallidos")
            self.retry_button.setEnabled(False)
            return
        
        self.retry_button.hide()
        self.progress_bar.setValue(0)
        self.face_detected = False
        self.auth_start_time = None
        self.setup_camera()
    
    def closeEvent(self, event):
        """Manejador de cierre de ventana"""
        # Liberar recursos de cámara
        if self.capture:
            self.capture.release()
        
        # Detener timers
        self.camera_timer.stop()
        
        event.accept()