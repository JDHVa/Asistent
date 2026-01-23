# auth_dialog_simple.py
# Diálogo de autenticación facial SIMPLIFICADO y FUNCIONAL

import sys
import cv2
import numpy as np
from datetime import datetime
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, 
    QFrame, QProgressBar, QMessageBox, QHBoxLayout
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QImage, QPixmap

class SimpleAuthDialog(QDialog):
    """Diálogo de autenticación facial simplificado que SÍ funciona"""
    
    auth_successful = Signal(dict)
    auth_failed = Signal(str)
    auth_skipped = Signal()
    
    def __init__(self, face_system=None, parent=None):
        super().__init__(parent)
        self.face_system = face_system
        
        # Configuración de ventana
        self.setWindowTitle("🔐 Reconocimiento Facial")
        self.setFixedSize(600, 500)
        
        # Variables de autenticación
        self.capture = None
        self.camera_active = False
        self.auth_start_time = None
        self.last_detected_name = None
        self.consecutive_matches = 0
        self.REQUIRED_MATCHES = 3
        
        # UI
        self.setup_ui()
        self.start_camera()
    
    def setup_ui(self):
        """Configurar interfaz de usuario"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Título
        title = QLabel("Autenticación Facial")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: white;")
        title.setAlignment(Qt.AlignCenter)
        
        # Vista de cámara
        self.camera_frame = QFrame()
        self.camera_frame.setMinimumSize(400, 300)
        self.camera_frame.setStyleSheet("background-color: black; border: 2px solid #555; border-radius: 10px;")
        
        self.camera_label = QLabel()
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setMinimumSize(396, 296)
        
        camera_layout = QVBoxLayout(self.camera_frame)
        camera_layout.addWidget(self.camera_label)
        
        # Estado
        self.status_label = QLabel("Iniciando cámara...")
        self.status_label.setStyleSheet("color: #fbbc04; font-size: 16px;")
        self.status_label.setAlignment(Qt.AlignCenter)
        
        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                height: 10px;
                border-radius: 5px;
                background-color: #333;
            }
            QProgressBar::chunk {
                background-color: #4285f4;
                border-radius: 5px;
            }
        """)
        
        # Botones
        btn_layout = QHBoxLayout()
        
        self.skip_btn = QPushButton("Saltar (Modo Desarrollo)")
        self.skip_btn.clicked.connect(self.skip_auth)
        
        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.skip_btn)
        btn_layout.addWidget(self.cancel_btn)
        
        # Agregar todo al layout
        layout.addWidget(title)
        layout.addWidget(self.camera_frame)
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)
        layout.addStretch()
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        
        # Timer para actualizar la cámara
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
    
    def start_camera(self):
        """Iniciar la cámara"""
        try:
            self.capture = cv2.VideoCapture(0)
            if not self.capture.isOpened():
                self.show_error("No se pudo abrir la cámara")
                return
            
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            self.camera_active = True
            self.timer.start(30)  # ~30 FPS
            
            self.update_status("Cámara activa. Mire a la cámara...")
            
        except Exception as e:
            self.show_error(f"Error en cámara: {str(e)}")
    
    def update_frame(self):
        """Actualizar el frame de la cámara"""
        if not self.camera_active or not self.capture:
            return
        
        ret, frame = self.capture.read()
        if ret:
            # Voltear para efecto espejo
            frame = cv2.flip(frame, 1)
            
            # Procesar frame para reconocimiento
            processed_frame, user_data = self.process_frame(frame)
            
            # Mostrar en la interfaz
            rgb_image = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            qt_image = QImage(rgb_image.data, w, h, ch * w, QImage.Format_RGB888)
            
            pixmap = QPixmap.fromImage(qt_image)
            pixmap = pixmap.scaled(self.camera_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.camera_label.setPixmap(pixmap)
            
            # Si se autenticó exitosamente
            if user_data:
                self.on_auth_success(user_data)
    
    def process_frame(self, frame):
        """Procesar frame para reconocimiento facial"""
        display_frame = frame.copy()
        user_data = None
        
        try:
            if not self.face_system:
                return display_frame, None
            
            # 1. Detectar rostros
            face_locations = self.face_system.detect_faces(frame)
            
            if not face_locations:
                self.consecutive_matches = 0
                self.update_status("Acércate a la cámara...")
                return display_frame, None
            
            # 2. Tomar el primer rostro
            x1, y1, x2, y2 = face_locations[0]
            face_region = frame[y1:y2, x1:x2]
            
            if face_region.size == 0:
                return display_frame, None
            
            # 3. Reconocer rostro
            name, confidence = self.face_system.recognize_face(face_region)
            
            # 4. Dibujar en el frame
            color = (0, 255, 0) if name != "Desconocido" and confidence >= 0.6 else (0, 0, 255)
            cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 2)
            
            label = f"{name} ({confidence:.2f})"
            cv2.putText(display_frame, label, (x1, y1-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            
            # 5. Lógica de autenticación
            if name != "Desconocido" and confidence >= 0.6:
                if name == self.last_detected_name:
                    self.consecutive_matches += 1
                else:
                    self.consecutive_matches = 1
                    self.last_detected_name = name
                
                # Actualizar progreso
                progress = min(int((self.consecutive_matches / self.REQUIRED_MATCHES) * 100), 100)
                self.progress_bar.setValue(progress)
                
                self.update_status(f"Reconociendo: {name}... ({self.consecutive_matches}/{self.REQUIRED_MATCHES})")
                
                # Si tenemos suficientes coincidencias
                if self.consecutive_matches >= self.REQUIRED_MATCHES:
                    user_data = {
                        "authenticated": True,
                        "name": name,
                        "id": f"user_{name.lower().replace(' ', '_')}",
                        "confidence": confidence,
                        "metadata": {"face_recognition": True}
                    }
                    self.update_status(f"¡Autenticado como {name}!")
            
            else:
                self.consecutive_matches = 0
                self.last_detected_name = None
                self.update_status("Rostro no reconocido")
            
            return display_frame, user_data
            
        except Exception as e:
            print(f"Error en reconocimiento: {e}")
            return display_frame, None
    
    def update_status(self, message):
        """Actualizar mensaje de estado"""
        self.status_label.setText(message)
    
    def on_auth_success(self, user_data):
        """Autenticación exitosa"""
        self.timer.stop()
        if self.capture:
            self.capture.release()
        
        self.progress_bar.setValue(100)
        self.update_status(f"¡Bienvenido, {user_data['name']}!")
        
        # Esperar 1.5 segundos y emitir señal
        QTimer.singleShot(1500, lambda: self.finish_auth(user_data))
    
    def finish_auth(self, user_data):
        """Finalizar autenticación"""
        self.auth_successful.emit(user_data)
        self.accept()
    
    def skip_auth(self):
        """Saltar autenticación"""
        reply = QMessageBox.question(
            self, "Modo Desarrollo",
            "¿Saltar autenticación y continuar en modo desarrollo?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.capture:
                self.capture.release()
            self.timer.stop()
            self.auth_skipped.emit()
            self.accept()
    
    def show_error(self, message):
        """Mostrar error"""
        self.update_status(f"Error: {message}")
        if self.capture:
            self.capture.release()
        self.timer.stop()
    
    def closeEvent(self, event):
        """Manejar cierre de ventana"""
        if self.capture:
            self.capture.release()
        if self.timer.isActive():
            self.timer.stop()
        event.accept()