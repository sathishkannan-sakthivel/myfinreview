from sqlmodel import Session, select
from database import engine
from models.portable_models import PriceCache
from services.reference_data_service import ReferenceDataService
from services.portable_price_service import PortablePriceService

def cleanup_price_cache():
    print("Starting Name Cleanup for PriceCache...")
    ref_service = ReferenceDataService()
    
    with Session(engine) as session:
        price_service = PortablePriceService(session)
        
        # 1. Get all symbols in cache
        statement = select(PriceCache)
        cached_items = session.exec(statement).all()
        
        updated_count = 0
        for item in cached_items:
            # Check if name is missing or just the symbol
            if not item.name or item.name.strip().upper() == item.symbol.strip().upper():
                print(f"Resolving name for: {item.symbol}...")
                new_name = ref_service.get_asset_name(item.symbol)
                
                if new_name and new_name.strip().upper() != item.symbol.strip().upper():
                    item.name = new_name
                    session.add(item)
                    updated_count += 1
                    print(f" -> Updated to: {new_name}")
                else:
                    print(f" -> No professional name found for {item.symbol}")
        
        session.commit()
        print(f"Cleanup complete! Updated {updated_count} names.")

if __name__ == "__main__":
    cleanup_price_cache()
