"""
RockAuto API Models

Pydantic models for type-safe RockAuto parts and tools data.
"""

from .account_activity import (
    AccountActivityResult,
    ExternalOrderRequest,
    OrderHistoryFilter,
    OrderHistoryItem,
    OrderHistoryResult,
    SavedAddress,
    SavedAddressesResult,
    SavedVehicle,
    SavedVehiclesResult,
)
from .engine import Engine
from .order_status import (
    BillingInfo,
    OrderItem,
    OrderListRequest,
    OrderLookupRequest,
    OrderStatus,
    OrderStatusError,
    OrderStatusResult,
    ShippingInfo,
)
from .part_cache import (
    CacheConfiguration,
    CachedPartInfo,
    CachedVehiclePartsResult,
    PartCache,
)
from .part_category import PartCategory
from .part_info import PartInfo, PartWithHistory
from .part_search_options import (
    ManufacturerOptions,
    PartGroupOptions,
    PartSearchOption,
    PartTypeOptions,
    WhatIsPartCalledResult,
    WhatIsPartCalledResults,
)
from .part_search_result import PartSearchResult
from .tool_categories import ToolCategories
from .tool_category import ToolCategory
from .tool_info import ToolInfo, ToolWithHistory
from .tools_result import ToolsResult
from .vehicle_engines import VehicleEngines
from .vehicle_makes import VehicleMakes
from .vehicle_models import VehicleModels
from .vehicle_part_categories import VehiclePartCategories
from .vehicle_parts_result import VehiclePartsResult
from .vehicle_years import VehicleYears
from .price_info import PriceInfo, PriceStockSnapshot, PartWithPricing, ToolWithPricing
from .enhanced_cache import EnhancedPartCache, StaticPartCache, PricingCache

__all__ = [
    "AccountActivityResult",
    "BillingInfo",
    "CachedPartInfo",
    "CachedVehiclePartsResult",
    "CacheConfiguration",
    "Engine",
    "ExternalOrderRequest",
    "ManufacturerOptions",
    "OrderHistoryFilter",
    "OrderHistoryItem",
    "OrderHistoryResult",
    "OrderItem",
    "OrderListRequest",
    "OrderLookupRequest",
    "OrderStatus",
    "OrderStatusError",
    "OrderStatusResult",
    "PartCache",
    "PartCategory",
    "PartGroupOptions",
    "PartInfo",
    "PartWithHistory",
    "PartSearchOption",
    "PartSearchResult",
    "PartTypeOptions",
    "SavedAddress",
    "SavedAddressesResult",
    "SavedVehicle",
    "SavedVehiclesResult",
    "ShippingInfo",
    "ToolCategory",
    "ToolInfo",
    "ToolWithHistory",
    "ToolCategories",
    "ToolsResult",
    "VehicleEngines",
    "VehicleMakes",
    "VehicleModels",
    "VehiclePartCategories",
    "VehiclePartsResult",
    "VehicleYears",
    "WhatIsPartCalledResult",
    "WhatIsPartCalledResults",
    # New pricing and enhanced cache models
    "PriceInfo",
    "PriceStockSnapshot",
    "PartWithPricing",
    "ToolWithPricing",
    "EnhancedPartCache",
    "StaticPartCache",
    "PricingCache",
]
