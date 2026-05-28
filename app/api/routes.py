from fastapi import APIRouter, Depends, Response, status

from app.api.dependencies import get_repository_service
from app.schemas.repository import RepositoryCreate, RepositoryResponse
from app.services.repository_service import RepositoryService

router = APIRouter(prefix="/repositories", tags=["repositories"])


@router.post(
    "",
    response_model=RepositoryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_repository(
    payload: RepositoryCreate,
    service: RepositoryService = Depends(get_repository_service),
) -> RepositoryResponse:
    return await service.create(payload.identifier)


@router.get(
    "/{repository_id}",
    response_model=RepositoryResponse,
    status_code=status.HTTP_200_OK,
)
async def read_repository(
    repository_id: int,
    service: RepositoryService = Depends(get_repository_service),
) -> RepositoryResponse:
    return await service.get(repository_id)


@router.put(
    "/{repository_id}",
    response_model=RepositoryResponse,
    status_code=status.HTTP_200_OK,
)
async def refresh_repository(
    repository_id: int,
    service: RepositoryService = Depends(get_repository_service),
) -> RepositoryResponse:
    return await service.refresh(repository_id)


@router.delete(
    "/{repository_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_repository(
    repository_id: int,
    service: RepositoryService = Depends(get_repository_service),
) -> Response:
    await service.delete(repository_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
