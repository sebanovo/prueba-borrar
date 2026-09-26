# app/views/reconocimiento_ia.py
import cv2
import numpy as np
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ultralytics import YOLO
from app.models.acceso import Reconocimiento, IntentoAcceso
from app.models.vehiculo import Vehiculo
from app.serializers.acceso import ReconocimientoSerializer, IntentoAccesoSerializer

# 🔹 Cargar modelo YOLO entrenado para placas
yolo_model = YOLO("yolov8n.pt")   # por ahora el default, luego lo cambiamos a uno especializado

class ReconocerIAView(APIView):
    def post(self, request):
        file = request.FILES.get("image")
        if not file:
            return Response({"error": "Debes enviar una imagen."}, status=400)

        # Leer la imagen en OpenCV
        img_bytes = file.read()
        np_arr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        # 🔹 Ejecutar YOLO detección
        results = yolo_model(frame)

        detections = []
        for r in results:
            for box in r.boxes:
                conf = float(box.conf[0])
                cls = int(box.cls[0])
                # Para placas, simplificado: guardar solo el bounding box
                detections.append({"clase": cls, "confianza": conf})

        if not detections:
            return Response({"message": "No se detectó nada"}, status=200)

        # 🔹 Simulación: tomamos la primera detección como placa reconocida
        plate_text = "PLACA123"  # aquí luego integras OCR
        vehicle = Vehiculo.objects.filter(placa=plate_text).first()

        # Guardar reconocimiento
        reco = Reconocimiento.objects.create(
            tipo="VEHICULO",
            captura=file,
        )

        intento = IntentoAcceso.objects.create(
            reconocimiento=reco,
            vehiculo=vehicle,
            resultado="ACEPTADO" if vehicle else "RECHAZADO",
            motivo="Vehículo registrado" if vehicle else "No encontrado en BD"
        )

        return Response({
            "detections": detections,
            "plate": plate_text,
            "matched": bool(vehicle),
            "intento": IntentoAccesoSerializer(intento).data
        }, status=200)
