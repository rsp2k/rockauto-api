"""VehicleMakes model for RockAuto API."""

from typing import List

from pydantic import BaseModel, Field


class VehicleMakes(BaseModel):
    """List of available vehicle makes."""

    makes: List[str] = Field(..., description="Alphabetically sorted list of vehicle makes")
    count: int = Field(..., description="Total number of makes")