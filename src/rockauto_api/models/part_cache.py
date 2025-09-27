"""Models for caching Part and PartInfo objects."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field

from .part_info import PartInfo
from .vehicle_parts_result import VehiclePartsResult


class CachedPartInfo(BaseModel):
    """Wrapper for cached PartInfo with metadata."""

    part_info: PartInfo = Field(..., description="The cached part information")
    cached_at: datetime = Field(..., description="When this part was cached")
    access_count: int = Field(default=1, description="Number of times this part was accessed")
    last_accessed: datetime = Field(..., description="When this part was last accessed")

    @classmethod
    def create(cls, part_info: PartInfo) -> "CachedPartInfo":
        """Create a new cached part entry."""
        now = datetime.now()
        return cls(
            part_info=part_info,
            cached_at=now,
            last_accessed=now
        )

    def access(self) -> PartInfo:
        """Access the part info and update access metadata."""
        self.access_count += 1
        self.last_accessed = datetime.now()
        return self.part_info

    def is_expired(self, ttl_hours: int = 12) -> bool:
        """Check if this cached part has expired."""
        return datetime.now() - self.cached_at > timedelta(hours=ttl_hours)


class CachedVehiclePartsResult(BaseModel):
    """Wrapper for cached VehiclePartsResult with metadata."""

    result: VehiclePartsResult = Field(..., description="The cached vehicle parts result")
    cache_key: str = Field(..., description="Unique key for this cache entry")
    cached_at: datetime = Field(..., description="When this result was cached")
    access_count: int = Field(default=1, description="Number of times this result was accessed")
    last_accessed: datetime = Field(..., description="When this result was last accessed")

    @classmethod
    def create(cls, result: VehiclePartsResult, cache_key: str) -> "CachedVehiclePartsResult":
        """Create a new cached vehicle parts result entry."""
        now = datetime.now()
        return cls(
            result=result,
            cache_key=cache_key,
            cached_at=now,
            last_accessed=now
        )

    def access(self) -> VehiclePartsResult:
        """Access the result and update access metadata."""
        self.access_count += 1
        self.last_accessed = datetime.now()
        return self.result

    def is_expired(self, ttl_hours: int = 12) -> bool:
        """Check if this cached result has expired."""
        return datetime.now() - self.cached_at > timedelta(hours=ttl_hours)


class PartCache(BaseModel):
    """In-memory cache for parts and part search results."""

    parts: Dict[str, CachedPartInfo] = Field(default_factory=dict, description="Cache of individual parts by part number")
    vehicle_results: Dict[str, CachedVehiclePartsResult] = Field(default_factory=dict, description="Cache of vehicle part search results")
    max_parts: int = Field(default=1000, description="Maximum number of parts to cache")
    max_results: int = Field(default=100, description="Maximum number of search results to cache")

    def get_part(self, part_number: str) -> Optional[PartInfo]:
        """Get a cached part by part number."""
        cached_part = self.parts.get(part_number)
        if cached_part and not cached_part.is_expired():
            return cached_part.access()
        elif cached_part:  # Expired
            del self.parts[part_number]
        return None

    def cache_part(self, part_info: PartInfo) -> None:
        """Cache a part info object."""
        # Check cache size limit
        if len(self.parts) >= self.max_parts:
            self._evict_oldest_part()

        self.parts[part_info.part_number] = CachedPartInfo.create(part_info)

    def get_vehicle_result(self, cache_key: str) -> Optional[VehiclePartsResult]:
        """Get a cached vehicle parts search result."""
        cached_result = self.vehicle_results.get(cache_key)
        if cached_result and not cached_result.is_expired():
            return cached_result.access()
        elif cached_result:  # Expired
            del self.vehicle_results[cache_key]
        return None

    def cache_vehicle_result(self, result: VehiclePartsResult, cache_key: str) -> None:
        """Cache a vehicle parts search result."""
        # Check cache size limit
        if len(self.vehicle_results) >= self.max_results:
            self._evict_oldest_result()

        self.vehicle_results[cache_key] = CachedVehiclePartsResult.create(result, cache_key)

    def _evict_oldest_part(self) -> None:
        """Remove the oldest cached part to make room."""
        if not self.parts:
            return

        oldest_key = min(self.parts.keys(), key=lambda k: self.parts[k].last_accessed)
        del self.parts[oldest_key]

    def _evict_oldest_result(self) -> None:
        """Remove the oldest cached result to make room."""
        if not self.vehicle_results:
            return

        oldest_key = min(self.vehicle_results.keys(), key=lambda k: self.vehicle_results[k].last_accessed)
        del self.vehicle_results[oldest_key]

    def clear_expired(self) -> tuple[int, int]:
        """Remove all expired entries from cache."""
        expired_parts = [k for k, v in self.parts.items() if v.is_expired()]
        expired_results = [k for k, v in self.vehicle_results.items() if v.is_expired()]

        for key in expired_parts:
            del self.parts[key]

        for key in expired_results:
            del self.vehicle_results[key]

        return len(expired_parts), len(expired_results)

    def clear_all(self) -> None:
        """Clear all cached data."""
        self.parts.clear()
        self.vehicle_results.clear()

    def get_cache_stats(self) -> Dict[str, Union[int, float]]:
        """Get statistics about the cache."""
        total_part_accesses = sum(p.access_count for p in self.parts.values())
        total_result_accesses = sum(r.access_count for r in self.vehicle_results.values())

        avg_part_accesses = total_part_accesses / len(self.parts) if self.parts else 0
        avg_result_accesses = total_result_accesses / len(self.vehicle_results) if self.vehicle_results else 0

        return {
            "cached_parts": len(self.parts),
            "cached_results": len(self.vehicle_results),
            "total_part_accesses": total_part_accesses,
            "total_result_accesses": total_result_accesses,
            "avg_part_accesses": round(avg_part_accesses, 2),
            "avg_result_accesses": round(avg_result_accesses, 2),
            "parts_capacity_used": round(len(self.parts) / self.max_parts * 100, 1),
            "results_capacity_used": round(len(self.vehicle_results) / self.max_results * 100, 1)
        }

    @staticmethod
    def generate_vehicle_cache_key(
        make: str,
        model: str,
        year: str,
        engine: Optional[str] = None,
        category: Optional[str] = None
    ) -> str:
        """Generate a consistent cache key for vehicle part searches."""
        key_parts = [make.lower(), model.lower(), year]
        if engine:
            key_parts.append(engine.lower())
        if category:
            key_parts.append(category.lower())
        return "|".join(key_parts)


class CacheConfiguration(BaseModel):
    """Configuration for part caching behavior."""

    enabled: bool = Field(default=True, description="Whether caching is enabled")
    part_ttl_hours: int = Field(default=12, description="TTL for individual parts in hours")
    result_ttl_hours: int = Field(default=12, description="TTL for search results in hours")
    max_parts: int = Field(default=1000, description="Maximum number of parts to cache")
    max_results: int = Field(default=100, description="Maximum number of search results to cache")
    auto_cleanup_interval: int = Field(default=3600, description="Auto cleanup interval in seconds")

    def create_cache(self) -> PartCache:
        """Create a new PartCache with this configuration."""
        return PartCache(
            max_parts=self.max_parts,
            max_results=self.max_results
        )