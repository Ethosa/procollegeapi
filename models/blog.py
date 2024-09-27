from pydantic import BaseModel


class NewBlogPost(BaseModel):
    title: str
    text: str
    tags: list[str] | None = None
    is_draft: bool = False
