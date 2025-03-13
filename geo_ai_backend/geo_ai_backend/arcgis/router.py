from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Query, status, Request

from geo_ai_backend.auth.schemas import UserServiceSchemas
from geo_ai_backend.auth.permissions import get_current_user_from_access
from geo_ai_backend.arcgis.service import gis_service
from geo_ai_backend.arcgis.schemas import TokenArcgisSchemas
from geo_ai_backend.arcgis.exceptions import BadRequestTokenException

router = APIRouter(
    prefix="/arcgis",
    tags=["arcgis"],
)


@router.get(
    "/generate-arcgis-token",
    response_model=TokenArcgisSchemas,
    responses={
        400: {
            "description": "Bad request token",
            "content": {
                "application/json": {
                    "example": {"detail": "Bad request token"}
                }
            },
        }
    },
)
async def generate_arcgis_token(
    request: Request,
    current_user: UserServiceSchemas = Depends(get_current_user_from_access)
) -> TokenArcgisSchemas:
    try:
        gis_service.set_referer(request)
        token = gis_service.get_token_arcgis_token_service
    except BadRequestTokenException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bad request token",
        )
    return token
