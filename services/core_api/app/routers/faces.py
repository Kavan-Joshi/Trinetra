"""Face gallery enrollment — add a known face (image upload) so the correlator
can match detected faces against it (cosine similarity over ArcFace embeddings).

The gallery lives in Redis (hash ``trinetra:face_gallery``): field = person name,
value = JSON list of 512 floats. The correlator reads it on every face event.
"""

import json
import logging

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from trinetra_core.config import settings
from trinetra_core.db import get_session
from ..auth import audit, require_role

log = logging.getLogger("trinetra.faces")
router = APIRouter(prefix="/api/v1/faces", tags=["faces"])

GALLERY_KEY = "trinetra:face_gallery"

_face_app = None


def _get_face_app():
    global _face_app
    if _face_app is None:
        from insightface.app import FaceAnalysis

        _face_app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
        _face_app.prepare(ctx_id=-1, det_size=(640, 640))
        log.info("InsightFace loaded for enrollment")
    return _face_app


@router.get("")
async def list_gallery(user=Depends(require_role("admin", "analyst"))):
    r = aioredis.from_url(settings.redis_url, decode_responses=True)
    try:
        names = await r.hkeys(GALLERY_KEY)
        return {"total": len(names), "items": names}
    finally:
        await r.close()


@router.post("/enroll")
async def enroll_face(
    file: UploadFile = File(...),
    name: str = Form(...),
    category: str = Form("wanted_person"),
    session: AsyncSession = Depends(get_session),
    user=Depends(require_role("admin", "analyst")),
):
    """Upload a face photo + name → compute ArcFace embedding → store in the gallery."""
    import cv2
    import numpy as np

    raw = await file.read()
    arr = np.frombuffer(raw, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(400, "invalid image (could not decode)")
    app = _get_face_app()
    faces = app.get(img)
    if not faces:
        raise HTTPException(422, "no face detected in the uploaded image")
    # use the largest face
    face = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
    emb = [round(float(v), 4) for v in face.embedding.tolist()]
    r = aioredis.from_url(settings.redis_url, decode_responses=True)
    try:
        await r.hset(GALLERY_KEY, name, json.dumps(emb))
    finally:
        await r.close()
    await audit(session, user.username, "face.enroll", name, {"category": category, "dims": len(emb)})
    await session.commit()
    return {"ok": True, "name": name, "category": category, "faces_detected": len(faces), "embedding_dims": len(emb)}


@router.delete("/{name}")
async def remove_face(name: str, session: AsyncSession = Depends(get_session), user=Depends(require_role("admin", "analyst"))):
    r = aioredis.from_url(settings.redis_url, decode_responses=True)
    try:
        removed = await r.hdel(GALLERY_KEY, name)
    finally:
        await r.close()
    await audit(session, user.username, "face.remove", name, {})
    await session.commit()
    return {"ok": True, "name": name, "removed": removed}
