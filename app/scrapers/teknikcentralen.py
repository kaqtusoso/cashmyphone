"""
Teknikcentralen-scraper

Teknikcentralen (teknikcentralen.se) köper in begagnad teknik men har
INTE publika inköpspriser på sin webbplats — de använder ett kontaktformulär
på /pages/salj-din-iphone. Dynamisk prissättning sker via manuell hantering.

Status: INAKTIV – returnerar alltid tom lista.
Aktivera igen om de lägger till publik prislista i framtiden.
"""
import logging
from typing import List, Dict, Any
from .base import BaseScraper

logger = logging.getLogger(__name__)


class TeknikcentralenScraper(BaseScraper):
    retailer_id = "teknikcentralen"
    retailer_name = "Teknikcentralen"

    async def fetch_prices(self) -> List[Dict[str, Any]]:
        logger.info(
            "Teknikcentralen: ingen publik prislista — hoppar över. "
            "De använder kontaktformulär för inköp."
        )
        return []
