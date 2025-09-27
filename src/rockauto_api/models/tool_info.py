"""Tool information model for individual tools."""

from typing import Optional
from pydantic import BaseModel, Field


class ToolInfo(BaseModel):
    """Represents an individual tool with all its details."""

    name: str = Field(..., description="Tool name")
    part_number: str = Field(default="Unknown", description="Tool part/model number")
    price: Optional[str] = Field(None, description="Tool price")
    brand: Optional[str] = Field(None, description="Tool manufacturer/brand")
    description: Optional[str] = Field(None, description="Tool description")
    url: Optional[str] = Field(None, description="URL to tool page")
    image_url: Optional[str] = Field(None, description="URL to tool image")
    info_url: Optional[str] = Field(None, description="URL to detailed tool information")
    video_url: Optional[str] = Field(None, description="URL to tool demonstration video")
    specifications: Optional[str] = Field(None, description="Technical specifications")

    def __str__(self) -> str:
        price_str = f" - {self.price}" if self.price else ""
        brand_str = f" ({self.brand})" if self.brand else ""
        return f"{self.name}{price_str}{brand_str}"