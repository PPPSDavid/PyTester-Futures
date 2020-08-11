from abc import ABC, abstractmethod
import event
from queue import Queue
import data_handler
import time
import copy
import toolss

class ScoringBasis(ABC):

    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def get_scoring(self, relevent_data, trading_contracts) -> list:
        return
    
    @abstractmethod
    def get_trading_set(self, relevent_data, trading_contracts, is_long_short) -> set:
        return
    
class TrendScore(ScoringBasis):
    def __init__(self, window_size, pool_size):
        self.window_size = window_size
        self.pool_size = pool_size
    
    def get_scoring(self, data, contracts) -> list:
        scoring_result = []
        for s in contracts:
            if (len(data[s][1]) < self.window_size):
                # Not enough data for this contract yet, skipping
                continue
            max_high = max(data[s][2])
            min_low = min(data[s][1])
            curr_close = data[s][0][-1]
            oldest_close = data[s][0][0]
            score = (curr_close - oldest_close) / (max_high - min_low)
            scoring_result.append((s, score))
        return scoring_result
    
    def get_trading_set(self, relevent_data, trading_contracts, is_long_short):
        scores = self.get_scoring(relevent_data, trading_contracts)
        # print(scores)
        scores = sorted(scores, key=lambda x: x[1], reverse=True)
        if not is_long_short:
            result = scores[:self.pool_size]
            new_contracts = set([i[0] for i in result])
            return (new_contracts,)
        else:
            longs = scores[:self.pool_size]
            shorts = scores[-1*self.pool_size:]
            longs = set([i[0] for i in longs])
            shorts = set([i[0] for i in shorts])
            return (longs, shorts)
        
        