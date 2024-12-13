import requests

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar, Optional, Type, TypeVar

from bb.core.config import BBConfig
from bb.typeshed import Result, Ok, Err

T = TypeVar("T", bound="BaseModel")


class BitbucketClient:
    """HTTP client for Bitbucket API interactions"""

    def __init__(self, config: BBConfig):
        self.config = config

    def get(self, url: str, **kwargs) -> Result:
        """Make authenticated GET request"""
        try:
            response = requests.get(
                url,
                auth=(
                    self.config.get("auth.username"),
                    self.config.get("auth.app_password"),
                ),
                **kwargs,
            )
            response.raise_for_status()
            return Ok(response.json())
        except Exception as e:
            return Err(e)

    def post(self, url: str, **kwargs) -> Result:
        """Make authenticated POST request"""
        try:
            response = requests.post(
                url,
                auth=(
                    self.config.get("auth.username"),
                    self.config.get("auth.app_password"),
                ),
                **kwargs,
            )
            response.raise_for_status()
            return Ok(response.json())
        except Exception as e:
            return Err(e)


@dataclass
class BaseModel(ABC):
    """Abstract base model for Bitbucket domain objects"""

    # Class-level constants
    BASE_API_URL: ClassVar[str] = "https://api.bitbucket.org/2.0"
    BASE_WEB_URL: ClassVar[str] = "https://bitbucket.org"

    # Shared client instance
    _client: ClassVar[Optional[BitbucketClient]] = None

    @classmethod
    def client(cls) -> BitbucketClient:
        """Get or create the BitbucketClient instance"""
        if cls._client is None:
            cls._client = BitbucketClient(BBConfig())
        return cls._client

    @classmethod
    @abstractmethod
    def resource_path(cls) -> str:
        """Return the base resource path for this model type"""
        pass

    @classmethod
    def api_url(cls) -> str:
        """Full API base URL for this resource type"""
        return f"{cls.BASE_API_URL}/{cls.resource_path()}"

    @classmethod
    def from_api_response(cls: Type[T], data: dict) -> T:
        """Create an instance from API response data"""
        field_names = cls.__dataclass_fields__.keys()
        filtered_data = {k: v for k, v in data.items() if k in field_names}
        return cls(**filtered_data)

    def update(self, **kwargs) -> None:
        """Update model attributes"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
