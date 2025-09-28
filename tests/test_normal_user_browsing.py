#!/usr/bin/env python3
"""Normal user browsing experience - find parts for my truck."""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from rockauto_api import RockAutoClient

async def browse_truck_parts():
    """Browse parts like a normal user would."""
    print("🚛 Let's find parts for my truck!")
    print("📋 Vehicle: 2017 Ford F-150 3.5L V6 Turbocharged\n")

    async with RockAutoClient() as client:
        try:
            # Step 1: Get to my specific truck
            print("🔍 Finding my truck...")
            engines = await client.get_engines_for_vehicle("FORD", 2017, "F-150")

            # Find my 3.5L turbo engine
            my_engine = None
            for engine in engines.engines:
                if "3.5" in engine.description and "turbo" in engine.description.lower():
                    my_engine = engine
                    break

            if not my_engine:
                print("❌ Couldn't find your engine")
                return

            print(f"✅ Found my truck: {my_engine.description}")
            print(f"🆔 Engine code: {my_engine.carcode}")

            # Step 2: Get all parts categories
            print(f"\n📦 Getting parts categories...")
            categories = await client.get_part_categories("FORD", 2017, "F-150", my_engine.carcode)
            print(f"✅ Found {categories.count} parts categories for my truck!\n")

            # Step 3: Show categories like a parts catalog
            print("🛠️  Available Parts Categories:")
            print("=" * 50)

            for i, category in enumerate(categories.categories, 1):
                print(f"{i:2d}. {category.name}")
                if hasattr(category, 'group_name') and category.group_name:
                    print(f"    └─ Group: {category.group_name}")
                print()

            # Step 4: Let's browse some popular categories
            popular_categories = ["Engine", "Brake & Wheel Hub", "Cooling System", "Drivetrain"]

            for category_name in popular_categories:
                matching_category = None
                for cat in categories.categories:
                    if cat.name == category_name:
                        matching_category = cat
                        break

                if matching_category:
                    print(f"\n🔧 Browsing {category_name} parts...")
                    print("=" * 40)

                    try:
                        parts = await client.get_parts_by_category(
                            make="FORD",
                            year=2017,
                            model="F-150",
                            carcode=my_engine.carcode,
                            category_group_name=matching_category.group_name if hasattr(matching_category, 'group_name') else category_name
                        )

                        print(f"✅ Found {parts.count} parts in {category_name}")

                        # Show first few parts
                        for i, part in enumerate(parts.parts[:5], 1):
                            print(f"\n{i}. {part.brand} - {part.part_number}")
                            print(f"   💰 ${part.price}")
                            print(f"   📝 {part.description}")
                            if hasattr(part, 'href') and part.href:
                                print(f"   🔗 {part.href}")

                        if parts.count > 5:
                            print(f"\n   ... and {parts.count - 5} more parts")

                    except Exception as e:
                        print(f"⚠️  Couldn't load {category_name} parts: {e}")

            print(f"\n🎉 Successfully browsed parts for your 2017 Ford F-150!")
            print(f"💡 You can now shop for any of the {categories.count} different types of parts")

        except Exception as e:
            print(f"❌ Error browsing parts: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(browse_truck_parts())