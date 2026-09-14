from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from trinetra_core.db import CameraRow, get_session
from trinetra_core.models import CommunityCameraIn
from ..auth import audit, current_user

router = APIRouter(prefix="/api/v1/community", tags=["community"])


@router.post("/cameras")
async def onboard_community_camera(
    cam: CommunityCameraIn,
    session: AsyncSession = Depends(get_session),
    user=Depends(current_user),
):
    """Self-service onboarding for private/public-facing cameras (societies,
    malls, commercial establishments). Records explicit consent and tags the
    camera as ``source_type=community`` with a restricted scope.
    """
    if not cam.consent:
        raise HTTPException(422, "explicit consent is required to onboard a community camera")
    if await session.get(CameraRow, cam.id):
        raise HTTPException(409, "camera id already exists")
    row = CameraRow(
        id=cam.id, name=cam.name, lat=cam.lat, lon=cam.lon,
        vendor="Community", vms="Standalone NVR", protocol="rtsp",
        status="online", department="Community (Private)", zone="Community",
        stream_url=cam.stream_url, direction="Both",
        source_type="community", consent=True,
    )
    session.add(row)
    await audit(session, user.username, "community.onboard", cam.id,
                {"owner_name": cam.owner_name, "owner_contact": cam.owner_contact, "notes": cam.notes})
    await session.commit()
    return {"ok": True, "id": cam.id, "source_type": "community", "consent": True}
