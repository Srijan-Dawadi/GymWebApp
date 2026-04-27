"""
face_service.py
---------------
Face recognition (InsightFace buffalo_l) + Anti-spoofing (MiniFASNet ONNX).

Registration: multi-angle enrollment — stores list of embeddings per member.
Attendance:   extract_embedding() → find_best_match() pipeline.
"""

import os
import threading
import warnings
warnings.filterwarnings('ignore', category=FutureWarning, module='insightface')

# ── Availability flags ────────────────────────────────────────
try:
    import numpy as np
    import insightface  # noqa: F401
    INSIGHTFACE_AVAILABLE = True
except ImportError:
    INSIGHTFACE_AVAILABLE = False

try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False

# ── Thread-safe singletons ────────────────────────────────────────
_face_app   = None
_spoof_sess = None
_face_lock  = threading.Lock()
_spoof_lock = threading.Lock()

_ANTISPOOF_MODEL = os.path.join(
    os.path.dirname(__file__), 'static', 'antispoof', 'antispoof.onnx'
)

LIVENESS_THRESHOLD = 0.6


def _get_face_app():
    """Load InsightFace once, thread-safe. Returns None if unavailable."""
    if not INSIGHTFACE_AVAILABLE:
        return None
    global _face_app
    if _face_app is not None:
        return _face_app
    with _face_lock:
        if _face_app is None:
            from insightface.app import FaceAnalysis
            app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
            app.prepare(ctx_id=-1, det_size=(640, 640))
            _face_app = app
    return _face_app


def _get_spoof_session():
    """Load anti-spoof ONNX session once, thread-safe. Returns None if unavailable."""
    if not ONNX_AVAILABLE or not os.path.exists(_ANTISPOOF_MODEL):
        return None
    global _spoof_sess
    if _spoof_sess is not None:
        return _spoof_sess
    with _spoof_lock:
        if _spoof_sess is None:
            opts = ort.SessionOptions()
            opts.inter_op_num_threads = 1
            opts.intra_op_num_threads = 2
            _spoof_sess = ort.InferenceSession(
                _ANTISPOOF_MODEL,
                sess_options=opts,
                providers=['CPUExecutionProvider'],
            )
    return _spoof_sess


def _check_liveness(img_bgr, bbox) -> tuple:
    """Run anti-spoof check. Returns (is_real: bool, score: float)."""
    sess = _get_spoof_session()
    if sess is None:
        return True, 1.0

    import cv2
    x1, y1, x2, y2 = [int(v) for v in bbox]
    h, w = img_bgr.shape[:2]
    pad_x = int((x2 - x1) * 0.2)
    pad_y = int((y2 - y1) * 0.2)
    x1 = max(0, x1 - pad_x); y1 = max(0, y1 - pad_y)
    x2 = min(w, x2 + pad_x); y2 = min(h, y2 + pad_y)
    face_crop = img_bgr[y1:y2, x1:x2]
    if face_crop.size == 0:
        return True, 1.0
    face_resized = cv2.resize(face_crop, (128, 128))
    face_rgb = cv2.cvtColor(face_resized, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
    face_tensor = np.transpose(face_rgb, (2, 0, 1))[np.newaxis, :]
    input_name = sess.get_inputs()[0].name
    outputs = sess.run(None, {input_name: face_tensor})
    logits = outputs[0][0]
    exp = np.exp(logits - np.max(logits))
    probs = exp / exp.sum()
    real_score = float(probs[1])
    return real_score >= LIVENESS_THRESHOLD, real_score


def extract_embedding_for_enrollment(image_bytes: bytes) -> dict:
    """
    Extract face embedding for member registration.
    NO liveness check — registration is done by staff in a controlled environment.

    Returns dict:
      status: 'ok' | 'no_face' | 'unavailable' | 'error'
      embedding: list[float] or None
      message: str
    """
    if not INSIGHTFACE_AVAILABLE:
        return {'status': 'unavailable', 'embedding': None,
                'message': 'Face recognition not available on this server.'}
    try:
        import cv2
        app = _get_face_app()
        if app is None:
            return {'status': 'unavailable', 'embedding': None,
                    'message': 'Face recognition model not loaded.'}
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return {'status': 'error', 'embedding': None, 'message': 'Could not decode image.'}
        faces = app.get(img)
        if not faces:
            return {'status': 'no_face', 'embedding': None, 'message': 'No face detected.'}
        face = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
        return {'status': 'ok', 'embedding': face.normed_embedding.tolist(), 'message': 'OK'}
    except Exception as e:
        return {'status': 'error', 'embedding': None,
                'message': f'Face processing error: {str(e)}'}


def extract_embedding(image_bytes: bytes) -> dict:
    """
    Detect face → liveness check → extract embedding from image bytes.

    Returns dict:
      status: 'ok' | 'no_face' | 'spoof' | 'unavailable' | 'error'
      embedding: list[float] or None
      liveness_score: float
      message: str
    """
    if not INSIGHTFACE_AVAILABLE:
        return {'status': 'unavailable', 'embedding': None, 'liveness_score': 0.0,
                'message': 'Face recognition not available on this server.'}
    try:
        import cv2
        app = _get_face_app()
        if app is None:
            return {'status': 'unavailable', 'embedding': None, 'liveness_score': 0.0,
                    'message': 'Face recognition model not loaded.'}
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return {'status': 'error', 'embedding': None, 'liveness_score': 0.0,
                    'message': 'Could not decode image.'}
        faces = app.get(img)
        if not faces:
            return {'status': 'no_face', 'embedding': None, 'liveness_score': 0.0,
                    'message': 'No face detected.'}
        face = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
        is_real, score = _check_liveness(img, face.bbox)
        if not is_real:
            return {'status': 'spoof', 'embedding': None,
                    'liveness_score': round(score, 3),
                    'message': 'Liveness check failed — please look directly at the camera.'}
        return {'status': 'ok', 'embedding': face.normed_embedding.tolist(),
                'liveness_score': round(score, 3), 'message': 'OK'}
    except Exception as e:
        return {'status': 'error', 'embedding': None, 'liveness_score': 0.0,
                'message': f'Face processing error: {str(e)}'}


def find_best_match(probe_embedding: list, threshold: float = 0.4) -> tuple:
    """
    Match probe_embedding against all stored member multi-angle embeddings.
    face_descriptor = [[emb1], [emb2], [emb3], [emb4], [emb5]]
    Returns (member_id, best_score) or (None, 0.0).
    """
    if not INSIGHTFACE_AVAILABLE or probe_embedding is None:
        return None, 0.0

    from members.models import Member
    probe = np.array(probe_embedding, dtype=np.float32)
    best_id, best_score = None, -1.0

    for m in Member.objects.exclude(face_descriptor__isnull=True).values('id', 'face_descriptor'):
        descriptor = m['face_descriptor']
        if not descriptor:
            continue
        for emb in descriptor:
            stored = np.array(emb, dtype=np.float32)
            score = float(np.dot(probe, stored))
            if score > best_score:
                best_score = score
                best_id = m['id']

    return (best_id, best_score) if best_score >= threshold else (None, best_score)
