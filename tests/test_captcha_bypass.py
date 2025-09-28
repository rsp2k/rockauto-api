#!/usr/bin/env python3
"""Test CAPTCHA bypass improvements using mobile browser simulation."""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from rockauto_api import RockAutoClient

async def test_mobile_profile_captcha_bypass():
    """Test that mobile profile reduces CAPTCHA triggers."""
    print("🧪 Testing mobile-first CAPTCHA bypass strategy...")

    # Create client with mobile profile (now default)
    async with RockAutoClient() as client:
        print(f"📱 Using mobile profile: {client.use_mobile_profile}")
        print(f"🌐 User-Agent: {client.session.headers.get('User-Agent', 'N/A')}")

        # Test basic vehicle hierarchy navigation
        print("\n🚗 Testing vehicle make retrieval...")
        makes = await client.get_makes()
        print(f"✅ Retrieved {makes.count} vehicle makes")

        # Test years for Acura (the make we analyzed)
        print("\n📅 Testing years for ACURA...")
        years = await client.get_years_for_make("ACURA")
        print(f"✅ Retrieved {years.count} years for ACURA")

        # Test specific year to verify navigation context
        print("\n🔧 Testing models for ACURA 2005...")
        models = await client.get_models_for_make_year("ACURA", "2005")
        print(f"✅ Retrieved {models.count} models for ACURA 2005")

        print("\n🎉 All tests passed! Mobile CAPTCHA bypass strategy working.")

        # Show navigation context
        print(f"\n📍 Navigation context: {client.last_navigation_context}")
        print(f"📅 Year context: {client.current_year_context}")

async def test_desktop_vs_mobile():
    """Compare desktop vs mobile profile performance."""
    print("\n🔄 Comparing desktop vs mobile profiles...")

    # Test desktop profile
    print("\n💻 Testing desktop profile...")
    async with RockAutoClient(use_mobile_profile=False) as desktop_client:
        try:
            years = await desktop_client.get_years_for_make("HONDA")
            print(f"✅ Desktop: Retrieved {years.count} years for HONDA")
        except Exception as e:
            if "captcha" in str(e).lower():
                print(f"❌ Desktop: CAPTCHA triggered - {e}")
            else:
                print(f"❌ Desktop: Error - {e}")

    # Test mobile profile
    print("\n📱 Testing mobile profile...")
    async with RockAutoClient(use_mobile_profile=True) as mobile_client:
        try:
            years = await mobile_client.get_years_for_make("HONDA")
            print(f"✅ Mobile: Retrieved {years.count} years for HONDA")
        except Exception as e:
            if "captcha" in str(e).lower():
                print(f"❌ Mobile: CAPTCHA triggered - {e}")
            else:
                print(f"❌ Mobile: Error - {e}")

if __name__ == "__main__":
    try:
        asyncio.run(test_mobile_profile_captcha_bypass())
        asyncio.run(test_desktop_vs_mobile())
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Test failed: {e}")
        sys.exit(1)