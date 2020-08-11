""" 
The "language" used between components
"""
from abc import ABC


class EventBase(ABC):
    """
    Event base class, has type
    A object to carry information between different engines

    Attributes:
        type : str
            market, signal, order, filled
        date : str
            when this event is created (str)
    """

    def __init__(self):
        """
        Initialize a Event class with type and date field
        """
        super().__init__()
        self.type = 'None'
        self.date = ''

    def get_type(self):
        """
        returns the type of this event

        Returns
        -------
        type: str, the type of this event
        """
        return self.type


class EventMarket(EventBase):
    """
    EventMarket, an event containing market information
    All daily data are stored as dictionary of dictionary, first dict by contract second by o,h,l,c,etc

    Attributes:
        type : str
            market, signal, order, filled
        date : str
            when this event is created (str)
        data : dict
            key is product id, value is an inner dict with key o,h,l,c,etc
    """

    def __init__(self):
        super().__init__()
        self.type = 'Market'
        self.date = ''
        self.data = {}

    def write_date(self, date: str) -> None:
        """write_date writes date to object

        Parameters
        ----------
        date : str
            date (string)
        """
        self.date = date

    def write_data(self, contract: str, dict_of_data: dict) -> None:
        """
        write_data writes the price volume data of a contract into this event

        Parameters
        ----------
        contract : str
            the contract name
        dict_of_data : dict
            the actual data
        """
        self.data[contract] = dict_of_data


class EventSignal(EventBase):
    """
    EventSignal, a event for strategy engine to send out buy/sell, open/close position signal for ALL contracts

    Attributes:
        type : str
            market, signal, order, filled
        date : str
            when this event is created (str)
        data : dict
            key is product id, value is a list of integer representing corresonding orders
    """

    def __init__(self):
        """
        __init__ intialize a signal event
        """
        super().__init__()
        self.type = 'Signal'
        self.date = ''
        self.data = {}

    def write_data(self, contract: str, signal: list) -> None:
        """
        write_data writes the signal and corresponding contract to data

        Parameters
        ----------
        contract : str
            contract name
        signal : list
            name of the signal, 0: close, 1: long, -1: short
            Note: current implementation of strategy class returns at most ONE signal per event, but in theory there can be multiple signals.
            Dealing with multiple/conflicting signals can be done either here or at strategy or at portfolio.
        """
        self.data[contract] = signal


class EventOrder(EventBase):
    """
    EventOrder contains order specification from portfolio to executer
    
    
    Attributes:
        type : str
            market, signal, order, filled
        data : dict
            key is product id, value is a list of tuples (action, amount).
    """

    def __init__(self):
        super().__init__()
        self.type = 'Order'
        self.data = {}

    def write_data(self, contract: str, action: str, amount: int) -> None:
        """
        write_data writes the action and corresponding amount of action to the event object

        Parameters
        ----------
        contract : str
            name of contract
        action : str
            what action to be performed
        amount : int
            how much this action need to be performed
        
        Note : for calculation efficiency, amount field carries cash value when it is a open position order, it carries position value when it is a closing order
        """
        self.data[contract] = (action, amount)


class EventOrderInterDay(EventOrder):

    def __init__(self):
        super().__init__()
        self.price = {}
    
    def write_price(self, contract, price: int) -> None:
        self.price[contract] = price

class EventFilled(EventOrder):
    """
    EventFilled contains the confirmation a certain order has been executed, it is used to update 
    the portfolio class's position

    It can also be captured by a seperate logging engine to be logged
    
    
    Attributes:
        type : str
            market, signal, order, filled
        date : str
            when this event is created (str)
        data : dict
            key is product id, value is a list of tuples (action, amount, cash).
    """

    def __init__(self):
        super().__init__()
        self.type = 'Fill'
        self.data = {}
        self.date = ''

    def write_data(self, contract: str, action: str, amount: int, cash: int) -> None:
        """
        write_data writes the action and corresponding amount of action to the event object

        Parameters
        ----------
        contract : str
            name of contract
        action : str
            what action to be performed
        amount : int
            how much this action need to be performed. For calculation efficiency, all amount are values multiplied by the "multipliers".
        cash : int
            the cost/ revenue of buy/sell given amount asset
        """
        self.data[contract] = (action, amount, cash)
