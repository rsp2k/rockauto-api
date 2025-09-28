"""PartInfo model for RockAuto API - Static information only."""

from typing import Optional

from pydantic import BaseModel, Field
from .price_info import PriceInfo


class PartInfo(BaseModel):
    """Represents a car part with static information (no pricing data)."""

    name: str = Field(..., description="Part name or description")
    part_number: str = Field(..., description="Manufacturer part number")
    brand: Optional[str] = Field(None, description="Manufacturer or brand name")
    url: Optional[str] = Field(None, description="Direct link to part page")
    image_url: Optional[str] = Field(None, description="Part image URL")
    info_url: Optional[str] = Field(None, description="More info/details page URL")
    video_url: Optional[str] = Field(None, description="Product video URL (from moreinfo.php)")

    # Static technical details that don't change frequently
    category: Optional[str] = Field(None, description="Part category")
    specifications: Optional[str] = Field(None, description="Technical specifications")
    compatibility_notes: Optional[str] = Field(None, description="Vehicle compatibility notes")


class PartWithHistory(BaseModel):
    """Complete part information including static data and pricing history."""

    # Static part information (long-term cacheable)
    part_info: PartInfo = Field(..., description="Static part information")

    # Dynamic pricing with full history (short-term cacheable)
    pricing_history: Optional[PriceInfo] = Field(None, description="Complete pricing and stock history")

    def get_current_price(self) -> Optional[str]:
        """Get the most recent price."""
        return self.pricing_history.get_current_price() if self.pricing_history else None

    def get_current_availability(self) -> Optional[str]:
        """Get the most recent availability status."""
        return self.pricing_history.get_current_availability() if self.pricing_history else None

    def get_price_history(self) -> list:
        """Get complete price history with timestamps."""
        if not self.pricing_history:
            return []
        return [
            {
                "price": snapshot.price,
                "availability": snapshot.availability,
                "stock_level": snapshot.stock_level,
                "time_collected": snapshot.time_collected,
                "shipping_info": snapshot.shipping_info,
                "sale_info": snapshot.sale_info
            }
            for snapshot in self.pricing_history.price_history
        ]

    def get_price_trend_analysis(self) -> dict:
        """Get comprehensive price trend analysis."""
        if not self.pricing_history:
            return {"trend": None, "lowest_price": None, "highest_price": None}

        return {
            "trend": self.pricing_history.get_price_trend(),
            "lowest_price": self.pricing_history.get_lowest_price(),
            "highest_price": self.pricing_history.get_highest_price(),
            "price_history_count": len(self.pricing_history.price_history),
            "has_recent_data": self.pricing_history.has_recent_data()
        }

    def needs_price_refresh(self, max_age_minutes: int = 30) -> bool:
        """Check if pricing data should be refreshed."""
        return not (self.pricing_history and self.pricing_history.has_recent_data(max_age_minutes))

    def update_pricing(self, price: Optional[str] = None, availability: Optional[str] = None,
                      stock_level: Optional[str] = None, shipping_info: Optional[str] = None,
                      sale_info: Optional[str] = None, source_url: Optional[str] = None) -> None:
        """Add new pricing snapshot to history."""
        from .price_info import PriceStockSnapshot

        # Initialize pricing history if not exists
        if self.pricing_history is None:
            self.pricing_history = PriceInfo(part_number=self.part_info.part_number)

        # Create and add new snapshot
        snapshot = PriceStockSnapshot(
            price=price,
            availability=availability,
            stock_level=stock_level,
            shipping_info=shipping_info,
            sale_info=sale_info,
            source_url=source_url
        )

        self.pricing_history.add_snapshot(snapshot)

    def __str__(self) -> str:
        """String representation showing current price and brand."""
        current_price = self.get_current_price()
        price_str = f" - {current_price}" if current_price else ""
        brand_str = f" ({self.part_info.brand})" if self.part_info.brand else ""
        return f"{self.part_info.name}{price_str}{brand_str}"
