"""VehicleModels model for RockAuto API."""

from typing import List

from pydantic import BaseModel, Field


class VehicleModels(BaseModel):
    """Models available for a specific make and year."""

    make: str = Field(..., description="Vehicle make")
    year: int = Field(..., description="Vehicle year")
    models: List[str] = Field(..., description="Available models")
    count: int = Field(..., description="Total number of models")