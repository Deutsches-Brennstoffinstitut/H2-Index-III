from dataclasses import dataclass
from typing import ClassVar
from base_python.source.model_base.Dataclasses.EconomicalDataclasses import check_percentage_rate
import logging
import datetime

class GenericSettings():
    def to_dataframe(self):
        """Returns Information of BasicEconomicalSettings or BasicTechnicalSettings Class as Dataframe

        Returns:

        """
        import pandas as pd

        index = pd.MultiIndex.from_product(iterables = [[self.__class__.__name__],
                                                              self.__dict__.keys()],
                                                 names=['settings','parameters'])
        columns = pd.Index(data=['values','unit'],name = 'columns')
        bs_df = pd.DataFrame(data=zip(*[list(self.__dict__.values()),
                                        [str(type(ii).__name__) for ii in self.__dict__.values()]
                                        ]
                                      ),
                             columns=columns,
                             index=index)
        return bs_df
@dataclass
class BasicTechnicalSettings(GenericSettings):
    time_resolution: int
    absolute_model_error: float = 1e-12
    timeout_max: int = 3


@dataclass
class BasicEconomicalSettings(GenericSettings):
    reference_year: int = None  # reference year all costs are referenced to (to calculate inflation, price development)
    start_year: int = None  # start year of project used for economical calculation
    end_year: int = None  # End year of economical calculation to determine total time period for VDI 2067 calculation
    basic_interest_rate: float = 0.05  # Interest rate for debit and credit interest
    estimated_inflation_rate: float = 0.02  # Overall inflation of the system
    eeg_levy_for_use_of_self_generated_power: float = 0

    basic_interest_rate_factor = None
    estimated_inflation_rate_factor = None

    def get_basic_reference_year(self) -> int:
        """

        Returns:
            int: Basic reference year of the project
        """
        return self.reference_year

    def get_basic_interest_rate(self):
        return self.basic_interest_rate

    def set_estimated_inflation_rate(self, inflation_rate):
        check_percentage_rate(name='Basic Settings', property_name='Inflation rate', value=inflation_rate,
                              lower_limit=0, upper_limit=0.25)
        self.estimated_inflation_rate = inflation_rate
        if inflation_rate is not None:
            self.estimated_inflation_rate_factor = inflation_rate + 1

    def set_basic_interest_rate(self, interest_rate):
        check_percentage_rate(name='Basic Settings', property_name='Interest Rate', value=interest_rate,
                              lower_limit=0, upper_limit=0.25)
        self.basic_interest_rate = interest_rate
        if interest_rate is not None:
            self.basic_interest_rate_factor = interest_rate + 1

    def set_start_year(self, start_year: int):
        """

        Args:
            start_year (int): Start year of the calculation range that shall be used

        Returns:

        """
        self.end_year = start_year
        self.calculate_total_time_period()

    def set_end_year(self, end_year: int):
        """

        Args:
            end_year (int): End year of the calculation range that shall be used

        Returns:

        """

        self.end_year = end_year
        self.calculate_total_time_period()

    def calculate_total_time_period(self):
        """
            Used to calculate the total time period based on start and end_year

        """
        self.total_time_period = self.end_year - self.start_year + 1 if self.end_year is not None and self.start_year is not None else None

    def __post_init__(self):
        self.set_basic_interest_rate(self.basic_interest_rate)
        self.set_estimated_inflation_rate(self.estimated_inflation_rate)
        self.calculate_total_time_period()