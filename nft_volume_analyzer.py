import pandas as pd
import requests
from loguru import logger
from typing import Dict, List, Optional
from config import Config

class NFTVolumeAnalyzer:
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.base_url = "https://api-mainnet.magiceden.dev/v2"
        
    def get_collection_stats(self, symbol: str) -> Dict:
        """Fetch collection statistics from Magic Eden."""
        try:
            response = requests.get(f"{self.base_url}/collections/{symbol}/stats")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching stats for {symbol}: {str(e)}")
            return {}

    def get_collection_listings(self, symbol: str) -> List[Dict]:
        """Fetch current listings for a collection."""
        try:
            response = requests.get(f"{self.base_url}/collections/{symbol}/listings")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching listings for {symbol}: {str(e)}")
            return []

    def analyze_collections(self, collections_df: pd.DataFrame) -> pd.DataFrame:
        """
        Analyze collections for thin floor opportunities.
        
        Args:
            collections_df: DataFrame with columns ['symbol', 'name', 'total_items']
        
        Returns:
            DataFrame with analyzed collections meeting criteria
        """
        analyzed_data = []
        
        for _, row in collections_df.iterrows():
            symbol = row['symbol']
            stats = self.get_collection_stats(symbol)
            listings = self.get_collection_listings(symbol)
            
            if not stats or not listings:
                continue
                
            floor_price = stats.get('floorPrice', 0) / 1e9  # Convert from lamports to SOL
            volume_7d = stats.get('volumeAll', 0) / 1e9
            listed_count = len(listings)
            
            # Calculate scarcity ratio
            scarcity_ratio = listed_count / row['total_items']
            
            # Check if collection meets our criteria
            if (volume_7d >= self.config.MIN_VOLUME_THRESHOLD and 
                scarcity_ratio <= self.config.MAX_SCARCITY_RATIO):
                
                analyzed_data.append({
                    'symbol': symbol,
                    'name': row['name'],
                    'floor_price': floor_price,
                    'volume_7d': volume_7d,
                    'listed_count': listed_count,
                    'scarcity_ratio': scarcity_ratio
                })
        
        return pd.DataFrame(analyzed_data)

    def get_profitable_listings(self, symbol: str, max_price: float) -> List[Dict]:
        """
        Get listings that are potentially profitable based on floor price.
        
        Args:
            symbol: Collection symbol
            max_price: Maximum price in SOL to consider
            
        Returns:
            List of profitable listings
        """
        listings = self.get_collection_listings(symbol)
        return [
            listing for listing in listings 
            if listing.get('price', float('inf')) / 1e9 <= max_price
        ] 