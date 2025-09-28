"""Tool category model for RockAuto tools section."""

from pydantic import BaseModel, Field


class ToolCategory(BaseModel):
    """Represents a tool category in RockAuto's tools section."""

    name: str = Field(..., description="Category name (e.g., 'Engine', 'Oil Pump Priming Tool')")
    group_name: str = Field(..., description="URL-safe group name for API calls")
    href: str = Field(..., description="Relative URL path to the category")
    level: int = Field(..., description="Hierarchy level (1=main, 2=subcategory, 3=specific tool)")

    def __str__(self) -> str:
        return f"{self.name} (Level {self.level})"
