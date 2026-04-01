from pydantic import BaseModel
from typing import List


class Paper(BaseModel):
    id: str
    title: str
    score: int
    tags: List[str]
    year: int
    month: str
    source: str
    link: str
    brief: str
    highlights: List[str]
    bossQuestions: List[str]
    actions: List[str]


class PapersResponse(BaseModel):
    ai: List[Paper]
    recsys: List[Paper]