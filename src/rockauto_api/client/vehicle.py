"""Vehicle class for scoped RockAuto operations."""

from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, ConfigDict, Field

from ..models import Engine, VehiclePartCategories, VehiclePartsResult

if TYPE_CHECKING:
    from .client import RockAutoClient


class Vehicle(BaseModel):
    """
    Represents a fully specified vehicle with engine configuration.

    Provides scoped access to parts data for the specific vehicle.
    """

    make: str = Field(..., description="Vehicle make")
    year: int = Field(..., description="Vehicle year")
    model: str = Field(..., description="Vehicle model")
    engine: Engine = Field(..., description="Selected engine configuration")
    _client: Optional["RockAutoClient"] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def model_post_init(self, __context) -> None:
        """Normalize make and model to uppercase."""
        self.make = self.make.upper()
        self.model = self.model.upper()

    def _set_client(self, client: "RockAutoClient") -> None:
        """Internal method to set the client reference."""
        object.__setattr__(self, "_client", client)

    @property
    def carcode(self) -> str:
        """Get the vehicle's carcode."""
        return self.engine.carcode

    async def get_part_categories(self) -> VehiclePartCategories:
        """Get part categories for this vehicle."""
        if not self._client:
            raise Exception("Vehicle not properly initialized - missing client reference")
        return await self._client.get_part_categories(self.make, self.year, self.model, self.carcode)

    async def get_parts_by_category(self, category_group_name: str) -> VehiclePartsResult:
        """Get parts for a specific category on this vehicle."""
        if not self._client:
            raise Exception("Vehicle not properly initialized - missing client reference")
        return await self._client.get_parts_by_category(
            self.make, self.year, self.model, self.carcode, category_group_name
        )

    async def get_individual_parts_from_subcategory(self, subcategory_url: str) -> VehiclePartsResult:
        """Get individual parts from a subcategory URL for this vehicle."""
        if not self._client:
            raise Exception("Vehicle not properly initialized - missing client reference")
        return await self._client.get_individual_parts_from_subcategory(
            self.make, self.year, self.model, self.carcode, subcategory_url
        )

    def __str__(self) -> str:
        """String representation of the vehicle."""
        return f"{self.make} {self.year} {self.model} - {self.engine.description}"

    def __repr__(self) -> str:
        """Detailed string representation of the vehicle."""
        return f"Vehicle(make='{self.make}', year={self.year}, model='{self.model}', carcode='{self.carcode}')"
