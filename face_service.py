"""
face_service.py
---------------
Singleton wrapper around InsightFace buffalo_l.
The model is loaded once when Django starts and reused for every request.
buffalo_l downloads to ~/.insightface/models/buffalo_l/ on first use only.
"""

import warnings
warnings.filterwarnings('ignore', category=FutureWarning, module='insightface')

import numpy as np

_app = None  # module-level singleton


def get_app():
    """Return the InsightFace app, loading it on first call."""
    global _app
    if _app is None:
        import insightface
        from insightface.app import FaceAnalysis
        _app = FaceAnalysis(
            name='buffalo_l',
            providers=['CPUExecutionProvider'],
        )
        # ctx_id=0 for GPU, -1 for CPU
        _app.prepare(ctx_id=-1, det_size=(640, 640))
    return _app


def extract_embedding(image_bytes: bytes) -> list | None:
    """
    Given raw image bytes (JPEG/PNG), detect the largest face
    and return its 512-float embedding as a Python list.
    Returns None if no face is detected.
    """
    import cv2

    app = get_app()

    # Decode bytes → numpy BGR image
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        return None

    faces = app.get(img)
    if not faces:
        return None

    # Pick the largest face by bounding box area
    largest = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
    return largest.normed_embedding.tolist()


def find_best_match(probe_embedding: list, threshold: float = 0.4) -> tuple[int | None, float]:
    """
    Compare probe_embedding against all stored member embeddings.
    Returns (member_id, similarity_score) of the best match above threshold,
    or (None, 0.0) if no match found.

    Uses cosine similarity — buffalo_l embeddings are already L2-normalised
    so dot product == cosine similarity.
    """
    from members.models import Member

    probe = np.array(probe_embedding, dtype=np.float32)

    best_id = None
    best_score = -1.0

    members = Member.objects.exclude(face_descriptor__isnull=True).values('id', 'face_descriptor')
    for m in members:
        stored = np.array(m['face_descriptor'], dtype=np.float32)
        score = float(np.dot(probe, stored))
        if score > best_score:
            best_score = score
            best_id = m['id']

    if best_score >= threshold:
        return best_id, best_score
    return None, best_score
