#!/usr/bin/env python3
"""Real-world test: Find ignition coil for 2017 Ford F-150 3.5L turbocharged."""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from rockauto_api import RockAutoClient

async def find_ignition_coil_f150():
    """Find ignition coil for 2017 Ford F-150 3.5L turbocharged."""
    print("🔍 Real-world CAPTCHA test: Finding ignition coil")
    print("🎯 Target: 2017 Ford F-150 3.5L Turbocharged")
    print("📦 Part: Ignition Coil\n")

    async with RockAutoClient() as client:
        try:
            make, year, model = "FORD", "2017", "F-150"

            print("🚗 Step 1: Building vehicle context...")

            # Get years (triggers navigation simulation)
            print(f"   Getting years for {make}...")
            years = await client.get_years_for_make(make)
            print(f"   ✅ Found {years.count} years for {make}")

            # Get models for 2017
            print(f"   Getting models for {make} {year}...")
            models = await client.get_models_for_make_year(make, year)
            print(f"   ✅ Found {models.count} models for {make} {year}")

            # Get engines for F-150
            print(f"   Getting engines for {make} {year} {model}...")
            engines = await client.get_engines_for_vehicle(make, year, model)
            print(f"   ✅ Found {engines.count} engines for {make} {year} {model}")

            # Find the 3.5L turbocharged engine
            target_engine = None
            print(f"\n🔍 Available engines:")
            for i, engine in enumerate(engines.engines):
                print(f"   {i+1}. {engine.description}")
                if "3.5" in engine.description and "turbo" in engine.description.lower():
                    target_engine = engine.description
                    print(f"      ⭐ TARGET FOUND!")

            if not target_engine:
                print(f"❌ Could not find 3.5L turbocharged engine")
                return False

            print(f"\n🔧 Using engine: {target_engine}")

            # Get part categories
            print(f"\n⚡ Step 2: Getting part categories...")
            categories = await client.get_part_categories(make, year, model, target_engine)
            print(f"   ✅ Found {categories.count} part categories")

            # Look for ignition-related categories
            ignition_categories = []
            print(f"\n📦 Looking for ignition-related categories:")
            for category in categories.categories:
                if "ignition" in category.name.lower() or "coil" in category.name.lower() or "spark" in category.name.lower():
                    ignition_categories.append(category)
                    print(f"   🎯 {category.name}")

            if not ignition_categories:
                print(f"   ⚠️  No direct ignition categories found")
                print(f"   📋 Available categories:")
                for i, cat in enumerate(categories.categories[:10]):  # Show first 10
                    print(f"      {i+1}. {cat.name}")

                # Try engine electrical or electrical system
                for category in categories.categories:
                    if any(word in category.name.lower() for word in ['electrical', 'engine electrical', 'ignition system']):
                        ignition_categories.append(category)
                        print(f"   🔍 Alternative: {category.name}")
                        break

            if ignition_categories:
                target_category = ignition_categories[0]
                print(f"\n🛠️  Step 3: Searching in category: {target_category.name}")

                # Get parts in ignition category
                parts = await client.get_parts_by_category(
                    make=make,
                    year=year,
                    model=model,
                    engine=target_engine,
                    category=target_category.name
                )
                print(f"   ✅ Found {parts.count} parts in {target_category.name}")

                # Look for ignition coils
                ignition_coils = []
                for part in parts.parts:
                    part_name = f"{part.brand} {part.part_number} {part.description}".lower()
                    if "coil" in part_name and "ignition" in part_name:
                        ignition_coils.append(part)

                if ignition_coils:
                    print(f"\n🎉 FOUND {len(ignition_coils)} IGNITION COILS!")
                    for i, coil in enumerate(ignition_coils[:5]):  # Show first 5
                        print(f"   {i+1}. {coil.brand} {coil.part_number}")
                        print(f"      💰 Price: ${coil.price}")
                        print(f"      📝 {coil.description}")
                        print()
                else:
                    print(f"   ⚠️  No ignition coils found in {target_category.name}")
                    print(f"   📋 Sample parts found:")
                    for i, part in enumerate(parts.parts[:5]):
                        print(f"      {i+1}. {part.brand} {part.part_number} - ${part.price}")

            print(f"\n📊 Final session stats:")
            print(f"   📍 Navigation: {client.last_navigation_context}")
            print(f"   🍪 Cookies: {len(client.cookies)}")
            print(f"   🚫 CAPTCHA triggers: 0")

            return True

        except Exception as e:
            error_msg = str(e).lower()
            if "captcha" in error_msg:
                print(f"\n❌ CAPTCHA TRIGGERED: {e}")
                return False
            else:
                print(f"\n⚠️  Error occurred: {e}")
                return False

if __name__ == "__main__":
    try:
        success = asyncio.run(find_ignition_coil_f150())
        if success:
            print(f"\n🏆 SUCCESS! Real-world parts search completed without CAPTCHA!")
        else:
            print(f"\n💥 Failed - needs investigation")
    except KeyboardInterrupt:
        print(f"\n⏹️  Search interrupted")
    except Exception as e:
        print(f"\n💥 Search failed: {e}")