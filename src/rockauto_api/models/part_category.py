"""PartCategory model for RockAuto API."""

from typing import Optional

from pydantic import BaseModel, Field


class PartCategory(BaseModel):
    """Represents a part category/group."""

    name: str = Field(..., description="Category name (e.g., 'Brake & Wheel Hub')")
    group_name: str = Field(..., description="URL-encoded group name for API calls")
    href: Optional[str] = Field(None, description="Link to category page")