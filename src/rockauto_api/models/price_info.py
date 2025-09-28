"""Price and stock information models with historical tracking."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class PriceStockSnapshot(BaseModel):
    """A single price/stock observation at a specific time."""

    price: Optional[str] = Field(None, description="Part price (e.g., '$49.99')")
    availability: Optional[str] = Field(None, description="Stock availability status")
    stock_level: Optional[str] = Field(None, description="Specific stock level if available")
    shipping_info: Optional[str] = Field(None, description="Shipping cost/time information")
    sale_info: Optional[str] = Field(None, description="Sale or discount information")
    time_collected: datetime = Field(default_factory=datetime.now, description="When this data was collected")
    source_url: Optional[str] = Field(None, description="URL where this data was scraped from")

    def is_recent(self, max_age_minutes: int = 60) -> bool:
        """Check if this snapshot is recent enough to be considered current."""
        age = datetime.now() - self.time_collected
        return age.total_seconds() < (max_age_minutes * 60)

    def __str__(self) -> str:
        price_str = self.price or "Price not available"
        availability_str = f" ({self.availability})" if self.availability else ""
        return f"{price_str}{availability_str} at {self.time_collected.strftime('%Y-%m-%d %H:%M')}"


class PriceInfo(BaseModel):
    """Historical price and stock tracking for a specific part."""

    part_number: str = Field(..., description="Manufacturer part number this pricing applies to")
    current_snapshot: Optional[PriceStockSnapshot] = Field(None, description="Most recent price/stock data")
    price_history: List[PriceStockSnapshot] = Field(default_factory=list, description="Historical price/stock observations")
    max_history_entries: int = Field(default=50, description="Maximum number of historical entries to keep")

    def add_snapshot(self, snapshot: PriceStockSnapshot) -> None:
        """Add a new price/stock snapshot and manage history."""
        # Set as current snapshot
        self.current_snapshot = snapshot

        # Add to history
        self.price_history.append(snapshot)

        # Maintain history size limit
        if len(self.price_history) > self.max_history_entries:
            # Keep most recent entries
            self.price_history = self.price_history[-self.max_history_entries:]

    def get_current_price(self) -> Optional[str]:
        """Get the current price if available and recent."""
        if self.current_snapshot and self.current_snapshot.is_recent():
            return self.current_snapshot.price
        return None

    def get_current_availability(self) -> Optional[str]:
        """Get the current availability if available and recent."""
        if self.current_snapshot and self.current_snapshot.is_recent():
            return self.current_snapshot.availability
        return None

    def has_recent_data(self, max_age_minutes: int = 60) -> bool:
        """Check if we have recent price/stock data."""
        return (self.current_snapshot is not None and
                self.current_snapshot.is_recent(max_age_minutes))

    def get_price_trend(self) -> Optional[str]:
        """Analyze price trend from recent history."""
        if len(self.price_history) < 2:
            return None

        # Get last 5 entries with valid prices
        recent_prices = []
        for snapshot in reversed(self.price_history[-5:]):
            if snapshot.price:
                try:
                    # Extract numeric price (remove $ and convert to float)
                    price_num = float(snapshot.price.replace('$', '').replace(',', ''))
                    recent_prices.append(price_num)
                except (ValueError, AttributeError):
                    continue

        if len(recent_prices) < 2:
            return None

        # Simple trend analysis
        first_price = recent_prices[-1]  # Oldest in our sample
        last_price = recent_prices[0]    # Most recent

        if last_price > first_price * 1.05:  # 5% increase threshold
            return "increasing"
        elif last_price < first_price * 0.95:  # 5% decrease threshold
            return "decreasing"
        else:
            return "stable"

    def get_lowest_price(self) -> Optional[str]:
        """Get the lowest price from history."""
        lowest_price = None
        lowest_value = float('inf')

        for snapshot in self.price_history:
            if snapshot.price:
                try:
                    price_num = float(snapshot.price.replace('$', '').replace(',', ''))
                    if price_num < lowest_value:
                        lowest_value = price_num
                        lowest_price = snapshot.price
                except (ValueError, AttributeError):
                    continue

        return lowest_price

    def get_highest_price(self) -> Optional[str]:
        """Get the highest price from history."""
        highest_price = None
        highest_value = 0

        for snapshot in self.price_history:
            if snapshot.price:
                try:
                    price_num = float(snapshot.price.replace('$', '').replace(',', ''))
                    if price_num > highest_value:
                        highest_value = price_num
                        highest_price = snapshot.price
                except (ValueError, AttributeError):
                    continue

        return highest_price


class PartWithPricing(BaseModel):
    """Combines static part information with dynamic pricing data."""

    # Static part information (cacheable long-term)
    name: str = Field(..., description="Part name or description")
    part_number: str = Field(..., description="Manufacturer part number")
    brand: Optional[str] = Field(None, description="Manufacturer or brand name")
    url: Optional[str] = Field(None, description="Direct link to part page")
    image_url: Optional[str] = Field(None, description="Part image URL")
    info_url: Optional[str] = Field(None, description="More info/details page URL")
    video_url: Optional[str] = Field(None, description="Product video URL")

    # Dynamic pricing information (short-term cache)
    pricing: Optional[PriceInfo] = Field(None, description="Current and historical pricing data")

    def update_pricing(self, price: Optional[str] = None, availability: Optional[str] = None,
                      stock_level: Optional[str] = None, shipping_info: Optional[str] = None,
                      sale_info: Optional[str] = None, source_url: Optional[str] = None) -> None:
        """Update pricing information with a new snapshot."""
        # Create new snapshot
        snapshot = PriceStockSnapshot(
            price=price,
            availability=availability,
            stock_level=stock_level,
            shipping_info=shipping_info,
            sale_info=sale_info,
            source_url=source_url
        )

        # Initialize pricing if not exists
        if self.pricing is None:
            self.pricing = PriceInfo(part_number=self.part_number)

        # Add the snapshot
        self.pricing.add_snapshot(snapshot)

    def get_current_price(self) -> Optional[str]:
        """Get current price if available and recent."""
        return self.pricing.get_current_price() if self.pricing else None

    def get_current_availability(self) -> Optional[str]:
        """Get current availability if available and recent."""
        return self.pricing.get_current_availability() if self.pricing else None

    def needs_price_update(self, max_age_minutes: int = 60) -> bool:
        """Check if pricing data needs to be refreshed."""
        return not (self.pricing and self.pricing.has_recent_data(max_age_minutes))

    def __str__(self) -> str:
        price_str = ""
        if self.pricing and self.pricing.current_snapshot:
            price_str = f" - {self.pricing.current_snapshot.price}" if self.pricing.current_snapshot.price else ""

        brand_str = f" ({self.brand})" if self.brand else ""
        return f"{self.name}{price_str}{brand_str}"


class ToolWithPricing(BaseModel):
    """Combines static tool information with dynamic pricing data."""

    # Static tool information (cacheable long-term)
    name: str = Field(..., description="Tool name")
    part_number: str = Field(default="Unknown", description="Tool part/model number")
    brand: Optional[str] = Field(None, description="Tool manufacturer/brand")
    description: Optional[str] = Field(None, description="Tool description")
    url: Optional[str] = Field(None, description="URL to tool page")
    image_url: Optional[str] = Field(None, description="URL to tool image")
    info_url: Optional[str] = Field(None, description="URL to detailed tool information")
    video_url: Optional[str] = Field(None, description="URL to tool demonstration video")
    specifications: Optional[str] = Field(None, description="Technical specifications")

    # Dynamic pricing information (short-term cache)
    pricing: Optional[PriceInfo] = Field(None, description="Current and historical pricing data")

    def update_pricing(self, price: Optional[str] = None, availability: Optional[str] = None,
                      stock_level: Optional[str] = None, shipping_info: Optional[str] = None,
                      sale_info: Optional[str] = None, source_url: Optional[str] = None) -> None:
        """Update pricing information with a new snapshot."""
        # Create new snapshot
        snapshot = PriceStockSnapshot(
            price=price,
            availability=availability,
            stock_level=stock_level,
            shipping_info=shipping_info,
            sale_info=sale_info,
            source_url=source_url
        )

        # Initialize pricing if not exists
        if self.pricing is None:
            self.pricing = PriceInfo(part_number=self.part_number)

        # Add the snapshot
        self.pricing.add_snapshot(snapshot)

    def get_current_price(self) -> Optional[str]:
        """Get current price if available and recent."""
        return self.pricing.get_current_price() if self.pricing else None

    def get_current_availability(self) -> Optional[str]:
        """Get current availability if available and recent."""
        return self.pricing.get_current_availability() if self.pricing else None

    def needs_price_update(self, max_age_minutes: int = 60) -> bool:
        """Check if pricing data needs to be refreshed."""
        return not (self.pricing and self.pricing.has_recent_data(max_age_minutes))

    def __str__(self) -> str:
        price_str = ""
        if self.pricing and self.pricing.current_snapshot:
            price_str = f" - {self.pricing.current_snapshot.price}" if self.pricing.current_snapshot.price else ""

        brand_str = f" ({self.brand})" if self.brand else ""
        return f"{self.name}{price_str}{brand_str}"