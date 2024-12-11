from abc import ABC, abstractmethod, abstractclassmethod
from typing import Any


class BaseResource(ABC):

    def __init__(self, config):
        self.config = config

    @abstractmethod
    def get_item(self, key: str) -> Any:
        raise NotImplementedError()
