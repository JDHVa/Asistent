import cv2
import time
import threading
from typing import Optional, Tuple, Dict
import logging

logger = logging.getLogger(__name__)

class FaceAuthenticator:
    def __init__(self, face_system, camera_index: int = 0):
        self.face_system = face_system
        self.camera_index = camera_index
        self.camera = None
        self.is_camera_running = False
        self.last_authentication = None
        self.auth_lock = threading.Lock()
        
        self.auth_timeout = 30
        self.min_confidence = 0.14
        self.required_consecutive_frames = 3
        
        self.stats = {
            "auth_attempts": 0,
            "successful_auths": 0,
            "failed_auths": 0,
            "registration_attempts": 0,
            "successful_registrations": 0
        }
        
        logger.info("FaceAuthenticator inicializado")

    def start_camera(self) -> bool:
        try:
            if self.camera is None or not self.camera.isOpened():
                self.camera = cv2.VideoCapture(self.camera_index)
                
                if not self.camera.isOpened():
                    logger.error("No se pudo abrir la cámara")
                    return False
                
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                
                self.is_camera_running = True
                logger.info("Cámara iniciada correctamente")
                return True
            
            return True
            
        except Exception as e:
            logger.error(f"Error al iniciar cámara: {e}")
            return False

    def stop_camera(self):
        if self.camera and self.camera.isOpened():
            self.camera.release()
            self.camera = None
        
        self.is_camera_running = False
        logger.info("Cámara detenida")

    def capture_frame(self):
        if not self.camera or not self.camera.isOpened():
            if not self.start_camera():
                return None
        
        try:
            ret, frame = self.camera.read()
            if ret and frame is not None:
                frame = cv2.flip(frame, 1)
                return frame
            
            return None
            
        except Exception as e:
            logger.error(f"Error capturando frame: {e}")
            return None

    def authenticate_user(self, timeout: int = None) -> Tuple[bool, Optional[str], float]:
        if timeout is None:
            timeout = self.auth_timeout
        
        logger.info(f"Iniciando autenticación (timeout: {timeout}s)")
        self.stats["auth_attempts"] += 1
        
        if self.face_system.get_user_count() == 0:
            logger.warning("No hay usuarios registrados para autenticar")
            return False, None, 0.0
        
        if not self.start_camera():
            return False, None, 0.0
        
        start_time = time.time()
        consecutive_matches = 0
        best_match = None
        best_confidence = 0.0
        
        try:
            while time.time() - start_time < timeout:
                frame = self.capture_frame()
                if frame is None:
                    time.sleep(0.1)
                    continue
                
                face_locations = self.face_system.detect_faces(frame)
                
                if not face_locations:
                    cv2.putText(frame, "No se detectan rostros", (10, 30),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    cv2.imshow("Autenticacion - Asistente Virtual", frame)
                    
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                    
                    time.sleep(0.1)
                    continue
                
                x1, y1, x2, y2 = face_locations[0]
                face_region = frame[y1:y2, x1:x2]
                
                if face_region.size == 0:
                    time.sleep(0.1)
                    continue
                
                name, confidence = self.face_system.recognize_face(face_region)
                
                from face_utils import FaceUtils
                utils = FaceUtils()
                
                frame = utils.draw_face_boxes(
                    frame,
                    face_locations,
                    [name],
                    [confidence]
                )
                
                elapsed = time.time() - start_time
                remaining = max(0, timeout - elapsed)
                
                cv2.putText(frame, f"Tiempo: {remaining:.1f}s", (10, 60),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                cv2.putText(frame, "Presiona 'q' para cancelar", (10, 90),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
                
                cv2.imshow("Autenticacion - Asistente Virtual", frame)
                
                if name != "Desconocido" and confidence >= self.min_confidence:
                    consecutive_matches += 1
                    
                    if confidence > best_confidence:
                        best_match = name
                        best_confidence = confidence
                    
                    if consecutive_matches >= self.required_consecutive_frames:
                        logger.info(f"Autenticación exitosa: {name} ({confidence:.2%})")
                        
                        self.stats["successful_auths"] += 1
                        self.last_authentication = {
                            "username": name,
                            "confidence": confidence,
                            "timestamp": time.time()
                        }
                        
                        cv2.waitKey(500)
                        cv2.destroyAllWindows()
                        
                        return True, name, confidence
                else:
                    consecutive_matches = 0
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    logger.info("Autenticación cancelada por el usuario")
                    break
        
        except Exception as e:
            logger.error(f"Error durante autenticación: {e}")
        
        finally:
            cv2.destroyAllWindows()
        
        self.stats["failed_auths"] += 1
        logger.warning("Autenticación fallida o tiempo agotado")
        
        return False, best_match, best_confidence

    def register_new_user(self, username: str) -> Tuple[bool, str]:
        logger.info(f"Iniciando registro para usuario: {username}")
        self.stats["registration_attempts"] += 1
        
        if not username or len(username.strip()) < 2:
            return False, "El nombre debe tener al menos 2 caracteres"
        
        if not self.start_camera():
            return False, "No se pudo iniciar la cámara"
        
        captured_frame = None
        registration_complete = False
        message = ""
        
        try:
            print(f"\nRegistrando usuario: {username}")
            print("   Instrucciones:")
            print("   1. Colócate frente a la cámara")
            print("   2. Asegúrate de tener buena iluminación")
            print("   3. Presiona ESPACIO para capturar")
            print("   4. Presiona 'q' para cancelar")
            
            while not registration_complete:
                frame = self.capture_frame()
                if frame is None:
                    time.sleep(0.1)
                    continue
                
                face_locations = self.face_system.detect_faces(frame)
                display_frame = frame.copy()
                
                if face_locations:
                    x1, y1, x2, y2 = face_locations[0]
                    face_region = frame[y1:y2, x1:x2]
                    
                    from face_utils import FaceUtils
                    utils = FaceUtils()
                    
                    quality_score, problems = utils.calculate_face_quality(face_region)
                    
                    color = (0, 255, 0) if quality_score >= 70 else (0, 165, 255) if quality_score >= 50 else (0, 0, 255)
                    
                    cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(display_frame, f"Calidad: {quality_score}/100",
                               (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                    
                    if problems:
                        for i, problem in enumerate(problems[:2]):
                            cv2.putText(display_frame, problem, (10, 60 + i*25),
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
                    
                    cv2.putText(display_frame, "ESPACIO: Capturar | q: Cancelar",
                               (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                    
                    if quality_score < 50:
                        cv2.putText(display_frame, "MUEVETE/ILUMINATE MEJOR",
                                   (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    
                else:
                    cv2.putText(display_frame, "ACERCATE A LA CAMARA",
                               (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    cv2.putText(display_frame, "ESPACIO: Capturar | q: Cancelar",
                               (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                
                cv2.putText(display_frame, f"Usuario: {username}",
                           (10, display_frame.shape[0] - 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                cv2.imshow(f"Registro: {username}", display_frame)
                
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord(' '):
                    if face_locations and len(face_locations) == 1:
                        if quality_score >= 50:
                            captured_frame = frame
                            success, message = self.face_system.register_face(captured_frame, username)
                            
                            if success:
                                self.stats["successful_registrations"] += 1
                                registration_complete = True
                            else:
                                cv2.putText(display_frame, f"ERROR: {message}",
                                           (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                                cv2.imshow(f"Registro: {username}", display_frame)
                                cv2.waitKey(2000)
                        
                        else:
                            cv2.putText(display_frame, "CALIDAD INSUFICIENTE",
                                       (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                            cv2.putText(display_frame, "Mejora la iluminacion/posicion",
                                       (10, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
                            cv2.imshow(f"Registro: {username}", display_frame)
                            cv2.waitKey(1500)
                    
                    else:
                        error_msg = "MULTIPLES ROSTROS" if len(face_locations) > 1 else "NO HAY ROSTRO"
                        cv2.putText(display_frame, error_msg,
                                   (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                        cv2.imshow(f"Registro: {username}", display_frame)
                        cv2.waitKey(1500)
                
                elif key == ord('q'):
                    message = "Registro cancelado por el usuario"
                    registration_complete = True
        
        except Exception as e:
            logger.error(f"Error durante registro: {e}")
            message = f"Error durante registro: {str(e)}"
        
        finally:
            cv2.destroyAllWindows()
        
        if registration_complete and captured_frame is not None and "exitosamente" in message:
            return True, message
        else:
            if not message:
                message = "Registro fallido"
            return False, message

    def get_status(self) -> Dict:
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
        self.stats = {
            "auth_attempts": 0,
            "successful_auths": 0,
            "failed_auths": 0,
            "registration_attempts": 0,
            "successful_registrations": 0
        }
        logger.info("Estadísticas reiniciadas")

def run_authentication_flow(face_system=None):
    try:
        if face_system is None:
            from face_system import FaceSystem
            face_system = FaceSystem()
        
        authenticator = FaceAuthenticator(face_system)
        
        print("\n" + "=" * 50)
        print("FLUJO DE AUTENTICACIÓN FACIAL")
        print("=" * 50)
        
        if face_system.get_user_count() == 0:
            print("\nNo hay usuarios registrados.")
            print("   ¿Deseas registrar un nuevo usuario? (s/n)")
            
            if input().strip().lower() == 's':
                username = input("Nombre del nuevo usuario: ").strip()
                if username:
                    success, message = authenticator.register_new_user(username)
                    print(f"\n{message}")
                    
                    if success:
                        print("\nUsuario registrado. Ahora puedes autenticarte.")
                    else:
                        return False, None, 0.0
            else:
                return False, None, 0.0
        
        print("\nColócate frente a la cámara para autenticarte...")
        print("   Tienes 30 segundos para reconocerte.")
        print("   Presiona 'q' en la ventana para cancelar.")
        
        success, username, confidence = authenticator.authenticate_user(timeout=10)
        
        if success:
            print(f"\n¡Autenticación exitosa!")
            print(f"   Bienvenido/a: {username}")
            print(f"   Confianza: {confidence:.2%}")
        else:
            print("\nAutenticación fallida")
            if username:
                print(f"   Mejor coincidencia: {username} ({confidence:.2%})")
        
        authenticator.stop_camera()
        return success, username, confidence
        
    except Exception as e:
        print(f"Error en el flujo de autenticación: {e}")
        return False, None, 0.0

if __name__ == "__main__":
    print("PRUEBA DE FACE_AUTH")
    print("=" * 50)
    
    try:
        from face_system import FaceSystem
        
        face_system = FaceSystem()
        authenticator = FaceAuthenticator(face_system)
        
        print("Módulos cargados correctamente")
        
        status = authenticator.get_status()
        print(f"\nEstado inicial:")
        print(f"   Usuarios registrados: {status['users_registered']}")
        print(f"   Cámara: {'Conectada' if status['camera_running'] else 'Desconectada'}")
        
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
                print("\nIniciando autenticación...")
                success, username, confidence = authenticator.authenticate_user(timeout=30)
                
                if success:
                    print(f"¡Autenticado como {username}! (confianza: {confidence:.2%})")
                else:
                    print("Autenticación fallida")
            
            elif choice == "2":
                username = input("Nombre del nuevo usuario: ").strip()
                if username:
                    success, message = authenticator.register_new_user(username)
                    print(f"\nResultado: {message}")
            
            elif choice == "3":
                status = authenticator.get_status()
                stats = status['stats']
                print(f"\nEstadísticas:")
                print(f"   Intentos de autenticación: {stats['auth_attempts']}")
                print(f"   Autenticaciones exitosas: {stats['successful_auths']}")
                print(f"   Autenticaciones fallidas: {stats['failed_auths']}")
                print(f"   Intentos de registro: {stats['registration_attempts']}")
                print(f"   Registros exitosos: {stats['successful_registrations']}")
            
            elif choice == "4":
                authenticator.reset_stats()
                print("Estadísticas reiniciadas")
            
            elif choice == "5":
                print("Saliendo...")
                authenticator.stop_camera()
                break
            
            else:
                print("Opción no válida")
    
    except ImportError as e:
        print(f"Error de importación: {e}")
        print("Asegúrate de que face_system.py esté en la misma carpeta.")
    except Exception as e:
        print(f"Error: {e}")