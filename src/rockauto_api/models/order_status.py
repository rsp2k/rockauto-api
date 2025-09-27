"""Models for RockAuto order status functionality."""

from datetime import datetime
from typing import List, Optional, Union
from pydantic import BaseModel, Field, validator


class OrderItem(BaseModel):
    """Individual item in an order."""

    part_number: str = Field(..., description="Part number")
    description: str = Field(..., description="Part description")
    brand: str = Field(..., description="Part brand/manufacturer")
    quantity: int = Field(..., description="Quantity ordered")
    unit_price: str = Field(..., description="Price per unit")
    total_price: str = Field(..., description="Total price for this item")
    status: str = Field(default="Unknown", description="Status of this item")
    tracking_number: Optional[str] = Field(None, description="Tracking number if shipped")


class ShippingInfo(BaseModel):
    """Shipping information for an order."""

    method: str = Field(..., description="Shipping method")
    cost: str = Field(..., description="Shipping cost")
    carrier: Optional[str] = Field(None, description="Shipping carrier")
    tracking_number: Optional[str] = Field(None, description="Main tracking number")
    estimated_delivery: Optional[str] = Field(None, description="Estimated delivery date")
    actual_delivery: Optional[str] = Field(None, description="Actual delivery date")


class BillingInfo(BaseModel):
    """Billing information for an order."""

    subtotal: str = Field(..., description="Order subtotal")
    shipping_cost: str = Field(..., description="Shipping cost")
    tax: str = Field(default="$0.00", description="Tax amount")
    total: str = Field(..., description="Order total")
    payment_method: Optional[str] = Field(None, description="Payment method used")
    payment_status: str = Field(default="Unknown", description="Payment status")


class OrderStatus(BaseModel):
    """Complete order status information."""

    order_number: str = Field(..., description="RockAuto order number")
    order_date: Optional[str] = Field(None, description="Date order was placed")
    status: str = Field(..., description="Overall order status")
    customer_email: Optional[str] = Field(None, description="Customer email")
    customer_phone: Optional[str] = Field(None, description="Customer phone")

    # Order contents
    items: List[OrderItem] = Field(default_factory=list, description="Items in the order")
    item_count: int = Field(default=0, description="Total number of different items")

    # Financial information
    billing: Optional[BillingInfo] = Field(None, description="Billing information")

    # Shipping information
    shipping: Optional[ShippingInfo] = Field(None, description="Shipping information")

    # Additional details
    notes: Optional[str] = Field(None, description="Order notes or special instructions")
    return_eligibility: bool = Field(default=False, description="Whether order is eligible for returns")
    last_updated: Optional[str] = Field(None, description="When status was last updated")

    @validator('order_number')
    def validate_order_number(cls, v):
        """Validate order number format."""
        if not v or not v.isdigit():
            raise ValueError("Order number must be numeric")
        if len(v) > 12:
            raise ValueError("Order number cannot exceed 12 digits")
        return v

    def get_total_items(self) -> int:
        """Get total quantity of all items."""
        return sum(item.quantity for item in self.items)

    def get_shipped_items(self) -> List[OrderItem]:
        """Get list of items that have been shipped."""
        return [item for item in self.items if item.tracking_number]

    def get_pending_items(self) -> List[OrderItem]:
        """Get list of items still pending/processing."""
        shipped_statuses = ["shipped", "delivered", "in transit"]
        return [item for item in self.items
                if item.status.lower() not in shipped_statuses]

    def is_fully_shipped(self) -> bool:
        """Check if all items have been shipped."""
        return len(self.get_shipped_items()) == len(self.items)

    def has_tracking_info(self) -> bool:
        """Check if any items have tracking information."""
        return any(item.tracking_number for item in self.items)


class OrderLookupRequest(BaseModel):
    """Request parameters for order lookup."""

    email_or_phone: str = Field(..., description="Customer email address or phone number")
    order_number: str = Field(..., description="RockAuto order number")

    @validator('order_number')
    def validate_order_number(cls, v):
        """Validate order number format."""
        if not v or not v.isdigit():
            raise ValueError("Order number must be numeric")
        if len(v) > 12:
            raise ValueError("Order number cannot exceed 12 digits")
        return v

    @validator('email_or_phone')
    def validate_email_or_phone(cls, v):
        """Basic validation for email or phone format."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Email or phone cannot be empty")
        if len(v) > 50:
            raise ValueError("Email or phone cannot exceed 50 characters")
        return v.strip()


class OrderListRequest(BaseModel):
    """Request to get list of orders for a customer."""

    method: str = Field(..., description="Delivery method: 'email' or 'sms'")
    contact: str = Field(..., description="Email address or phone number")

    @validator('method')
    def validate_method(cls, v):
        """Validate delivery method."""
        if v.lower() not in ['email', 'sms']:
            raise ValueError("Method must be 'email' or 'sms'")
        return v.lower()

    @validator('contact')
    def validate_contact(cls, v):
        """Validate contact information."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Contact information cannot be empty")
        if len(v) > 50:
            raise ValueError("Contact information cannot exceed 50 characters")
        return v.strip()


class OrderStatusError(BaseModel):
    """Error response from order status lookup."""

    error_type: str = Field(..., description="Type of error")
    message: str = Field(..., description="Error message")
    order_number: Optional[str] = Field(None, description="Order number that failed")
    suggestions: List[str] = Field(default_factory=list, description="Suggestions to resolve error")

    @classmethod
    def order_not_found(cls, order_number: str) -> "OrderStatusError":
        """Create error for order not found."""
        return cls(
            error_type="ORDER_NOT_FOUND",
            message=f"Order {order_number} was not found",
            order_number=order_number,
            suggestions=[
                "Verify the order number is correct",
                "Check that the email/phone matches the order",
                "Ensure the order was placed with RockAuto"
            ]
        )

    @classmethod
    def invalid_credentials(cls, order_number: str) -> "OrderStatusError":
        """Create error for invalid email/phone."""
        return cls(
            error_type="INVALID_CREDENTIALS",
            message="Email or phone does not match order records",
            order_number=order_number,
            suggestions=[
                "Verify email address spelling",
                "Try phone number if email doesn't work",
                "Check for alternate email addresses used"
            ]
        )

    @classmethod
    def system_error(cls, message: str) -> "OrderStatusError":
        """Create error for system issues."""
        return cls(
            error_type="SYSTEM_ERROR",
            message=message,
            suggestions=[
                "Try again in a few minutes",
                "Clear browser cache and cookies",
                "Contact RockAuto customer service"
            ]
        )


class OrderStatusResult(BaseModel):
    """Result from order status lookup."""

    success: bool = Field(..., description="Whether lookup was successful")
    order: Optional[OrderStatus] = Field(None, description="Order information if found")
    error: Optional[OrderStatusError] = Field(None, description="Error information if failed")
    lookup_time: str = Field(default_factory=lambda: datetime.now().isoformat(),
                           description="When lookup was performed")

    @classmethod
    def success_result(cls, order: OrderStatus) -> "OrderStatusResult":
        """Create successful result."""
        return cls(success=True, order=order)

    @classmethod
    def error_result(cls, error: OrderStatusError) -> "OrderStatusResult":
        """Create error result."""
        return cls(success=False, error=error)

    def __str__(self) -> str:
        if self.success and self.order:
            return f"Order {self.order.order_number}: {self.order.status}"
        elif self.error:
            return f"Error: {self.error.message}"
        return "Unknown result"