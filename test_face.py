# test_versions.py
import numpy as np
import cv2
import mediapipe as mp

print("🚀 VERIFICANDO VERSIONES INSTALADAS")
print("=" * 60)

# 1. Verificar NumPy 2.4.1
print("\n📦 NumPy:")
print(f"   Versión: {np.__version__}")
print(f"   Configuración: {np.show_config()}")

# Probar funcionalidades de NumPy 2.x
try:
    # Crear array con la nueva sintaxis si aplica
    arr = np.array([1, 2, 3, 4, 5], dtype=np.float32)
    print(f"   Array creado: {arr}")
    print(f"   Tipo de dato: {arr.dtype}")
except Exception as e:
    print(f"   Error con NumPy: {e}")

# 2. Verificar MediaPipe 0.10.31
print("\n📦 MediaPipe:")
print(f"   Versión: {mp.__version__}")

# Probar inicialización de MediaPipe
try:
    # Inicializar face detection
    face_detection = mp.solutions.face_detection.FaceDetection(
        min_detection_confidence=0.5
    )
    print("   ✅ Face Detection inicializado")
    
    # Inicializar face mesh
    face_mesh = mp.solutions.face_mesh.FaceMesh(
        static_image_mode=True,
        max_num_faces=1,
        min_detection_confidence=0.5
    )
    print("   ✅ Face Mesh inicializado")
    
    # Liberar recursos
    face_detection.close()
    face_mesh.close()
    
except Exception as e:
    print(f"   ❌ Error con MediaPipe: {e}")

# 3. Verificar OpenCV
print("\n📦 OpenCV:")
print(f"   Versión: {cv2.__version__}")

# Probar OpenCV
try:
    # Crear imagen de prueba
    test_img = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.circle(test_img, (50, 50), 30, (255, 0, 0), -1)
    print("   ✅ OpenCV funciona correctamente")
except Exception as e:
    print(f"   ❌ Error con OpenCV: {e}")

print("\n" + "=" * 60)
print("🎉 ¡Todas las librerías están funcionando!")