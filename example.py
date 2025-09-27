#!/usr/bin/env python3
"""
Example usage of the RockAuto API Client

This demonstrates the complete workflow:
1. Get available makes
2. Get years for a specific make
3. Get models for a make/year combination
4. Get engines for a specific vehicle
5. Search parts using carcode

Perfect for integration with FastMCP servers.
"""

import asyncio
from rockauto_api import RockAutoClient

async def demo_rockauto_api():
    """Demonstrate the RockAuto API client capabilities"""

    client = RockAutoClient()

    try:
        print("🚗 RockAuto API Client Demo")
        print("=" * 40)

        # 1. Get all available makes
        print("\n1. Fetching available vehicle makes...")
        makes_result = await client.get_makes()
        print(f"   Found {makes_result.count} makes")
        print(f"   Sample makes: {', '.join(makes_result.makes[:10])}...")

        # 2. Get years for Honda
        if "HONDA" in makes_result.makes:
            print("\n2. Fetching years for Honda...")
            years_result = await client.get_years_for_make("Honda")
            print(f"   Found {years_result.count} years")
            print(f"   Years range: {years_result.years[0]} - {years_result.years[-1]}")
            print(f"   Recent years: {', '.join(map(str, years_result.years[:5]))}")

            # 3. Get models for Honda 2020
            if 2020 in years_result.years:
                print("\n3. Fetching models for Honda 2020...")
                models_result = await client.get_models_for_make_year("Honda", 2020)
                print(f"   Found {models_result.count} models")
                print(f"   Models: {', '.join(models_result.models[:5])}...")

                # 4. Get engines for Honda 2020 Civic
                if "CIVIC" in models_result.models:
                    print("\n4. Fetching engines for Honda 2020 Civic...")
                    engines_result = await client.get_engines_for_vehicle("Honda", 2020, "Civic")
                    print(f"   Found {engines_result.count} engine configurations")

                    for i, engine in enumerate(engines_result.engines[:3]):
                        print(f"   Engine {i+1}: {engine.description} (carcode: {engine.carcode})")

                    # 5. Search parts for the first engine
                    if engines_result.engines:
                        first_engine = engines_result.engines[0]
                        print(f"\n5. Searching parts for carcode {first_engine.carcode}...")
                        parts_result = await client.search_parts(first_engine.carcode)
                        print(f"   Found {parts_result.count} parts")

                        if parts_result.parts:
                            print("   Sample parts:")
                            for part in parts_result.parts[:3]:
                                price_info = f" - {part.price}" if part.price else ""
                                brand_info = f" ({part.brand})" if part.brand else ""
                                print(f"   • {part.name}{price_info}{brand_info}")

        print("\n✅ Demo completed successfully!")
        print("\nThe API client returns structured Pydantic models with:")
        print("• Type safety and validation")
        print("• Clear field descriptions")
        print("• Consistent data structure")
        print("• Perfect for FastMCP integration")

    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await client.close()
        print("\n🔒 HTTP session closed")

if __name__ == "__main__":
    asyncio.run(demo_rockauto_api())