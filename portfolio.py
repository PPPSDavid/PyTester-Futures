""" 
Record position, issue trading event, record filled trading events
"""

from abc import ABC
import event
from queue import Queue
import datetime
import copy
import data_handler
import strategy as st
import time

class PortfolioBasis(ABC):
    def __init__(self):
        super().__init__()
    
    def process_signal(self, input_event: event.EventSignal) -> event.EventOrder:
        """process_signal takes in a signal and issue corresponding trading instruction to executor

        Parameters
        ----------
        input_event : event.EventSignal
            A signal event

        Returns
        -------
        result : event.EventOrder
            Execution instruction
        """
        return None
    
    def process_market(self, market_event : event.EventMarket):
        """process_market takes in a market event and record its price information
        (Only to calculate the instantanious wealth, no other use, so one can omit this)

        Parameters
        ----------
        market_event : event.EventMarket
            a market event
        """
        pass

    def process_filled(self, filled_event: event.EventFilled):
        """process_filled updates portfolio holdings based on filled transaction

        Parameters
        ----------
        filled_event : event.EventFilled
            confirmation from executor
        """
        pass

class SimplePortfolio(PortfolioBasis):

    def __init__(self, initial_cash = 10000000):
        super().__init__()
        self.curr_day = None
        self.current_portfolio = {}
        self.previous_portfolio_recorder = {}
        self.cash = initial_cash
        self.wealth = initial_cash
        self.current_price = {}
        self.previous_wealth_recorder = {}
        self.date = ''
        self.prev_date = ''
    
    def process_signal(self, input_event: event.EventSignal) -> event.EventOrder:
        """process_signal takes in a signal and issue corresponding trading instruction to executor

        Parameters
        ----------
        input_event : event.EventSignal
            A signal event

        Returns
        -------
        result : event.EventOrder
            Execution instruction
        """
        result = event.EventOrder()
        recorded_contracts = self.current_portfolio.keys()
        order_book = {}
        short_num = 0
        long_num = 0
        for s in input_event.data.keys():
            signals = input_event.data[s]
            if (len(signals) == 0):
                # No trading Signal
                continue
            elif (len(signals) == 1):
                # Single directional Signal
                if (signals[0]) == 0:
                    if (self.current_portfolio == None or not (s in recorded_contracts) or self.current_portfolio[s] == 0):
                        continue
                    else:
                        order_book[s] = ('Close', self.current_portfolio[s])
                elif signals[0] > 0:
                    if (self.current_portfolio == None):
                        self.current_portfolio = {}
                    if (not (s in recorded_contracts)):
                        self.current_portfolio[s] = 0
                    if (self.current_portfolio[s] > 0):
                        continue
                    elif (self.current_portfolio[s] < 0):
                        order_book[s] = ('Close', self.current_portfolio[s])
                    else:
                        order_book[s] = ('Long', 0)
                        long_num += 1
                
                else:
                    if (self.current_portfolio == None):
                        self.current_portfolio = {}
                    if (not (s in recorded_contracts)):
                        self.current_portfolio[s] = 0
                    if (self.current_portfolio[s] < 0):
                        continue
                    elif (self.current_portfolio[s] > 0):
                        order_book[s] = ('Close', self.current_portfolio[s])
                    else:
                        order_book[s] = ('Short', 0)
                        short_num += 1
                        
        if long_num + short_num == 0:
            per_contract_cash = 0
        else:
            per_contract_cash = self.cash/ (long_num + short_num)
        for s in order_book.keys():
            action, amount = order_book[s]
            if (action == 'Close'):
                result.write_data(s,action,amount)
            else:
                result.write_data(s,action,per_contract_cash)
        return result


    def process_market(self, market_event : event.EventMarket):
        self.prev_date = self.date
        self.date = market_event.date
        curr_data  = market_event.data
        for s in curr_data:
            if (curr_data[s] != None):
                self.current_price[s] = curr_data[s]['Open']
    
    def process_filled(self, filled_event: event.EventFilled):
        """process_filled updates portfolio holdings based on filled transaction

        Parameters
        ----------
        filled_event : event.EventFilled
            confirmation from executor
        """
        # Save current portfolio to past
        self.previous_portfolio_recorder[self.prev_date] = copy.deepcopy(self.current_portfolio)
        self.previous_wealth_recorder[self.prev_date] = self.wealth
        
        data = filled_event.data
        self.date = filled_event.date
        contracts = data.keys()
        for s in contracts:
            action, amount, cash = data[s]
            if action == 'Close':
                self.cash += cash
            else:
                self.cash -= cash
            if (action == 'Open'):
                self.current_portfolio[s] = amount
            elif (action == 'Close'):
                self.current_portfolio[s] = 0
        self.wealth = self.cash
        for s in self.current_portfolio:
            self.wealth += self.current_portfolio[s] * self.current_price[s]
                
                
if __name__ == "__main__":
    data = data_handler.EngineCSV()
    strategy = st.SimpleDonChain(window_size = 5, window_size_hl = 5)
    port = SimplePortfolio()
    list_of_events = []
    list_of_signals = []
    list_of_orders = []
    start_time = time.time()
    for i in range(5):
        list_of_events.append(data.get_event())
        strategy.load_data(list_of_events[i])
        list_of_signals.append(strategy.get_event())
        list_of_orders.append(port.process_signal(list_of_signals[i]))
    print("--- %s seconds ---" % (time.time() - start_time))
    
    
    

    