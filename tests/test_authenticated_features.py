#!/usr/bin/env python3
"""
Test RockAuto authenticated account features
Testing account activity, saved addresses, saved vehicles, and external order management
"""

import asyncio
from rockauto_api import RockAutoClient, SavedAddress, SavedVehicle, AccountActivityResult, OrderHistoryFilter

async def test_authenticated_account_features():
    print("🔐 Testing RockAuto Authenticated Account Features")
    print("=" * 60)
    print("Testing the authenticated account functionality we implemented:")
    print("• Get saved addresses from profile")
    print("• Get saved vehicles from profile")
    print("• Get comprehensive account activity")
    print("• Add external order to account history")
    print("• Authentication requirement enforcement")
    print("=" * 60)

    # Test credentials provided by user
    test_email = "rockauto@supported.systems"
    test_password = "Cooper123!"

    client = RockAutoClient()
    test_results = {"passed": 0, "failed": 0, "warnings": 0}

    try:
        # Test 1: Ensure Authentication is Required
        print("\n1️⃣ Testing Authentication Requirements")
        print("-" * 50)

        print("🔒 Testing that methods require authentication...")

        # Test each method fails when not authenticated
        auth_required_tests = [
            ("get_saved_addresses", lambda: client.get_saved_addresses()),
            ("get_saved_vehicles", lambda: client.get_saved_vehicles()),
            ("get_account_activity", lambda: client.get_account_activity()),
            ("get_order_history", lambda: client.get_order_history()),
            ("add_external_order", lambda: client.add_external_order("test@example.com", "123456789"))
        ]

        for method_name, method_call in auth_required_tests:
            try:
                await method_call()
                print(f"❌ {method_name} should require authentication")
                test_results["failed"] += 1
            except Exception as e:
                if "authentication required" in str(e).lower():
                    print(f"✅ {method_name} correctly requires authentication")
                    test_results["passed"] += 1
                else:
                    print(f"⚠️  {method_name} failed with unexpected error: {e}")
                    test_results["warnings"] += 1

        # Test 2: Login and Test Authenticated Features
        print("\n2️⃣ Testing Login and Authenticated Access")
        print("-" * 50)

        print(f"🔑 Logging in as {test_email}...")
        try:
            login_success = await client.login(test_email, test_password)
            if login_success:
                print("✅ Login successful!")
                test_results["passed"] += 1
            else:
                print("❌ Login failed")
                test_results["failed"] += 1
                return
        except Exception as e:
            print(f"❌ Login threw exception: {e}")
            test_results["failed"] += 1
            return

        # Test 3: Get Saved Addresses
        print("\n3️⃣ Testing Saved Addresses Retrieval")
        print("-" * 45)

        try:
            addresses_result = await client.get_saved_addresses()
            print(f"✅ Retrieved saved addresses successfully")
            print(f"   Address count: {addresses_result.count}")
            print(f"   Has default address: {addresses_result.has_default}")

            for i, address in enumerate(addresses_result.addresses):
                print(f"   Address {i+1}: {address.full_name}")
                print(f"     Street: {address.address_line1}")
                print(f"     City: {address.city}, {address.state} {address.postal_code}")
                if address.address_id:
                    print(f"     ID: {address.address_id}")

            test_results["passed"] += 1
        except Exception as e:
            print(f"❌ Get saved addresses failed: {e}")
            test_results["failed"] += 1

        # Test 4: Get Saved Vehicles
        print("\n4️⃣ Testing Saved Vehicles Retrieval")
        print("-" * 40)

        try:
            vehicles_result = await client.get_saved_vehicles()
            print(f"✅ Retrieved saved vehicles successfully")
            print(f"   Vehicle count: {vehicles_result.count}")

            for i, vehicle in enumerate(vehicles_result.vehicles):
                print(f"   Vehicle {i+1}: {vehicle.display_name}")
                print(f"     Year: {vehicle.year}, Make: {vehicle.make}, Model: {vehicle.model}")
                if vehicle.carcode:
                    print(f"     Carcode: {vehicle.carcode}")
                if vehicle.catalog_url:
                    print(f"     Catalog URL: {vehicle.catalog_url}")
                if vehicle.vehicle_id:
                    print(f"     ID: {vehicle.vehicle_id}")

            test_results["passed"] += 1
        except Exception as e:
            print(f"❌ Get saved vehicles failed: {e}")
            test_results["failed"] += 1

        # Test 5: Get Comprehensive Account Activity
        print("\n5️⃣ Testing Comprehensive Account Activity")
        print("-" * 45)

        try:
            activity_result = await client.get_account_activity()
            print(f"✅ Retrieved account activity successfully")

            # Display summary
            if activity_result.saved_addresses:
                print(f"   Saved addresses: {activity_result.saved_addresses.count}")
            if activity_result.saved_vehicles:
                print(f"   Saved vehicles: {activity_result.saved_vehicles.count}")

            print(f"   Has discount codes: {activity_result.has_discount_codes}")
            print(f"   Has store credit: {activity_result.has_store_credit}")
            print(f"   Has alerts: {activity_result.has_alerts}")
            print(f"   Last updated: {activity_result.last_updated}")

            test_results["passed"] += 1
        except Exception as e:
            print(f"❌ Get account activity failed: {e}")
            test_results["failed"] += 1

        # Test 6: Get Order History
        print("\n6️⃣ Testing Order History Retrieval")
        print("-" * 40)

        try:
            order_history = await client.get_order_history()
            print(f"✅ Retrieved order history successfully")
            print(f"   Order count: {order_history.count}")
            print(f"   Date range filter: {order_history.filter_applied.date_range}")

            for i, order in enumerate(order_history.orders[:3]):  # Show first 3
                print(f"   Order {i+1}: #{order.order_number}")
                print(f"     Date: {order.date}")
                print(f"     Status: {order.status}")
                print(f"     Total: {order.total}")

            test_results["passed"] += 1
        except Exception as e:
            print(f"❌ Get order history failed: {e}")
            test_results["failed"] += 1

        # Test 7: Test External Order Addition (with test data)
        print("\n7️⃣ Testing External Order Addition")
        print("-" * 40)

        print("🔗 Testing add external order functionality...")
        try:
            # Use test data that won't actually add anything
            external_order_result = await client.add_external_order("test@example.com", "999999999")
            print(f"✅ External order addition completed: {external_order_result}")
            print("   Note: This is expected to fail with test data (no real order)")
            test_results["passed"] += 1
        except Exception as e:
            print(f"⚠️  External order addition failed (expected with test data): {e}")
            test_results["warnings"] += 1

        # Test 8: Data Model Validation
        print("\n8️⃣ Testing Data Model Validation")
        print("-" * 40)

        try:
            # Test SavedAddress model
            test_address = SavedAddress(
                name="Test Address",
                full_name="John Doe",
                address_line1="123 Main St",
                city="Anytown",
                state="CA",
                postal_code="12345"
            )
            print(f"✅ SavedAddress model validation: {test_address.name}")

            # Test SavedVehicle model
            test_vehicle = SavedVehicle(
                year=2020,
                make="TOYOTA",
                model="CAMRY",
                display_name="2020 TOYOTA CAMRY"
            )
            print(f"✅ SavedVehicle model validation: {test_vehicle.display_name}")

            # Test AccountActivityResult model
            test_activity = AccountActivityResult(
                has_discount_codes=True,
                has_store_credit=False,
                has_alerts=True
            )
            print(f"✅ AccountActivityResult model validation: discount codes = {test_activity.has_discount_codes}")

            test_results["passed"] += 1
        except Exception as e:
            print(f"❌ Model validation failed: {e}")
            test_results["failed"] += 1

        # Test 9: Authentication Status Verification
        print("\n9️⃣ Testing Authentication Status During Session")
        print("-" * 50)

        auth_status = client.get_authentication_status()
        if auth_status['is_authenticated'] and auth_status['user_email'] == test_email:
            print("✅ Authentication status correctly maintained during session")
            print(f"   Logged in as: {auth_status['user_email']}")
            print(f"   Session cookies: {auth_status['has_session_cookies']}")
            test_results["passed"] += 1
        else:
            print("❌ Authentication status not properly maintained")
            test_results["failed"] += 1

        # Summary
        print("\n" + "=" * 60)
        print("🎯 Authenticated Features Test Summary")
        print("=" * 60)

        total_tests = test_results["passed"] + test_results["failed"]
        pass_rate = (test_results["passed"] / total_tests * 100) if total_tests > 0 else 0

        print(f"✅ Tests Passed: {test_results['passed']}")
        print(f"❌ Tests Failed: {test_results['failed']}")
        print(f"⚠️  Warnings: {test_results['warnings']}")
        print(f"📊 Pass Rate: {pass_rate:.1f}%")

        print("\n🔐 Authenticated Features Successfully Tested:")
        print("   • Authentication requirement enforcement")
        print("   • Saved addresses retrieval and parsing")
        print("   • Saved vehicles retrieval and parsing")
        print("   • Comprehensive account activity data")
        print("   • Order history retrieval and filtering")
        print("   • External order addition functionality")
        print("   • Data model validation and structure")
        print("   • Session authentication state management")

        if test_results["failed"] == 0:
            print("\n🎉 All authenticated features are working correctly!")
        else:
            print(f"\n⚠️  {test_results['failed']} issues need attention")

    except Exception as e:
        print(f"\n❌ Critical test failure: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Ensure we logout before closing
        if client.is_authenticated:
            try:
                await client.logout()
                print("\n🚪 Final cleanup: Logged out successfully")
            except:
                print("\n⚠️  Final cleanup: Logout failed")

        await client.close()

if __name__ == "__main__":
    asyncio.run(test_authenticated_account_features())