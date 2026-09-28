import cv2
import easyocr
import requests
import matplotlib.pyplot as plt

# ======= CONFIGURACIÓN =======
ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzU4OTEzMDU0LCJpYXQiOjE3NTg5MTI3NTQsImp0aSI6IjE0MWNlYjVmMDExNjQzNjE4NzhjOTEyMWMzMjI0N2Y3IiwidXNlcl9pZCI6IjE4MSIsInJvbCI6IkFETUlOIn0.ZCLxM1wO4tbUauKKrolSwRGsyHgKZ1TZx-HUUthCA0E"  # 🔑 Coloca aquí tu access token JWT
HEADERS = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
DJANGO_URL = "http://127.0.0.1:8000/api/reconocimientos/procesar/"
CAMARA_ID = 1  # Solo tienes una cámara
# ==============================

# Inicializar OCR
reader = easyocr.Reader(['en'])

def enviar_a_django(placa, frame):
    data = {
        "tipo": "Placa",
        "texto": placa,
        "camara_id": CAMARA_ID,
    }

    # Codificar frame a JPEG para mandarlo
    _, buffer = cv2.imencode(".jpg", frame)
    files = {"captura": ("captura.jpg", buffer.tobytes(), "image/jpeg")}

    try:
        resp = requests.post(DJANGO_URL, headers=HEADERS, data=data, files=files, timeout=5)
        print("📡 Status:", resp.status_code)
        print("📡 Respuesta cruda:", resp.text[:200])
        if "application/json" in resp.headers.get("Content-Type", ""):
            print("📡 JSON:", resp.json())
    except Exception as e:
        print("⚠️ Error enviando a Django:", e)

# Abrir cámara
cap = cv2.VideoCapture(0)
print("📹 Procesando cámara... Ctrl+C para salir")

frame_count = 0

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("⚠️ No se pudo acceder a la cámara")
            break

        frame_count += 1
        if frame_count % 5 != 0:  # procesar 1 de cada 5 frames para fluidez
            continue

        # Preprocesamiento básico
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blur, 100, 200)

        # Detectar contornos candidatos a placa
        contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            aspect_ratio = w / float(h)

            if 2 < aspect_ratio < 6 and w > 100 and h > 30:
                placa_roi = frame[y:y+h, x:x+w]
                results = reader.readtext(placa_roi)

                for (bbox, text, prob) in results:
                    if prob > 0.3:
                        placa = text.strip().upper()
                        print("📌 Placa detectada:", placa)
                        enviar_a_django(placa, frame)

        # Mostrar cámara en VSCode usando matplotlib
        plt.imshow(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        plt.axis("off")
        plt.show(block=False)
        plt.pause(0.001)
        plt.clf()

except KeyboardInterrupt:
    print("\n🛑 Detenido por el usuario")

finally:
    cap.release()
