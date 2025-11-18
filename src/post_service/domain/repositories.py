from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from .models import Post


class PostRepository(ABC):
    @abstractmethod
    async def save(self, post: Post) -> Post:
        pass

    @abstractmethod
    async def find_by_id(self, post_id: str) -> Optional[Post]:
        pass

    @abstractmethod
    async def find_by_author(self, author_id: str, skip: int = 0, limit: int = 100) -> List[Post]:
        pass

    @abstractmethod
    async def find_published(self, skip: int = 0, limit: int = 100,
                             tags: List[str] = None) -> List[Post]:
        pass

    @abstractmethod
    async def find_popular(self, days: int = 7, limit: int = 10) -> List[Post]:
        pass

    @abstractmethod
    async def search(self, query: str, skip: int = 0, limit: int = 100) -> List[Post]:
        pass

    @abstractmethod
    async def delete(self, post_id: str) -> bool:
        pass

    @abstractmethod
    async def increment_view_count(self, post_id: str) -> bool:
        pass