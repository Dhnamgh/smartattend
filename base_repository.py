"""
Base repository interface.
"""

from abc import ABC, abstractmethod
import pandas as pd


class BaseOGSMRepository(ABC):

    @abstractmethod
    def fetch_master_dataframe(self) -> pd.DataFrame:
        pass
