import os
from dotenv import load_dotenv
from loguru import logger

# Load environment variables from .env file
load_dotenv()

class Config:
    def __init__(self):
        # API Configuration
        self.RPC_ENDPOINT = os.getenv('SOLANA_RPC_ENDPOINT', 'https://api.mainnet-beta.solana.com')
        
        # Trading Parameters
        self.MIN_VOLUME_THRESHOLD = float(os.getenv('MIN_VOLUME_THRESHOLD', '10.0'))  # Minimum 7-day volume in SOL
        self.MAX_SCARCITY_RATIO = float(os.getenv('MAX_SCARCITY_RATIO', '0.1'))  # Maximum ratio of listed/total items
        self.MAX_PRICE_SOL = float(os.getenv('MAX_PRICE_SOL', '10.0'))  # Maximum price to pay for an NFT
        
        # Wallet Configuration
        self.PRIVATE_KEY = self._get_private_key()
        
        # Logging Configuration
        logger.add(
            "logs/trading_{time}.log",
            rotation="1 day",
            retention="1 week",
            level="INFO"
        )
        
    def _get_private_key(self) -> bytes:
        """Get private key from environment variables."""
        key = os.getenv('SOLANA_PRIVATE_KEY')
        if not key:
            raise ValueError("SOLANA_PRIVATE_KEY environment variable is required")
            
        try:
            # Convert string of comma-separated values to bytes
            return bytes([int(x) for x in key.split(',')])
        except Exception as e:
            raise ValueError(f"Invalid private key format: {str(e)}")
            
    def validate(self):
        """Validate configuration settings."""
        required_vars = [
            ('SOLANA_RPC_ENDPOINT', self.RPC_ENDPOINT),
            ('SOLANA_PRIVATE_KEY', self.PRIVATE_KEY),
        ]
        
        missing = [var for var, val in required_vars if not val]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
            
        if self.MIN_VOLUME_THRESHOLD <= 0:
            raise ValueError("MIN_VOLUME_THRESHOLD must be positive")
            
        if not (0 < self.MAX_SCARCITY_RATIO <= 1):
            raise ValueError("MAX_SCARCITY_RATIO must be between 0 and 1") 