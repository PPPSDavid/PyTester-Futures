"""
Process order 
@author David Yu
"""

from abc import ABC
import event
from queue import Queue
import datetime
import copy
import data_handler
import strategy as st
import time
import portfolio
import toolss

class OrderBasis(ABC):
    def __init__(self):
        super().__init__()
    def perform_trading(self, event : event.EventMarket)-> event.EventFilled:
        """perform_trading takes in the latest market price, etc and attempt to furfill the currently cached order.

        Parameters
        ----------
        event : event.EventMarket
            input data

        Returns
        -------
        event.EventFilled
            filled confirmation
        """
        pass
    def process_order(self, order_event : event.EventOrder) :
        """process_order takes in an order generated by portfolio, temporarily store it and try to trade it when possible.

        Parameters
        ----------
        order_event : event.EventOrder
            [description]
        """
        pass
    
class SimpleOrder(OrderBasis):
    def __init__(self):
        super().__init__()
        self.curr_price = {}
        self.fee = 0
        self.tick = 0
        self.volume_information = {}
        self.tick_information = {}
        self.order_queue = None
    
    

    def calculate_price(self, amount: float, action: str, price:float, contract:str):
        """
        calculate_price returns the actual finished price (after adding tick in reverse direction)

        Parameters
        ----------
        amount : float
            amount in quantity if close, in cash if open
        action : str
            Close, Long or Short
        price : float
            The working price
        contract : str
            name of the contract
        """
        def get_ticked_price(amount, action, price):
            if contract not in self.tick_information:
                return price
            if (action == 'Close'):
                if amount > 0:
                    return (price - self.tick_information[contract] * self.tick) * (1-self.fee)
                else:
                    return (price + self.tick_information[contract] * self.tick) * (1+self.fee)
            elif action == 'Long':
                return (price + self.tick_information[contract] * self.tick) * (1+self.fee)
            elif action == 'Short':
                return (price - self.tick_information[contract] * self.tick) * (1-self.fee)
        return get_ticked_price(amount, action, price) 
            

    def perform_trading(self, input_event : event.EventMarket) -> event.EventFilled:
        data = input_event.data
        result = event.EventFilled()
        result.date = input_event.date
        for s in data.keys():
            if (data[s] is not None):
                self.curr_price[s] = data[s]['Open']
        if (self.order_queue is None):
            return result
        data = self.order_queue.data
        if len(data.keys()) == 0:
            return result
        for s in data.keys():
            action, amount = data[s]
            # If is close, amount is in unit, if buy, amount is cash

            op_price = self.calculate_price(amount, action, self.curr_price[s], s)
            multiplier = 1
            if s in self.volume_information:
                multiplier = self.volume_information[s]

            if action == 'Close':
                transaction_amount = amount * op_price
                result.write_data(s, action, amount, transaction_amount)
            elif action == 'Long':
                actual_transaction = int(amount / (op_price * multiplier)) * multiplier
                transaction_amount = actual_transaction * op_price 
                result.write_data(s, 'Open', actual_transaction, transaction_amount)
            elif action == 'Short':
                actual_transaction = -1 * int(amount / (op_price * multiplier)) * multiplier
                transaction_amount = actual_transaction * op_price 
                result.write_data(s, 'Open', actual_transaction, transaction_amount)
        
        return result
    
    def process_order(self, order_event : event.EventOrder):
        self.order_queue = order_event

class OrderWithFrition(SimpleOrder):
    def __init__(self, fee, tick):
        super().__init__()
        self.fee = fee
        self.tick = tick
        self.volume_information, self.tick_information = toolss.download_size_information()
    


if __name__ == "__main__":
    
    data = data_handler.EngineCSV()
    strategy = st.SimpleDonChain(window_size = 5, window_size_hl = 5)
    port = portfolio.SimplePortfolio()
    broker = OrderWithFrition(0,0.5)
    
    list_of_events = []
    list_of_signals = []
    list_of_orders = []
    list_of_filled = []
 
    for i in range(5):
        list_of_events.append(data.get_event())
        port.process_market(list_of_events[i])
        list_of_filled.append(broker.perform_trading(list_of_events[i]))
        port.process_filled(list_of_filled[i])
        strategy.load_data(list_of_events[i])
        list_of_signals.append(strategy.get_event())
        list_of_orders.append(port.process_signal(list_of_signals[i]))
        broker.process_order(list_of_orders[i])