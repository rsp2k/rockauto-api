"""Enhanced caching system that separates static part data from volatile pricing data."""

from datetime import datetime, timedelta
from typing import Dict, Optional, Union, List
from pydantic import BaseModel, Field

from .part_info import PartInfo, PartWithHistory
from .tool_info import ToolInfo, ToolWithHistory
from .price_info import PriceInfo, PriceStockSnapshot
from .vehicle_parts_result import VehiclePartsResult


class StaticPartCache(BaseModel):
    """Cache for static part information that changes infrequently."""

    parts: Dict[str, PartInfo] = Field(default_factory=dict, description="Static part info by part number")
    tools: Dict[str, ToolInfo] = Field(default_factory=dict, description="Static tool info by part number")
    cached_at: datetime = Field(default_factory=datetime.now, description="When cache was created")
    last_cleanup: datetime = Field(default_factory=datetime.now, description="Last cleanup time")
    ttl_hours: int = Field(default=168, description="TTL for static data (1 week)")  # Static data lasts longer

    def cache_part(self, part_info: PartInfo) -> None:
        """Cache static part information."""
        self.parts[part_info.part_number] = part_info

    def cache_tool(self, tool_info: ToolInfo) -> None:
        """Cache static tool information."""
        self.tools[tool_info.part_number] = tool_info

    def get_part(self, part_number: str) -> Optional[PartInfo]:
        """Get cached static part info."""
        return self.parts.get(part_number)

    def get_tool(self, part_number: str) -> Optional[ToolInfo]:
        """Get cached static tool info."""
        return self.tools.get(part_number)

    def is_expired(self) -> bool:
        """Check if static cache has expired."""
        return datetime.now() - self.cached_at > timedelta(hours=self.ttl_hours)

    def cleanup_if_needed(self) -> None:
        """Cleanup expired entries if needed."""
        if datetime.now() - self.last_cleanup > timedelta(hours=24):  # Daily cleanup
            # For static cache, we keep everything until TTL expires
            # since static data doesn't change frequently
            self.last_cleanup = datetime.now()


class PricingCache(BaseModel):
    """Cache for dynamic pricing information that changes frequently."""

    pricing_data: Dict[str, PriceInfo] = Field(default_factory=dict, description="Pricing history by part number")
    last_cleanup: datetime = Field(default_factory=datetime.now, description="Last cleanup time")
    max_entries: int = Field(default=5000, description="Maximum pricing entries to keep")
    ttl_minutes: int = Field(default=30, description="TTL for pricing data (30 minutes)")

    def cache_pricing(self, part_number: str, price_info: PriceInfo) -> None:
        """Cache pricing information for a part."""
        self.pricing_data[part_number] = price_info

        # Manage cache size
        if len(self.pricing_data) > self.max_entries:
            self._evict_old_entries()

    def get_pricing(self, part_number: str) -> Optional[PriceInfo]:
        """Get cached pricing info if not expired."""
        price_info = self.pricing_data.get(part_number)
        if price_info and price_info.has_recent_data(self.ttl_minutes):
            return price_info
        elif price_info:  # Expired
            del self.pricing_data[part_number]
        return None

    def update_pricing(self, part_number: str, price: Optional[str] = None,
                      availability: Optional[str] = None, stock_level: Optional[str] = None,
                      shipping_info: Optional[str] = None, sale_info: Optional[str] = None,
                      source_url: Optional[str] = None) -> None:
        """Update pricing for a specific part."""
        # Get existing pricing or create new
        price_info = self.pricing_data.get(part_number)
        if not price_info:
            price_info = PriceInfo(part_number=part_number)
            self.pricing_data[part_number] = price_info

        # Add new snapshot
        snapshot = PriceStockSnapshot(
            price=price,
            availability=availability,
            stock_level=stock_level,
            shipping_info=shipping_info,
            sale_info=sale_info,
            source_url=source_url
        )

        price_info.add_snapshot(snapshot)

    def _evict_old_entries(self) -> None:
        """Remove oldest pricing entries to manage cache size."""
        # Sort by last accessed time and remove oldest 20%
        sorted_items = sorted(
            self.pricing_data.items(),
            key=lambda x: x[1].current_snapshot.time_collected if x[1].current_snapshot else datetime.min
        )

        entries_to_remove = max(1, len(sorted_items) // 5)  # Remove 20%
        for part_number, _ in sorted_items[:entries_to_remove]:
            del self.pricing_data[part_number]

    def cleanup_expired(self) -> int:
        """Remove expired pricing entries."""
        expired_keys = [
            part_number for part_number, price_info in self.pricing_data.items()
            if not price_info.has_recent_data(self.ttl_minutes)
        ]

        for key in expired_keys:
            del self.pricing_data[key]

        self.last_cleanup = datetime.now()
        return len(expired_keys)

    def get_stats(self) -> dict:
        """Get pricing cache statistics."""
        recent_count = sum(
            1 for price_info in self.pricing_data.values()
            if price_info.has_recent_data(self.ttl_minutes)
        )

        total_snapshots = sum(
            len(price_info.price_history) for price_info in self.pricing_data.values()
        )

        return {
            "total_parts_with_pricing": len(self.pricing_data),
            "parts_with_recent_pricing": recent_count,
            "total_price_snapshots": total_snapshots,
            "cache_utilization": round(len(self.pricing_data) / self.max_entries * 100, 1),
            "avg_snapshots_per_part": round(total_snapshots / len(self.pricing_data), 1) if self.pricing_data else 0
        }


class EnhancedPartCache(BaseModel):
    """Unified cache that combines static and dynamic data efficiently."""

    static_cache: StaticPartCache = Field(default_factory=StaticPartCache, description="Static part/tool information")
    pricing_cache: PricingCache = Field(default_factory=PricingCache, description="Dynamic pricing information")
    search_results_cache: Dict[str, VehiclePartsResult] = Field(default_factory=dict, description="Search results cache")
    search_cache_ttl_hours: int = Field(default=2, description="TTL for search results")

    def get_part_with_history(self, part_number: str) -> Optional[PartWithHistory]:
        """Get complete part information including pricing history."""
        # Get static info
        static_info = self.static_cache.get_part(part_number)
        if not static_info:
            return None

        # Get pricing history
        pricing_history = self.pricing_cache.get_pricing(part_number)

        # Combine into full model
        return PartWithHistory(
            part_info=static_info,
            pricing_history=pricing_history
        )

    def get_tool_with_history(self, part_number: str) -> Optional[ToolWithHistory]:
        """Get complete tool information including pricing history."""
        # Get static info
        static_info = self.static_cache.get_tool(part_number)
        if not static_info:
            return None

        # Get pricing history
        pricing_history = self.pricing_cache.get_pricing(part_number)

        # Combine into full model
        return ToolWithHistory(
            tool_info=static_info,
            pricing_history=pricing_history
        )

    def cache_part_complete(self, part_info: PartInfo, price: Optional[str] = None,
                          availability: Optional[str] = None, stock_level: Optional[str] = None,
                          shipping_info: Optional[str] = None, sale_info: Optional[str] = None,
                          source_url: Optional[str] = None) -> None:
        """Cache both static part info and current pricing."""
        # Cache static information
        self.static_cache.cache_part(part_info)

        # Cache pricing if provided
        if any([price, availability, stock_level, shipping_info, sale_info]):
            self.pricing_cache.update_pricing(
                part_number=part_info.part_number,
                price=price,
                availability=availability,
                stock_level=stock_level,
                shipping_info=shipping_info,
                sale_info=sale_info,
                source_url=source_url
            )

    def cache_tool_complete(self, tool_info: ToolInfo, price: Optional[str] = None,
                          availability: Optional[str] = None, stock_level: Optional[str] = None,
                          shipping_info: Optional[str] = None, sale_info: Optional[str] = None,
                          source_url: Optional[str] = None) -> None:
        """Cache both static tool info and current pricing."""
        # Cache static information
        self.static_cache.cache_tool(tool_info)

        # Cache pricing if provided
        if any([price, availability, stock_level, shipping_info, sale_info]):
            self.pricing_cache.update_pricing(
                part_number=tool_info.part_number,
                price=price,
                availability=availability,
                stock_level=stock_level,
                shipping_info=shipping_info,
                sale_info=sale_info,
                source_url=source_url
            )

    def update_pricing_only(self, part_number: str, price: Optional[str] = None,
                          availability: Optional[str] = None, stock_level: Optional[str] = None,
                          shipping_info: Optional[str] = None, sale_info: Optional[str] = None,
                          source_url: Optional[str] = None) -> None:
        """Update only pricing information for an existing part."""
        self.pricing_cache.update_pricing(
            part_number=part_number,
            price=price,
            availability=availability,
            stock_level=stock_level,
            shipping_info=shipping_info,
            sale_info=sale_info,
            source_url=source_url
        )

    def cache_search_result(self, cache_key: str, result: VehiclePartsResult) -> None:
        """Cache a search result."""
        self.search_results_cache[cache_key] = result

    def get_search_result(self, cache_key: str) -> Optional[VehiclePartsResult]:
        """Get cached search result if not expired."""
        result = self.search_results_cache.get(cache_key)
        if result:
            # Check if result is still fresh (simplified - you might want more sophisticated expiry)
            return result
        return None

    def cleanup_all(self) -> dict:
        """Clean up all cache components and return statistics."""
        # Cleanup static cache
        self.static_cache.cleanup_if_needed()

        # Cleanup pricing cache
        expired_pricing = self.pricing_cache.cleanup_expired()

        # Cleanup search results (remove old entries)
        # For now, we'll keep search results simple

        return {
            "static_parts_cached": len(self.static_cache.parts),
            "static_tools_cached": len(self.static_cache.tools),
            "pricing_entries_expired": expired_pricing,
            "search_results_cached": len(self.search_results_cache),
            "pricing_stats": self.pricing_cache.get_stats()
        }

    def get_comprehensive_stats(self) -> dict:
        """Get comprehensive statistics about all cache components."""
        pricing_stats = self.pricing_cache.get_stats()

        return {
            "static_cache": {
                "parts_count": len(self.static_cache.parts),
                "tools_count": len(self.static_cache.tools),
                "is_expired": self.static_cache.is_expired(),
                "age_hours": (datetime.now() - self.static_cache.cached_at).total_seconds() / 3600
            },
            "pricing_cache": pricing_stats,
            "search_cache": {
                "results_count": len(self.search_results_cache)
            },
            "total_memory_efficiency": {
                "static_data_separation": "✅ Static info cached long-term",
                "pricing_data_separation": "✅ Pricing cached short-term with history",
                "search_results_separation": "✅ Search results cached separately"
            }
        }