#!/usr/bin/env python3
"""THE BIG TEST: Can we get part data without triggering CAPTCHA?"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from rockauto_api import RockAutoClient

async def test_parts_search_captcha_bypass():
    """The ultimate CAPTCHA test - searching for actual parts."""
    print("🔥 THE BIG TEST: Part search CAPTCHA bypass...")
    print("This is where CAPTCHA detection is most aggressive!\n")

    async with RockAutoClient() as client:
        print(f"📱 Mobile profile: {client.use_mobile_profile}")
        print(f"🌐 User-Agent: {client.session.headers.get('User-Agent', 'N/A')[:60]}...\n")

        try:
            # Step 1: Navigate vehicle hierarchy (builds navigation context)
            print("🚗 Step 1: Getting vehicle makes...")
            makes = await client.get_makes()
            print(f"✅ Retrieved {makes.count} makes")

            print("\n📅 Step 2: Getting years for ACURA...")
            years = await client.get_years_for_make("ACURA")
            print(f"✅ Retrieved {years.count} years for ACURA")

            print("\n🚙 Step 3: Getting models for ACURA 2005...")
            models = await client.get_models_for_make_year("ACURA", "2005")
            print(f"✅ Retrieved {models.count} models for ACURA 2005")

            print("\n🔧 Step 4: Getting engines for ACURA 2005 TL...")
            engines = await client.get_engines_for_vehicle("ACURA", "2005", "TL")
            print(f"✅ Retrieved {engines.count} engines for ACURA 2005 TL")

            # Step 5: THE BIG TEST - Get part categories (this often triggers CAPTCHA)
            print("\n🛠️  Step 5: THE BIG TEST - Getting part categories...")
            print("This is where CAPTCHA usually triggers! 🤞")
            categories = await client.get_part_categories("ACURA", "2005", "TL", "3.2L V6 GAS SOHC Naturally Aspirated")
            print(f"🎉 SUCCESS! Retrieved {categories.count} part categories")

            # Step 6: ULTIMATE TEST - Get actual parts data
            print("\n🔩 Step 6: ULTIMATE TEST - Getting actual parts...")
            if categories.categories:
                first_category = categories.categories[0]
                print(f"Searching for parts in category: {first_category.name}")

                parts = await client.get_parts_by_category(
                    make="ACURA",
                    year="2005",
                    model="TL",
                    engine="3.2L V6 GAS SOHC Naturally Aspirated",
                    category=first_category.name
                )
                print(f"🎯 ULTIMATE SUCCESS! Retrieved {parts.count} parts")

                if parts.parts:
                    print(f"   First part: {parts.parts[0].brand} - {parts.parts[0].part_number}")
                    print(f"   Price: ${parts.parts[0].price}")

            print(f"\n📍 Final navigation context: {client.last_navigation_context}")
            print(f"📅 Final year context: {client.current_year_context}")

        except Exception as e:
            error_msg = str(e).lower()
            if "captcha" in error_msg:
                print(f"❌ CAPTCHA TRIGGERED: {e}")
                return False
            elif "blocked" in error_msg or "forbidden" in error_msg:
                print(f"❌ BLOCKED: {e}")
                return False
            else:
                print(f"❌ ERROR: {e}")
                return False

    print("\n🎉🎉🎉 ALL TESTS PASSED! CAPTCHA BYPASS SUCCESSFUL! 🎉🎉🎉")
    return True

async def stress_test_multiple_requests():
    """Stress test: Multiple rapid requests to see if we maintain bypass."""
    print("\n🔥 STRESS TEST: Multiple rapid requests...")

    async with RockAutoClient() as client:
        vehicles = [
            ("HONDA", "2010", "CIVIC"),
            ("TOYOTA", "2015", "CAMRY"),
            ("FORD", "2008", "F-150"),
            ("CHEVROLET", "2012", "CRUZE"),
            ("NISSAN", "2018", "ALTIMA")
        ]

        for i, (make, year, model) in enumerate(vehicles, 1):
            try:
                print(f"\n{i}/5 Testing {make} {year} {model}...")

                # Get years (triggers navigation simulation)
                years = await client.get_years_for_make(make)
                print(f"  ✅ Years: {years.count}")

                # Get models
                models = await client.get_models_for_make_year(make, year)
                print(f"  ✅ Models: {models.count}")

                # Get engines
                engines = await client.get_engines_for_vehicle(make, year, model)
                print(f"  ✅ Engines: {engines.count}")

                if engines.engines:
                    # Get part categories (CAPTCHA trigger point)
                    categories = await client.get_part_categories(make, year, model, engines.engines[0].name)
                    print(f"  🎯 Categories: {categories.count}")

            except Exception as e:
                if "captcha" in str(e).lower():
                    print(f"  ❌ CAPTCHA triggered on request {i}")
                    return False
                else:
                    print(f"  ⚠️  Error on {make}: {e}")

    print("\n🚀 STRESS TEST PASSED! No CAPTCHA triggers detected!")
    return True

if __name__ == "__main__":
    try:
        # Run the ultimate test
        success = asyncio.run(test_parts_search_captcha_bypass())

        if success:
            # If basic test passes, run stress test
            stress_success = asyncio.run(stress_test_multiple_requests())

            if stress_success:
                print("\n🏆 COMPLETE SUCCESS! CAPTCHA bypass working perfectly!")
            else:
                print("\n⚠️  Basic test passed but stress test failed")
        else:
            print("\n💥 CAPTCHA bypass needs more work")

    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Test failed with exception: {e}")
        sys.exit(1)