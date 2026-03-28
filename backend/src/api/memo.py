"""Memo management API endpoints."""

import logging
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.models.database import get_db
from src.services import memo_service, memo_category_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/memos", tags=["Memos"])


# ─── Schemas ───────────────────────────────────────────────────


class MemoResponse(BaseModel):
    id: str
    content: str
    content_type: str
    category_id: str | None = None
    tags: list[str]
    image_url: str | None = None
    image_ocr_text: str | None = None
    url: str | None = None
    url_title: str | None = None
    url_summary: str | None = None
    url_thumbnail: str | None = None
    created_at: str
    updated_at: str


class CategoryResponse(BaseModel):
    id: str
    name: str
    sort_order: int
    is_default: bool


class CreateCategoryRequest(BaseModel):
    name: str


class UpdateCategoryRequest(BaseModel):
    name: str


class ReorderCategoriesRequest(BaseModel):
    category_ids: list[str]


# ─── Helpers ───────────────────────────────────────────────────


def _get_user_id_from_header(user_id: str = Query(..., alias="user_id")) -> uuid.UUID:
    """Extract user_id from query parameter.

    TODO: Replace with proper auth dependency that extracts user from JWT/session.
    """
    try:
        return uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id format")


def _memo_to_response(memo) -> MemoResponse:
    """Convert Memo ORM object to response schema."""
    return MemoResponse(
        id=str(memo.id),
        content=memo.content,
        content_type=memo.content_type.value,
        category_id=str(memo.category_id) if memo.category_id else None,
        tags=memo.tags or [],
        image_url=memo.image_url,
        image_ocr_text=memo.image_ocr_text,
        url=memo.url,
        url_title=memo.url_title,
        url_summary=memo.url_summary,
        url_thumbnail=memo.url_thumbnail,
        created_at=memo.created_at.isoformat(),
        updated_at=memo.updated_at.isoformat(),
    )


def _category_to_response(cat) -> CategoryResponse:
    """Convert MemoCategory ORM object to response schema."""
    return CategoryResponse(
        id=str(cat.id),
        name=cat.name,
        sort_order=cat.sort_order,
        is_default=cat.is_default,
    )


# ─── Memo Endpoints ───────────────────────────────────────────


@router.get("", response_model=list[MemoResponse])
def list_memos(
    user_id: uuid.UUID = Depends(_get_user_id_from_header),
    query: str | None = Query(None),
    category_id: str | None = Query(None),
    tags: str | None = Query(None, description="Comma-separated tags"),
    db: Session = Depends(get_db),
):
    """Search/list memos with optional filters."""
    cat_uuid = None
    if category_id:
        try:
            cat_uuid = uuid.UUID(category_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid category_id format")

    tag_list = None
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]

    memos = memo_service.search_memo(
        user_id=user_id,
        db=db,
        query=query,
        category_id=cat_uuid,
        tags=tag_list,
    )
    return [_memo_to_response(m) for m in memos]


@router.post("", response_model=MemoResponse, status_code=201)
async def create_memo(
    user_id: uuid.UUID = Depends(_get_user_id_from_header),
    content: str = Form(""),
    content_type: str = Form("text"),
    file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    """Create a new memo (multipart: text/image/url)."""
    if content_type not in ("text", "image", "url"):
        raise HTTPException(status_code=400, detail="content_type must be text, image, or url")

    file_data = None
    filename = None
    if content_type == "image":
        if not file:
            raise HTTPException(status_code=400, detail="File is required for image type")
        file_data = await file.read()
        filename = file.filename or "image.png"

    if content_type == "text" and not content:
        raise HTTPException(status_code=400, detail="Content is required for text type")

    if content_type == "url" and not content:
        raise HTTPException(status_code=400, detail="URL is required for url type")

    memo = await memo_service.save_memo(
        user_id=user_id,
        content=content,
        content_type=content_type,
        db=db,
        file_data=file_data,
        filename=filename,
    )
    return _memo_to_response(memo)


# ─── Category Endpoints (registered before /{memo_id} to avoid path conflicts) ─


@router.get("/categories", response_model=list[CategoryResponse])
def list_categories(
    user_id: uuid.UUID = Depends(_get_user_id_from_header),
    db: Session = Depends(get_db),
):
    """List all memo categories for the user."""
    categories = memo_category_service.list_categories(user_id, db)
    return [_category_to_response(c) for c in categories]


@router.post("/categories", response_model=CategoryResponse, status_code=201)
def create_category(
    body: CreateCategoryRequest,
    user_id: uuid.UUID = Depends(_get_user_id_from_header),
    db: Session = Depends(get_db),
):
    """Create a new memo category."""
    try:
        category = memo_category_service.create_category(user_id, body.name, db)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return _category_to_response(category)


@router.put("/categories/reorder", response_model=list[CategoryResponse])
def reorder_categories(
    body: ReorderCategoriesRequest,
    user_id: uuid.UUID = Depends(_get_user_id_from_header),
    db: Session = Depends(get_db),
):
    """Reorder memo categories."""
    try:
        cat_uuids = [uuid.UUID(cid) for cid in body.category_ids]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid category_id format in list")

    categories = memo_category_service.reorder_categories(user_id, cat_uuids, db)
    return [_category_to_response(c) for c in categories]


@router.put("/categories/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: str,
    body: UpdateCategoryRequest,
    user_id: uuid.UUID = Depends(_get_user_id_from_header),
    db: Session = Depends(get_db),
):
    """Update a memo category name."""
    try:
        cat_uuid = uuid.UUID(category_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid category_id format")

    try:
        category = memo_category_service.update_category(user_id, cat_uuid, body.name, db)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return _category_to_response(category)


@router.delete("/categories/{category_id}", status_code=204)
def delete_category(
    category_id: str,
    user_id: uuid.UUID = Depends(_get_user_id_from_header),
    db: Session = Depends(get_db),
):
    """Delete a memo category."""
    try:
        cat_uuid = uuid.UUID(category_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid category_id format")

    success = memo_category_service.delete_category(user_id, cat_uuid, db)
    if not success:
        raise HTTPException(status_code=404, detail="Category not found or is default")


# ─── Memo by ID (after /categories to avoid path conflicts) ───


@router.delete("/{memo_id}", status_code=204)
def delete_memo_endpoint(
    memo_id: str,
    user_id: uuid.UUID = Depends(_get_user_id_from_header),
    db: Session = Depends(get_db),
):
    """Soft-delete a memo."""
    try:
        mid = uuid.UUID(memo_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid memo_id format")

    success = memo_service.delete_memo(user_id, mid, db)
    if not success:
        raise HTTPException(status_code=404, detail="Memo not found")
