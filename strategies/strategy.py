from abc import ABC, abstractmethod
from typing import Optional

import pandas as pd

from strategies.Trade import Trade


class Strategy(ABC):
    def __init__(self, risk_to_reward: float):
        self.risk_to_reward = risk_to_reward

    @abstractmethod
    def apply_signal(self, row: pd.Series, df: pd.DataFrame) -> Optional[Trade]:
        pass

