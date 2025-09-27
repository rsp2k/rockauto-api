"""PartInfo model for RockAuto API."""

from typing import Optional

from pydantic import BaseModel, Field


class PartInfo(BaseModel):
    """Represents a car part with detailed information."""

    name: str = Field(..., description="Part name or description")
    part_number: str = Field(..., description="Manufacturer part number")
    price: Optional[str] = Field(None, description="Part price (e.g., '$49.99')")
    brand: Optional[str] = Field(None, description="Manufacturer or brand name")
    availability: Optional[str] = Field(None, description="Stock availability status")
    url: Optional[str] = Field(None, description="Direct link to part page")
    image_url: Optional[str] = Field(None, description="Part image URL")
    info_url: Optional[str] = Field(None, description="More info/details page URL")
    video_url: Optional[str] = Field(None, description="Product video URL (from moreinfo.php)")