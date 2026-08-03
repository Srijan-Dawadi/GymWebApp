"""
face_service.py
---------------
Face recognition (InsightFace buffalo_l) + Anti-spoofing (MiniFASNet ONNX).

Registration: multi-angle enrollment — stores list of embeddings per member.
Attendance:   extract_embedding() → find_best_match() pipeline.
"""

import os
import logging
import threading
import time
import warnings

warnings.filterwarnings('ignore', category=FutureWarning, module='insightface')

logger = logging.getLogger(__name__)

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
_face_app        = None   # None = not yet loaded; False = last load failed
_face_app_retry_at = 0.0  # monotonic timestamp after which a failed load may be retried
_spoof_sess      = None   # None = not yet loaded; False = failed to load
_face_lock       = threading.Lock()
_spoof_lock      = threading.Lock()

_ANTISPOOF_MODEL = os.path.join(
    os.path.dirname(__file__), 'static', 'antispoof', 'antispoof.onnx'
)

LIVENESS_THRESHOLD = 0.2

# ── Descriptor matrix cache ──────────────────────────────────────
# Matching is O(1) against a cached (N x D) numpy matrix instead of
# re-parsing every member's JSON descriptor on each check-in frame.
_descriptor_lock   = threading.Lock()
_descriptor_cache  = None   # (matrix: np.ndarray, member_ids: np.ndarray) or None
_descriptor_cache_at = 0.0
_DESCRIPTOR_CACHE_TTL = 30.0


def invalidate_descriptor_cache():
    """Force the next find_best_match call to rebuild the matrix.
    Call after any face_descriptor write (enrollment / edit / delete)."""
    global _descriptor_cache
    with _descriptor_lock:
        _descriptor_cache = None


def _build_descriptor_matrix():
    """Load all member embeddings once into aligned numpy arrays.

    Handles both storage shapes: a flat single embedding from a photo
    ([...]) and multi-angle enrollment ([[...], [...], ...]).
    """
    from members.models import Member

    rows = list(
        Member.objects.exclude(face_descriptor__isnull=True)
        .values_list('id', 'face_descriptor')
    )
    member_ids = []
    embeddings = []
    dim = None
    skipped = 0
    for member_id, descriptor in rows:
        if not descriptor or not isinstance(descriptor, list):
            continue
        if descriptor and isinstance(descriptor[0], list):
            candidate_embs = [e for e in descriptor if isinstance(e, list) and e]
        else:
            candidate_embs = [descriptor]
        for emb in candidate_embs:
            try:
                vec = np.asarray(emb, dtype=np.float32)
            except Exception:
                skipped += 1
                continue
            if vec.ndim != 1 or vec.size == 0:
                skipped += 1
                continue
            if dim is None:
                dim = vec.size
            if vec.size != dim:
                # Mixed-dimension descriptors (e.g. old 128-d vs new 512-d) are
                # dropped the same way the previous matcher skipped them.
                skipped += 1
                continue
            embeddings.append(vec)
            member_ids.append(member_id)

    if skipped:
        logging.getLogger(__name__).warning(
            'Descriptor matrix build skipped %d malformed/mismatched embedding(s).', skipped
        )

    if not embeddings:
        return np.empty((0, dim or 0), dtype=np.float32), np.empty(0, dtype=np.int64)
    return np.vstack(embeddings), np.asarray(member_ids, dtype=np.int64)


def get_descriptor_matrix():
    """Return (matrix, member_ids) — the cached numpy matrix, rebuilt
    when invalidated or after TTL. Thread-safe."""
    global _descriptor_cache, _descriptor_cache_at
    with _descriptor_lock:
        if _descriptor_cache is None or time.monotonic() - _descriptor_cache_at > _DESCRIPTOR_CACHE_TTL:
            _descriptor_cache = _build_descriptor_matrix()
            _descriptor_cache_at = time.monotonic()
        return _descriptor_cache


def _get_face_app():
    """Load InsightFace once, thread-safe.
    Returns the app on success, None if unavailable or failed to load.
    A failed load is retried after a 60s cooldown (a transient disk/ONNX
    hiccup must not permanently disable face recognition until restart).
    """
    if not INSIGHTFACE_AVAILABLE:
        return None
    global _face_app, _face_app_retry_at
    now = time.monotonic()
    if _face_app is not None and _face_app is not False:
        return _face_app
    if _face_app is False and now < _face_app_retry_at:
        return None
    with _face_lock:
        if _face_app is not None and _face_app is not False:
            return _face_app
        if _face_app is False and time.monotonic() < _face_app_retry_at:
            return None
        try:
            from insightface.app import FaceAnalysis
            app = FaceAnalysis(name='buffalo_m', providers=['CPUExecutionProvider'])
            app.prepare(ctx_id=-1, det_size=(320, 320))
            _face_app = app
            _face_app_retry_at = 0.0
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(
                'InsightFace model failed to load (will retry in 60s): %s', e, exc_info=True
            )
            _face_app = False
            _face_app_retry_at = time.monotonic() + 60
    return _face_app if _face_app is not False else None


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
    """Run anti-spoof check. Returns (is_real: bool, score: float).
    On any error, fails open (returns True, 1.0) so a liveness failure
    never silently blocks a legitimate check-in due to a code bug.
    """
    try:
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
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(
            'Liveness check failed unexpectedly, failing open: %s', e
        )
        return True, 1.0


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
        # ── Anti-spoofing ──────────────────────────────────────────────
        is_real, score = _check_liveness(img, face.bbox)
        if not is_real:
            return {'status': 'spoof', 'embedding': None,
                    'liveness_score': round(score, 3),
                    'message': 'Liveness check failed — ensure good lighting and move closer to the camera.'}
        return {'status': 'ok', 'embedding': face.normed_embedding.tolist(),
                'liveness_score': round(score, 3), 'message': 'OK'}
    except Exception as e:
        return {'status': 'error', 'embedding': None, 'liveness_score': 0.0,
                'message': f'Face processing error: {str(e)}'}


def find_best_match(probe_embedding: list, threshold: float = 0.4) -> tuple:
    """
    Match probe_embedding against the cached descriptor matrix (O(1) numpy
    dot product over all enrolled embeddings).
    face_descriptor = [[emb1], [emb2], [emb3], [emb4], [emb5]]
    Returns (member_id, best_score) or (None, best_score) if below threshold.
    """
    if not INSIGHTFACE_AVAILABLE or probe_embedding is None:
        return None, 0.0

    try:
        probe = np.asarray(probe_embedding, dtype=np.float32)
    except Exception as e:
        logging.getLogger(__name__).warning(
            'find_best_match: could not convert probe embedding: %s', e
        )
        return None, 0.0

    if probe.ndim != 1 or probe.size == 0:
        return None, 0.0

    matrix, member_ids = get_descriptor_matrix()
    if matrix.shape[0] == 0 or matrix.shape[1] != probe.size:
        return None, 0.0

    scores = matrix @ probe
    idx = int(np.argmax(scores))
    best_score = float(scores[idx])

    if best_score >= threshold:
        return int(member_ids[idx]), best_score
    return None, best_score

