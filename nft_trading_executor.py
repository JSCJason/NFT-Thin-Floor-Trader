import aiohttp
from solana.rpc.async_api import AsyncClient
from solana.transaction import Transaction
from solana.publickey import PublicKey
from solana.keypair import Keypair
from loguru import logger
from typing import Dict, List, Optional
from config import Config

class NFTTradingExecutor:
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.base_url = "https://api-mainnet.magiceden.dev/v2"
        self.session = aiohttp.ClientSession()
        self.client = AsyncClient(self.config.RPC_ENDPOINT)
        self.wallet = Keypair.from_secret_key(bytes(self.config.PRIVATE_KEY))

    async def close(self):
        """Close aiohttp session."""
        await self.session.close()
        await self.client.close()

    async def fetch_floor_listings(self, symbol: str) -> List[Dict]:
        """Fetch floor listings for a collection."""
        try:
            async with self.session.get(f"{self.base_url}/collections/{symbol}/listings") as response:
                if response.status == 200:
                    listings = await response.json()
                    return sorted(listings, key=lambda x: x.get('price', float('inf')))
                return []
        except Exception as e:
            logger.error(f"Error fetching floor listings for {symbol}: {str(e)}")
            return []

    async def execute_buy(self, mint_address: str, price_in_sol: float) -> bool:
        """
        Execute a buy transaction on Magic Eden.
        
        Args:
            mint_address: NFT mint address
            price_in_sol: Price in SOL
            
        Returns:
            bool: Whether the transaction was successful
        """
        try:
            # Get buy instructions from Magic Eden API
            async with self.session.get(
                f"{self.base_url}/instructions/buy",
                params={
                    "buyer": str(self.wallet.public_key),
                    "seller": mint_address,
                    "price": int(price_in_sol * 1e9)  # Convert SOL to lamports
                }
            ) as response:
                if response.status != 200:
                    logger.error(f"Failed to get buy instructions: {await response.text()}")
                    return False
                    
                instruction_data = await response.json()

            # Create and sign transaction
            transaction = Transaction()
            for ix in instruction_data['instructions']:
                # Convert instruction data to Solana format
                program_id = PublicKey(ix['programId'])
                accounts = [
                    {'pubkey': PublicKey(acc['pubkey']), 'isSigner': acc['isSigner'], 'isWritable': acc['isWritable']}
                    for acc in ix['accounts']
                ]
                data = bytes(ix['data'])
                
                transaction.add(program_id, accounts, data)

            # Sign and send transaction
            signature = await self.client.send_transaction(
                transaction, 
                self.wallet,
                opts={"skip_confirmation": False, "preflight_commitment": "confirmed"}
            )
            
            logger.info(f"Buy transaction successful: {signature['result']}")
            return True

        except Exception as e:
            logger.error(f"Error executing buy transaction: {str(e)}")
            return False 