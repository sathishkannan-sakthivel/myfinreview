from abc import ABC, abstractmethod

class BaseProvider(ABC):
    @abstractmethod
    def get_price(self, symbol: str) -> float:
        pass

    @abstractmethod
    def get_batch_prices(self, symbols: list) -> dict:
        pass
