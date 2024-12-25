import asyncio
import pandas as pd
from loguru import logger
from nft_volume_analyzer import NFTVolumeAnalyzer
from nft_trading_executor import NFTTradingExecutor
from config import Config

async def fetch_collections() -> pd.DataFrame:
    """
    Fetch initial collection data for analysis.
    In a production environment, this would fetch from a more comprehensive source.
    """
    # Example collections - in production, fetch from an API or database
    return pd.DataFrame([
        {"symbol": "degods", "name": "DeGods", "total_items": 10000},
        {"symbol": "okay_bears", "name": "Okay Bears", "total_items": 10000},
        # Add more collections as needed
    ])

async def main():
    try:
        # Initialize configuration
        config = Config()
        config.validate()
        
        # Initialize components
        analyzer = NFTVolumeAnalyzer(config)
        executor = NFTTradingExecutor(config)
        
        while True:  # Continuous monitoring loop
            try:
                # Fetch and analyze collections
                collections_df = await fetch_collections()
                analyzed = analyzer.analyze_collections(collections_df)
                
                if analyzed.empty:
                    logger.info("No collections meeting criteria found")
                    continue
                
                # Log analysis results
                logger.info(f"Found {len(analyzed)} collections meeting criteria:")
                for _, collection in analyzed.iterrows():
                    logger.info(
                        f"Collection: {collection['name']}, "
                        f"Floor: {collection['floor_price']:.2f} SOL, "
                        f"Volume 7d: {collection['volume_7d']:.2f} SOL, "
                        f"Scarcity: {collection['scarcity_ratio']:.2%}"
                    )
                
                # Check each collection for buying opportunities
                for _, collection in analyzed.iterrows():
                    floor_listings = await executor.fetch_floor_listings(collection['symbol'])
                    
                    if not floor_listings:
                        continue
                        
                    # Find listings below our maximum price
                    profitable_listings = [
                        listing for listing in floor_listings
                        if listing['price'] / 1e9 <= config.MAX_PRICE_SOL
                    ]
                    
                    for listing in profitable_listings:
                        price_in_sol = listing['price'] / 1e9
                        logger.info(f"Attempting to buy {collection['name']} at {price_in_sol} SOL")
                        
                        success = await executor.execute_buy(
                            listing['mintAddress'],
                            price_in_sol
                        )
                        
                        if success:
                            logger.success(
                                f"Successfully bought {collection['name']} "
                                f"NFT for {price_in_sol} SOL"
                            )
                            break  # Move to next collection after successful purchase
                
            except Exception as e:
                logger.error(f"Error in main loop: {str(e)}")
                
            # Wait before next iteration
            await asyncio.sleep(60)  # Adjust timing based on your needs
            
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
    finally:
        await executor.close()

if __name__ == "__main__":
    asyncio.run(main())
