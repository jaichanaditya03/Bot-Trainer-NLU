
from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
from typing import Optional, Any, Dict
import re


class RegisterRequest(BaseModel):
    """User registration request model"""
    username: str
    email: EmailStr
    password: str
    is_admin: bool = False  # Optional field for admin registration

    @field_validator("username")
    @classmethod
    def username_not_blank(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Username must be at least 2 characters.")
        return value

    @field_validator("password")
    @classmethod
    def password_strength(cls, value: str) -> str:
        if len(value) < 6 or not re.search(r"[^\w\s]", value):
            raise ValueError("Password must be at least 6 characters and include at least one special character.")
        return value


class LoginRequest(BaseModel):
    """User login request model"""
    email: EmailStr
    password: str


class ProjectCreate(BaseModel):
    """Project creation request model"""
    name: str
    description: Optional[str] = ""

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Project name cannot be empty.")
        return value

    @field_validator("description")
    @classmethod
    def description_trim(cls, value: Optional[str]) -> str:
        if value is None:
            return ""
        return value.strip()


class DatasetPayload(BaseModel):
    """Dataset save request model"""
    filename: str
    analysis: Dict[str, Any]
    evaluation: Dict[str, Any]
    checksum: Optional[str] = None
    workspace_id: Optional[str] = None

    model_config = ConfigDict(extra="ignore")


class DatasetSelection(BaseModel):
    """Dataset selection request model"""
    checksum: str
    filename: Optional[str] = None


class WorkspaceCreate(BaseModel):
    """Create a workspace"""
    name: str
    description: Optional[str] = ""

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Workspace name cannot be empty.")
        return value


class WorkspaceSelect(BaseModel):
    """Select active workspace"""
    workspace_id: str
