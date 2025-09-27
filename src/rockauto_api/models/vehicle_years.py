"""VehicleYears model for RockAuto API."""

from typing import List

from pydantic import BaseModel, Field


class VehicleYears(BaseModel):
    """Years available for a specific make."""

    make: str = Field(..., description="Vehicle make")
    years: List[int] = Field(..., description="Available years in descending order")
    count: int = Field(..., description="Total number of years")