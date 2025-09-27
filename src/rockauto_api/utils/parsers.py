"""Data parsing utilities for RockAuto API."""

import re
from typing import List, Optional

from bs4 import BeautifulSoup

from ..models import PartInfo


class PartExtractor:
    """Utility class for extracting part information from HTML."""

    BRAND_PATTERNS = [
        r"(?:Brand|Mfg|Manufacturer)\s*:?\s*([A-Z][a-zA-Z\s&]{2,20})",  # Brand: Toyota
        r"\b(HONDA|TOYOTA|FORD|CHEVROLET|NISSAN|BMW|MERCEDES|AUDI|LEXUS|ACURA|INFINITI)\b",  # OEM brands
        r"\b(BOSCH|DENSO|NGK|MOBIL|CASTROL|VALVOLINE|MONROE|KYB|BILSTEIN|BREMBO|ATE|ZIMMERMANN|DELPHI|GATES|DAYCO|HOLSTEIN|ULTRA-POWER|AUTOTECNICA|FAMOUS)\b",  # Aftermarket brands
    ]

    PART_NUMBER_PATTERNS = [
        r"(?:Part|P/N|PN|#)\s*:?\s*([A-Z0-9\-]{4,})",  # Part: ABC123
        r"\b([A-Z]{2,}[0-9]{3,}[A-Z0-9\-]*)\b",  # ABC123DEF
        r"\b([0-9]{3,}[A-Z]{2,}[A-Z0-9\-]*)\b",  # 123ABCDEF
        r"\b([A-Z0-9\-]{6,})\b",  # Long alphanumeric codes
    ]

    PRICE_PATTERNS = [
        r"\$([0-9,]+\.?[0-9]*)",  # $123.45 or $123
        r"USD\s*([0-9,]+\.?[0-9]*)",  # USD 123.45
        r"Price:\s*\$([0-9,]+\.?[0-9]*)",  # Price: $123.45
    ]

    VIDEO_PATTERNS = [
        r"youtube\.com/watch\?v=([a-zA-Z0-9_-]+)",
        r"youtu\.be/([a-zA-Z0-9_-]+)",
        r"vimeo\.com/([0-9]+)",
        r"\.mp4['\"]?",
        r"\.webm['\"]?",
        r"\.mov['\"]?",
    ]

    NOISE_PATTERNS = ["Info", "Fits", "Related Parts", "Intentionally blank"]

    @classmethod
    def extract_from_element(cls, element) -> Optional[PartInfo]:
        """Extract part information from HTML element."""
        try:
            text = element.get_text(strip=True)
            if not text or len(text) < 3:
                return None

            href = element.get("href", "")

            # Skip navigation elements
            if any(nav_word in text.lower() for nav_word in ["show", "hide", "expand", "collapse", "toggle"]):
                return None

            name = text
            part_number = "Unknown"
            price = None
            brand = None

            # Extract price
            for pattern in cls.PRICE_PATTERNS:
                price_match = re.search(pattern, text, re.IGNORECASE)
                if price_match:
                    price = f"${price_match.group(1)}"
                    break

            # Extract part number
            for pattern in cls.PART_NUMBER_PATTERNS:
                part_match = re.search(pattern, text, re.IGNORECASE)
                if part_match:
                    potential_part = part_match.group(1)
                    if re.search(r"[0-9]", potential_part) and len(potential_part) >= 4:
                        part_number = potential_part
                        break

            # Extract brand
            for pattern in cls.BRAND_PATTERNS:
                brand_match = re.search(pattern, text, re.IGNORECASE)
                if brand_match:
                    brand = brand_match.group(1).title()
                    break

            # Clean up the name
            clean_name = cls._clean_name(text, price, part_number, brand)

            # Format URL
            full_url = cls._format_url(href)

            return PartInfo(
                name=clean_name if clean_name else text,
                part_number=part_number,
                price=price,
                brand=brand,
                url=full_url,
                image_url=None,  # Will be filled by detailed extraction
                info_url=None,  # Will be filled by detailed extraction
                video_url=None,  # Will be filled by detailed extraction
            )
        except Exception:
            return None

    @classmethod
    def extract_from_table_row(cls, row, cells: List) -> Optional[PartInfo]:
        """Extract part information from a table row with detailed parsing."""
        try:
            # Extract text from each cell
            cell_texts = [cell.get_text(strip=True) for cell in cells]

            # Initialize part info
            part_info = {
                "name": None,
                "part_number": "Unknown",
                "price": None,
                "brand": None,
                "url": None,
                "image_url": None,
                "info_url": None,
                "video_url": None,
            }

            # Extract price
            for cell_text in cell_texts:
                price_match = re.search(cls.PRICE_PATTERNS[0], cell_text)
                if price_match:
                    part_info["price"] = f"${price_match.group(1)}"
                    break

            # Extract part number
            for cell_text in cell_texts:
                part_match = re.search(r"\b[A-Z0-9\-]{6,}\b", cell_text)
                if part_match and "$" not in cell_text:
                    part_info["part_number"] = part_match.group()
                    break

            # Extract brand
            brands = ["DENSO", "BOSCH", "NGK", "HONDA", "TOYOTA", "FORD", "CHEVROLET", "DELPHI", "GATES", "DAYCO", "MONROE", "KYB", "BILSTEIN", "BREMBO", "HOLSTEIN", "ULTRA-POWER", "AUTOTECNICA", "FAMOUS"]
            for cell_text in cell_texts:
                for brand in brands:
                    if brand in cell_text.upper():
                        part_info["brand"] = brand
                        break
                if part_info["brand"]:
                    break

            # Extract part name
            name_candidates = [text for text in cell_texts if text and "$" not in text and len(text) > 5]
            if name_candidates:
                longest_candidate = max(name_candidates, key=len)
                clean_name = cls._clean_part_name(longest_candidate, part_info["brand"], part_info["part_number"])
                part_info["name"] = clean_name if clean_name else longest_candidate

            # Extract URLs
            cls._extract_urls_from_row(row, part_info)

            # Only return if we found meaningful part information
            if part_info["price"] or part_info["part_number"] != "Unknown":
                return PartInfo(
                    name=part_info["name"] or "Unknown Part",
                    part_number=part_info["part_number"],
                    price=part_info["price"],
                    brand=part_info["brand"],
                    url=part_info["url"],
                    image_url=part_info["image_url"],
                    info_url=part_info["info_url"],
                    video_url=part_info["video_url"],
                )

            return None

        except Exception:
            return None

    @classmethod
    def extract_video_url(cls, page_text: str, soup: BeautifulSoup) -> Optional[str]:
        """Extract video URL from page content."""
        try:
            # Look for video patterns in text
            for pattern in cls.VIDEO_PATTERNS:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    if "youtube" in pattern or "youtu.be" in pattern:
                        video_id = match.group(1)
                        return f"https://www.youtube.com/watch?v={video_id}"
                    elif "vimeo" in pattern:
                        video_id = match.group(1)
                        return f"https://vimeo.com/{video_id}"
                    else:
                        return match.group(0)

            # Look for video tags
            video_elements = soup.find_all(["video", "iframe"])
            for video in video_elements:
                src = video.get("src", "")
                if src and any(vid_ext in src for vid_ext in [".mp4", ".webm", ".mov", "youtube", "vimeo"]):
                    if not src.startswith("http"):
                        return f"https://www.rockauto.com{src}"
                    return src

            return None

        except Exception:
            return None

    @classmethod
    def _clean_name(cls, text: str, price: Optional[str], part_number: str, brand: Optional[str]) -> str:
        """Clean up the part name by removing extracted info."""
        clean_name = text
        if price:
            clean_name = re.sub(r"\$[0-9,]+\.?[0-9]*", "", clean_name)
        if part_number != "Unknown":
            clean_name = re.sub(re.escape(part_number), "", clean_name, flags=re.IGNORECASE)
        if brand:
            clean_name = re.sub(re.escape(brand), "", clean_name, flags=re.IGNORECASE)

        clean_name = re.sub(r"\s+", " ", clean_name).strip()
        clean_name = clean_name.strip(":-.,")
        return clean_name

    @classmethod
    def _clean_part_name(cls, name: str, brand: Optional[str], part_number: str) -> str:
        """Clean up part name from table extraction."""
        clean_name = name
        if brand:
            clean_name = clean_name.replace(brand, "").strip()
        if part_number != "Unknown":
            clean_name = clean_name.replace(part_number, "").strip()

        # Remove common noise
        for noise in cls.NOISE_PATTERNS:
            clean_name = clean_name.replace(noise, "").strip()

        return clean_name

    @classmethod
    def _format_url(cls, href: str) -> Optional[str]:
        """Format URL to be absolute."""
        if not href:
            return None
        if href.startswith("http"):
            return href
        elif href.startswith("/"):
            return f"https://www.rockauto.com{href}"
        else:
            return f"https://www.rockauto.com/{href}"

    @classmethod
    def _extract_urls_from_row(cls, row, part_info: dict) -> None:
        """Extract URLs from table row."""
        # Look for main product link
        main_links = row.find_all("a", href=True)
        for link in main_links:
            href = link.get("href", "")
            if "catalog" in href and "moreinfo" not in href:
                part_info["url"] = cls._format_url(href)
                break

        # Look for images
        img = row.find("img")
        if img:
            img_src = img.get("src", "")
            if img_src and "flag_" not in img_src and "loading.gif" not in img_src:
                part_info["image_url"] = cls._format_url(img_src)

        # Look for info links
        info_links = row.find_all("a", href=re.compile(r"moreinfo\.php|details|info", re.I))
        if info_links:
            info_href = info_links[0].get("href", "")
            if info_href:
                part_info["info_url"] = cls._format_url(info_href)