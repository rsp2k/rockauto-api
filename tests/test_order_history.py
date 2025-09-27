#!/usr/bin/env python3
"""
Test RockAuto order history functionality
"""

import asyncio
from rockauto_api import RockAutoClient, OrderHistoryFilter

async def test_order_history():
    print("📦 Testing RockAuto Order History")
    print("=" * 50)

    # Test credentials
    test_email = "rockauto@supported.systems"
    test_password = "Cooper123!"

    client = RockAutoClient()

    try:
        # Test 1: Authentication requirement
        print("1️⃣ Testing authentication requirement...")
        try:
            await client.get_order_history()
            print("❌ Order history should require authentication")
        except Exception as e:
            if "authentication required" in str(e).lower():
                print("✅ Order history correctly requires authentication")
            else:
                print(f"⚠️ Unexpected error: {e}")

        # Test 2: Login and get order history
        print("\n2️⃣ Testing authenticated order history...")
        login_success = await client.login(test_email, test_password)

        if login_success:
            print("✅ Login successful")

            # Test with default filter
            print("📋 Getting order history with default filter...")
            order_history = await client.get_order_history()

            print(f"✅ Order history retrieved successfully")
            print(f"   Orders found: {order_history.count}")
            print(f"   Filter applied: {order_history.filter_applied.date_range}")

            if order_history.orders:
                print("   Recent orders:")
                for i, order in enumerate(order_history.orders[:3]):  # Show first 3
                    print(f"     {i+1}. Order #{order.order_number}")
                    print(f"        Date: {order.date}")
                    print(f"        Status: {order.status}")
                    print(f"        Total: {order.total}")
                    if order.order_url:
                        print(f"        URL: {order.order_url}")
            else:
                print("   No orders found (this is expected for test account)")

            # Test 3: Custom filter
            print("\n3️⃣ Testing custom filter...")
            custom_filter = OrderHistoryFilter(
                date_range="1 Year",
                vehicle="All",
                part_category="All"
            )

            filtered_history = await client.get_order_history(custom_filter)
            print(f"✅ Filtered order history retrieved")
            print(f"   Orders found: {filtered_history.count}")
            print(f"   Date range: {filtered_history.filter_applied.date_range}")

        else:
            print("❌ Login failed")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if client.is_authenticated:
            await client.logout()
            print("\n🚪 Logged out successfully")
        await client.close()

if __name__ == "__main__":
    asyncio.run(test_order_history())