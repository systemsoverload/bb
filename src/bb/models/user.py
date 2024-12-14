from dataclasses import dataclass, field
from typing import Dict, List, Optional, Self


from bb.core.config import BBConfig
from bb.models.base import BaseModel, BitbucketClient
from bb.tui.types import RepositoryType
from bb.typeshed import Ok, Result


@dataclass
class UserStatus:
    """Represents the authentication and account status of a user"""

    display_name: str
    nickname: str
    account_status: str
    has_2fa_enabled: bool
    app_password_preview: str  # First 4 chars + asterisks
    scopes: List[str]
    uuid: str

    def format_message(self) -> List[str]:
        """Format the status as a list of message lines"""
        msg = ["[bold]bitbucket.org[/]"]
        msg.append(f"- Logged in as [bold]{self.display_name}[/] ({self.nickname})")
        msg.append(f"- Account status: {self.account_status}")
        msg.append(f"- 2FA enabled: {self.has_2fa_enabled}")
        msg.append(f"- App password: {self.app_password_preview}")
        msg.append(f"- Scopes: {[f"'{s}'" for s in self.scopes]}")
        return msg


@dataclass
class User(BaseModel):
    """Represents a Bitbucket user with their key attributes"""

    INCLUDED_FIELDS = [
        "uuid",
        "nickname",
        "display_name",
        "account_status",
        "has_2fa_enabled",
        "is_staff",
    ]

    EXCLUDED_FIELDS = [
        "links",
        "created_on",
    ]

    uuid: str
    display_name: str
    nickname: Optional[str] = None
    account_status: Optional[str] = None
    has_2fa_enabled: Optional[bool] = None
    is_staff: Optional[bool] = False
    type: str = "user"
    links: Dict = field(default_factory=dict)

    @classmethod
    def resource_path(cls) -> str:
        """Return the base resource path for user endpoints"""
        return "users"

    @classmethod
    def from_api_response(cls, data: Dict) -> "User":
        """Create a User instance from API response data"""
        return cls(
            uuid=data["uuid"],
            display_name=data["display_name"],
            nickname=data.get("nickname"),
            account_status=data.get("account_status"),
            has_2fa_enabled=data.get("has_2fa_enabled"),
            is_staff=data.get("is_staff", False),
            type=data.get("type", "user"),
            links=data.get("links", {}),
        )

    @classmethod
    def from_current_config(cls) -> Self:
        conf = BBConfig()
        return cls(uuid=conf.get("auth.uuid"), display_name=conf.get("auth.username"))

    @classmethod
    def validate_credentials(
        cls, username: str, app_password: str
    ) -> Result[UserStatus, Exception]:
        """Validate credentials by making an authenticated request with them"""
        client = BitbucketClient(BBConfig())  # Create new client
        result = client._make_request(
            "GET", f"{cls.BASE_API_URL}/user", auth=(username, app_password)
        )

        if result.is_err():
            return result

        # Get response data
        user_data = result.unwrap()

        # Create status object with provided credentials
        app_password_preview = f"{app_password[0:4]}{'*' * (len(app_password) - 4)}"
        scopes = user_data["headers"]["X-Oauth-Scopes"].split(",")

        return Ok(
            UserStatus(
                display_name=user_data["display_name"],
                nickname=user_data.get(
                    "nickname", user_data.get("username", "unknown")
                ),
                account_status=user_data.get("account_status", "unknown"),
                has_2fa_enabled=user_data.get("has_2fa_enabled", False),
                app_password_preview=app_password_preview,
                scopes=scopes,
                uuid=user_data.get("uuid", ""),
            )
        )

    @classmethod
    def get_status(cls) -> Result[UserStatus, Exception]:
        """Get the current user's authentication and account status"""
        client = cls.client()
        raw_result = client.get(f"{cls.BASE_API_URL}/user")
        if raw_result.is_err():
            return raw_result

        raw_response = raw_result.unwrap()
        user_data = raw_response

        # Get app password from config
        conf = BBConfig()
        app_password = conf.get("auth.app_password")
        app_password_preview = f"{app_password[0:4]}{'*' * (len(app_password) - 4)}"

        # Extract scopes from response headers
        scopes = raw_response["headers"]["X-Oauth-Scopes"].split(",")

        return Ok(
            UserStatus(
                display_name=user_data["display_name"],
                nickname=user_data.get(
                    "nickname", user_data.get("username", "unknown")
                ),
                account_status=user_data.get("account_status", "unknown"),
                has_2fa_enabled=user_data.get("has_2fa_enabled", False),
                app_password_preview=app_password_preview,
                scopes=scopes,
                uuid=user_data.get("uuid", ""),
            )
        )

    @property
    def web_url(self) -> str:
        """Get the web URL for the user's profile"""
        if self.links and "html" in self.links:
            return self.links["html"]["href"]
        return f"{self.BASE_WEB_URL}/{self.nickname or self.uuid}"

    @property
    def api_detail_url(self) -> str:
        """Get the API URL for this specific user"""
        return f"{self.api_url()}/{self.uuid}"

    def get_repositories(self) -> Result[List[RepositoryType], Exception]:
        """Get repositories owned by this user"""
        from bb.models import Repository

        result = self.client().get(
            f"{self.api_url()}/{self.uuid}/repositories", model_cls=Repository
        )
        if result.is_err():
            return result

        data = result.unwrap()
        return Ok([Repository.from_api_response(repo) for repo in data["values"]])

    def __str__(self) -> str:
        return f"{self.display_name} ({self.nickname or self.uuid})"

    def __hash__(self):
        return hash(self.uuid)
