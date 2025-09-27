"""Main RockAuto API client implementation."""

import re
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from bs4 import BeautifulSoup

from ..models import (
    AccountActivityResult,
    BillingInfo,
    CacheConfiguration,
    Engine,
    ExternalOrderRequest,
    ManufacturerOptions,
    OrderHistoryFilter,
    OrderHistoryItem,
    OrderHistoryResult,
    OrderItem,
    OrderListRequest,
    OrderLookupRequest,
    OrderStatus,
    OrderStatusError,
    OrderStatusResult,
    PartCache,
    PartCategory,
    PartGroupOptions,
    PartInfo,
    PartSearchOption,
    PartSearchResult,
    PartTypeOptions,
    SavedAddress,
    SavedAddressesResult,
    SavedVehicle,
    SavedVehiclesResult,
    ShippingInfo,
    ToolCategories,
    ToolCategory,
    ToolInfo,
    ToolsResult,
    VehicleEngines,
    VehicleMakes,
    VehicleModels,
    VehiclePartCategories,
    VehiclePartsResult,
    VehicleYears,
    WhatIsPartCalledResult,
    WhatIsPartCalledResults,
)
from ..utils import PartExtractor
from .base import BaseClient

if TYPE_CHECKING:
    from .vehicle import Vehicle


class RockAutoClient(BaseClient):
    """
    Python client for RockAuto.com API interactions.

    Provides methods for searching vehicle parts with comprehensive filtering
    and Vehicle-scoped operations for intuitive part discovery.
    """

    def __init__(
        self,
        # === CACHE SETTINGS ===
        enable_caching: bool = True,
        part_cache_hours: int = 12,
        search_cache_hours: int = 12,
        dropdown_cache_hours: int = 24,
        max_cached_parts: int = 1000,
        max_cached_searches: int = 100
    ):
        """
        Initialize client with configurable caching settings.

        Args:
            enable_caching: Enable/disable all caching (default: True)
            part_cache_hours: Hours to cache individual part data (default: 12)
            search_cache_hours: Hours to cache search results (default: 12)
            dropdown_cache_hours: Hours to cache dropdown options (default: 24)
            max_cached_parts: Maximum number of parts to cache (default: 1000)
            max_cached_searches: Maximum number of search results to cache (default: 100)
        """
        super().__init__()

        # === CACHE CONFIGURATION ===
        self.cache_config = CacheConfiguration(
            enabled=enable_caching,
            part_ttl_hours=part_cache_hours,
            result_ttl_hours=search_cache_hours,
            max_parts=max_cached_parts,
            max_results=max_cached_searches
        )

        # Initialize caches
        self._part_cache: Optional[PartCache] = self.cache_config.create_cache() if enable_caching else None

        # Dropdown caches (separate from main part cache for different TTL)
        self._dropdown_cache_hours = dropdown_cache_hours
        self._manufacturer_cache: Optional[ManufacturerOptions] = None
        self._part_group_cache: Optional[PartGroupOptions] = None
        self._part_type_cache: Optional[PartTypeOptions] = None

    # === BASIC CATALOG METHODS ===

    async def get_makes(self) -> VehicleMakes:
        """Get all available vehicle makes."""
        try:
            response = await self.session.get(f"{self.CATALOG_BASE}/")
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            makes = set()
            for link in soup.find_all("a", href=True):
                href = link.get("href", "")
                if "/catalog/" in href and href.count("/") >= 3:
                    parts = href.strip("/").split("/")
                    if len(parts) >= 2 and parts[1] != "catalog":
                        continue
                    if len(parts) >= 3:
                        make = parts[2].split(",")[0]
                        if make and len(make) > 1:
                            makes.add(make.upper())

            sorted_makes = sorted(list(makes))
            return VehicleMakes(makes=sorted_makes, count=len(sorted_makes))

        except Exception as e:
            raise Exception(f"Failed to fetch makes: {str(e)}")

    async def get_years_for_make(self, make: str) -> VehicleYears:
        """Get available years for a specific make."""
        try:
            response = await self.session.get(f"{self.CATALOG_BASE}/{make.lower()}")
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            years = set()
            for link in soup.find_all("a", href=True):
                href = link.get("href", "")
                if f"/{make.lower()}," in href:
                    parts = href.split(",")
                    if len(parts) >= 2:
                        try:
                            year = int(parts[1])
                            if 1950 <= year <= 2030:
                                years.add(year)
                        except ValueError:
                            continue

            sorted_years = sorted(list(years), reverse=True)
            return VehicleYears(make=make.upper(), years=sorted_years, count=len(sorted_years))

        except Exception as e:
            raise Exception(f"Failed to fetch years for {make}: {str(e)}")

    async def get_models_for_make_year(self, make: str, year: int) -> VehicleModels:
        """Get available models for a specific make and year."""
        try:
            response = await self.session.get(f"{self.CATALOG_BASE}/{make.lower()},{year}")
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            models = set()
            for link in soup.find_all("a", href=True):
                href = link.get("href", "")
                if f"/{make.lower()},{year}," in href:
                    parts = href.split(",")
                    if len(parts) >= 3:
                        model = parts[2]
                        if model and len(model) > 1:
                            models.add(model.upper())

            sorted_models = sorted(list(models))
            return VehicleModels(
                make=make.upper(), year=year, models=sorted_models, count=len(sorted_models)
            )

        except Exception as e:
            raise Exception(f"Failed to fetch models for {make} {year}: {str(e)}")

    async def get_engines_for_vehicle(self, make: str, year: int, model: str) -> VehicleEngines:
        """Get available engines for a specific make, year, and model."""
        try:
            url = f"{self.CATALOG_BASE}/{make.lower()},{year},{model.lower()}"
            response = await self.session.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            engines = []
            for link in soup.find_all("a", href=True):
                href = link.get("href", "")
                if f"/{make.lower()},{year},{model.lower()}," in href:
                    parts = href.split(",")
                    if len(parts) >= 5:
                        engine_desc = parts[3]
                        carcode = parts[4]

                        if engine_desc and carcode and carcode.isdigit():
                            engine = Engine(
                                description=engine_desc.replace("+", " "),
                                carcode=carcode,
                                href=href,
                            )

                            # Avoid duplicates
                            if not any(e.carcode == engine.carcode for e in engines):
                                engines.append(engine)

            return VehicleEngines(
                make=make.upper(),
                year=year,
                model=model.upper(),
                engines=engines,
                count=len(engines),
            )

        except Exception as e:
            raise Exception(f"Failed to fetch engines for {make} {year} {model}: {str(e)}")

    async def get_part_categories(
        self, make: str, year: int, model: str, carcode: str
    ) -> VehiclePartCategories:
        """Get part categories for a specific vehicle."""
        try:
            payload = {
                "jsn": {
                    "carcode": carcode,
                    "tab": "catalog",
                    "idepth": 3,
                    "nodetype": "carcode",
                    "jsdata": {
                        "markets": [{"c": "US"}, {"c": "CA"}],
                        "mktlist": "US,CA",
                        "Show": 1,
                    },
                }
            }

            result = await self._make_api_request("navnode_fetch", payload)
            categories = []

            if "html_fill_sections" in result and "navchildren[]" in result["html_fill_sections"]:
                html_content = result["html_fill_sections"]["navchildren[]"]
                soup = BeautifulSoup(html_content, "html.parser")

                for link in soup.find_all("a", href=True):
                    text = link.get_text(strip=True)
                    href = link.get("href", "")

                    if text and len(text) > 2:
                        # Extract group name from href for API calls
                        group_name = text.lower().replace(" ", "+").replace("&", "%26")

                        category = PartCategory(name=text, group_name=group_name, href=href)
                        categories.append(category)

            return VehiclePartCategories(
                make=make.upper(),
                year=year,
                model=model.upper(),
                carcode=carcode,
                categories=categories,
                count=len(categories),
            )

        except Exception as e:
            raise Exception(f"Failed to fetch part categories: {str(e)}")

    async def get_parts_by_category(
        self, make: str, year: int, model: str, carcode: str, category_group_name: str
    ) -> VehiclePartsResult:
        """Get parts for a specific vehicle and category with caching."""
        # Check cache first if enabled
        if self._part_cache and self.cache_config.enabled:
            cache_key = PartCache.generate_vehicle_cache_key(
                make, model, str(year), carcode, category_group_name
            )
            cached_result = self._part_cache.get_vehicle_result(cache_key)
            if cached_result:
                return cached_result

        try:
            payload = {
                "jsn": {
                    "carcode": carcode,
                    "groupname": category_group_name.replace("+", " "),
                    "tab": "catalog",
                    "idepth": 5,
                    "nodetype": "groupname",
                    "jsdata": {
                        "markets": [{"c": "US"}, {"c": "CA"}],
                        "mktlist": "US,CA",
                        "Show": 1,
                    },
                }
            }
            result = await self._make_api_request("navnode_fetch", payload)
            parts = []

            if "html_fill_sections" in result and "navchildren[]" in result["html_fill_sections"]:
                html_content = result["html_fill_sections"]["navchildren[]"]
                soup = BeautifulSoup(html_content, "html.parser")

                # Look for structured part data
                for item in soup.find_all(
                    ["div", "tr", "a"], class_=re.compile(r"part|product|item", re.I)
                ):
                    part_info = PartExtractor.extract_from_element(item)
                    if part_info:
                        parts.append(part_info)

                        # Cache individual parts if caching enabled
                        if self._part_cache and self.cache_config.enabled:
                            self._part_cache.cache_part(part_info)

                # Fallback parsing - look for links with meaningful text
                if not parts:
                    links = soup.find_all("a", href=True)
                    for link in links:
                        part_info = PartExtractor.extract_from_element(link)
                        if part_info and part_info.name not in [p.name for p in parts]:
                            parts.append(part_info)

                            # Cache individual parts if caching enabled
                            if self._part_cache and self.cache_config.enabled:
                                self._part_cache.cache_part(part_info)

            vehicle_result = VehiclePartsResult(
                make=make.upper(),
                year=year,
                model=model.upper(),
                carcode=carcode,
                category=category_group_name.replace("+", " "),
                parts=parts,
                count=len(parts),
            )

            # Cache the complete search result if caching enabled
            if self._part_cache and self.cache_config.enabled:
                cache_key = PartCache.generate_vehicle_cache_key(
                    make, model, str(year), carcode, category_group_name
                )
                self._part_cache.cache_vehicle_result(vehicle_result, cache_key)

            return vehicle_result

        except Exception as e:
            raise Exception(f"Failed to fetch parts for category: {str(e)}")

    async def get_individual_parts_from_subcategory(
        self, make: str, year: int, model: str, carcode: str, subcategory_url: str
    ) -> VehiclePartsResult:
        """Get individual parts from a subcategory URL using web scraping."""
        try:
            # Ensure we have a full URL
            if not subcategory_url.startswith("http"):
                if subcategory_url.startswith("/"):
                    full_url = f"https://www.rockauto.com{subcategory_url}"
                else:
                    full_url = f"https://www.rockauto.com/{subcategory_url}"
            else:
                full_url = subcategory_url

            # Parse the URL to extract category name
            url_parts = subcategory_url.strip("/").split(",")
            category_name = "Unknown"
            if len(url_parts) >= 7:
                category_name = url_parts[6].replace("+", " ")

            # Fetch the web page
            response = await self.session.get(full_url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            parts = []

            # Look for tables containing parts data
            tables = soup.find_all("table")

            for table in tables:
                rows = table.find_all("tr")

                for row in rows:
                    row_text = row.get_text(strip=True)

                    # Look for rows with price information (likely parts)
                    if "$" in row_text and len(row_text) > 20:
                        cells = row.find_all(["td", "th"])

                        if len(cells) >= 3:  # Likely a part row with multiple columns
                            part_info = await self._extract_part_from_table_row(row, cells)
                            if part_info:
                                parts.append(part_info)

            return VehiclePartsResult(
                make=make.upper(),
                year=year,
                model=model.upper(),
                carcode=carcode,
                category=category_name,
                parts=parts,
                count=len(parts),
            )

        except Exception as e:
            raise Exception(f"Failed to fetch individual parts from subcategory: {str(e)}")

    async def _extract_part_from_table_row(self, row, cells) -> Optional["PartInfo"]:
        """Extract part information from a table row with detailed parsing."""
        part_info = PartExtractor.extract_from_table_row(row, cells)

        # Extract video URL if info URL is available
        if part_info and part_info.info_url:
            video_url = await self._extract_video_url(part_info.info_url)
            if video_url:
                # Create new PartInfo with video URL
                part_info = PartInfo(
                    name=part_info.name,
                    part_number=part_info.part_number,
                    price=part_info.price,
                    brand=part_info.brand,
                    url=part_info.url,
                    image_url=part_info.image_url,
                    info_url=part_info.info_url,
                    video_url=video_url,
                )

        return part_info

    async def _extract_video_url(self, info_url: str) -> Optional[str]:
        """Extract video URL from moreinfo.php page."""
        try:
            response = await self.session.get(info_url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            page_text = soup.get_text()

            return PartExtractor.extract_video_url(page_text, soup)

        except Exception:
            return None

    # === VEHICLE-SCOPED OPERATIONS ===

    async def get_vehicle(self, make: str, year: int, model: str, engine_index: int = 0) -> "Vehicle":
        """Create a Vehicle object for scoped parts operations."""
        try:
            engines_result = await self.get_engines_for_vehicle(make, year, model)
            if not engines_result.engines:
                raise Exception(f"No engines found for {make} {year} {model}")

            if engine_index >= len(engines_result.engines):
                raise Exception(
                    f"Engine index {engine_index} out of range. Available engines: {len(engines_result.engines)}"
                )

            selected_engine = engines_result.engines[engine_index]

            # Import here to avoid circular imports
            from .vehicle import Vehicle

            vehicle = Vehicle(make=make, year=year, model=model, engine=selected_engine)
            vehicle._set_client(self)
            return vehicle

        except Exception as e:
            raise Exception(f"Failed to create vehicle: {str(e)}")

    # === TOOLS OPERATIONS ===

    async def get_tool_categories(self, category_path: str = "") -> ToolCategories:
        """Get tool categories from the tools section."""
        try:
            # Build URL based on category path
            if category_path:
                url = f"https://www.rockauto.com/en/tools/{category_path}"
            else:
                url = "https://www.rockauto.com/en/tools/"

            response = await self.session.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            categories = []

            # Determine current hierarchy level based on path
            level = len(category_path.split(",")) if category_path else 1

            # Find all tool category links - look for specific patterns from the main page
            for link in soup.find_all("a", href=True):
                href = link.get("href", "")
                text = link.get_text(strip=True)

                # Look for tool category links matching the pattern we saw
                if "/en/tools/" in href and text and len(text) > 2:
                    # Skip navigation and UI elements
                    if any(skip_word in text.lower() for skip_word in ["toggle", "help", "cart", "search", "rockauto", "bigger"]):
                        continue

                    # Extract category path from href
                    path_part = href.replace("/en/tools/", "").strip("/")

                    if category_path == "":
                        # For main page, look for single-level categories
                        if path_part and "," not in path_part:
                            # Create URL-safe group name
                            group_name = path_part.replace(" ", "+").replace("&", "%26")

                            category = ToolCategory(
                                name=text,
                                group_name=group_name,
                                href=href,
                                level=1
                            )

                            # Avoid duplicates
                            if not any(c.name == category.name for c in categories):
                                categories.append(category)
                    else:
                        # For sub-categories, look for appropriate level
                        if path_part:
                            path_segments = path_part.split(",")
                            expected_segments = len(category_path.split(",")) + 1

                            if len(path_segments) == expected_segments:
                                # Create URL-safe group name
                                group_name = path_part.replace(" ", "+").replace("&", "%26")

                                category = ToolCategory(
                                    name=text,
                                    group_name=group_name,
                                    href=href,
                                    level=len(path_segments)
                                )

                                # Avoid duplicates
                                if not any(c.name == category.name for c in categories):
                                    categories.append(category)

            return ToolCategories(
                categories=categories,
                count=len(categories),
                level=level,
                parent_path=category_path
            )

        except Exception as e:
            raise Exception(f"Failed to fetch tool categories: {str(e)}")

    async def get_tools_by_category(self, category_path: str) -> ToolsResult:
        """Get individual tools for a specific category path."""
        try:
            url = f"https://www.rockauto.com/en/tools/{category_path}"
            response = await self.session.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            tools = []

            # Look for tool listings in tables
            tables = soup.find_all("table")

            for table in tables:
                rows = table.find_all("tr")

                for row in rows:
                    row_text = row.get_text(strip=True)

                    # Look for rows with price information (likely tools)
                    if "$" in row_text and len(row_text) > 20:
                        cells = row.find_all(["td", "th"])

                        if len(cells) >= 3:  # Likely a tool row with multiple columns
                            tool_info = await self._extract_tool_from_table_row(row, cells)
                            if tool_info:
                                tools.append(tool_info)

            # Extract category name from path
            category_name = category_path.split(",")[-1].replace("+", " ") if category_path else "Unknown"

            return ToolsResult(
                tools=tools,
                count=len(tools),
                category=category_name,
                category_path=category_path
            )

        except Exception as e:
            raise Exception(f"Failed to fetch tools for category: {str(e)}")

    async def _extract_tool_from_table_row(self, row, cells) -> Optional[ToolInfo]:
        """Extract tool information from a table row."""
        try:
            # Extract text from each cell
            cell_texts = [cell.get_text(strip=True) for cell in cells]

            # Initialize tool info
            tool_info = {
                "name": None,
                "part_number": "Unknown",
                "price": None,
                "brand": None,
                "description": None,
                "url": None,
                "image_url": None,
                "info_url": None,
                "video_url": None,
                "specifications": None,
            }

            # Extract price using existing patterns
            for cell_text in cell_texts:
                price_match = re.search(r"\$([0-9,]+\.?[0-9]*)", cell_text)
                if price_match:
                    tool_info["price"] = f"${price_match.group(1)}"
                    break

            # Extract part number
            for cell_text in cell_texts:
                part_match = re.search(r"\b[A-Z0-9\-]{6,}\b", cell_text)
                if part_match and "$" not in cell_text:
                    tool_info["part_number"] = part_match.group()
                    break

            # Extract brand (using common tool brands)
            tool_brands = ["CRAFTSMAN", "MATCO", "SNAP-ON", "MAC", "CORNWELL", "PROTO", "SK", "WILLIAMS", "WRIGHT", "GEARWRENCH", "STANLEY", "DEWALT", "MILWAUKEE", "KOBALT", "HUSKY"]
            for cell_text in cell_texts:
                for brand in tool_brands:
                    if brand in cell_text.upper():
                        tool_info["brand"] = brand
                        break
                if tool_info["brand"]:
                    break

            # Extract tool name
            name_candidates = [text for text in cell_texts if text and "$" not in text and len(text) > 5]
            if name_candidates:
                longest_candidate = max(name_candidates, key=len)
                clean_name = self._clean_tool_name(longest_candidate, tool_info["brand"], tool_info["part_number"])
                tool_info["name"] = clean_name if clean_name else longest_candidate

            # Extract URLs from row
            self._extract_urls_from_tool_row(row, tool_info)

            # Only return if we found meaningful tool information
            if tool_info["price"] or tool_info["part_number"] != "Unknown":
                return ToolInfo(
                    name=tool_info["name"] or "Unknown Tool",
                    part_number=tool_info["part_number"],
                    price=tool_info["price"],
                    brand=tool_info["brand"],
                    description=tool_info["description"],
                    url=tool_info["url"],
                    image_url=tool_info["image_url"],
                    info_url=tool_info["info_url"],
                    video_url=tool_info["video_url"],
                    specifications=tool_info["specifications"],
                )

            return None

        except Exception:
            return None

    def _clean_tool_name(self, name: str, brand: Optional[str], part_number: str) -> str:
        """Clean up tool name from table extraction."""
        clean_name = name
        if brand:
            clean_name = clean_name.replace(brand, "").strip()
        if part_number != "Unknown":
            clean_name = clean_name.replace(part_number, "").strip()

        # Remove common noise
        noise_patterns = ["Info", "Toggle", "Intentionally blank"]
        for noise in noise_patterns:
            clean_name = clean_name.replace(noise, "").strip()

        return clean_name

    def _extract_urls_from_tool_row(self, row, tool_info: dict) -> None:
        """Extract URLs from tool table row."""
        # Look for main tool link
        main_links = row.find_all("a", href=True)
        for link in main_links:
            href = link.get("href", "")
            if "/en/tools/" in href and "moreinfo" not in href:
                tool_info["url"] = self._format_tool_url(href)
                break

        # Look for images
        img = row.find("img")
        if img:
            img_src = img.get("src", "")
            if img_src and "flag_" not in img_src and "loading.gif" not in img_src:
                tool_info["image_url"] = self._format_tool_url(img_src)

        # Look for info links
        info_links = row.find_all("a", href=re.compile(r"moreinfo\.php|details|info", re.I))
        if info_links:
            info_href = info_links[0].get("href", "")
            if info_href:
                tool_info["info_url"] = self._format_tool_url(info_href)

    def _format_tool_url(self, href: str) -> Optional[str]:
        """Format URL to be absolute."""
        if not href:
            return None
        if href.startswith("http"):
            return href
        elif href.startswith("/"):
            return f"https://www.rockauto.com{href}"
        else:
            return f"https://www.rockauto.com/{href}"

    # === PARTS SEARCH METHODS ===

    async def get_manufacturers(self, use_cache: bool = True) -> ManufacturerOptions:
        """
        Get all available manufacturers for parts search.

        Args:
            use_cache: Whether to use cached data if available

        Returns:
            ManufacturerOptions containing all manufacturer options
        """
        if use_cache and self._manufacturer_cache:
            return self._manufacturer_cache

        try:
            response = await self.session.get("https://www.rockauto.com/en/partsearch/")
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Find manufacturer dropdown
            manufacturer_select = soup.find("select", {"id": "manufacturer_partsearch_007"})
            if not manufacturer_select:
                raise ValueError("Could not find manufacturer dropdown on parts search page")

            manufacturers = []
            for option in manufacturer_select.find_all("option"):
                value = option.get("value", "")
                text = option.get_text(strip=True)
                if text:  # Skip empty options
                    manufacturers.append(PartSearchOption(value=value, text=text))

            self._manufacturer_cache = ManufacturerOptions(
                manufacturers=manufacturers,
                count=len(manufacturers),
                last_updated=datetime.now().isoformat()
            )

            return self._manufacturer_cache

        except Exception as e:
            raise Exception(f"Failed to fetch manufacturers: {str(e)}")

    async def get_part_groups(self, use_cache: bool = True) -> PartGroupOptions:
        """
        Get all available part groups for parts search.

        Args:
            use_cache: Whether to use cached data if available

        Returns:
            PartGroupOptions containing all part group options
        """
        if use_cache and self._part_group_cache:
            return self._part_group_cache

        try:
            response = await self.session.get("https://www.rockauto.com/en/partsearch/")
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Find part group dropdown
            part_group_select = soup.find("select", {"id": "partgroup_partsearch_007"})
            if not part_group_select:
                raise ValueError("Could not find part group dropdown on parts search page")

            part_groups = []
            for option in part_group_select.find_all("option"):
                value = option.get("value", "")
                text = option.get_text(strip=True)
                if text:  # Skip empty options
                    part_groups.append(PartSearchOption(value=value, text=text))

            self._part_group_cache = PartGroupOptions(
                part_groups=part_groups,
                count=len(part_groups),
                last_updated=datetime.now().isoformat()
            )

            return self._part_group_cache

        except Exception as e:
            raise Exception(f"Failed to fetch part groups: {str(e)}")

    async def get_part_types(self, use_cache: bool = True) -> PartTypeOptions:
        """
        Get all available part types for parts search.

        Args:
            use_cache: Whether to use cached data if available

        Returns:
            PartTypeOptions containing all part type options
        """
        if use_cache and self._part_type_cache:
            return self._part_type_cache

        try:
            response = await self.session.get("https://www.rockauto.com/en/partsearch/")
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Find part type dropdown
            part_type_select = soup.find("select", {"id": "parttype_partsearch_007"})
            if not part_type_select:
                raise ValueError("Could not find part type dropdown on parts search page")

            part_types = []
            for option in part_type_select.find_all("option"):
                value = option.get("value", "")
                text = option.get_text(strip=True)
                if text:  # Skip empty options
                    part_types.append(PartSearchOption(value=value, text=text))

            self._part_type_cache = PartTypeOptions(
                part_types=part_types,
                count=len(part_types),
                last_updated=datetime.now().isoformat()
            )

            return self._part_type_cache

        except Exception as e:
            raise Exception(f"Failed to fetch part types: {str(e)}")

    def clear_parts_search_cache(self) -> None:
        """Clear all cached parts search dropdown data."""
        self._manufacturer_cache = None
        self._part_group_cache = None
        self._part_type_cache = None

    async def search_parts_by_number(
        self,
        part_number: str,
        manufacturer: Optional[str] = None,
        part_group: Optional[str] = None,
        part_type: Optional[str] = None,
        part_name: Optional[str] = None
    ) -> PartSearchResult:
        """
        Search for parts by part number with optional filters.

        Args:
            part_number: Part number to search for (supports wildcards with *)
            manufacturer: Optional manufacturer filter (name or "All")
            part_group: Optional part group filter (name or "All")
            part_type: Optional part type filter (name or "All")
            part_name: Optional additional part name search text

        Returns:
            PartSearchResult containing found parts and search metadata
        """
        try:
            # Get initial page to extract security token
            response = await self.session.get("https://www.rockauto.com/en/partsearch/")
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Extract security token
            nck_input = soup.find("input", {"name": "_nck"})
            if not nck_input:
                raise ValueError("Could not find security token on parts search page")

            security_token = nck_input.get("value", "")

            # Resolve filter values to their form values
            manufacturer_value = ""
            part_group_value = ""
            part_type_value = ""

            if manufacturer and manufacturer.lower() != "all":
                manufacturers = await self.get_manufacturers()
                mfr_option = manufacturers.get_manufacturer_by_name(manufacturer)
                if mfr_option:
                    manufacturer_value = mfr_option.value

            if part_group and part_group.lower() != "all":
                part_groups = await self.get_part_groups()
                group_option = part_groups.get_part_group_by_name(part_group)
                if group_option:
                    part_group_value = group_option.value

            if part_type and part_type.lower() != "all":
                part_types = await self.get_part_types()
                type_option = part_types.get_part_type_by_name(part_type)
                if type_option:
                    part_type_value = type_option.value

            # Prepare form data
            form_data = {
                "_nck": security_token,
                "dopartsearch": "1",
                "partsearch[partnum][partsearch_007]": part_number,
                "partsearch[manufacturer][partsearch_007]": manufacturer_value,
                "partsearch[partgroup][partsearch_007]": part_group_value,
                "partsearch[parttype][partsearch_007]": part_type_value,
                "partsearch[partname][partsearch_007]": part_name or "",
                "partsearch[do][partsearch_007]": "Search"
            }

            # Submit search
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Referer": "https://www.rockauto.com/en/partsearch/"
            }

            search_response = await self.session.post(
                "https://www.rockauto.com/en/partsearch/",
                data=form_data,
                headers=headers
            )
            search_response.raise_for_status()

            # Parse search results
            result_soup = BeautifulSoup(search_response.text, "html.parser")
            parts = self._parse_parts_search_results(result_soup)

            return PartSearchResult(
                parts=parts,
                count=len(parts),
                search_term=part_number,
                manufacturer=manufacturer or "All",
                part_group=part_group or "All"
            )

        except Exception as e:
            raise Exception(f"Failed to search parts: {str(e)}")

    async def what_is_part_called(self, search_query: str) -> WhatIsPartCalledResults:
        """
        Search for part categories using the 'what is part called' functionality.

        Args:
            search_query: Keywords to search for (e.g., "brake pads", "oil filter")

        Returns:
            WhatIsPartCalledResults containing category matches
        """
        try:
            # Get initial page to extract security token
            response = await self.session.get("https://www.rockauto.com/en/partsearch/")
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Extract security token
            nck_input = soup.find("input", {"name": "_nck"})
            if not nck_input:
                raise ValueError("Could not find security token on parts search page")

            security_token = nck_input.get("value", "")

            # Prepare form data for top search
            form_data = {
                "_nck": security_token,
                "topsearchinput[submit]": "1",
                "topsearchinput[input]": search_query,
                "btntabsearch": "Search"
            }

            # Submit search
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Referer": "https://www.rockauto.com/en/partsearch/"
            }

            search_response = await self.session.post(
                "https://www.rockauto.com/en/partsearch/",
                data=form_data,
                headers=headers
            )
            search_response.raise_for_status()

            # Parse category results
            result_soup = BeautifulSoup(search_response.text, "html.parser")
            results = self._parse_what_is_part_called_results(result_soup)

            return WhatIsPartCalledResults(
                results=results,
                count=len(results),
                search_term=search_query
            )

        except Exception as e:
            raise Exception(f"Failed to search part categories: {str(e)}")

    def _parse_parts_search_results(self, soup: BeautifulSoup) -> list[PartInfo]:
        """Parse parts from search results page."""
        parts = []

        # Look for part results in tables or specific result containers
        # This would need to be adapted based on the actual structure of results
        result_tables = soup.find_all("table")

        for table in result_tables:
            rows = table.find_all("tr")
            for row in rows:
                cells = row.find_all(["td", "th"])
                if len(cells) >= 3:  # Minimum cells for part data
                    part_info = self._extract_part_from_search_row(row, cells)
                    if part_info:
                        parts.append(part_info)

        return parts

    def _extract_part_from_search_row(self, row, cells) -> Optional[PartInfo]:
        """Extract part information from a search result row."""
        try:
            # This would need to be adapted based on actual search result structure
            # For now, return a basic PartInfo with available data

            # Look for part number
            part_number = "Unknown"
            for cell in cells:
                text = cell.get_text(strip=True)
                if text and len(text) > 2:
                    part_number = text
                    break

            # Look for links
            href = ""
            link = row.find("a", href=True)
            if link:
                href = link.get("href", "")
                if href and not href.startswith("http"):
                    href = f"https://www.rockauto.com{href}"

            return PartInfo(
                part_number=part_number,
                brand="Unknown",
                price="Unknown",
                description="Unknown",
                href=href,
                specifications={}
            )

        except Exception:
            return None

    def _parse_what_is_part_called_results(self, soup: BeautifulSoup) -> list[WhatIsPartCalledResult]:
        """Parse category results from 'what is part called' search."""
        results = []

        # Look for category results - this would need to be adapted based on actual result structure
        # The results typically show as a table with Main Category/Subcategory columns
        tables = soup.find_all("table")

        for table in tables:
            rows = table.find_all("tr")
            for row in rows:
                cells = row.find_all(["td", "th"])
                if len(cells) >= 2:
                    main_category = cells[0].get_text(strip=True)
                    subcategory = cells[1].get_text(strip=True)

                    if main_category and subcategory and "/" not in main_category:
                        results.append(WhatIsPartCalledResult(
                            main_category=main_category,
                            subcategory=subcategory,
                            full_path=f"{main_category}/{subcategory}"
                        ))

        return results

    # === CACHE MANAGEMENT METHODS ===

    def get_cache_stats(self) -> dict:
        """Get comprehensive cache statistics."""
        stats = {
            "caching_enabled": self.cache_config.enabled,
            "cache_settings": {
                "part_cache_hours": self.cache_config.part_ttl_hours,
                "search_cache_hours": self.cache_config.result_ttl_hours,
                "dropdown_cache_hours": self._dropdown_cache_hours,
                "max_cached_parts": self.cache_config.max_parts,
                "max_cached_searches": self.cache_config.max_results
            },
            "dropdown_caches": {
                "manufacturers_cached": self._manufacturer_cache is not None,
                "part_groups_cached": self._part_group_cache is not None,
                "part_types_cached": self._part_type_cache is not None
            },
            "part_cache": None
        }

        if self._part_cache:
            stats["part_cache"] = self._part_cache.get_cache_stats()

        return stats

    def clear_all_caches(self) -> dict:
        """Clear all caches and return what was cleared."""
        cleared = {
            "manufacturers": self._manufacturer_cache is not None,
            "part_groups": self._part_group_cache is not None,
            "part_types": self._part_type_cache is not None,
            "parts_cleared": 0,
            "searches_cleared": 0
        }

        # Clear dropdown caches
        self._manufacturer_cache = None
        self._part_group_cache = None
        self._part_type_cache = None

        # Clear part cache
        if self._part_cache:
            stats = self._part_cache.get_cache_stats()
            cleared["parts_cleared"] = stats["cached_parts"]
            cleared["searches_cleared"] = stats["cached_results"]
            self._part_cache.clear_all()

        return cleared

    def clear_expired_caches(self) -> dict:
        """Clear only expired cache entries."""
        cleared = {
            "expired_parts": 0,
            "expired_searches": 0,
            "expired_dropdowns": 0
        }

        # Check dropdown cache expiration
        from datetime import datetime, timedelta
        cutoff = datetime.now() - timedelta(hours=self._dropdown_cache_hours)

        if self._manufacturer_cache and self._manufacturer_cache.last_updated:
            cached_time = datetime.fromisoformat(self._manufacturer_cache.last_updated)
            if cached_time < cutoff:
                self._manufacturer_cache = None
                cleared["expired_dropdowns"] += 1

        if self._part_group_cache and self._part_group_cache.last_updated:
            cached_time = datetime.fromisoformat(self._part_group_cache.last_updated)
            if cached_time < cutoff:
                self._part_group_cache = None
                cleared["expired_dropdowns"] += 1

        if self._part_type_cache and self._part_type_cache.last_updated:
            cached_time = datetime.fromisoformat(self._part_type_cache.last_updated)
            if cached_time < cutoff:
                self._part_type_cache = None
                cleared["expired_dropdowns"] += 1

        # Clear expired part cache entries
        if self._part_cache:
            expired_parts, expired_searches = self._part_cache.clear_expired()
            cleared["expired_parts"] = expired_parts
            cleared["expired_searches"] = expired_searches

        return cleared

    def configure_cache(
        self,
        enable_caching: Optional[bool] = None,
        part_cache_hours: Optional[int] = None,
        search_cache_hours: Optional[int] = None,
        dropdown_cache_hours: Optional[int] = None,
        max_cached_parts: Optional[int] = None,
        max_cached_searches: Optional[int] = None
    ) -> dict:
        """
        Reconfigure cache settings at runtime.

        Returns the new cache configuration.
        """
        if enable_caching is not None:
            self.cache_config.enabled = enable_caching
            if not enable_caching:
                self._part_cache = None
            elif self._part_cache is None:
                self._part_cache = self.cache_config.create_cache()

        if part_cache_hours is not None:
            self.cache_config.part_ttl_hours = part_cache_hours

        if search_cache_hours is not None:
            self.cache_config.result_ttl_hours = search_cache_hours

        if dropdown_cache_hours is not None:
            self._dropdown_cache_hours = dropdown_cache_hours

        if max_cached_parts is not None:
            self.cache_config.max_parts = max_cached_parts
            if self._part_cache:
                self._part_cache.max_parts = max_cached_parts

        if max_cached_searches is not None:
            self.cache_config.max_results = max_cached_searches
            if self._part_cache:
                self._part_cache.max_results = max_cached_searches

        return self.get_cache_stats()

    # === ORDER STATUS METHODS ===

    async def lookup_order_status(
        self,
        email_or_phone: str,
        order_number: str
    ) -> OrderStatusResult:
        """
        Look up order status using email/phone and order number.

        Args:
            email_or_phone: Customer email address or phone number
            order_number: RockAuto order number (up to 12 digits)

        Returns:
            OrderStatusResult containing order information or error details
        """
        try:
            # Validate input
            request = OrderLookupRequest(
                email_or_phone=email_or_phone,
                order_number=order_number
            )

            # Get initial page to extract CSRF token
            response = await self.session.get("https://www.rockauto.com/orderstatus/")
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Extract CSRF token
            nck_input = soup.find("input", {"name": "_nck"})
            if not nck_input:
                return OrderStatusResult.error_result(
                    OrderStatusError.system_error("Could not find security token on order status page")
                )

            security_token = nck_input.get("value", "")

            # Prepare form data for order lookup
            form_data = {
                "_nck": security_token,
                "action": "lookup",
                "emailorphone": request.email_or_phone,
                "ordernum": request.order_number,
                "lookup": "Find Order"
            }

            # Submit order lookup
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Referer": "https://www.rockauto.com/orderstatus/"
            }

            lookup_response = await self.session.post(
                "https://www.rockauto.com/orderstatus/orderstatus.php",
                data=form_data,
                headers=headers
            )
            lookup_response.raise_for_status()

            # Parse order status results
            result_soup = BeautifulSoup(lookup_response.text, "html.parser")
            order_status = self._parse_order_status_response(result_soup, request.order_number)

            if order_status:
                return OrderStatusResult.success_result(order_status)
            else:
                # Check for specific error messages in the response
                error_message = self._extract_order_error_message(result_soup)
                if "not found" in error_message.lower():
                    error = OrderStatusError.order_not_found(request.order_number)
                elif "email" in error_message.lower() or "phone" in error_message.lower():
                    error = OrderStatusError.invalid_credentials(request.order_number)
                else:
                    error = OrderStatusError.system_error(error_message or "Order lookup failed")

                return OrderStatusResult.error_result(error)

        except Exception as e:
            error = OrderStatusError.system_error(f"Order lookup failed: {str(e)}")
            return OrderStatusResult.error_result(error)

    async def request_order_list(
        self,
        method: str,
        contact: str
    ) -> bool:
        """
        Request order list to be sent via email or SMS.

        Args:
            method: 'email' or 'sms'
            contact: Email address or phone number

        Returns:
            bool: True if request was submitted successfully
        """
        try:
            # Validate input
            request = OrderListRequest(method=method, contact=contact)

            # Get initial page to extract CSRF token and timestamp
            response = await self.session.get("https://www.rockauto.com/orderstatus/")
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Extract CSRF token
            nck_input = soup.find("input", {"name": "_nck"})
            if not nck_input:
                raise ValueError("Could not find security token")

            security_token = nck_input.get("value", "")

            # Extract timestamp
            timestamp_input = soup.find("input", {"name": "timestamp"})
            timestamp = timestamp_input.get("value", "") if timestamp_input else ""

            # Prepare form data based on method
            if request.method == "email":
                form_data = {
                    "_nck": security_token,
                    "action": "sendorders",
                    "sendordermethod": "email",
                    "emailaddrsend": request.contact,
                    "timestamp": timestamp
                }
            else:  # SMS
                form_data = {
                    "_nck": security_token,
                    "action": "sendorders",
                    "sendordermethod": "mms",
                    "mmsnumbersend": request.contact,
                    "timestamp": timestamp
                }

            # Submit request
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Referer": "https://www.rockauto.com/orderstatus/"
            }

            request_response = await self.session.post(
                "https://www.rockauto.com/orderstatus/orderstatus.php",
                data=form_data,
                headers=headers
            )
            request_response.raise_for_status()

            # Check if request was successful (basic success detection)
            response_text = request_response.text.lower()
            success_indicators = ["sent", "delivered", "order list"]
            return any(indicator in response_text for indicator in success_indicators)

        except Exception as e:
            raise Exception(f"Failed to request order list: {str(e)}")

    def _parse_order_status_response(self, soup: BeautifulSoup, order_number: str) -> Optional[OrderStatus]:
        """Parse order status information from response HTML."""
        try:
            # Look for order information containers
            order_containers = soup.find_all(["div", "table", "section"],
                                           class_=re.compile(r"order|status|details", re.I))

            if not order_containers:
                # Try finding by order number text
                order_text = soup.find(text=re.compile(order_number))
                if not order_text:
                    return None

            # Initialize order status with basic info
            order_status = OrderStatus(
                order_number=order_number,
                status="Unknown",
                items=[],
                item_count=0
            )

            # Parse order details
            self._extract_basic_order_info(soup, order_status)
            self._extract_order_items(soup, order_status)
            self._extract_shipping_info(soup, order_status)
            self._extract_billing_info(soup, order_status)

            # Update item count
            order_status.item_count = len(order_status.items)

            # Validate that this is real order data vs massive JS localization
            if not self._is_real_order_data(order_status, order_number):
                return None

            return order_status

        except Exception:
            return None

    def _extract_basic_order_info(self, soup: BeautifulSoup, order_status: OrderStatus) -> None:
        """Extract basic order information like status and dates."""
        # Look for status information
        status_elements = soup.find_all(text=re.compile(r"status|shipped|processing|delivered", re.I))
        for element in status_elements:
            parent = element.parent if element.parent else None
            if parent:
                text = parent.get_text(strip=True)
                if any(word in text.lower() for word in ["shipped", "processing", "delivered", "cancelled"]):
                    order_status.status = text
                    break

        # Look for order date
        date_patterns = [
            re.compile(r"order date[:\s]*(.+)", re.I),
            re.compile(r"placed[:\s]*(.+)", re.I),
            re.compile(r"date[:\s]*(\d{1,2}/\d{1,2}/\d{4})", re.I)
        ]

        for pattern in date_patterns:
            date_match = soup.find(text=pattern)
            if date_match:
                match = pattern.search(date_match.strip())
                if match:
                    order_status.order_date = match.group(1).strip()
                    break

    def _extract_order_items(self, soup: BeautifulSoup, order_status: OrderStatus) -> None:
        """Extract order items from the response."""
        # Look for item tables or lists
        item_tables = soup.find_all("table")
        item_rows = []

        for table in item_tables:
            rows = table.find_all("tr")
            for row in rows:
                cells = row.find_all(["td", "th"])
                if len(cells) >= 3:  # Minimum cells for item data
                    item_rows.append(cells)

        # Parse items from rows
        for cells in item_rows:
            try:
                # Extract available information from cells
                part_number = "Unknown"
                description = "Unknown"
                brand = "Unknown"
                quantity = 1
                unit_price = "$0.00"
                total_price = "$0.00"

                # Try to extract data from cells
                for i, cell in enumerate(cells):
                    text = cell.get_text(strip=True)
                    if text and len(text) > 2:
                        if i == 0 and re.match(r"[A-Z0-9\-]+", text):
                            part_number = text
                        elif "qty" in text.lower() or text.isdigit():
                            try:
                                quantity = int(re.search(r"\d+", text).group())
                            except:
                                pass
                        elif "$" in text:
                            if "." in text:
                                if unit_price == "$0.00":
                                    unit_price = text
                                else:
                                    total_price = text

                # Only add if we have meaningful data
                if part_number != "Unknown" or any("$" in cell.get_text() for cell in cells):
                    item = OrderItem(
                        part_number=part_number,
                        description=description,
                        brand=brand,
                        quantity=quantity,
                        unit_price=unit_price,
                        total_price=total_price
                    )
                    order_status.items.append(item)

            except Exception:
                continue

    def _extract_shipping_info(self, soup: BeautifulSoup, order_status: OrderStatus) -> None:
        """Extract shipping information from the response."""
        try:
            # Look for tracking numbers
            tracking_patterns = [
                re.compile(r"tracking[:\s]*([A-Z0-9]+)", re.I),
                re.compile(r"track[:\s]*([A-Z0-9]+)", re.I),
                re.compile(r"ups[:\s]*([A-Z0-9]+)", re.I),
                re.compile(r"fedex[:\s]*([A-Z0-9]+)", re.I),
                re.compile(r"usps[:\s]*([A-Z0-9]+)", re.I)
            ]

            tracking_number = None
            carrier = None

            for pattern in tracking_patterns:
                tracking_match = soup.find(text=pattern)
                if tracking_match:
                    match = pattern.search(tracking_match.strip())
                    if match:
                        tracking_number = match.group(1).strip()
                        if "ups" in tracking_match.lower():
                            carrier = "UPS"
                        elif "fedex" in tracking_match.lower():
                            carrier = "FedEx"
                        elif "usps" in tracking_match.lower():
                            carrier = "USPS"
                        break

            # Look for shipping cost
            shipping_cost = "$0.00"
            shipping_patterns = [
                re.compile(r"shipping[:\s]*(\$[\d.]+)", re.I),
                re.compile(r"freight[:\s]*(\$[\d.]+)", re.I)
            ]

            for pattern in shipping_patterns:
                cost_match = soup.find(text=pattern)
                if cost_match:
                    match = pattern.search(cost_match.strip())
                    if match:
                        shipping_cost = match.group(1)
                        break

            if tracking_number or shipping_cost != "$0.00":
                order_status.shipping = ShippingInfo(
                    method="Standard",
                    cost=shipping_cost,
                    carrier=carrier,
                    tracking_number=tracking_number
                )

        except Exception:
            pass

    def _extract_billing_info(self, soup: BeautifulSoup, order_status: OrderStatus) -> None:
        """Extract billing information from the response."""
        try:
            # Look for total amount
            total_patterns = [
                re.compile(r"total[:\s]*(\$[\d.]+)", re.I),
                re.compile(r"amount[:\s]*(\$[\d.]+)", re.I)
            ]

            total = "$0.00"
            subtotal = "$0.00"
            shipping_cost = "$0.00"

            for pattern in total_patterns:
                total_match = soup.find(text=pattern)
                if total_match:
                    match = pattern.search(total_match.strip())
                    if match:
                        total = match.group(1)
                        break

            # Try to extract subtotal
            subtotal_patterns = [
                re.compile(r"subtotal[:\s]*(\$[\d.]+)", re.I),
                re.compile(r"parts[:\s]*(\$[\d.]+)", re.I)
            ]

            for pattern in subtotal_patterns:
                subtotal_match = soup.find(text=pattern)
                if subtotal_match:
                    match = pattern.search(subtotal_match.strip())
                    if match:
                        subtotal = match.group(1)
                        break

            if total != "$0.00" or subtotal != "$0.00":
                order_status.billing = BillingInfo(
                    subtotal=subtotal,
                    shipping_cost=shipping_cost,
                    total=total
                )

        except Exception:
            pass

    def _extract_order_error_message(self, soup: BeautifulSoup) -> str:
        """Extract error message from failed order lookup."""
        try:
            # Look for error messages
            error_elements = soup.find_all(["div", "span", "p"],
                                         class_=re.compile(r"error|alert|warning", re.I))

            for element in error_elements:
                text = element.get_text(strip=True)
                if text and len(text) > 10:
                    return text

            # Look for any text containing error keywords
            error_text = soup.find(text=re.compile(r"error|not found|invalid|failed", re.I))
            if error_text:
                return error_text.strip()

            return "Order lookup failed"

        except Exception:
            return "Unknown error occurred"

    def _is_real_order_data(self, order_status: OrderStatus, order_number: str) -> bool:
        """Detect if order contains real data vs massive JS localization strings."""
        if not order_status:
            return False

        # Check if essential fields contain reasonable data vs huge JS objects
        status = getattr(order_status, 'status', '')
        order_date = getattr(order_status, 'order_date', '')

        # If status field is massive (>1000 chars), it's likely JS localization
        if len(str(status)) > 1000:
            return False

        # If order_date is massive, it's likely JS localization
        if order_date and len(str(order_date)) > 1000:
            return False

        # If order_number doesn't match what we searched for, likely localization
        actual_order_num = getattr(order_status, 'order_number', '')
        if actual_order_num and str(actual_order_num) != str(order_number):
            return False

        # Check if we have meaningful item count or billing info
        item_count = getattr(order_status, 'item_count', 0)
        has_billing = hasattr(order_status, 'billing') and order_status.billing

        # Real orders should have either items or billing info, but not fake items
        # Fake items are usually created from JS localization data
        if item_count > 0:
            # Check if items look real vs generated from localization
            if hasattr(order_status, 'items') and order_status.items:
                first_item = order_status.items[0]
                # Check if item data looks real
                item_desc = getattr(first_item, 'description', '')
                item_brand = getattr(first_item, 'brand', '')
                if len(str(item_desc)) > 500 or len(str(item_brand)) > 500:
                    return False  # Likely JS localization in items too

        # If we have a reasonable status, date, and items, it's probably real
        return (
            item_count > 0 or has_billing or
            (len(str(status)) < 100 and status.lower() not in ['unknown', ''])
        )

    # === AUTHENTICATED ACCOUNT METHODS ===

    async def add_external_order(self, email_or_phone: str, order_number: str) -> bool:
        """
        Add an order from another email/phone to this account's history.
        Requires authentication.

        Args:
            email_or_phone: Email address or phone number from the external order
            order_number: Order number to add to account history

        Returns:
            bool: True if order was successfully added

        Raises:
            Exception: If not authenticated or request fails
        """
        if not self.is_authenticated:
            raise Exception("Authentication required for adding external orders")

        try:
            # Validate input
            request = ExternalOrderRequest(
                email_or_phone=email_or_phone,
                order_number=order_number
            )

            # Get account activity page to extract form tokens
            response = await self.session.get("https://www.rockauto.com/en/accountactivity/")
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Extract CSRF token if present
            nck_input = soup.find("input", {"name": "_nck"})
            security_token = nck_input.get("value", "") if nck_input else ""

            # Prepare form data for adding external order
            form_data = {
                "email_or_phone": request.email_or_phone,
                "order_number": request.order_number,
                "add_external_order": "1"
            }

            # Add security token if found
            if security_token:
                form_data["_nck"] = security_token

            # Submit request
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Referer": "https://www.rockauto.com/en/accountactivity/"
            }

            add_response = await self.session.post(
                "https://www.rockauto.com/en/accountactivity/",
                data=form_data,
                headers=headers
            )
            add_response.raise_for_status()

            # Check response for success indicators
            response_text = add_response.text.lower()
            success_indicators = ["added", "success", "order added"]
            failure_indicators = ["error", "failed", "not found", "invalid"]

            is_success = any(indicator in response_text for indicator in success_indicators)
            is_failure = any(indicator in response_text for indicator in failure_indicators)

            return is_success and not is_failure

        except Exception as e:
            raise Exception(f"Failed to add external order: {str(e)}")

    async def get_saved_addresses(self) -> SavedAddressesResult:
        """
        Get all saved addresses for the authenticated account.
        Requires authentication.

        Returns:
            SavedAddressesResult: List of saved addresses

        Raises:
            Exception: If not authenticated or request fails
        """
        if not self.is_authenticated:
            raise Exception("Authentication required for accessing saved addresses")

        try:
            # Get profile page which contains saved addresses with browser headers
            headers = {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"Windows"',
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1",
                "Referer": "https://www.rockauto.com/",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache"
            }

            response = await self.session.get(
                "https://www.rockauto.com/en/profile/",
                headers=headers
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            addresses = []

            # Find saved addresses section
            addresses_section = soup.find("region", {"aria-label": "Saved Addresses"}) or \
                              soup.find(text=lambda text: text and "saved addresses" in text.lower())

            if addresses_section:
                # Look for address rows in tables
                if hasattr(addresses_section, 'find_parent'):
                    parent = addresses_section.find_parent()
                    address_tables = parent.find_all("table") if parent else []
                else:
                    # If addresses_section is text, find nearby tables
                    address_tables = soup.find_all("table")

                for table in address_tables:
                    rows = table.find_all("tr")
                    for row in rows:
                        # Look for rows with address data
                        cells = row.find_all(["td", "th"])
                        if len(cells) >= 2:
                            address_cell = cells[0]
                            actions_cell = cells[-1]

                            # Extract address information
                            address_text = address_cell.get_text(strip=True)
                            if address_text and "edit" not in address_text.lower():
                                # Parse address components
                                lines = [line.strip() for line in address_text.split('\n') if line.strip()]
                                if len(lines) >= 3:  # Name, street, city/state/zip
                                    full_name = lines[0]
                                    address_line1 = lines[1]
                                    city_state_zip = lines[2] if len(lines) > 2 else ""

                                    # Parse city, state, zip
                                    city = state = postal_code = ""
                                    if city_state_zip:
                                        parts = city_state_zip.split(',')
                                        if len(parts) >= 2:
                                            city = parts[0].strip()
                                            state_zip = parts[1].strip().split()
                                            if len(state_zip) >= 2:
                                                state = state_zip[0]
                                                postal_code = ' '.join(state_zip[1:])

                                    # Extract address ID from edit button if available
                                    address_id = None
                                    edit_buttons = actions_cell.find_all("button") if actions_cell else []
                                    for button in edit_buttons:
                                        if "edit" in button.get_text().lower():
                                            # Try to extract ID from button attributes
                                            onclick = button.get("onclick", "")
                                            if onclick:
                                                # Parse ID from onclick attribute
                                                import re
                                                id_match = re.search(r'(\d+)', onclick)
                                                if id_match:
                                                    address_id = id_match.group(1)

                                    address = SavedAddress(
                                        name=full_name,
                                        full_name=full_name,
                                        address_line1=address_line1,
                                        city=city,
                                        state=state,
                                        postal_code=postal_code,
                                        country="US",
                                        address_id=address_id
                                    )
                                    addresses.append(address)

            return SavedAddressesResult(
                addresses=addresses,
                count=len(addresses),
                has_default=any(addr.is_default for addr in addresses)
            )

        except Exception as e:
            raise Exception(f"Failed to get saved addresses: {str(e)}")

    async def get_saved_vehicles(self) -> SavedVehiclesResult:
        """
        Get all saved vehicles for the authenticated account.
        Requires authentication.

        Returns:
            SavedVehiclesResult: List of saved vehicles

        Raises:
            Exception: If not authenticated or request fails
        """
        if not self.is_authenticated:
            raise Exception("Authentication required for accessing saved vehicles")

        try:
            # Get profile page which contains saved vehicles with browser headers
            headers = {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"Windows"',
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1",
                "Referer": "https://www.rockauto.com/",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache"
            }

            response = await self.session.get(
                "https://www.rockauto.com/en/profile/",
                headers=headers
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            vehicles = []

            # Find saved vehicles section
            vehicles_section = soup.find("region", {"aria-label": "Saved Vehicles"}) or \
                             soup.find(text=lambda text: text and "saved vehicles" in text.lower())

            if vehicles_section:
                # Look for vehicle links and delete buttons
                if hasattr(vehicles_section, 'find_parent'):
                    parent = vehicles_section.find_parent()
                    vehicle_tables = parent.find_all("table") if parent else []
                else:
                    # If vehicles_section is text, find nearby tables
                    vehicle_tables = soup.find_all("table")

                for table in vehicle_tables:
                    rows = table.find_all("tr")
                    for row in rows:
                        cells = row.find_all(["td", "th"])
                        if len(cells) >= 2:
                            vehicle_cell = cells[0]
                            actions_cell = cells[-1] if len(cells) > 1 else None

                            # Look for vehicle links
                            vehicle_link = vehicle_cell.find("a")
                            if vehicle_link:
                                vehicle_text = vehicle_link.get_text(strip=True)
                                catalog_url = vehicle_link.get("href", "")

                                # Parse vehicle info (e.g., "2017 FORD F-150")
                                parts = vehicle_text.split()
                                if len(parts) >= 3:
                                    year = int(parts[0]) if parts[0].isdigit() else 0
                                    make = parts[1]
                                    model = ' '.join(parts[2:])

                                    # Extract carcode from URL if available
                                    carcode = None
                                    if catalog_url and ',' in catalog_url:
                                        url_parts = catalog_url.split(',')
                                        if len(url_parts) >= 5:
                                            carcode = url_parts[-1]

                                    # Extract vehicle ID from delete button if available
                                    vehicle_id = None
                                    if actions_cell:
                                        delete_buttons = actions_cell.find_all("button")
                                        for button in delete_buttons:
                                            if "delete" in button.get_text().lower():
                                                # Try to extract ID from button attributes
                                                onclick = button.get("onclick", "")
                                                if onclick:
                                                    import re
                                                    id_match = re.search(r'(\d+)', onclick)
                                                    if id_match:
                                                        vehicle_id = id_match.group(1)

                                    vehicle = SavedVehicle(
                                        year=year,
                                        make=make,
                                        model=model,
                                        carcode=carcode,
                                        display_name=vehicle_text,
                                        catalog_url=f"https://www.rockauto.com{catalog_url}" if catalog_url and not catalog_url.startswith("http") else catalog_url,
                                        vehicle_id=vehicle_id
                                    )
                                    vehicles.append(vehicle)

            return SavedVehiclesResult(
                vehicles=vehicles,
                count=len(vehicles)
            )

        except Exception as e:
            raise Exception(f"Failed to get saved vehicles: {str(e)}")

    async def get_account_activity(self) -> AccountActivityResult:
        """
        Get comprehensive account activity information including addresses and vehicles.
        Requires authentication.

        Returns:
            AccountActivityResult: Complete account activity data

        Raises:
            Exception: If not authenticated or request fails
        """
        if not self.is_authenticated:
            raise Exception("Authentication required for account activity")

        try:
            # Get saved addresses and vehicles in parallel
            saved_addresses = await self.get_saved_addresses()
            saved_vehicles = await self.get_saved_vehicles()

            # Check account activity page for additional features with browser headers
            headers = {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"Windows"',
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1",
                "Referer": "https://www.rockauto.com/",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache"
            }

            response = await self.session.get(
                "https://www.rockauto.com/en/accountactivity/",
                headers=headers
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Check for presence of different sections
            has_discount_codes = bool(soup.find(text=lambda text: text and "discount code" in text.lower()))
            has_store_credit = bool(soup.find(text=lambda text: text and "store credit" in text.lower()))
            has_alerts = bool(soup.find(text=lambda text: text and "availability alerts" in text.lower()))

            return AccountActivityResult(
                saved_addresses=saved_addresses,
                saved_vehicles=saved_vehicles,
                has_discount_codes=has_discount_codes,
                has_store_credit=has_store_credit,
                has_alerts=has_alerts
            )

        except Exception as e:
            raise Exception(f"Failed to get account activity: {str(e)}")

    async def get_order_history(self, filter_params: Optional[OrderHistoryFilter] = None) -> OrderHistoryResult:
        """
        Get order history for the authenticated account.
        Requires authentication.

        Args:
            filter_params: Optional filters for order history search

        Returns:
            OrderHistoryResult: Order history data

        Raises:
            Exception: If not authenticated or request fails
        """
        if not self.is_authenticated:
            raise Exception("Authentication required for accessing order history")

        # Use default filter if none provided
        if filter_params is None:
            filter_params = OrderHistoryFilter()

        try:
            # Navigate to order history page with browser-like headers
            headers = {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"Windows"',
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1",
                "Referer": "https://www.rockauto.com/",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache"
            }

            response = await self.session.get(
                "https://www.rockauto.com/en/orderhistory/",
                headers=headers
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            orders = []

            # Look for order history table or sections
            order_tables = soup.find_all("table")

            for table in order_tables:
                rows = table.find_all("tr")

                # Skip header rows and look for order data
                for row in rows[1:]:  # Skip first row (likely header)
                    cells = row.find_all(["td", "th"])

                    if len(cells) >= 3:  # Need at least order number, date, status
                        try:
                            # Extract order information from table cells
                            order_number_cell = cells[0].get_text(strip=True)
                            date_cell = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                            status_cell = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                            total_cell = cells[3].get_text(strip=True) if len(cells) > 3 else ""

                            # Only add if we have valid order data
                            if order_number_cell and date_cell:
                                # Look for order status link
                                order_url = None
                                status_link = row.find("a")
                                if status_link and status_link.get("href"):
                                    order_url = f"https://www.rockauto.com{status_link['href']}"

                                order = OrderHistoryItem(
                                    order_number=order_number_cell,
                                    date=date_cell,
                                    status=status_cell or "Unknown",
                                    total=total_cell or "$0.00",
                                    order_url=order_url
                                )
                                orders.append(order)

                        except Exception:
                            # Skip invalid order rows
                            continue

            # Alternative: Look for order information in other formats
            if not orders:
                # Check for order cards or divs
                order_sections = soup.find_all(["div", "section"], class_=lambda x: x and "order" in x.lower())

                for section in order_sections:
                    order_text = section.get_text()

                    # Look for order number patterns
                    import re
                    order_match = re.search(r'order\s*#?\s*(\d+)', order_text, re.IGNORECASE)
                    date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', order_text)

                    if order_match:
                        order_number = order_match.group(1)
                        date = date_match.group(1) if date_match else "Unknown"

                        order = OrderHistoryItem(
                            order_number=order_number,
                            date=date,
                            status="Unknown",
                            total="$0.00"
                        )
                        orders.append(order)

            return OrderHistoryResult(
                orders=orders,
                count=len(orders),
                filter_applied=filter_params
            )

        except Exception as e:
            raise Exception(f"Failed to get order history: {str(e)}")
