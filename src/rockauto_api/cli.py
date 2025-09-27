"""Command-line interface for RockAuto API."""

import asyncio
import sys
from typing import Optional

from .client import RockAutoClient


async def search_parts(make: str, year: int, model: str, category: Optional[str] = None) -> None:
    """Search for parts using command-line arguments."""
    async with RockAutoClient() as client:
        try:
            print(f"🚗 Searching parts for {year} {make} {model}")

            vehicle = await client.get_vehicle(make, year, model)
            print(f"✅ Vehicle: {vehicle}")

            categories = await vehicle.get_part_categories()
            print(f"📁 Found {categories.count} part categories")

            if category:
                # Search specific category
                matching_categories = [c for c in categories.categories
                                     if category.lower() in c.name.lower()]
                if matching_categories:
                    cat = matching_categories[0]
                    print(f"🔍 Searching category: {cat.name}")

                    parts = await vehicle.get_parts_by_category(cat.group_name)
                    print(f"📦 Found {parts.count} parts")

                    for i, part in enumerate(parts.parts[:5], 1):
                        print(f"  {i}. {part.name}")
                        if part.price:
                            print(f"     Price: {part.price}")
                else:
                    print(f"❌ Category '{category}' not found")
            else:
                # List categories
                print("\n📋 Available categories:")
                for i, cat in enumerate(categories.categories, 1):
                    print(f"  {i:2d}. {cat.name}")

        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)


def main() -> None:
    """Main CLI entry point."""
    if len(sys.argv) < 4:
        print("Usage: rockauto-search <make> <year> <model> [category]")
        print("Example: rockauto-search Honda 2020 Civic brake")
        sys.exit(1)

    make = sys.argv[1]
    year = int(sys.argv[2])
    model = sys.argv[3]
    category = sys.argv[4] if len(sys.argv) > 4 else None

    asyncio.run(search_parts(make, year, model, category))


if __name__ == "__main__":
    main()