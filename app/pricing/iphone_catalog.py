from typing import Iterable, List, Optional


# Official storage capacities, in GB, for iPhone models Televera currently sees
# in buyback data. Keep this list conservative: scraper rows outside these
# capacities are usually buyer-site typos or generic calculator fallbacks.
VALID_STORAGE_BY_MODEL_GB: dict[str, tuple[int, ...]] = {
    "iphone 17e": (256, 512),
    "iphone air": (256, 512, 1024),
    "iphone 17 pro max": (256, 512, 1024, 2048),
    "iphone 17 pro": (256, 512, 1024),
    "iphone 17": (256, 512),
    "iphone 16e": (128, 256, 512),
    "iphone 16 pro max": (256, 512, 1024),
    "iphone 16 pro": (128, 256, 512, 1024),
    "iphone 16 plus": (128, 256, 512),
    "iphone 16": (128, 256, 512),
    "iphone 15 pro max": (256, 512, 1024),
    "iphone 15 pro": (128, 256, 512, 1024),
    "iphone 15 plus": (128, 256, 512),
    "iphone 15": (128, 256, 512),
    "iphone 14 pro max": (128, 256, 512, 1024),
    "iphone 14 pro": (128, 256, 512, 1024),
    "iphone 14 plus": (128, 256, 512),
    "iphone 14": (128, 256, 512),
    "iphone 13 pro max": (128, 256, 512, 1024),
    "iphone 13 pro": (128, 256, 512, 1024),
    "iphone 13 mini": (128, 256, 512),
    "iphone 13": (128, 256, 512),
    "iphone 12 pro max": (128, 256, 512),
    "iphone 12 pro": (128, 256, 512),
    "iphone 12 mini": (64, 128, 256),
    "iphone 12": (64, 128, 256),
    "iphone se 2022": (64, 128, 256),
    "iphone se 2020": (64, 128, 256),
    "iphone 11 pro max": (64, 256, 512),
    "iphone 11 pro": (64, 256, 512),
    "iphone 11": (64, 128, 256),
    "iphone xs max": (64, 256, 512),
    "iphone xs": (64, 256, 512),
    "iphone xr": (64, 128, 256),
    "iphone x": (64, 256),
    "iphone 8 plus": (64, 128, 256),
    "iphone 8": (64, 128, 256),
    "iphone 7 plus": (32, 128, 256),
    "iphone 7": (32, 128, 256),
}


def _key(model: str) -> str:
    return " ".join((model or "").lower().split())


def valid_storage_options_for_model(model: str) -> Optional[List[int]]:
    options = VALID_STORAGE_BY_MODEL_GB.get(_key(model))
    return list(options) if options else None


def is_valid_storage_for_model(model: str, storage_gb: Optional[int]) -> bool:
    options = valid_storage_options_for_model(model)
    if options is None:
        return True
    return storage_gb in options


def filter_storage_options(model: str, storages: Iterable[Optional[int]]) -> List[int]:
    valid_options = valid_storage_options_for_model(model)
    unique = {storage for storage in storages if storage is not None}
    if valid_options is None:
        return sorted(unique)
    return [storage for storage in valid_options if storage in unique]
