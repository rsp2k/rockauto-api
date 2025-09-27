"""VehicleEngines model for RockAuto API."""

from typing import List

from pydantic import BaseModel, Field

from .engine import Engine


class VehicleEngines(BaseModel):
    """Engines available for a specific make, year, and model."""

    make: str = Field(..., description="Vehicle make")
    year: int = Field(..., description="Vehicle year")
    model: str = Field(..., description="Vehicle model")
    engines: List[Engine] = Field(..., description="Available engine configurations")
    count: int = Field(..., description="Total number of engines")