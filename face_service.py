"""
face_service.py
---------------
Singleton wrapper around InsightFace buffalo_l.
Loaded once on first use, cached for the lifetime of the process.
buffalo_l downloads to ~/.insightface/models/buffalo_l/ on first use only.

On Render (cloud deployment), InsightFace is not installed.
All functions return None/graceful fallback so the app still runs —
face recognition is simply unavailable in the cloud.
"""

import warnings
warnings.filterwarnings('ignore', category=FutureWarning, module='insightface')

try:
    import numpy as np
    import insightface  # noqa: F401
    INSIGHTFACE_AVAILABLE = True
except ImportError:
    INSIGHTFACE_AVAILABLE = False

_app = None


def get_app():
    """Return the InsightFace app, loading it on first call. Returns None if not available."""
    if not INSIGHTFACE_AVAILABLE:
        return None
    global _app
    if _app is None:
        from insightface.app import FaceAnalysis
        _app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
        _app.prepare(ctx_id=-1, det_size=(640, 640))
    return _app


def extract_embedding(image_bytes: bytes):
    """
    Extract 512-float face embedding from image bytes.
    Returns list of floats, or None if no face detected or InsightFace unavailable.
    """
    app = get_app()
    if app is None:
        return None

    import cv2
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        return None

    faces = app.get(img)
    if not faces:
        return None

    largest = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
    return largest.normed_embedding.tolist()


def find_best_match(probe_embedding: list, threshold: float = 0.4):
    """
    Match probe_embedding against all stored member embeddings.
    Returns (member_id, score) or (None, 0.0).
    Returns (None, 0.0) immediately if InsightFace is unavailable.
    """
    if not INSIGHTFACE_AVAILABLE or probe_embedding is None:
        return None, 0.0

    from members.models import Member
    probe = np.array(probe_embedding, dtype=np.float32)

    best_id    = None
    best_score = -1.0

    for m in Member.objects.exclude(face_descriptor__isnull=True).values('id', 'face_descriptor'):
        stored = np.array(m['face_descriptor'], dtype=np.float32)
        score  = float(np.dot(probe, stored))
        if score > best_score:
            best_score = score
            best_id    = m['id']

    if best_score >= threshold:
        return best_id, best_score
    return None, best_score
