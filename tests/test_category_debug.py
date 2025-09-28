#!/usr/bin/env python3
"""Debug why part categories are returning 0 results."""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from rockauto_api import RockAutoClient

async def debug_categories():
    """Debug the category extraction issue."""
    print("🔍 Debugging part category extraction...")

    async with RockAutoClient() as client:
        try:
            # Test with a simpler, known-good vehicle first
            make, year, model = "HONDA", "2010", "CIVIC"

            print(f"🧪 Testing with {make} {year} {model}...")

            # Get engines
            engines = await client.get_engines_for_vehicle(make, year, model)
            print(f"✅ Found {engines.count} engines")

            if engines.engines:
                engine = engines.engines[0]
                print(f"🔧 Testing engine: {engine.description}")

                # Try to get categories and see what happens
                try:
                    categories = await client.get_part_categories(make, year, model, engine.description)
                    print(f"📦 Categories result: {categories.count}")

                    if categories.count == 0:
                        print("⚠️  Getting 0 categories - let's debug the method...")

                        # Let's look at what the raw response contains
                        # Make the same request the method would make
                        response = await client.session.get(
                            f"{client.CATALOG_BASE}/{make.lower()},{year},{model.replace(' ', '+')},{engine.carcode}"
                        )
                        print(f"📄 Raw response status: {response.status_code}")
                        print(f"📄 Raw response length: {len(response.text)}")

                        # Look for signs of CAPTCHA or blocking
                        response_text = response.text.lower()
                        if "captcha" in response_text:
                            print("❌ CAPTCHA detected in response")
                        elif "blocked" in response_text or "forbidden" in response_text:
                            print("❌ Blocking detected in response")
                        elif "catalog" in response_text:
                            print("✅ Response appears to contain catalog data")
                            # Show a snippet
                            print(f"📄 Response snippet: {response.text[:200]}...")
                        else:
                            print("⚠️  Unexpected response content")

                except Exception as e:
                    print(f"❌ Category method failed: {e}")

            # Also test the Ford F-150 case
            print(f"\n🔍 Now testing original Ford F-150 case...")
            ford_engines = await client.get_engines_for_vehicle("FORD", "2017", "F-150")
            if ford_engines.engines:
                turbo_engine = None
                for engine in ford_engines.engines:
                    if "3.5" in engine.description and "turbo" in engine.description.lower():
                        turbo_engine = engine
                        break

                if turbo_engine:
                    print(f"🔧 Testing Ford engine: {turbo_engine.description}")
                    print(f"🔧 Engine carcode: {turbo_engine.carcode}")

                    # Check the URL that would be called
                    url = f"{client.CATALOG_BASE}/ford,2017,f-150,{turbo_engine.carcode}"
                    print(f"🌐 Would call URL: {url}")

                    try:
                        response = await client.session.get(url)
                        print(f"📄 Ford response status: {response.status_code}")
                        print(f"📄 Ford response length: {len(response.text)}")

                        if "captcha" in response.text.lower():
                            print("❌ CAPTCHA detected in Ford response")
                        else:
                            print("✅ Ford response looks good")

                    except Exception as e:
                        print(f"❌ Ford request failed: {e}")

        except Exception as e:
            print(f"💥 Debug failed: {e}")

if __name__ == "__main__":
    asyncio.run(debug_categories())