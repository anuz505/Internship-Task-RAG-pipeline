from typing import List, Dict, Any, Protocol, Tuple
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Vector_Search_Result:
    id: str
    score: float
    metadata: Dict[str, Any]


class Vector_Store_Protocal(Protocol):
    async def initialize(self) -> None: ...

    async def upsert(
        self, vectors: List[Tuple[str, List[float], Dict[str, Any]]]
    ) -> None: ...
    async def search(
        self, query_vector: List[float], top_k: int, filter_dict: Dict[str, Any] = None
    ) -> List[Vector_Search_Result]: ...

    async def delete(self, ids: List[str]) -> None: ...


class Base_Vector_Store(ABC):
    @abstractmethod
    async def initialize(self) -> None:
        pass

    @abstractmethod
    async def upsert(
        self, vectors: List[Tuple[str, List[float], Dict[str, Any]]]
    ) -> None:
        pass

    @abstractmethod
    async def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filter_dict: Dict[str, Any] = None,
    ) -> List[Vector_Search_Result]:
        pass

    @abstractmethod
    async def delete(self, ids: List[str]) -> None:
        pass
