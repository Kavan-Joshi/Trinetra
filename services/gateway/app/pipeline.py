import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from trinetra_core.analytics import AnalyticsEngine
from trinetra_core.config import settings

log = logging.getLogger("trinetra.pipeline")

VEHICLE_CLASSES = {2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}
PLATE_RE = re.compile(r"\b([A-Z]{2}[\s\-]?\d{1,2}[\s\-]?[A-Z]{0,3}[\s\-]?\d{3,4})\b")


class AnalyticsPipeline(AnalyticsEngine):
    """Default engine: YOLOv8n vehicle detection + RapidOCR ANPR + InsightFace face detection & embedding (edge, CPU/GPU)."""
    def __init__(self, evidence_dir: Path):
        self.evidence_dir = evidence_dir
        self._model = None
        self._ocr = None
        self._face_app = None

    def _ensure_loaded(self) -> None:
        if self._model is None:
            from ultralytics import YOLO

            self._model = YOLO("yolov8n.pt")
            log.info("YOLOv8n detector loaded")
        if self._ocr is None:
            from rapidocr_onnxruntime import RapidOCR

            self._ocr = RapidOCR()
            log.info("RapidOCR engine loaded")
        if self._face_app is None:
            if not settings.face_detection:
                self._face_app = False
            else:
                try:
                    from insightface.app import FaceAnalysis

                    self._face_app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
                    self._face_app.prepare(ctx_id=-1, det_size=(640, 640))
                    log.info("InsightFace face analyzer loaded (buffalo_l)")
                except Exception as e:
                    self._face_app = False
                    log.warning("face analyzer unavailable: %s", e)

    def process(self, frame_bgr, camera) -> list[dict]:
        self._ensure_loaded()
        ts = datetime.now(timezone.utc)
        results = self._model.predict(frame_bgr, verbose=False, conf=0.45)
        detections = []

        def save_snapshot(path: str, img=frame_bgr) -> None:
            import cv2

            cv2.imwrite(path, img)

        # --- vehicles (ANPR) ---
        for box in results[0].boxes:
            cls = int(box.cls[0])
            if cls not in VEHICLE_CLASSES:
                continue
            x1, y1, x2, y2 = (int(v) for v in box.xyxy[0])
            vehicle_class = VEHICLE_CLASSES[cls]
            crop = frame_bgr[max(y1, 0):y2, max(x1, 0):x2]
            if crop.size == 0:
                continue
            plate, conf = self._read_plate(crop)
            color = self._detect_color(crop)
            detections.append({
                "kind": "vehicle",
                "bbox": [x1, y1, x2, y2],
                "vehicle_class": vehicle_class,
                "plate": plate,
                "plate_confidence": conf,
                "color": color,
                "ts": ts,
                "save_snapshot": save_snapshot,
            })

        # --- faces (InsightFace: detect + 512-d ArcFace embedding for accurate recognition) ---
        if self._face_app:
            try:
                faces = self._face_app.get(frame_bgr)
                for f in faces:
                    x1, y1, x2, y2 = (int(v) for v in f.bbox)
                    # round embedding to 4 dp to keep the event payload small
                    emb = [round(float(v), 4) for v in f.embedding.tolist()] if f.embedding is not None else None
                    detections.append({
                        "kind": "person",
                        "bbox": [x1, y1, x2, y2],
                        "vehicle_class": None,
                        "plate": None,
                        "plate_confidence": float(f.det_score),
                        "color": None,
                        "ts": ts,
                        "face": True,
                        "embedding": emb,
                        "save_snapshot": save_snapshot,
                    })
            except Exception:
                log.debug("face detection skipped on this frame", exc_info=True)
        return detections

    def _read_plate(self, vehicle_img) -> tuple[str | None, float | None]:
        import cv2

        # upscale small crops so the plate is legible to OCR
        h, w = vehicle_img.shape[:2]
        if max(h, w) < 500:
            scale = 2 if max(h, w) < 300 else 1.5
            vehicle_img = cv2.resize(vehicle_img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC)
        try:
            ocr_results, _ = self._ocr(vehicle_img)
        except Exception:
            return None, None
        if not ocr_results:
            return None, None
        best: tuple[str, float] | None = None
        for _box, text, score in ocr_results:
            cleaned = text.upper().replace(" ", "")
            m = PLATE_RE.search(cleaned.replace("-", ""))
            if m and (best is None or score > best[1]):
                best = (m.group(1), float(score))
        if best is None:
            return None, None
        plate = re.sub(r"[^A-Z0-9]", "", best[0])
        return plate, best[1]

    def _detect_color(self, crop) -> str | None:
        """Estimate the dominant vehicle colour from the crop's average BGR."""
        try:
            avg = crop.mean(axis=(0, 1))
            b, g, r = float(avg[0]), float(avg[1]), float(avg[2])
            if r > 180 and g > 180 and b > 180:
                return "White"
            if r < 60 and g < 60 and b < 60:
                return "Black"
            if abs(r - g) < 25 and abs(g - b) < 25 and r > 90:
                return "Silver/Grey"
            if r > 140 and g < 110 and b < 110:
                return "Red"
            if r < 110 and g < 140 and b > 130:
                return "Blue"
            if r > 190 and g > 170 and b < 90:
                return "Yellow"
            if r > 170 and g > 110 and b < 70:
                return "Orange"
            return "Silver/Grey"
        except Exception:
            return None


class MockAnalyticsEngine(AnalyticsEngine):
    """No-op engine for CPU-less/test environments — emits no detections.
    Selected via ``TRINETRA_ANALYTICS_ENGINE=mock``."""

    def process(self, frame_bgr, camera) -> list[dict]:
        return []


def get_analytics_engine(evidence_dir: Path) -> AnalyticsEngine:
    """Factory selecting the analytics engine from ``TRINETRA_ANALYTICS_ENGINE``.

    Default ``yolo_rapidocr`` → :class:`AnalyticsPipeline`. ``mock`` →
    :class:`MockAnalyticsEngine`. New engines register here (or via a future
    entry-point) without touching the adapter or bus.
    """
    name = os.getenv("TRINETRA_ANALYTICS_ENGINE", "yolo_rapidocr").lower()
    if name in ("mock", "none", "noop"):
        log.info("analytics engine: mock (no detections)")
        return MockAnalyticsEngine()
    log.info("analytics engine: yolo_rapidocr (YOLOv8n + RapidOCR)")
    return AnalyticsPipeline(evidence_dir=evidence_dir)
