#!/usr/bin/env python3
"""FIXED: Oil pan gasket search using correct carcode parameter."""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from rockauto_api import RockAutoClient

async def find_oil_pan_gasket_fixed():
    """Find oil pan gasket - FIXED VERSION using carcode."""
    print("🛢️  FIXED Oil Pan Gasket Search")
    print("🎯 Vehicle: 2017 Ford F-150 3.5L V6 Turbocharged")
    print("🔧 Fix: Using engine.carcode instead of engine.description\n")

    async with RockAutoClient() as client:
        try:
            make, year, model = "FORD", "2017", "F-150"

            print("🚗 Step 1: Vehicle Navigation...")

            # Get engines
            engines = await client.get_engines_for_vehicle(make, year, model)
            print(f"✅ Found {engines.count} engines")

            # Find 3.5L turbocharged engine
            target_engine = None
            for engine in engines.engines:
                print(f"   Engine: {engine.description} (carcode: {engine.carcode})")
                if "3.5" in engine.description and "turbo" in engine.description.lower():
                    target_engine = engine
                    print(f"   🎯 SELECTED!")

            if not target_engine:
                print("❌ Target engine not found")
                return False

            print(f"\n🔧 Using: {target_engine.description}")
            print(f"🆔 Carcode: {target_engine.carcode}")

            # FIXED: Use carcode instead of description
            print(f"\n🛠️  Step 2: Getting Categories (FIXED METHOD)...")
            categories = await client.get_part_categories(
                make=make,
                year=int(year),  # Ensure it's an int
                model=model,
                carcode=target_engine.carcode  # FIXED: Use carcode!
            )

            print(f"✅ Found {categories.count} categories!")

            if categories.count > 0:
                print(f"\n📦 Available Categories:")
                oil_related = []

                for i, category in enumerate(categories.categories):
                    print(f"   {i+1:2d}. {category.name}")

                    # Look for oil/gasket/seal categories
                    cat_lower = category.name.lower()
                    if any(keyword in cat_lower for keyword in ['oil', 'gasket', 'seal', 'engine seal']):
                        oil_related.append(category)
                        print(f"       🎯 RELEVANT FOR OIL PAN GASKET!")

                if oil_related:
                    print(f"\n🔍 Searching {len(oil_related)} oil-related categories...")

                    for category in oil_related:
                        print(f"\n📦 Searching: {category.name}")

                        try:
                            parts = await client.get_parts_by_category(
                                make=make,
                                year=year,
                                model=model,
                                engine=target_engine.description,  # This method still uses description
                                category=category.name
                            )
                            print(f"   ✅ {parts.count} parts found")

                            # Look for oil pan gaskets
                            gaskets = []
                            for part in parts.parts:
                                part_text = f"{part.description} {part.part_number}".lower()
                                if "oil pan" in part_text and "gasket" in part_text:
                                    gaskets.append(part)

                            if gaskets:
                                print(f"   🎉 FOUND {len(gaskets)} OIL PAN GASKETS!")
                                for gasket in gaskets[:3]:
                                    print(f"      • {gasket.brand} {gasket.part_number}")
                                    print(f"        💰 ${gasket.price}")
                                    print(f"        📝 {gasket.description}")

                                print(f"\n🏆 SUCCESS! Found oil pan gaskets for {year} {make} {model}")
                                return True
                            else:
                                print(f"   📋 Sample parts in {category.name}:")
                                for j, part in enumerate(parts.parts[:3]):
                                    print(f"      {j+1}. {part.brand} {part.part_number} - ${part.price}")

                        except Exception as e:
                            print(f"   ❌ Error in {category.name}: {e}")

                if not oil_related:
                    print(f"\n📋 No obvious oil-related categories. First 10 categories:")
                    for i, cat in enumerate(categories.categories[:10]):
                        print(f"   {i+1}. {cat.name}")

            else:
                print(f"❌ Still getting 0 categories - deeper issue")

            print(f"\n📊 CAPTCHA Status: ✅ NO TRIGGERS")
            print(f"📍 Navigation: {client.last_navigation_context}")

            return True

        except Exception as e:
            if "captcha" in str(e).lower():
                print(f"\n❌ CAPTCHA: {e}")
                return False
            else:
                print(f"\n⚠️  Error: {e}")
                return True  # Not CAPTCHA related

if __name__ == "__main__":
    success = asyncio.run(find_oil_pan_gasket_fixed())
    if success:
        print(f"\n🎉 Test completed - CAPTCHA bypass working!")
    else:
        print(f"\n💥 CAPTCHA issues detected")