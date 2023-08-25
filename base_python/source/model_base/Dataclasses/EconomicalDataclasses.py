from dataclasses import dataclass
from base_python.source.basic.Streamtypes import StreamMass
from base_python.source.basic.Units import Unit
from base_python.source.basic.CustomErrors import EconomicDataClassError
from typing import List
import sys
import logging


def check_percentage_rate(name: str, property_name: str, value: float, lower_limit: float, upper_limit: float):
    """
    Checks whether the value is inside the given limits

    Args:
        name (str):             Name of Element
        property_name (str):    Name of the property for which the value should be set (e.g. interest_rate)
        value (float):          Value that should be set
        lower_limit (float):    Lower tolerated limit for this property
        upper_limit (float):    Upper tolerated limit for this property

    """
    if value is not None:
        if value > upper_limit or value < lower_limit:
            logging.warning(f'Trying to give {name} an {property_name} of {value}. '
                            f'Estimated range is between {lower_limit} and {upper_limit}.')


@dataclass
class CAPEXParameters:
    from collections.abc import Callable

    name: str = None
    investment_cost: float = None
    investment_function: Callable = None
    investment_year: int = None
    reference_year: int = None #reference_year < first_payment_year of OPEXOperationalParameters(!)
    #todo: if the reference_year is > first_payment_year of OPEXOperationalParameters the results for the operational opex are going to be not valid. (by far too big numbers are going to be the result)
    life_cycle: float = 0
    risk_surcharge: float = 0
    price_dev: float = 0
    funding_volume: float = 0
    interest_rate: float = None

    risk_surcharge_factor = None
    price_dev_factor = None
    interest_rate_factor = None

    def get_name(self) -> str:
        """

        Returns:
            str: Name of the capex element
        """
        return self.name

    def get_investment_costs(self) -> float:
        """

        Returns:
            float: Investment costs of the capex element
        """
        return self.investment_cost

    def get_funding_volume(self) -> float:
        """

        Returns:
            float: Funding volume of the first investment
        """
        return self.funding_volume

    def get_interest_rate(self) -> float:
        """

        Returns:
            Interest rate specified for the element
        """
        return self.interest_rate

    def get_interest_rate_factor(self) -> float:
        """

        Returns:
            Interest rate factor specified for the element
        """
        return self.interest_rate_factor

    def get_life_cycle(self) -> float:
        """

        Returns:
            Life cycle of the element
        """
        return self.life_cycle

    def get_investment_year(self) -> int:
        """

        Returns:
            Year of the first investment
        """
        return self.investment_year

    def get_risk_surcharge_factor(self) -> float:
        """
        Returns:
            float: Risk surcharge factor of the specific Element
        """
        return self.risk_surcharge_factor

    def get_risk_surcharge(self) -> float:
        """
        Returns:
            float: Risk surcharge of the specific Element
        """
        return self.risk_surcharge

    def get_price_dev_factor(self) -> float:
        """
        Returns:
            float: Price development factor of the specific Element
        """
        return self.price_dev_factor

    def get_investment_function(self):
        """

        Returns:
            funct: Interpolated investment function of the component
        """
        return self.investment_function

    def get_reference_year(self):
        """

        Returns:
            int: Year from which the price development is referenced (including inflation)
        """
        return self.reference_year

    def set_investment_function(self, interpolated_investment_function):
        """

        Args:
            interpolated_investment_function (funct): Interpolation function of investment costs

        Returns:

        """
        if self.investment_cost is None:
            self.investment_function = interpolated_investment_function
        else:
            logging.critical(
                f'Cant set investment function for investment {self.name} because fixed investment_costs already set')

    def set_life_cycle(self, life_cycle: int):
        """
        Args:
            life_cycle (int): Life cycle of the Element that should be set
        """
        self.life_cycle = life_cycle

    def set_interest_rate(self, interest_rate: float):
        """
        Args:
            interest_rate (float): Interest rate of the Element that should be set
        """
        check_percentage_rate(self.name, 'interest rate', interest_rate, lower_limit=0,
                              upper_limit=0.20)
        self.interest_rate = interest_rate
        if interest_rate is not None:
            self.interest_rate_factor = interest_rate + 1

    def set_price_dev_factor(self, price_dev: float):
        """
        Args:
            price_dev (float): Price development factor of the Element
        """
        check_percentage_rate(self.name, 'price development', price_dev, lower_limit=-0.25, upper_limit=0.25)
        self.price_dev = price_dev
        if price_dev is not None:
            self.price_dev_factor = price_dev + 1

    def set_risk_surcharge(self, risk_surcharge: float):
        """
        Args:
            risk_surcharge (float): Risk sourcharge of the element
        """
        check_percentage_rate(self.name, 'Risk surcharge', risk_surcharge, lower_limit=0, upper_limit=0.25)
        self.risk_surcharge = risk_surcharge
        if risk_surcharge is not None:
            self.risk_surcharge_factor = risk_surcharge + 1

    def set_investment_costs(self, investment_costs: float):
        """

        Args:
            investment_costs (float): Total CAPEX costs in € at reference year

        """

        self.investment_cost = investment_costs

    def set_investment_year(self, investment_year: int):
        """

        Args:
            investment_year (int): Year when first investment has to be paid

        Returns:

        """

        self.investment_year = investment_year

    def __post_init__(self):
        """
        Post init function to set the parameters which are given at init with the setter function to check for limits
        """
        self.set_risk_surcharge(self.risk_surcharge)
        self.set_price_dev_factor(self.price_dev)
        self.set_interest_rate(self.interest_rate)
        if self.investment_function != None and self.investment_cost != None:
            logging.critical(f'Investment costs and function set for capex element {self.name}')


@dataclass
class OPEXOperationalParameters:
    opex_in_percentage_per_year: float = None
    first_payment_year: int = None
    include_inflation: bool = True
    use_database_values: bool = False

    def get_inflation_bool(self) -> bool:
        """

        Returns:
            bool: Boolean value whether inflation shall be included
        """
        return self.include_inflation

    def get_first_payment_year(self) -> int:
        """

        Returns:
            int: First payment year of the opex
        """
        return self.first_payment_year

    def get_operational_percentage(self) -> float:
        """

        Returns:
            float: Percentage of operational opex per year
        """
        return self.opex_in_percentage_per_year

    def get_database_bool(self) -> bool:
        """

        Returns:
            bool: Boolean value whether the database values shall be used to calculate the operational opex
        """
        return self.use_database_values

    def set_overall_opex_in_percentage_per_year(self, overall_opex_in_percentage_per_year: float):
        """
        Sets the percentage of the investment value which has to be paid yearly to cover maintenance etc.
        Args:
            overall_opex_in_percentage_per_year (float): Percentage of Opex for this component and all elements
        """
        check_percentage_rate('Component', 'overall yearly opex in percent', overall_opex_in_percentage_per_year, 0,
                              0.1)
        self.opex_in_percentage_per_year = overall_opex_in_percentage_per_year


@dataclass
class OPEXFixParameters:
    name: str
    yearly_fixed_opex: float
    include_inflation: bool = True
    reference_year: int = None
    first_payment_year: int = None
    interest_rate: float = None
    runout_year: int = None

    interest_rate_factor = None


    def set_opex(self, value):
        self.yearly_fixed_opex = value

    def get_opex(self):
        return self.yearly_fixed_opex

    def get_name(self):
        return self.name

    def get_reference_year(self) -> int:
        """

        Returns:
            int: Reference year from which the opex are referenced
        """

        return self.reference_year

    def get_include_inflation(self) -> bool:
        """

        Returns:
            bool: Boolean value whether the infclation shall be included in this OPEX Set
        """
        return self.include_inflation

    def get_interest_rate(self) -> float:
        """
        Returns:
            float: Interest rate of the Element
        """
        return self.interest_rate

    def set_interest_rate(self, interest_rate: float):
        """
        Args:
            interest_rate (float): Interest rate of the Element that should be set
        """
        check_percentage_rate(self.name, 'interest rate', interest_rate, lower_limit=0,
                              upper_limit=0.20)
        self.interest_rate = interest_rate
        if interest_rate is not None:
            self.interest_rate_factor = interest_rate + 1

    def __post_init__(self):
        """
        Post init function to set the parameters which are given at init with the setter function to check for limits
        """
        self.set_interest_rate(self.interest_rate)


@dataclass
class Direction:
    unit: Unit
    costs_in: dict = None
    costs_out: dict = None

    def set_costs_out(self, cost_dict):
        self.costs_out = cost_dict

    def set_costs_in(self, cost_dict):
        self.costs_in = cost_dict

    def create_results(self)->dict:
        _dict={}
        for key,value in self.__dict__.items():
            if isinstance(value,dict):
                for key2,value2 in value.items():
                    _dict[key2]=value2
            else:
                _dict[key]=value
        return _dict
@dataclass
class StreamEconParameters:
    stream_type: StreamMass
    first_payment_year: int
    power_related_costs: Direction = Direction(Unit.euro_per_kW)
    amount_related_costs: Direction = Direction(Unit.euro_per_kWh)
    yearly_fixed_costs: Direction = Direction(Unit.euro_per_year)
    price_dev: float = 0  # Development factor for the cos ts
    include_inflation: bool = True
    interest_rate: float = None
    reference_year: int = None
    interest_rate_factor = None
    price_dev_factor = None

    def get_price_dev_factor(self) -> float:
        """
        Returns:
            float: Price development Factor of the Element (based on VDI 2067)
        """
        return self.price_dev_factor

    def get_reference_year(self) -> int:
        """

        Returns:
            int: Reference year from which the opex are referenced
        """

        return self.reference_year

    def get_include_inflation(self) -> bool:
        """

        Returns:
            bool: Boolean value whether the infclation shall be included in this OPEX Set
        """
        return self.include_inflation

    def set_yearly_fixed_costs(self, direction: str, value_dictionary: dict):
        """
        Args:
            direction (str): Decide which direction the costs should be set ('in' or 'out')
            value_dictionary (dict): Dictionary with the cost values containing Names and cost_values in Euro per year
            (e.g. {'Wartung': 50000})

        """
        self._set_direction_costs(self.yearly_fixed_costs, direction, value_dictionary)

    def set_amount_related_costs(self, direction: str, value_dictionary):
        """
        Args:
            direction (str): Decide which direction the costs should be set ('in' or 'out')
            value_dictionary (dict): Dictionary with the cost values containing Names and cost_values in Euro per amount
            (e.g. {'EEG': 0.05}

        """
        self._set_direction_costs(self.amount_related_costs, direction, value_dictionary)

    def set_power_related_costs(self, direction: str, value_dictionary: dict):
        """
        Args:
            direction (str): Decide which direction the costs should be set ('in' or 'out')
            value_dictionary (dict): Dictionary with the cost values containing Names and cost_values in Euro per
            maximum power over time (e.g. {'Leistungspreis': 120}

        """
        self._set_direction_costs(self.power_related_costs, direction, value_dictionary)

    @staticmethod
    def _set_direction_costs(parameter: Direction, direction: str, value_dictionary: dict):
        """
        Args:
            parameter (Direction): The Direction Class for which the costs should be set
            direction (str): Decide which direction the costs should be set ('in' or 'out')
            value_dictionary (dict): Dictionary with the cost values containing Names and cost_values
        """

        if direction == 'in':
            parameter.set_costs_in(value_dictionary)
        elif direction == 'out':
            parameter.set_costs_out(value_dictionary)

    def set_interest_rate(self, interest_rate: float):
        """
        Args:
            interest_rate (float): Specific interest rate of the element
        """
        check_percentage_rate(self.stream_type, 'interest rate', interest_rate, lower_limit=0,
                              upper_limit=0.20)
        self.interest_rate = interest_rate
        if interest_rate is not None:
            self.interest_rate_factor = interest_rate + 1

    def set_price_dev_factor(self, price_dev: float):
        """
        Args:
            price_dev (float): Price development factor of the Element
        """

        check_percentage_rate(self.stream_type, 'price development', price_dev, lower_limit=-0.25, upper_limit=0.25)
        self.price_dev = price_dev
        if price_dev is not None:
            self.price_dev_factor = price_dev + 1

    def __post_init__(self):
        """
        Post init function to set the parameters which are given at init with the setter function to check for limits
        """

        self.set_price_dev_factor(self.price_dev)
        self.set_interest_rate(self.interest_rate)

        if self.amount_related_costs is not None:
            if self.amount_related_costs.unit not in [Unit.euro_per_kWh, Unit.euro_per_kg]:
                raise EconomicDataClassError(f'Given amount related costs must meet required Units: '
                                 f'{Unit.euro_per_kWh.value, Unit.euro_per_kg.value}')
        if self.yearly_fixed_costs is not None:
            if self.yearly_fixed_costs.unit not in [Unit.euro_per_year]:
                raise EconomicDataClassError(f'Given yearly costs must meet required Units: {Unit.euro_per_year.value}')
        if self.power_related_costs is not None:
            if self.power_related_costs.unit not in [Unit.euro_per_kW]:
                raise EconomicDataClassError(f'Given power related costs must meet required Units:{Unit.euro_per_kW.value}')
    def create_results(self)->dict:
        _dict = {}
        for key,value in self.__dict__.items():
            if isinstance(value,Direction):
                _dict[key] = value.create_results()
            else:
                _dict[key] =value
        return _dict
@dataclass
class EconomicalParameters:
    use_database_values: bool = False
    component_capex: List[CAPEXParameters] = None
    fixed_opex: List[OPEXFixParameters] = None
    operational_opex: OPEXOperationalParameters = None
    stream_econ: List[StreamEconParameters] = None

    def get_capex_element_by_name(self, name) -> CAPEXParameters:
        if self.component_capex is not None:
            capex_element_names = [i.get_name() for i in self.component_capex]
            if name in capex_element_names:
                return self.component_capex[capex_element_names.index(name)]
            else:
                return None
        else:
            return None

    def get_opex_element_by_name(self, name) ->OPEXFixParameters:
        if self.fixed_opex is not None:
            opex_element_names = [i.get_name() for i in self.fixed_opex]
            if name in opex_element_names:
                return self.fixed_opex[opex_element_names.index(name)]
            else:
                return None
        else:
            return None

    def get_database_bool(self) -> bool:
        """

        Returns:
            bool: Boolean value whether database values shall be used to calculate costs
        """
        return self.use_database_values

    def get_stream_econ_by_stream_type(self, stream_type: StreamMass) -> StreamEconParameters:
        """
        Function to get a stream econ element by a specific stream type
        Args:
            stream_type (StreamMass):   Stream_type for which the econ_parameters shall be returned
        """

        for single_stream_econ in self.stream_econ:
            if single_stream_econ.stream_type == stream_type:
                return single_stream_econ

    def get_all_capex_elements(self) -> list:
        """

        Returns:
            list: List of capex elements for this component
        """
        return self.component_capex

    def get_operational_opex(self) -> OPEXOperationalParameters:
        """

        Returns:
            OPEXOperationalParameters: OPEX Element for the operational opex based on VDI 2067 given in percent per year
        """
        return self.operational_opex

    def set_all_capex_interest_rates(self, interest_rate: float):
        """
        Sets a specific interest rate for all capex elements of this component
        Args:
            interest_rate (float): Interest rate that should be set to the elements
        """
        for component in self.component_capex:
            component.set_interest_rate(interest_rate)

    def set_all_opex_interest_rates(self, interest_rate):
        """
        Sets a specific interest rate for all opex elements of this component
        Args:
            interest_rate (float): Interest rate that should be set to the elements
        """
        for component in self.fixed_opex:
            component.set_interest_rate(interest_rate)

    def set_all_stream_interest_rates(self, interest_rate):
        """
        Sets a specific interest rate for all stream_cost elements of this component
        Args:
            interest_rate (float): Interest rate that should be set to the elements
        """
        for component in self.stream_econ:
            component.set_interest_rate(interest_rate)

    def set_all_interest_rates(self, interest_rate):
        """
        Sets a specific interest rate for all elements of this component
        Args:
            interest_rate (float): Interest rate that should be set to the elements
        """
        self.set_all_capex_interest_rates(interest_rate)
        self.set_all_opex_interest_rates(interest_rate)
        self.set_all_stream_interest_rates(interest_rate)
