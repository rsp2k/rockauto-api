"""Engine model for RockAuto API."""

from typing import Optional

from pydantic import BaseModel, Field


class Engine(BaseModel):
    """Represents a vehicle engine configuration."""

    description: str = Field(..., description="Engine description (e.g., '2.4L L4 DOHC')")
    carcode: str = Field(..., description="RockAuto's unique vehicle identifier")
    href: Optional[str] = Field(None, description="Link to engine catalog page")
