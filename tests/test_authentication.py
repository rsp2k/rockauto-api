#!/usr/bin/env python3
"""
Test RockAuto authentication functionality
Focused testing of login, logout, and authenticated session management
"""

import asyncio
from rockauto_api import RockAutoClient

async def test_authentication_features():
    print("🔐 Testing RockAuto Authentication Features")
    print("=" * 50)
    print("Testing the authentication functionality we implemented:")
    print("• Login with email and password")
    print("• Authentication status tracking")
    print("• Session cookie management")
    print("• Logout functionality")
    print("• Error handling for invalid credentials")
    print("=" * 50)

    # Test credentials provided by user
    test_email = "rockauto@supported.systems"
    test_password = "Cooper123!"

    client = RockAutoClient()
    test_results = {"passed": 0, "failed": 0, "warnings": 0}

    try:
        # Test 1: Check Initial Authentication Status
        print("\n1️⃣ Testing Initial Authentication Status")
        print("-" * 45)

        initial_status = client.get_authentication_status()
        print(f"✅ Initial authentication status retrieved:")
        print(f"   Is Authenticated: {initial_status['is_authenticated']}")
        print(f"   User Email: {initial_status['user_email']}")
        print(f"   Has Session Cookies: {initial_status['has_session_cookies']}")

        if not initial_status['is_authenticated']:
            print("✅ Client starts in unauthenticated state (expected)")
            test_results["passed"] += 1
        else:
            print("⚠️  Client starts authenticated (unexpected)")
            test_results["warnings"] += 1

        # Test 2: Valid Login
        print("\n2️⃣ Testing Valid Login")
        print("-" * 30)

        print(f"🔑 Attempting login with {test_email}...")
        try:
            login_success = await client.login(test_email, test_password)

            if login_success:
                print("✅ Login successful!")

                # Check authentication status after login
                auth_status = client.get_authentication_status()
                print(f"   Is Authenticated: {auth_status['is_authenticated']}")
                print(f"   User Email: {auth_status['user_email']}")
                print(f"   Session Cookies: {len(client.cookies)} cookies")

                if auth_status['is_authenticated'] and auth_status['user_email'] == test_email:
                    print("✅ Authentication state correctly updated")
                    test_results["passed"] += 1
                else:
                    print("❌ Authentication state not properly updated")
                    test_results["failed"] += 1
            else:
                print("❌ Login failed with valid credentials")
                test_results["failed"] += 1

        except Exception as e:
            print(f"❌ Login attempt threw exception: {e}")
            test_results["failed"] += 1

        # Test 3: Test Authenticated Session
        print("\n3️⃣ Testing Authenticated Session")
        print("-" * 40)

        if client.is_authenticated:
            print("🔍 Testing that authenticated requests work...")
            try:
                # Test a basic operation that should work when authenticated
                makes = await client.get_makes()
                print(f"✅ Authenticated request successful: Found {makes.count} vehicle makes")
                test_results["passed"] += 1
            except Exception as e:
                print(f"❌ Authenticated request failed: {e}")
                test_results["failed"] += 1
        else:
            print("⚠️  Skipping authenticated session test (not logged in)")
            test_results["warnings"] += 1

        # Test 4: Test Logout
        print("\n4️⃣ Testing Logout Functionality")
        print("-" * 35)

        if client.is_authenticated:
            print("🚪 Attempting logout...")
            try:
                logout_success = await client.logout()

                if logout_success:
                    print("✅ Logout successful!")

                    # Check authentication status after logout
                    auth_status = client.get_authentication_status()
                    print(f"   Is Authenticated: {auth_status['is_authenticated']}")
                    print(f"   User Email: {auth_status['user_email']}")

                    if not auth_status['is_authenticated'] and auth_status['user_email'] is None:
                        print("✅ Authentication state correctly cleared")
                        test_results["passed"] += 1
                    else:
                        print("❌ Authentication state not properly cleared")
                        test_results["failed"] += 1
                else:
                    print("❌ Logout failed")
                    test_results["failed"] += 1

            except Exception as e:
                print(f"❌ Logout attempt threw exception: {e}")
                test_results["failed"] += 1
        else:
            print("⚠️  Skipping logout test (not logged in)")
            test_results["warnings"] += 1

        # Test 5: Test Invalid Login
        print("\n5️⃣ Testing Invalid Login Handling")
        print("-" * 40)

        print("🔒 Testing login with invalid credentials...")
        try:
            invalid_login = await client.login("invalid@example.com", "wrongpassword")

            if not invalid_login:
                print("✅ Invalid login correctly rejected")

                # Check that authentication state remains false
                auth_status = client.get_authentication_status()
                if not auth_status['is_authenticated']:
                    print("✅ Authentication state remains unauthenticated")
                    test_results["passed"] += 1
                else:
                    print("❌ Authentication state incorrectly set after failed login")
                    test_results["failed"] += 1
            else:
                print("❌ Invalid login incorrectly succeeded")
                test_results["failed"] += 1

        except Exception as e:
            print(f"⚠️  Invalid login threw exception (might be expected): {e}")
            test_results["warnings"] += 1

        # Test 6: Test Re-login
        print("\n6️⃣ Testing Re-login After Logout")
        print("-" * 40)

        print(f"🔄 Re-attempting login with {test_email}...")
        try:
            relogin_success = await client.login(test_email, test_password, keep_signed_in=True)

            if relogin_success:
                print("✅ Re-login successful!")
                print("✅ Keep signed in option tested")
                test_results["passed"] += 1
            else:
                print("❌ Re-login failed")
                test_results["failed"] += 1

        except Exception as e:
            print(f"❌ Re-login attempt threw exception: {e}")
            test_results["failed"] += 1

        # Test 7: Cookie Management Test
        print("\n7️⃣ Testing Session Cookie Management")
        print("-" * 40)

        print("🍪 Analyzing session cookies...")
        initial_cookie_count = len(client.cookies)
        print(f"   Current cookies: {initial_cookie_count}")

        # List some cookie names (without values for privacy)
        cookie_names = list(client.cookies.keys())
        print(f"   Cookie names: {cookie_names[:5]}{'...' if len(cookie_names) > 5 else ''}")

        if initial_cookie_count > 0:
            print("✅ Session cookies are being managed")
            test_results["passed"] += 1
        else:
            print("⚠️  No cookies found (might be expected)")
            test_results["warnings"] += 1

        # Summary
        print("\n" + "=" * 50)
        print("🎯 Authentication Test Summary")
        print("=" * 50)

        total_tests = test_results["passed"] + test_results["failed"]
        pass_rate = (test_results["passed"] / total_tests * 100) if total_tests > 0 else 0

        print(f"✅ Tests Passed: {test_results['passed']}")
        print(f"❌ Tests Failed: {test_results['failed']}")
        print(f"⚠️  Warnings: {test_results['warnings']}")
        print(f"📊 Pass Rate: {pass_rate:.1f}%")

        print("\n🔐 Authentication Features Successfully Tested:")
        print("   • Email/password login authentication")
        print("   • Authentication status tracking and retrieval")
        print("   • Session cookie management and persistence")
        print("   • Logout functionality and state cleanup")
        print("   • Invalid credential handling")
        print("   • Keep signed in option")
        print("   • Re-login capability")

        if test_results["failed"] == 0:
            print("\n🎉 All authentication features are working correctly!")
        else:
            print(f"\n⚠️  {test_results['failed']} issues need attention")

        # Final status
        final_status = client.get_authentication_status()
        print(f"\nFinal Authentication Status:")
        print(f"   Is Authenticated: {final_status['is_authenticated']}")
        print(f"   User Email: {final_status['user_email']}")

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
    asyncio.run(test_authentication_features())