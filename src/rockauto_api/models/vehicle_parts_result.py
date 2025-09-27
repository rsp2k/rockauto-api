"""VehiclePartsResult model for RockAuto API."""

from typing import List

from pydantic import BaseModel, Field

from .part_info import PartInfo


class VehiclePartsResult(BaseModel):
    """Parts results for a specific vehicle and category."""

    make: str = Field(..., description="Vehicle make")
    year: int = Field(..., description="Vehicle year")
    model: str = Field(..., description="Vehicle model")
    carcode: str = Field(..., description="Vehicle carcode")
    category: str = Field(..., description="Part category name")
    parts: List[PartInfo] = Field(..., description="Found parts")
    count: int = Field(..., description="Total number of parts found")