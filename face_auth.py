"""
app/facial_recognition/face_auth.py
Sistema de autenticación facial que maneja el flujo completo.
"""
import cv2
import time
import threading
from typing import Optional, Tuple, Dict
import logging

logger = logging.getLogger(__name__)


class FaceAuthenticator:
    """
    Sistema completo de autenticación facial.
    Controla cámara, autenticación y registro de usuarios.
    """
    
    def __init__(self, face_system, camera_index: int = 0):
        """
        Inicializa el autenticador facial.
        
        Args:
            face_system: Instancia de FaceSystem
            camera_index: Índice de la cámara a usar
        """
        self.face_system = face_system
        self.camera_index = camera_index
        self.camera = None
        self.is_camera_running = False
        self.last_authentication = None
        self.auth_lock = threading.Lock()
        
        # Configuración
        self.auth_timeout = 30  # segundos
        self.min_confidence = 0.14  # confianza mínima para autenticar
        self.required_consecutive_frames = 3  # frames consecutivos para validar
        
        # Estadísticas
        self.stats = {
            "auth_attempts": 0,
            "successful_auths": 0,
            "failed_auths": 0,
            "registration_attempts": 0,
            "successful_registrations": 0
        }
        
        logger.info("✅ FaceAuthenticator inicializado")
    
    def start_camera(self) -> bool:
        """
        Inicia la cámara para captura de video.
        
        Returns:
            True si la cámara se inició correctamente, False en caso contrario.
        """
        try:
            if self.camera is None or not self.camera.isOpened():
                self.camera = cv2.VideoCapture(self.camera_index)
                
                if not self.camera.isOpened():
                    logger.error("❌ No se pudo abrir la cámara")
                    return False
                
                # Configurar resolución
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                
                self.is_camera_running = True
                logger.info("📷 Cámara iniciada correctamente")
                return True
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error al iniciar cámara: {e}")
            return False
    
    def stop_camera(self):
        """Detiene la cámara y libera recursos."""
        if self.camera and self.camera.isOpened():
            self.camera.release()
            self.camera = None
        
        self.is_camera_running = False
        logger.info("📷 Cámara detenida")
    
    def capture_frame(self):
        """
        Captura un frame de la cámara.
        
        Returns:
            Frame capturado o None si hay error.
        """
        if not self.camera or not self.camera.isOpened():
            if not self.start_camera():
                return None
        
        try:
            ret, frame = self.camera.read()
            if ret and frame is not None:
                # Voltear horizontalmente para efecto espejo
                frame = cv2.flip(frame, 1)
                return frame
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error capturando frame: {e}")
            return None
    
    def authenticate_user(self, timeout: int = None) -> Tuple[bool, Optional[str], float]:
        """
        Autentica un usuario mediante reconocimiento facial.
        
        Args:
            timeout: Tiempo máximo en segundos para intentar autenticación.
        
        Returns:
            Tuple: (éxito, nombre_usuario, confianza)
        """
        if timeout is None:
            timeout = self.auth_timeout
        
        logger.info(f"🔐 Iniciando autenticación (timeout: {timeout}s)")
        self.stats["auth_attempts"] += 1
        
        # Verificar que haya usuarios registrados
        if self.face_system.get_user_count() == 0:
            logger.warning("⚠️ No hay usuarios registrados para autenticar")
            return False, None, 0.0
        
        # Iniciar cámara si no está activa
        if not self.start_camera():
            return False, None, 0.0
        
        # Variables para seguimiento
        start_time = time.time()
        consecutive_matches = 0
        best_match = None
        best_confidence = 0.0
        
        try:
            while time.time() - start_time < timeout:
                # Capturar frame
                frame = self.capture_frame()
                if frame is None:
                    time.sleep(0.1)
                    continue
                
                # Detectar rostros en el frame
                face_locations = self.face_system.detect_faces(frame)
                
                if not face_locations:
                    # Mostrar mensaje en frame
                    cv2.putText(frame, "No se detectan rostros", (10, 30),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    cv2.imshow("Autenticacion - Asistente Virtual", frame)
                    
                    # Salir con 'q'
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                    
                    time.sleep(0.1)
                    continue
                
                # Tomar el primer rostro (asumimos que es el usuario principal)
                x1, y1, x2, y2 = face_locations[0]
                face_region = frame[y1:y2, x1:x2]
                
                if face_region.size == 0:
                    time.sleep(0.1)
                    continue
                
                # Reconocer rostro
                name, confidence = self.face_system.recognize_face(face_region)
                
                # Dibujar resultados en el frame
                from face_utils import FaceUtils
                utils = FaceUtils()
                
                frame = utils.draw_face_boxes(
                    frame, 
                    face_locations, 
                    [name], 
                    [confidence]
                )
                
                # Mostrar tiempo restante
                elapsed = time.time() - start_time
                remaining = max(0, timeout - elapsed)
                
                cv2.putText(frame, f"Tiempo: {remaining:.1f}s", (10, 60),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                # Mostrar instrucciones
                cv2.putText(frame, "Presiona 'q' para cancelar", (10, 90),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
                
                # Mostrar frame
                cv2.imshow("Autenticacion - Asistente Virtual", frame)
                
                # Procesar reconocimiento
                if name != "Desconocido" and confidence >= self.min_confidence:
                    consecutive_matches += 1
                    
                    if confidence > best_confidence:
                        best_match = name
                        best_confidence = confidence
                    
                    # Si tenemos suficientes frames consecutivos, autenticamos
                    if consecutive_matches >= self.required_consecutive_frames:
                        logger.info(f"✅ Autenticación exitosa: {name} ({confidence:.2%})")
                        
                        # Actualizar estadísticas
                        self.stats["successful_auths"] += 1
                        self.last_authentication = {
                            "username": name,
                            "confidence": confidence,
                            "timestamp": time.time()
                        }
                        
                        # Cerrar ventana después de breve pausa
                        cv2.waitKey(500)
                        cv2.destroyAllWindows()
                        
                        return True, name, confidence
                else:
                    consecutive_matches = 0
                
                # Salir si se presiona 'q'
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    logger.info("⏹️ Autenticación cancelada por el usuario")
                    break
        
        except Exception as e:
            logger.error(f"❌ Error durante autenticación: {e}")
        
        finally:
            cv2.destroyAllWindows()
        
        # Si llegamos aquí, la autenticación falló
        self.stats["failed_auths"] += 1
        logger.warning("❌ Autenticación fallida o tiempo agotado")
        
        return False, best_match, best_confidence
    
    def register_new_user(self, username: str) -> Tuple[bool, str]:
        """
        Registra un nuevo usuario mediante la cámara.
        
        Args:
            username: Nombre del nuevo usuario
        
        Returns:
            Tuple: (éxito, mensaje)
        """
        logger.info(f"📝 Iniciando registro para usuario: {username}")
        self.stats["registration_attempts"] += 1
        
        # Validar nombre
        if not username or len(username.strip()) < 2:
            return False, "❌ El nombre debe tener al menos 2 caracteres"
        
        # Iniciar cámara
        if not self.start_camera():
            return False, "❌ No se pudo iniciar la cámara"
        
        # Variables para el registro
        captured_frame = None
        registration_complete = False
        message = ""
        
        try:
            print(f"\n📸 Registrando usuario: {username}")
            print("   Instrucciones:")
            print("   1. Colócate frente a la cámara")
            print("   2. Asegúrate de tener buena iluminación")
            print("   3. Presiona ESPACIO para capturar")
            print("   4. Presiona 'q' para cancelar")
            
            while not registration_complete:
                # Capturar frame
                frame = self.capture_frame()
                if frame is None:
                    time.sleep(0.1)
                    continue
                
                # Detectar rostros
                face_locations = self.face_system.detect_faces(frame)
                
                # Preparar frame para mostrar
                display_frame = frame.copy()
                
                if face_locations:
                    # Hay rostros detectados
                    x1, y1, x2, y2 = face_locations[0]
                    
                    # Validar calidad para registro
                    face_region = frame[y1:y2, x1:x2]
                    from face_utils import FaceUtils
                    utils = FaceUtils()
                    
                    quality_score, problems = utils.calculate_face_quality(face_region)
                    
                    # Dibujar cuadro y información
                    color = (0, 255, 0) if quality_score >= 70 else (0, 165, 255) if quality_score >= 50 else (0, 0, 255)
                    
                    cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(display_frame, f"Calidad: {quality_score}/100", 
                               (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                    
                    # Mostrar problemas si los hay
                    if problems:
                        for i, problem in enumerate(problems[:2]):
                            cv2.putText(display_frame, problem, (10, 60 + i*25),
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
                    
                    # Instrucciones
                    cv2.putText(display_frame, "ESPACIO: Capturar | q: Cancelar", 
                               (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                    
                    if quality_score < 50:
                        cv2.putText(display_frame, "MUEVETE/ILUMINATE MEJOR", 
                                   (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    
                else:
                    # No hay rostros detectados
                    cv2.putText(display_frame, "ACERCATE A LA CAMARA", 
                               (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    cv2.putText(display_frame, "ESPACIO: Capturar | q: Cancelar", 
                               (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                
                # Mostrar nombre del usuario
                cv2.putText(display_frame, f"Usuario: {username}", 
                           (10, display_frame.shape[0] - 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                # Mostrar frame
                cv2.imshow(f"Registro: {username}", display_frame)
                
                # Manejar teclas
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord(' '):  # ESPACIO - Capturar
                    if face_locations and len(face_locations) == 1:
                        # Validar que la calidad sea suficiente
                        if quality_score >= 50:
                            captured_frame = frame
                            success, message = self.face_system.register_face(captured_frame, username)
                            
                            if success:
                                self.stats["successful_registrations"] += 1
                                registration_complete = True
                            else:
                                # Mostrar error y continuar
                                cv2.putText(display_frame, f"ERROR: {message}", 
                                           (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                                cv2.imshow(f"Registro: {username}", display_frame)
                                cv2.waitKey(2000)
                        
                        else:
                            # Calidad insuficiente
                            cv2.putText(display_frame, "CALIDAD INSUFICIENTE", 
                                       (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                            cv2.putText(display_frame, "Mejora la iluminacion/posicion", 
                                       (10, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
                            cv2.imshow(f"Registro: {username}", display_frame)
                            cv2.waitKey(1500)
                    
                    else:
                        # No hay rostro o hay múltiples
                        error_msg = "MULTIPLES ROSTROS" if len(face_locations) > 1 else "NO HAY ROSTRO"
                        cv2.putText(display_frame, error_msg, 
                                   (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                        cv2.imshow(f"Registro: {username}", display_frame)
                        cv2.waitKey(1500)
                
                elif key == ord('q'):  # q - Cancelar
                    message = "❌ Registro cancelado por el usuario"
                    registration_complete = True
        
        except Exception as e:
            logger.error(f"❌ Error durante registro: {e}")
            message = f"❌ Error durante registro: {str(e)}"
        
        finally:
            cv2.destroyAllWindows()
        
        if registration_complete and captured_frame is not None and "exitosamente" in message:
            return True, message
        else:
            if not message:
                message = "❌ Registro fallido"
            return False, message
    
    def get_status(self) -> Dict:
        """
        Obtiene el estado actual del autenticador.
        
        Returns:
            Diccionario con información de estado.
        """
        return {
            "camera_running": self.is_camera_running,
            "camera_index": self.camera_index,
            "users_registered": self.face_system.get_user_count(),
            "last_authentication": self.last_authentication,
            "auth_timeout": self.auth_timeout,
            "min_confidence": self.min_confidence,
            "stats": self.stats.copy()
        }
    
    def reset_stats(self):
        """Reinicia las estadísticas del autenticador."""
        self.stats = {
            "auth_attempts": 0,
            "successful_auths": 0,
            "failed_auths": 0,
            "registration_attempts": 0,
            "successful_registrations": 0
        }
        logger.info("📊 Estadísticas reiniciadas")


# ========== FUNCIONES DE CONVENIENCIA ==========

def run_authentication_flow(face_system=None):
    """
    Ejecuta un flujo completo de autenticación.
    
    Args:
        face_system: Instancia de FaceSystem (opcional, se crea si es None)
    
    Returns:
        Tuple: (éxito, nombre_usuario, confianza) o (False, None, 0.0)
    """
    try:
        if face_system is None:
            from face_system import FaceSystem
            face_system = FaceSystem()
        
        authenticator = FaceAuthenticator(face_system)
        
        print("\n" + "=" * 50)
        print("🔐 FLUJO DE AUTENTICACIÓN FACIAL")
        print("=" * 50)
        
        # Verificar si hay usuarios registrados
        if face_system.get_user_count() == 0:
            print("\n⚠️  No hay usuarios registrados.")
            print("   ¿Deseas registrar un nuevo usuario? (s/n)")
            
            if input().strip().lower() == 's':
                username = input("Nombre del nuevo usuario: ").strip()
                if username:
                    success, message = authenticator.register_new_user(username)
                    print(f"\n{message}")
                    
                    if success:
                        print("\n✅ Usuario registrado. Ahora puedes autenticarte.")
                    else:
                        return False, None, 0.0
            else:
                return False, None, 0.0
        
        # Ejecutar autenticación
        print("\n🎯 Colócate frente a la cámara para autenticarte...")
        print("   Tienes 30 segundos para reconocerte.")
        print("   Presiona 'q' en la ventana para cancelar.")
        
        success, username, confidence = authenticator.authenticate_user(timeout=10)
        
        if success:
            print(f"\n✅ ¡Autenticación exitosa!")
            print(f"   Bienvenido/a: {username}")
            print(f"   Confianza: {confidence:.2%}")
        else:
            print("\n❌ Autenticación fallida")
            if username:
                print(f"   Mejor coincidencia: {username} ({confidence:.2%})")
        
        authenticator.stop_camera()
        return success, username, confidence
        
    except Exception as e:
        print(f"❌ Error en el flujo de autenticación: {e}")
        return False, None, 0.0


# ========== PRUEBA DEL MÓDULO ==========

if __name__ == "__main__":
    print("🧪 PRUEBA DE FACE_AUTH")
    print("=" * 50)
    
    try:
        from face_system import FaceSystem
        
        # Crear instancias
        face_system = FaceSystem()
        authenticator = FaceAuthenticator(face_system)
        
        print("✅ Módulos cargados correctamente")
        
        # Mostrar estado inicial
        status = authenticator.get_status()
        print(f"\n📊 Estado inicial:")
        print(f"   Usuarios registrados: {status['users_registered']}")
        print(f"   Cámara: {'Conectada' if status['camera_running'] else 'Desconectada'}")
        
        # Menú de pruebas
        while True:
            print("\n" + "=" * 50)
            print("MENÚ DE PRUEBAS - FACE_AUTH")
            print("=" * 50)
            print("1. Probar autenticación (30 segundos)")
            print("2. Registrar nuevo usuario")
            print("3. Ver estadísticas")
            print("4. Reiniciar estadísticas")
            print("5. Salir")
            
            choice = input("\nSelecciona opción (1-5): ").strip()
            
            if choice == "1":
                print("\n🔐 Iniciando autenticación...")
                success, username, confidence = authenticator.authenticate_user(timeout=30)
                
                if success:
                    print(f"✅ ¡Autenticado como {username}! (confianza: {confidence:.2%})")
                else:
                    print("❌ Autenticación fallida")
            
            elif choice == "2":
                username = input("Nombre del nuevo usuario: ").strip()
                if username:
                    success, message = authenticator.register_new_user(username)
                    print(f"\nResultado: {message}")
            
            elif choice == "3":
                status = authenticator.get_status()
                stats = status['stats']
                print(f"\n📊 Estadísticas:")
                print(f"   Intentos de autenticación: {stats['auth_attempts']}")
                print(f"   Autenticaciones exitosas: {stats['successful_auths']}")
                print(f"   Autenticaciones fallidas: {stats['failed_auths']}")
                print(f"   Intentos de registro: {stats['registration_attempts']}")
                print(f"   Registros exitosos: {stats['successful_registrations']}")
            
            elif choice == "4":
                authenticator.reset_stats()
                print("✅ Estadísticas reiniciadas")
            
            elif choice == "5":
                print("👋 Saliendo...")
                authenticator.stop_camera()
                break
            
            else:
                print("❌ Opción no válida")
    
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        print("💡 Asegúrate de que face_system.py esté en la misma carpeta.")
    except Exception as e:
        print(f"❌ Error: {e}")