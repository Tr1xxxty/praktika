import io
import os
import threading
import time
from PIL import Image, ImageOps, UnidentifiedImageError
WEIGHTS = os.getenv("YOLO_WEIGHTS", "yolov8n.pt")
DEFAULT_CONFIDENCE = float(os.getenv("YOLO_CONFIDENCE", "0.25"))
MAX_BYTES = 10 * 1024 * 1024
Image.MAX_IMAGE_PIXELS = 20_000_000
_model = None
_lock = threading.RLock()
class DetectionError(Exception):
    def __init__(self, message, status=422):
        super().__init__(message)
        self.status = status

def load_model():
    global _model
    with _lock:
        if _model is None:
            from ultralytics import YOLO
            _model = YOLO(WEIGHTS)
        return _model

def detect(image_bytes, confidence=DEFAULT_CONFIDENCE):
    if not 0 <= confidence <= 1:
        raise DetectionError("Поріг має бути від 0 до 1")
    if not image_bytes: raise DetectionError("Порожній файл")
    if len(image_bytes) > MAX_BYTES: raise DetectionError("Файл більший за 10 МБ", 413)
    try:
        with Image.open(io.BytesIO(image_bytes)) as source:
            if source.width * source.height > Image.MAX_IMAGE_PIXELS:
                raise DetectionError("Зображення завелике", 413)
            image = ImageOps.exif_transpose(source).convert("RGB")
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as exc:
        raise DetectionError("Файл не є коректним зображенням") from exc
    try:
        with _lock:
            model = load_model()
            started = time.perf_counter()
            prediction = model.predict(image, conf=confidence, verbose=False)[0]
            objects = [{"class": model.names[int(b.cls.item())],
                        "confidence": float(b.conf.item()),
                        "box": [float(v) for v in b.xyxy[0].tolist()]}
                       for b in prediction.boxes if float(b.conf.item()) >= confidence]
            elapsed = time.perf_counter() - started
        return {"objects": objects, "count": len(objects), "elapsed": elapsed,
                "width": image.width, "height": image.height, "confidence": confidence}
    except Exception as exc:
        raise DetectionError("Не вдалося виконати модель. Перевірте ваги й залежності", 503) from exc
