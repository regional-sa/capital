from typing import Optional

from fastapi import APIRouter, Body, Depends, Response, HTTPException
from starlette import status
from app.resources import strings
from app.api.dependencies.articles import get_article_by_slug_from_path
from app.api.dependencies.authentication import get_current_user_authorizer
from app.api.dependencies.comments import (
    check_comment_modification_permissions,
    get_comment_by_id_from_path,
)
from app.api.dependencies.database import get_repository
from app.db.repositories.comments import CommentsRepository
from app.models.domain.articles import Article
from app.models.domain.comments import Comment
from app.models.domain.users import User
from app.models.schemas.comments import (
    CommentInCreate,
    CommentInResponse,
    ListOfCommentsInResponse,
)
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

router = APIRouter()

from sqlmodel import SQLModel, Field, create_engine, Session, select

router = APIRouter()
# Create the SQLite database
sqlite_url = "sqlite:///./test.db"
engine = create_engine(sqlite_url, echo=True)
SQLModel.metadata.create_all(engine)

@router.get(
    "",
    response_model=ListOfCommentsInResponse,
    name="comments:get-comments-for-article",
)
async def list_comments_for_article(
    article: Article = Depends(get_article_by_slug_from_path),
    user: Optional[User] = Depends(get_current_user_authorizer(required=False)),
    comments_repo: CommentsRepository = Depends(get_repository(CommentsRepository)),
) -> ListOfCommentsInResponse:
    comments = await comments_repo.get_comments_for_article(article=article, user=user)
    return ListOfCommentsInResponse(comments=comments)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=CommentInResponse,
    name="comments:create-comment-for-article",
)
async def create_comment_for_article(
    comment_create: CommentInCreate = Body(..., embed=True, alias="comment"),
    article: Article = Depends(get_article_by_slug_from_path),
    user: User = Depends(get_current_user_authorizer()),
    comments_repo: CommentsRepository = Depends(get_repository(CommentsRepository)),
) -> CommentInResponse:
    if not comment_create.body or not comment_create.body.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=strings.COMMENT_IS_NULL,
        )
    comment = await comments_repo.create_comment_for_article(
        body=comment_create.body,
        article=article,
        user=user,
    )
    return CommentInResponse(comment=comment)


@router.delete(
    "/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    name="comments:delete-comment-from-article",
)
async def delete_comment_from_article(
    comment: Comment = Depends(get_comment_by_id_from_path),
    comments_repo: CommentsRepository = Depends(get_repository(CommentsRepository)),
    user: User = Depends(get_current_user_authorizer()),
    ) -> JSONResponse:
        await comments_repo.delete_comment(comment=comment)
        json_compatible_item_data = jsonable_encoder({"message": "Your comment has been deleted"})
        if comment.author.username != user.username:
            json_compatible_item_data = jsonable_encoder({"message": strings.BOLA(), "description": strings.DescriptionBOLA})
        return JSONResponse(content=json_compatible_item_data)



@router.get("/vulnerable/")
def vulnerable_get_user(username: str):
    with Session(engine) as session:
        # Vulnerable to SQL Injection
        query = f"SELECT * FROM comment WHERE username = '{username}'"
        result = session.execute(query)
        user = result.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {"id": user[0], "username": user[1], "email": user[2]}
