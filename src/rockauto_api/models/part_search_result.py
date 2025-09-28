"""Part search result model for part number searches."""

from typing import List

from pydantic import BaseModel, Field

from .part_info import PartInfo


class PartSearchResult(BaseModel):
    """Result of a part number search."""

    parts: List[PartInfo] = Field(..., description="List of parts found")
    count: int = Field(..., description="Number of parts found")
    search_term: str = Field(..., description="Original search term")
    manufacturer: str = Field(default="All", description="Manufacturer filter used")
    part_group: str = Field(default="All", description="Part group filter used")

    def __str__(self) -> str:
        return f"PartSearchResult({self.count} parts for '{self.search_term}')"
