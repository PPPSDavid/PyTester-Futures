""" 
The logic of which to trade
"""
from abc import ABC, abstractmethod
import event
from queue import Queue
import data_handler
import time
import copy
import toolss
import strategy_scoring as scoring
import strategy_scoring_lite as scoring_lte

class StrategyBasis(ABC):

    def __init__(self):
        super().__init__()
    
    def load_data(self, market_event : event.EventMarket) -> None:
        return
    
    @abstractmethod
    def get_event(self) -> event.EventSignal:
        return
    
class DataRecordingBasis(StrategyBasis):
    def __init__(self):
        super().__init__()
    
    def load_data(self, market_event : event.EventMarket) -> None:
        return
    
    @abstractmethod
    def get_event(self) -> event.EventSignal:
        return
    
    def get_data(self) -> dict:
        return {}
    

class IndexScoreRecorder(DataRecordingBasis):

    def __init__(self):
        super().__init__()
        self.prev_data = {}
        self.prev_indexed = {}
        self.indexed_data_recorder = {}
        self.pct_change_recorder = {}
        self.index = 1000
        self.curr_date = ''
    
    def load_data(self, market_event : event.EventMarket) -> None:
        self.indexed_data_recorder[self.curr_date] = copy.deepcopy(self.prev_indexed)
        self.indexed_data_recorder[self.curr_date]['Index'] = self.index
        self.curr_date = market_event.date
        curr_data = market_event.data
        index_change = 0
        count = 0
        curr_pct_changes = {}
        for s in curr_data:
            if (curr_data[s] != None):
                if (s not in self.prev_data):
                    self.prev_data[s] = curr_data[s]['Close']
                else:
                    pct_change = (curr_data[s]['Close'] - self.prev_data[s]) / self.prev_data[s]
                    curr_pct_changes[s] = pct_change
                    index_change += pct_change
                    count += 1
                    self.prev_data[s] = curr_data[s]['Close']
        if (index_change != 0):
            index_change = index_change / count # Simple Averaging
        self.pct_change_recorder[self.curr_date] = copy.deepcopy(curr_pct_changes)
        self.pct_change_recorder[self.curr_date]['Index'] = index_change
        for s in curr_pct_changes:
            if s not in self.prev_indexed:
                self.prev_indexed[s] = self.index
            self.prev_indexed[s] = self.prev_indexed[s] * (1+curr_pct_changes[s])
        self.index = self.index * (1+index_change)
    
    def get_event(self):
        result = event.EventSignal()
        result.date = self.curr_date
        return result
    
    def get_data(self):
        return self.indexed_data_recorder
    
    def get_pct_data(self):
        return self.pct_change_recorder

class SimpleDonChain(StrategyBasis):

    def __init__(self, window_size, window_size_hl):
        super().__init__()
        self.prev_data = {}
        self.winsize = window_size
        self.winsizehl = window_size_hl
        self.curr_trading_contracts = set()
        self.curr_date = ''
    
    def load_data(self, market_event : event.EventMarket) -> None:
        self.curr_date = market_event.date
        curr_data = market_event.data
        for s in curr_data:
            if (curr_data[s] != None):
                # Has data, consider trading it
                
                if (s not in self.curr_trading_contracts):
                    self.curr_trading_contracts.add(s)
                    
                if (s not in self.prev_data):
                    # Unrecorded contract, add it to list
                    self.prev_data[s] = {'Close': [], 'High':[], 'Low':[]}
                    
                for name in curr_data[s]:
                            
                    if (name == 'Close'):
                        if len(self.prev_data[s][name]) == self.winsize + 1:
                            self.prev_data[s][name].pop(0)
                        self.prev_data[s][name].append(curr_data[s][name])
                        
                    elif name == 'High'or name == 'Low':
                        if len(self.prev_data[s][name]) == self.winsizehl + 1:
                            self.prev_data[s][name].pop(0)
                        self.prev_data[s][name].append(curr_data[s][name])                    
    
    def get_dc_signal(self,high_band, low_band, mid_band, curr_high, curr_mid, curr_low):
        signals = []
        if (curr_high >= high_band):
            signals.append(1)
        elif (curr_low <= low_band):
            signals.append(-1)
        if (mid_band >= curr_low and mid_band <= curr_high):
            if (len(signals) != 0):
                signals[0] = 0
            else:
                signals.append(0)
        return signals

    def get_event(self)-> event.EventSignal:
        result = event.EventSignal()
        result.date = self.curr_date
        for s in self.curr_trading_contracts:
            signals = []
            high_lst = self.prev_data[s]['High'][:-1]
            curr_high = self.prev_data[s]['High'][-1]
            low_lst = self.prev_data[s]['Low'][:-1]
            curr_low = self.prev_data[s]['Low'][-1]
            mid_lst = self.prev_data[s]['Close'][:-1]
            curr_mid = self.prev_data[s]['Close'][-1]
            # if len(mid_lst) < self.winsize or len(high_lst) < self.winsizehl:
            #     result.write_data(s,signals)
            #     return result
            if len(high_lst) == 0 or len(mid_lst) == 0:
                return result
            high_band = max(high_lst)
            low_band = min(low_lst)
            mid_band = sum(mid_lst) / len(mid_lst)
            signals = self.get_dc_signal(high_band, low_band, mid_band, curr_high, curr_mid, curr_low)
            result.write_data(s,signals)
        return result

class SelectiveDonChain(SimpleDonChain):
    def __init__(self, window_size, window_size_hl, ttrend_window, selection_pool, selection_window):
        super().__init__(window_size, window_size_hl)
        self.ttrend_window = ttrend_window
        self.selection_pool = selection_pool
        self.selection_window = selection_window
        self.counter = 0
        self.selected_contracts = []
    def load_data(self, market_event : event.EventMarket) -> None:
        super().load_data(market_event)
        curr_data = market_event.data
        for s in curr_data:
            if (curr_data[s] != None):
                for name in curr_data[s]:      
                    if (name == 'Close'):
                        if (('Trend_' +name) not in self.prev_data[s].keys()):
                            # Also record it in trend part
                            self.prev_data[s]['Trend_' + name] = []
                        if len(self.prev_data[s][('Trend_' +name)]) == self.ttrend_window + 1:
                            self.prev_data[s]['Trend_' +name].pop(0)
                        self.prev_data[s]['Trend_' +name].append(curr_data[s][name])    
                    elif name == 'High'or name == 'Low':
                        if (('Trend_' + name) not in self.prev_data[s].keys()):
                            # Also record it in trend part
                            self.prev_data[s]['Trend_' + name] = []
                        if len(self.prev_data[s][('Trend_' + name)]) == self.ttrend_window + 1:
                            self.prev_data[s]['Trend_'  + name].pop(0)
                        self.prev_data[s]['Trend_' + name].append(curr_data[s][name])
    
    def get_score_trend(self,s:str):
        curr_close = self.prev_data[s]['Trend_Close'][-1]
        oldest_close = self.prev_data[s]['Trend_Close'][0]
        max_high = max(self.prev_data[s]['Trend_High'])
        min_low = min(self.prev_data[s]['Trend_Low'])
        score = (curr_close - oldest_close)/(max_high - min_low)
        return score
    
    def get_event(self)-> event.EventSignal:
        result = event.EventSignal()
        result.date = self.curr_date
        # When reached time to switch trading pool, run following
        if self.counter == 0:
            scores = []
            for s in self.curr_trading_contracts:
                if (len(self.prev_data[s]['Trend_Close']) < self.ttrend_window):
                    # Skipping those contract which has insufficient past data for trend window
                    continue
                # Calculate the trend score
                score = self.get_score_trend(s)
                scores.append((s,score))
            scores = sorted(scores, key=lambda x: x[1], reverse=True)[:self.selection_pool]
            new_contracts = [i[0] for i in scores]
            # Issue close markert order to all contracts no longer traded
            no_longer_traded = set(self.selected_contracts) - set(new_contracts)
            for s in no_longer_traded:
                signals = [0]
                result.write_data(s, signals)

            # switch to newly selected pool
            self.selected_contracts = new_contracts
        
        # Perform normal day-to-day trading
        for s in self.selected_contracts:
            signals = []
            high_lst = self.prev_data[s]['High'][:-1]
            curr_high = self.prev_data[s]['High'][-1]
            low_lst = self.prev_data[s]['Low'][:-1]
            curr_low = self.prev_data[s]['Low'][-1]
            mid_lst = self.prev_data[s]['Close'][:-1]
            curr_mid = self.prev_data[s]['Close'][-1]
            # if len(mid_lst) < self.winsize or len(high_lst) < self.winsizehl:
            #     result.write_data(s,signals)
            #     return result
            if len(high_lst) == 0 or len(mid_lst) == 0:
                return result
            high_band = max(high_lst)
            low_band = min(low_lst)
            mid_band = sum(mid_lst) / len(mid_lst)
            signals = super().get_dc_signal(high_band, low_band, mid_band, curr_high, curr_mid, curr_low)
            result.write_data(s,signals)
        self.counter += 1
        if self.counter == self.selection_window:
            self.counter = 0
        return result


class SimpleHedge(StrategyBasis):

    def __init__(self, selection_pool_size, scoing_window):
        super().__init__()
        self.selection_pool_size = selection_pool_size
        self.curr_date = ''
        self.trend_score = scoring.TrendScore(scoing_window, selection_pool_size)
        self.prev_long = []
        self.prev_short = []

    def load_data(self, market_event : event.EventMarket) -> None:
        self.curr_date = market_event.date
        self.trend_score.load_data(market_event)
    
    def get_event(self) -> event.EventSignal:
        result = event.EventSignal()
        result.date = self.curr_date
        longs,shorts = self.trend_score.get_trading_set(long_short = True)
        for s in longs:
            signals = [1]
            result.write_data(s, signals)
        for s in shorts:
            signals = [-1]
            result.write_data(s, signals)
        changed_longs = list(set(self.prev_long)-set(longs))
        for s in changed_longs:
            signals = [0]
            result.write_data(s, signals)
        changed_shorts = list(set(self.prev_short)-set(shorts))
        for s in changed_shorts:
            signals = [0]
            result.write_data(s, signals)
        self.prev_long = longs
        self.prev_short = shorts
        return result

class SimpleHedgeLite(StrategyBasis):
    def __init__(self, selection_pool_size, scoing_window):
        super().__init__()
        self.selection_pool_size = selection_pool_size
        self.curr_date = ''
        self.trend_score = scoring_lte.TrendScore(scoing_window, selection_pool_size)
        self.prev_long = set()
        self.prev_short = set()
        self.window = scoing_window
        self.prev_data = {}
    
    def load_data(self, market_event : event.EventMarket) -> None:
        self.curr_date = market_event.date
        curr_data = market_event.data
        self.curr_trading_contracts = set()
        for s in curr_data:
            if (curr_data[s] != None):
                # Has data, consider trading it
                self.curr_trading_contracts.add(s)

                if (s not in self.prev_data):
                    # Unrecorded contract, add it to list
                    self.prev_data[s] = [[],[],[]]
                    
                for name in curr_data[s]:

                    if (name == 'Close'):
                        if len(self.prev_data[s][0]) == self.window + 1:
                            self.prev_data[s][0].pop(0)
                        self.prev_data[s][0].append(curr_data[s][name])
                        
                    elif name == 'High'or name == 'Low':
                        temp = 1
                        if name == 'High':
                            temp = 2
                        if len(self.prev_data[s][temp]) == self.window + 1:
                            self.prev_data[s][temp].pop(0)
                        self.prev_data[s][temp].append(curr_data[s][name])  
    
    def get_event(self):
        result = event.EventSignal()
        result.date = self.curr_date
        longs,shorts = self.trend_score.get_trading_set(self.prev_data, self.curr_trading_contracts, is_long_short = True)
        for s in longs:
            signals = [1]
            result.write_data(s, signals)
        for s in shorts:
            signals = [-1]
            result.write_data(s, signals)
        changed_longs = ((self.prev_long)-(longs))
        for s in changed_longs:
            signals = [0]
            result.write_data(s, signals)
        changed_shorts = (self.prev_short-shorts)
        for s in changed_shorts:
            signals = [0]
            result.write_data(s, signals)
        self.prev_long = longs
        self.prev_short = shorts
        return result
    
    



if __name__ == "__main__" :
    # list_of_symbols = ['i','rb','hc','j','jm','ZC', 'SM', 'FG']
    # list_of_symbols = ['cu','al','zn','ni','pb','ag']
    # list_of_symbols = ['sc','fu','bu','TA','pp','v','l','MA','eg','ru']
    # data = data_handler.EngineCSVSelected(list_of_symbols)
    # strategy = IndexScoreRecorder()
    # list_of_events = []
    # list_of_signals = []
    # start_time = time.time()
    # i = 0
    # while True:
    #     try:
    #         list_of_events.append(data.get_event())
    #         strategy.load_data(list_of_events[i])
    #         i += 1
    #     except UserWarning: 
    #         break
    # result = strategy.get_pct_data()
    # # result = strategy.get_data()
    # formatted = toolss.data_export_csv(result)
    # print("--- %s seconds ---" % (time.time() - start_time))
    
    
    # data = data_handler.EngineCSV()
    # strategy = SelectiveDonChain(window_size = 5, window_size_hl = 5, ttrend_window = 5, selection_pool = 5, selection_window = 5)
    # list_of_events = []
    # list_of_signals = []
    # list_of_orders = []
    # start_time = time.time()
    # for i in range(50):
    #     list_of_events.append(data.get_event())
    #     strategy.load_data(list_of_events[i])
    #     list_of_signals.append(strategy.get_event())
    # print("--- %s seconds ---" % (time.time() - start_time))
            

    data = data_handler.EngineCSV()
    strategy = SimpleHedgeLite(5,3)
    list_of_events = []
    list_of_signals = []
    list_of_orders = []
    start_time = time.time()
    for i in range(50):
        list_of_events.append(data.get_event())
        strategy.load_data(list_of_events[i])
        list_of_signals.append(strategy.get_event())
    print("--- %s seconds ---" % (time.time() - start_time))
    
    data = data_handler.EngineCSV()
    strategy = SimpleHedge(5,3)
    list_of_events = []
    list_of_signals = []
    list_of_orders = []
    start_time = time.time()
    for i in range(50):
        list_of_events.append(data.get_event())
        strategy.load_data(list_of_events[i])
        list_of_signals.append(strategy.get_event())
    print("--- %s seconds ---" % (time.time() - start_time))
            