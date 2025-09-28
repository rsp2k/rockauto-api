"""Models for RockAuto authenticated account activity features."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class OrderHistoryFilter(BaseModel):
    """Filter parameters for order history search."""

    date_range: str = Field(default="3 Months", description="Time range filter")
    vehicle: str = Field(default="All", description="Vehicle filter")
    part_category: str = Field(default="All", description="Part category filter")
    part_number: Optional[str] = Field(None, description="Part number wildcard search")

    @field_validator('date_range')
    @classmethod
    def validate_date_range(cls, v):
        """Validate date range options."""
        valid_ranges = ["1 Month", "3 Months", "6 Months", "9 Months", "1 Year", "2 Years", "All"]
        if v not in valid_ranges:
            raise ValueError(f"Date range must be one of: {', '.join(valid_ranges)}")
        return v


class OrderHistoryItem(BaseModel):
    """Individual order in order history."""

    order_number: str = Field(..., description="Order number")
    date: str = Field(..., description="Order date")
    status: str = Field(..., description="Order status")
    total: str = Field(..., description="Order total amount")
    vehicle: Optional[str] = Field(None, description="Associated vehicle")
    order_url: Optional[str] = Field(None, description="URL for detailed order status")


class OrderHistoryResult(BaseModel):
    """Result from order history search."""

    orders: List[OrderHistoryItem] = Field(default_factory=list, description="List of orders")
    count: int = Field(default=0, description="Number of orders found")
    filter_applied: OrderHistoryFilter = Field(..., description="Filters used in search")
    search_time: str = Field(default_factory=lambda: datetime.now().isoformat(),
                           description="When search was performed")

    def get_orders_by_status(self, status: str) -> List[OrderHistoryItem]:
        """Get orders with specific status."""
        return [order for order in self.orders if status.lower() in order.status.lower()]

    def get_total_amount(self) -> float:
        """Calculate total amount of all orders (if possible)."""
        total = 0.0
        for order in self.orders:
            try:
                # Extract numeric value from price string like "$123.45"
                amount_str = order.total.replace('$', '').replace(',', '')
                total += float(amount_str)
            except (ValueError, AttributeError):
                continue
        return total


class ExternalOrderRequest(BaseModel):
    """Request to add external order to account history."""

    email_or_phone: str = Field(..., description="Email address or phone number from external order")
    order_number: str = Field(..., description="Order number to add")

    @field_validator('order_number')
    @classmethod
    def validate_order_number(cls, v):
        """Validate order number format."""
        if not v or not v.isdigit():
            raise ValueError("Order number must be numeric")
        if len(v) > 12:
            raise ValueError("Order number cannot exceed 12 digits")
        return v

    @field_validator('email_or_phone')
    @classmethod
    def validate_email_or_phone(cls, v):
        """Basic validation for email or phone format."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Email or phone cannot be empty")
        if len(v) > 50:
            raise ValueError("Email or phone cannot exceed 50 characters")
        return v.strip()


class SavedAddress(BaseModel):
    """Saved address information."""

    name: str = Field(..., description="Address name/label")
    full_name: str = Field(..., description="Full name for shipping")
    address_line1: str = Field(..., description="Street address")
    address_line2: Optional[str] = Field(None, description="Apartment, suite, etc.")
    city: str = Field(..., description="City")
    state: str = Field(..., description="State/province")
    postal_code: str = Field(..., description="ZIP/postal code")
    country: str = Field(default="US", description="Country code")
    phone: Optional[str] = Field(None, description="Phone number")
    is_default: bool = Field(default=False, description="Whether this is the default address")
    address_id: Optional[str] = Field(None, description="Internal address ID for editing")


class SavedAddressesResult(BaseModel):
    """Result from retrieving saved addresses."""

    addresses: List[SavedAddress] = Field(default_factory=list, description="List of saved addresses")
    count: int = Field(default=0, description="Number of addresses")
    has_default: bool = Field(default=False, description="Whether a default address is set")

    def get_default_address(self) -> Optional[SavedAddress]:
        """Get the default address if one is set."""
        for address in self.addresses:
            if address.is_default:
                return address
        return None


class SavedVehicle(BaseModel):
    """Saved vehicle information."""

    year: int = Field(..., description="Vehicle year")
    make: str = Field(..., description="Vehicle make")
    model: str = Field(..., description="Vehicle model")
    engine: Optional[str] = Field(None, description="Engine description")
    carcode: Optional[str] = Field(None, description="RockAuto carcode")
    display_name: str = Field(..., description="Display name (e.g., '2017 FORD F-150')")
    catalog_url: Optional[str] = Field(None, description="Direct URL to parts catalog")
    vehicle_id: Optional[str] = Field(None, description="Internal vehicle ID for deletion")


class SavedVehiclesResult(BaseModel):
    """Result from retrieving saved vehicles."""

    vehicles: List[SavedVehicle] = Field(default_factory=list, description="List of saved vehicles")
    count: int = Field(default=0, description="Number of vehicles")

    def get_vehicle_by_year_make_model(self, year: int, make: str, model: str) -> Optional[SavedVehicle]:
        """Find vehicle by year, make, and model."""
        for vehicle in self.vehicles:
            if (vehicle.year == year and
                vehicle.make.upper() == make.upper() and
                vehicle.model.upper() == model.upper()):
                return vehicle
        return None


class AccountActivityResult(BaseModel):
    """Comprehensive account activity information."""

    order_history: Optional[OrderHistoryResult] = Field(None, description="Order history data")
    saved_addresses: Optional[SavedAddressesResult] = Field(None, description="Saved addresses")
    saved_vehicles: Optional[SavedVehiclesResult] = Field(None, description="Saved vehicles")
    has_discount_codes: bool = Field(default=False, description="Whether account has discount codes")
    has_store_credit: bool = Field(default=False, description="Whether account has store credit")
    has_alerts: bool = Field(default=False, description="Whether account has availability alerts")
    last_updated: str = Field(default_factory=lambda: datetime.now().isoformat(),
                             description="When data was retrieved")
