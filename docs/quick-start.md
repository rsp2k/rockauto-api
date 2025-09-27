# 🚀 Quick Start Guide

Get up and running with the RockAuto API Client in 5 minutes!

## 1. Installation

```bash
# Install required dependencies
pip install httpx beautifulsoup4 pydantic

# Or use the project directly
git clone <repository-url>
cd rockauto-api
```

## 2. Basic Usage (No Login Required)

```python
import asyncio
from rockauto_api import RockAutoClient

async def find_parts():
    async with RockAutoClient() as client:
        # Find a specific vehicle
        vehicle = await client.get_vehicle("TOYOTA", 2020, "CAMRY")
        print(f"Found: {vehicle.year} {vehicle.make} {vehicle.model}")

        # Get brake parts
        brake_parts = await vehicle.get_parts_by_category("Brake & Wheel Hub")
        print(f"Available brake parts: {brake_parts.count}")

        # Show first 3 parts
        for part in brake_parts.parts[:3]:
            print(f"- {part.brand} {part.part_number}: ${part.price}")

# Run the example
asyncio.run(find_parts())
```

## 3. Authenticated Features (Login Required)

```python
import asyncio
from rockauto_api import RockAutoClient

async def check_account():
    async with RockAutoClient() as client:
        # Login (use your actual credentials)
        success = await client.login("your-email@example.com", "your-password")

        if success:
            print("✅ Logged in successfully!")

            # Check your saved vehicles
            vehicles = await client.get_saved_vehicles()
            print(f"Your garage has {vehicles.count} vehicles")

            # Check recent orders
            orders = await client.get_order_history()
            print(f"Recent orders: {orders.count}")

            # Logout when done
            await client.logout()
        else:
            print("❌ Login failed")

# Run with your credentials
asyncio.run(check_account())
```

## 4. Vehicle Discovery Workflow

```python
import asyncio
from rockauto_api import RockAutoClient

async def explore_catalog():
    async with RockAutoClient() as client:
        # Step 1: Browse all makes
        makes = await client.get_makes()
        print(f"Available makes: {makes.count}")
        print(f"Popular makes: {', '.join(makes.makes[:10])}")

        # Step 2: Get years for Honda
        years = await client.get_years_for_make("HONDA")
        print(f"Honda years: {min(years.years)}-{max(years.years)}")

        # Step 3: Get 2021 Honda models
        models = await client.get_models_for_make_year("HONDA", 2021)
        print(f"2021 Honda models: {', '.join(models.models[:5])}")

        # Step 4: Get engines for Civic
        engines = await client.get_engines_for_vehicle("HONDA", 2021, "CIVIC")
        print(f"Civic engines: {engines.count} options")
        for engine in engines.engines:
            print(f"  - {engine.description}")

asyncio.run(explore_catalog())
```

## 5. Order Status Lookup (Public)

```python
import asyncio
from rockauto_api import RockAutoClient

async def track_order():
    async with RockAutoClient() as client:
        # Look up order status (no login required)
        result = await client.lookup_order_status(
            email_or_phone="customer@example.com",
            order_number="123456789"
        )

        if result.success and result.order:
            order = result.order
            print(f"Order {order.order_number}: {order.status}")
            print(f"Items: {order.item_count}")
            if order.shipping and order.shipping.tracking_number:
                print(f"Tracking: {order.shipping.tracking_number}")
        else:
            print(f"Order lookup failed: {result.error.message}")

asyncio.run(track_order())
```

## 6. Error Handling Pattern

```python
import asyncio
from rockauto_api import RockAutoClient

async def robust_search():
    async with RockAutoClient() as client:
        try:
            # Attempt operation
            vehicle = await client.get_vehicle("TOYOTA", 2020, "CAMRY")
            parts = await vehicle.get_parts_by_category("Engine")
            print(f"Found {parts.count} engine parts")

        except Exception as e:
            # Handle common errors
            if "authentication required" in str(e).lower():
                print("🔐 This operation requires login")
            elif "captcha" in str(e).lower():
                print("🤖 CAPTCHA detected - try again later")
            elif "not found" in str(e).lower():
                print("🔍 Vehicle/parts not found")
            else:
                print(f"❌ Error: {e}")

asyncio.run(robust_search())
```

## 7. Performance Tips

```python
import asyncio
from rockauto_api import RockAutoClient

async def concurrent_operations():
    async with RockAutoClient() as client:
        # Run multiple operations concurrently
        tasks = [
            client.get_makes(),
            client.get_manufacturers(),
            client.get_tool_categories()
        ]

        makes, manufacturers, tools = await asyncio.gather(*tasks)

        print(f"Loaded in parallel:")
        print(f"  - {makes.count} makes")
        print(f"  - {manufacturers.count} manufacturers")
        print(f"  - {tools.count} tool categories")

asyncio.run(concurrent_operations())
```

## 8. Testing Your Setup

```bash
# Test unauthenticated features (should always work)
PYTHONPATH=src python tests/test_unauthenticated_features.py

# Test authenticated features (requires valid credentials)
PYTHONPATH=src python tests/test_authenticated_debug.py
```

## 🎯 Next Steps

1. **Read the Full Documentation**: Check out the [main README](../README.md) for comprehensive examples
2. **Explore Models**: Review the [API Reference](api-reference.md) for all available methods
3. **Join Development**: See [Contributing Guidelines](contributing.md) to help improve the project
4. **Performance Tuning**: Read [Benchmarks](benchmarks.md) for optimization tips

## 🆘 Need Help?

- **Common Issues**: Check [Troubleshooting](troubleshooting.md)
- **Examples**: Browse [Examples Directory](examples/)
- **Technical Details**: See [Architecture Documentation](architecture.md)

---

**🚗 Happy parts hunting with your new API client!**