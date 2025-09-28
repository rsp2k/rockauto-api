"""VehiclePartCategories model for RockAuto API."""

from typing import List

from pydantic import BaseModel, Field

from .part_category import PartCategory


class VehiclePartCategories(BaseModel):
    """Part categories available for a specific vehicle."""

    make: str = Field(..., description="Vehicle make")
    year: int = Field(..., description="Vehicle year")
    model: str = Field(..., description="Vehicle model")
    carcode: str = Field(..., description="Vehicle carcode")
    categories: List[PartCategory] = Field(..., description="Available part categories")
    count: int = Field(..., description="Total number of categories")
