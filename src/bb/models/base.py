from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar, Dict, List, Optional, Set, Type, TypeVar, Union

import requests

from bb.core.config import BBConfig
from bb.exceptions import IPWhitelistException
from bb.typeshed import Err, Ok, Result

FieldSpec = Union[str, List[str], Set[str]]


class BitbucketClient:
    """HTTP client for Bitbucket API interactions"""

    def __init__(self, config: BBConfig):
        self.config = config

    @property
    def user_uuid(self) -> str:
        """Get current user's UUID in quoted format for queries"""
        return f'"{self.config.get("auth.uuid")}"'

    def build_query(self, **kwargs) -> Optional[str]:
        """Build a Bitbucket query string from keyword arguments

        Examples:
            build_query(state="OPEN")  # state="OPEN"
            build_query(state="OPEN", author=client.user_uuid)  # state="OPEN" AND author.uuid="123"
            build_query(_or=[("state", "OPEN"), ("state", "MERGED")])  # state="OPEN" OR state="MERGED"
        """
        conditions = []

        # Handle special _or key for OR conditions
        if "_or" in kwargs:
            or_conditions = [f'{k}="{v}"' for k, v in kwargs.pop("_or")]
            if or_conditions:
                conditions.append(f"({' OR '.join(or_conditions)})")

        # Process remaining kwargs as AND conditions
        for key, value in kwargs.items():
            # Handle special cases
            if key.endswith("_uuid"):  # author_uuid -> author.uuid="{value}"
                field = f"{key[:-5]}.uuid"
                conditions.append(f"{field}={value}")
            else:
                conditions.append(f'{key}="{value}"')

        return " AND ".join(conditions) if conditions else None

    def _build_fields_param(
        self,
        model_cls: Type["BaseModel"],
        include: Optional[FieldSpec] = None,
        exclude: Optional[FieldSpec] = None,
    ) -> Optional[str]:
        """Build fields parameter for API request"""
        # Start with model's default inclusions/exclusions
        fields = set(model_cls.INCLUDED_FIELDS)
        excluded = set(model_cls.EXCLUDED_FIELDS)

        # Add request-specific includes/excludes
        if include:
            if isinstance(include, str):
                fields.add(include)
            else:
                fields.update(include)

        if exclude:
            if isinstance(exclude, str):
                excluded.add(exclude)
            else:
                excluded.update(exclude)

        if not fields and not excluded:
            return None

        # Build the fields parameter
        field_parts = []
        for field in fields:
            field_parts.append(f"+{field}")
        for field in excluded:
            field_parts.append(f"-{field}")

        return ",".join(field_parts)

    def _handle_response_error(self, exc: requests.HTTPError) -> Exception:
        """Convert HTTP errors into appropriate exceptions"""
        if exc.response.status_code == 403 and "whitelist" in exc.response.text:
            return IPWhitelistException(
                "[bold red] 403 fetching data, ensure your IP has been whitelisted"
            )
        return exc

    def _make_request(
        self,
        method: str,
        url: str,
        model_cls: Optional[Type["BaseModel"]] = None,
        include_fields: Optional[FieldSpec] = None,
        exclude_fields: Optional[FieldSpec] = None,
        query_params: Optional[Dict] = None,
        **kwargs,
    ) -> Result:
        """Make an authenticated request and handle common errors"""
        try:
            params = kwargs.pop("params", {}).copy()

            # Add fields parameter if model class is provided
            if model_cls:
                fields = self._build_fields_param(
                    model_cls, include_fields, exclude_fields
                )
                if fields:
                    params["fields"] = fields

            # Add query filter if provided
            if query_params:
                query = self.build_query(**query_params)
                if query:
                    params["q"] = query

            if params:
                kwargs["params"] = params

            if kwargs.get("auth"):
                auth = kwargs.pop("auth")
            else:
                auth = auth = (
                    self.config.get("auth.username"),
                    self.config.get("auth.app_password"),
                )

            response = requests.request(
                method,
                url,
                allow_redirects=True,
                auth=auth,
                **kwargs,
            )

            response.raise_for_status()

            content_type = kwargs.get("content_type", "")
            if "application/json" in content_type:
                result = response.json()
            elif "text/plain" in content_type:
                result = response.text
            else:
                # Default to json if no content-type or unknown
                try:
                    result = response.json()
                except ValueError:
                    result = response.text

            # XXX - Always include headers if response is a dict
            # A bit hack, this could probably be cleaner
            if isinstance(result, dict):
                result["headers"] = dict(response.headers)
            return Ok(result)

        except requests.HTTPError as e:
            return Err(self._handle_response_error(e))
        except Exception as e:
            return Err(e)

    def get(
        self,
        url: str,
        model_cls: Optional[Type["BaseModel"]] = None,
        include_fields: Optional[FieldSpec] = None,
        exclude_fields: Optional[FieldSpec] = None,
        query_params: Optional[Dict] = None,
        **kwargs,
    ) -> Result:
        """Make authenticated GET request"""
        return self._make_request(
            "GET",
            url,
            model_cls,
            include_fields,
            exclude_fields,
            query_params,
            **kwargs,
        )

    def post(
        self,
        url: str,
        model_cls: Optional[Type["BaseModel"]] = None,
        include_fields: Optional[FieldSpec] = None,
        exclude_fields: Optional[FieldSpec] = None,
        query_params: Optional[Dict] = None,
        **kwargs,
    ) -> Result:
        """Make authenticated POST request"""
        return self._make_request(
            "POST",
            url,
            model_cls,
            include_fields,
            exclude_fields,
            query_params,
            **kwargs,
        )


T = TypeVar("T", bound="BaseModel")


@dataclass
class BaseModel(ABC):
    """Abstract base model for Bitbucket domain objects"""

    # Class-level constants
    BASE_API_INTERNAL_URL: ClassVar[str] = "https://api.bitbucket.org/internal"
    BASE_API_URL: ClassVar[str] = "https://api.bitbucket.org/2.0"
    BASE_WEB_URL: ClassVar[str] = "https://bitbucket.org"

    # Default field specifications
    INCLUDED_FIELDS: ClassVar[List[str]] = []
    EXCLUDED_FIELDS: ClassVar[List[str]] = []

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

    @property
    @abstractmethod
    def web_url(self) -> str:
        """Web UI URL for this resource"""
        pass
