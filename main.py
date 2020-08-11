"""
The main script containing the overall queue and event driving system
@author David Yu
"""

from abc import ABC
import event
from queue import Queue
import queue
import datetime
import copy
import data_handler
import event
import order_processing
import portfolio
import strategy
import time

def backtest(data_engine: data_handler.EngineBasis ,
 portfolio_engine : portfolio.PortfolioBasis , 
 strategy_engine : strategy.StrategyBasis, 
 order_process_engine : order_processing.OrderBasis, pool: Queue, limit = 100):
    """
    backtest is the main function to do backtest. it takes in 4 main engines and a shared data queue.
    no return is done, one should use portfolio object and other helper functions to obtain needed charts

    Parameters
    ----------
    data_engine : data_handler.EngineBasis
        datasource, produce a data event whenever the shared data queue is empty(no event unfinished)
    portfolio_engine : portfolio.PortfolioBasis
        keep tracks of the current position and records history(if needed), use signal to give real orders in Cash
    strategy_engine : strategy.StrategyBasis
        takes in market data, give out directional signals on how to trade
    order_process_engine : order_processing.OrderBasis
        clears the trade at actual market level (currently designed to be T+1 for daily trading to mimick actual workflow)
    pool : Queue
        The shared data structure where all the communication is done
    limit : int, optional
        for debug purpose, a maximium of iterations finshed before forcing a return, by default 100
    """
    count = 0
    while True:
        count += 1
        if (count == limit):
            break
        try:
            mkt = data_engine.get_event()
        except UserWarning:
            return
        pool.put(mkt)
        
        while True:
            event = None
            try:
                event = pool.get(block = False)
            except queue.Empty:
                break

            if event is not None:
                if event.type == 'Market':
                    # strategy takes it, broker takes it, portfolio takes it
                    portfolio_engine.process_market(event)
                    pool.put(order_process_engine.perform_trading(event))
                    strategy_engine.load_data(event)
                    pool.put(strategy_engine.get_event())
                elif event.type == 'Signal':
                    pool.put(portfolio_engine.process_signal(event))
                elif event.type == 'Order':
                    order_process_engine.process_order(event)
                elif event.type == 'Fill':
                    portfolio_engine.process_filled(event)

if __name__ == "__main__":
    list_of_symbols = ['i','j','hc','rb','jm','ZC']
    data = data_handler.EngineCSV()
    strategy = strategy.SimpleDonChain(window_size = 5, window_size_hl = 5)
    port = portfolio.SimplePortfolio()
    broker = order_processing.OrderWithFrition(0,0.5)
    pool = Queue()
    start = time.time()
    backtest(data, port, strategy, broker, pool)
    print(str(time.time() - start))
    # data = data_handler.EngineCSVSelected(list_of_symbols)
    # strategy = strategy.IndexScoreRecorder()
    # port = portfolio.SimplePortfolio()
    # broker = order_processing.OrderWithFrition(0,0)
    # pool = Queue()
    # start = time.time()
    # backtest(data, port, strategy, broker, pool)
    # print(str(time.time() - start))
    
    
