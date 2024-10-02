from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

import pandas as pd

from simulator.trade import Trade


class Strategy(ABC):
    def __init__(self, risk_to_reward: Optional[float] = None, iteration_data: Optional[Dict[str, Any]] = None):
        self.risk_to_reward = risk_to_reward
        self.iteration_data = iteration_data

    @abstractmethod
    def apply_signal(self, row: pd.Series, df: pd.DataFrame) -> Optional[Trade]:
        pass

