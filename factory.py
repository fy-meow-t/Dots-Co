"""Factory classes for Dots & Co game
"""

from abc import ABC, abstractmethod

from cell import Cell, VoidCell
from dot import AbstractKindlessDot

class AbstractFactory(ABC):
    """Abstract factory"""

    @abstractmethod
    def generate(self, position):
        """(*) Abstract method to return a new instance

        Parameters:
            position (tuple<int, int>) The (row, column) position of the dot
        """
        raise NotImplementedError


class WeightedFactory(AbstractFactory):
    """Factory to generate instances based upon WeightedSelector value"""

    def __init__(self, selector, constructor):
        """Constructor

        Parameters:
            selector (WeightedSelector): The weighted selector to choose from
            constructor (WeightedSelector): A weighted selector to choose
                                            the constructor class from
        """
        self._selector = selector
        self._constructor = constructor

    def generate(self, position):
        """(*) Generates a new instance"""
        constructor = self._constructor.choose()
        return constructor(self._selector.choose())


class CellFactory(AbstractFactory):
    """A basic factory for grid cells determined by a set of dead cells

    Generates a VoidCell for every position in dead cells, otherwise Cell
    """

    def __init__(self, dead_cells=None):
        """
        Constructor

        Parameters:
            dead_cells (set<tuple<int, int>>): Set of cells that are disabled (i.e. VoidCells) 
        """
        if dead_cells is None:
            dead_cells = set()
        self._dead_cells = dead_cells

    def generate(self, position):
        """(*) Generates a new dot"""
        return Cell(None) if position not in self._dead_cells else VoidCell()


class DotFactory(AbstractFactory):
    """Factory to generate dot instances"""

    def __init__(self, selector, constructor):
        """Constructor

        Parameters:
            selector (WeightedSelector): The weighted selector to choose from
            constructor (WeightedSelector): A weighted selector to choose
                                            the constructor class from
        """
        self._selector = selector
        self._constructor = constructor

    def generate(self, position):
        """(*) Generates a new dot"""
        constructor = self._constructor.choose()

        if issubclass(constructor, AbstractKindlessDot):
            return constructor()

        return constructor(self._selector.choose())
