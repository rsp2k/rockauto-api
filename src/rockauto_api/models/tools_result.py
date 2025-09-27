"""Tools search result model."""

from typing import List
from pydantic import BaseModel, Field

from .tool_info import ToolInfo


class ToolsResult(BaseModel):
    """Result of a tools search containing individual tools."""

    tools: List[ToolInfo] = Field(..., description="List of tools found")
    count: int = Field(..., description="Number of tools found")
    category: str = Field(..., description="Category these tools belong to")
    category_path: str = Field(..., description="Full category path")

    def __str__(self) -> str:
        return f"ToolsResult({self.count} tools in {self.category})"