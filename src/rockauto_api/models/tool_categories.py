"""Tool categories collection model."""

from typing import List
from pydantic import BaseModel, Field

from .tool_category import ToolCategory


class ToolCategories(BaseModel):
    """Collection of tool categories."""

    categories: List[ToolCategory] = Field(..., description="List of tool categories")
    count: int = Field(..., description="Number of categories")
    level: int = Field(..., description="Current hierarchy level")
    parent_path: str = Field(default="", description="Parent category path")

    def __str__(self) -> str:
        return f"ToolCategories({self.count} categories at level {self.level})"