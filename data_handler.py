""" The data generation engine
"""
from abc import ABC
import event
import import_csv as csv
import time


class EngineBasis(ABC):
    """EngineBasis is an abstract interface supplying market data
    """

    def __init__(self):
        super().__init__()

    def get_event(self) -> event.EventMarket:
        """get_event return a market event

        Returns
        -------
        event.EventMarket
        """
        return None


class EngineCSV(EngineBasis):
    """
    Data engine based on TB csv file

    Attributes:
        data:    A dictionary with key of contract name and value of a smaller dictionary with key of date (str)
        symbols: A list of future symbols included (no digits)
        data_index: The longest index (time horizon) list 

    WARNING: data_index is simply the longest index from child csv fils, it is used assuming no daily data loss/gap happend
    """
    def __init__(self):
        super().__init__()
        self.data, self.symbols, self.data_index = csv.get_all_data()
        self.pointer = 0

    def get_event(self) -> event.EventMarket:
        """get_event returns a market event of new BAR for every contract

        Returns
        -------
        event.EventMarket
            

        Raises
        ------
        UserWarning
            when reach EOF, raise userwarning
        """

        if self.pointer >= len(self.data_index):
            raise UserWarning("Backtest finished")

        result = event.EventMarket()
        curr_time = self.data_index[self.pointer]
        for s in self.symbols:
            try:
                curr_data = self.data[s][self.data_index[self.pointer]]
            except KeyError:
                curr_data = None
            result.write_data(s, curr_data)
            result.write_date(curr_time)
        self.pointer += 1
        return result

class EngineCSVSelected(EngineCSV):

    def __init__(self, symbols:list):
        super().__init__()
        self.symbols = symbols
    



if __name__ == "__main__":
    a = EngineCSV()
    start_time = time.time()
    b = a.get_event()
    print("--- %s seconds ---" % (time.time() - start_time))
    c = a.get_event()
    print("--- %s seconds ---" % (time.time() - start_time))
