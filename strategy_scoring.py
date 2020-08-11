""" 
Contains helper classes for strategy. 
"""
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
    
    def load_data(self, market_event : event.EventMarket) -> None:
        return
    
    @abstractmethod
    def get_scoring(self) -> list:
        return
    
    @abstractmethod
    def get_trading_set(self) -> set:
        return

class TrendScore(ScoringBasis):

    def __init__(self, trend_window, pool_size):
        super().__init__()
        self.prev_data = {}
        self.trend_window = trend_window
        self.pool_size = pool_size
        self.curr_trading_contracts = set()

    def load_data(self, market_event : event.EventMarket) -> None:
        curr_data = market_event.data
        self.curr_trading_contract = {}
        for s in curr_data:
            if (curr_data[s] != None):
                # Has data, consider trading it
                if (s not in self.curr_trading_contracts):
                    self.curr_trading_contracts.add(s)
                if (s not in self.prev_data):
                    # Unrecorded contract, add it to list
                    self.prev_data[s] = {}
                for name in curr_data[s]:
                    if (name not in self.prev_data[s].keys()):
                            self.prev_data[s][name] = []
                    if (name == 'Close'):
                        if len(self.prev_data[s][name]) == self.trend_window + 1:
                            self.prev_data[s][name].pop(0)
                        self.prev_data[s][name].append(curr_data[s][name])
                    elif name == 'High'or name == 'Low':
                        if len(self.prev_data[s][name]) == self.trend_window + 1:
                            self.prev_data[s][name].pop(0)
                        self.prev_data[s][name].append(curr_data[s][name])
    
    def get_scoring(self):
        scoring_result = []
        for s in self.curr_trading_contracts:
            if (len(self.prev_data[s]['High']) < self.trend_window):
                continue
            max_high = max(self.prev_data[s]['High'])
            min_low = min(self.prev_data[s]['Low'])
            curr_close = self.prev_data[s]['Close'][-1]
            oldest_close = self.prev_data[s]['Close'][0]
            score = (curr_close - oldest_close)/(max_high - min_low)
            scoring_result.append((s,score))
        return scoring_result
    
    def get_trading_set(self, long_short = False):
        scores = self.get_scoring()
        scores = sorted(scores, key=lambda x: x[1], reverse=True)
        if not long_short:
            result = scores[:self.pool_size]
            new_contracts = [i[0] for i in result]
            return (new_contracts,)
        else:
            longs = scores[:self.pool_size]
            shorts = scores[-1*self.pool_size:]
            longs = [i[0] for i in longs]
            shorts = [i[0] for i in shorts]
            return (longs, shorts)

