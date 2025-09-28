"""Models for parts search dropdown options and caching."""

from typing import List, Optional

from pydantic import BaseModel, Field


class PartSearchOption(BaseModel):
    """A single dropdown option for parts search."""

    value: str = Field(..., description="Option value sent to server")
    text: str = Field(..., description="Display text for option")


class ManufacturerOptions(BaseModel):
    """Collection of manufacturer options for parts search."""

    manufacturers: List[PartSearchOption] = Field(..., description="List of manufacturer options")
    count: int = Field(..., description="Number of manufacturers available")
    last_updated: Optional[str] = Field(None, description="ISO timestamp of last cache update")

    def get_manufacturer_by_name(self, name: str) -> Optional[PartSearchOption]:
        """Find manufacturer option by display name (case-insensitive)."""
        name_lower = name.lower()
        for mfr in self.manufacturers:
            if mfr.text.lower() == name_lower:
                return mfr
        return None

    def get_manufacturer_names(self) -> List[str]:
        """Get list of all manufacturer display names."""
        return [mfr.text for mfr in self.manufacturers]


class PartGroupOptions(BaseModel):
    """Collection of part group options for parts search."""

    part_groups: List[PartSearchOption] = Field(..., description="List of part group options")
    count: int = Field(..., description="Number of part groups available")
    last_updated: Optional[str] = Field(None, description="ISO timestamp of last cache update")

    def get_part_group_by_name(self, name: str) -> Optional[PartSearchOption]:
        """Find part group option by display name (case-insensitive)."""
        name_lower = name.lower()
        for group in self.part_groups:
            if group.text.lower() == name_lower:
                return group
        return None

    def get_part_group_names(self) -> List[str]:
        """Get list of all part group display names."""
        return [group.text for group in self.part_groups]


class PartTypeOptions(BaseModel):
    """Collection of part type options for parts search."""

    part_types: List[PartSearchOption] = Field(..., description="List of part type options")
    count: int = Field(..., description="Number of part types available")
    last_updated: Optional[str] = Field(None, description="ISO timestamp of last cache update")

    def get_part_type_by_name(self, name: str) -> Optional[PartSearchOption]:
        """Find part type option by display name (case-insensitive)."""
        name_lower = name.lower()
        for part_type in self.part_types:
            if part_type.text.lower() == name_lower:
                return part_type
        return None


class WhatIsPartCalledResult(BaseModel):
    """Result from 'what is part called' keyword search."""

    main_category: str = Field(..., description="Main category name")
    subcategory: str = Field(..., description="Subcategory name")
    full_path: str = Field(..., description="Full category path")

    def __str__(self) -> str:
        return f"{self.main_category}/{self.subcategory}"


class WhatIsPartCalledResults(BaseModel):
    """Collection of results from 'what is part called' search."""

    results: List[WhatIsPartCalledResult] = Field(..., description="List of category matches")
    count: int = Field(..., description="Number of matches found")
    search_term: str = Field(..., description="Original search query")

    def get_category_tuples(self) -> List[tuple[str, str]]:
        """Get results as list of (main_category, subcategory) tuples."""
        return [(result.main_category, result.subcategory) for result in self.results]
