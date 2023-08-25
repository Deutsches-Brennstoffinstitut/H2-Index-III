import openpyxl
import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from dataclasses import dataclass, field, InitVar, asdict
from typing import ClassVar
from base_python.source.model_base import ModelBase
from base_python.source.model_base.Dataclasses.EconomicalDataclasses import *
from base_python.source.basic.Quantities import PhysicalQuantity
from base_python.source.basic.Settings import *
from base_python.source.helper.ExcelCoordinates import num2col
from base_python.source.basic.CustomErrors import ExportDataClassError
from datetime import datetime


@dataclass
class ElementCAPEX:
    element_name: str
    all_investments: list
    annuity_series: list = None
    input_parameters: CAPEXParameters = None
    annuity: float = 0
    remain_value: float = 0

    def create_dictionary(self):
        """ function to create a dictionary of ElementCAPEX (including input_parameters)

        :return:
        :rtype:
        """
        _dict1 = self.__dict__
        _dict2 = self.input_parameters.__dict__
        _dicts = {**_dict1, **_dict2}  # combinding dictionaries in python 3.8.
        # in >=3.09 you could do dict3 = dict1 | dict2
        _dict_ret = {}

        def _timeseries(investment_year, investments):
            _init_year = int(investment_year)
            _range = range(_init_year, _init_year + len(investments), 1)
            for _r, _i in zip(_range, investments):
                yield _r, _i

        _dict_timeseries = dict(_timeseries(
            investment_year=self.input_parameters.get_investment_year(),
            investments=self.all_investments))

        for key, value in _dicts.items():
            if isinstance(key, (int, float)):
                _key = str(key)
            else:
                _key = key
            if key in ['name', 'element_name', 'annuity_series',
                       'input_parameters']:  # "name" is the same as "element_name"
                # i dont know what "annuity_series" is and "input_parameters" is handled extra.
                pass
            else:
                if key in list(_dict1.keys()):
                    if key in ['all_investments']:
                        for k_ts, v_ts in _dict_timeseries.items():
                            _dict_ret[(self.__class__.__name__, 'output', str(k_ts))] = v_ts
                    else:
                        _dict_ret[(self.__class__.__name__, 'output', _key)] = value
                elif key in list(_dict2.keys()):
                    _dict_ret[(self.__class__.__name__, 'input', _key)] = value
        return _dict_ret

    def to_dataframe(self):
        return pd.DataFrame(self.create_dictionary(), index=[self.element_name])

    def get_risk_surcharge(self) -> float:
        """

        Returns:
            Risk surcharge for the specific element
        """
        return self.input_parameters.get_risk_surcharge()

    def get_interest_rate(self) -> float:
        """

        Returns:
            Interest Rate for the specific element
        """
        return self.input_parameters.get_interest_rate()

    def get_price_dev_factor(self) -> float:
        """

        Returns:
            Price development factor for the specific element
        """
        return self.input_parameters.get_price_dev_factor()

    def get_life_cycle(self) -> int:
        """

        Returns:
            Life Cycle of the specific element which is given as input parameter
        """
        return self.input_parameters.get_life_cycle()

    def get_name(self) -> str:
        """

        Returns:
            Name of the element which is part of the whole component
        """
        return self.element_name

    def get_first_investment_year(self) -> int:
        """

        Returns:
            Year of the first investment
        """
        return self.input_parameters.get_investment_year()

    def get_first_investment(self) -> float:
        """

        Returns:
            First investment values
        """
        return self.all_investments[0]

    def get_replacement_invests(self) -> list:
        """

        Returns:
            All Replacement invests
        """
        return self.all_investments[1:]

    def get_remain_value(self) -> float:
        """

        Returns:
            Remain value of the element
        """
        return self.remain_value

    def get_annuity(self) -> float:
        """

        Returns:
            CAPEX Annuity of the element
        """
        return self.annuity


@dataclass
class ElementVariableOPEX:
    element_name: str
    first_investment: float
    annuity_series: list = None
    percentage_of_invest: float = None
    annuity: float = 0

    def get_name(self) -> str:
        """
        Returns:
            Name of the OPEX element
        """

        return self.element_name

    def get_opex_costs_first_payment_year(self) -> float:
        """

        Returns:
            OPEX costs in the first payment year
        """

        return self.first_investment * self.percentage_of_invest

    def get_opex_percentage(self) -> float:
        """

        Returns:
            OPEX in percentage of first investment
        """

        return self.percentage_of_invest

    def get_annuity(self) -> float:
        """

        Returns:
            Annuity for the opex element
        """
        return self.annuity

    def create_dictionary(self) -> dict:
        _dict = {}
        for key, value in self.__dict__.items():
            if not key is self.element_name or isinstance(value, list):
                _dict[key] = value
        return _dict

    def to_dataframe(self):
        _df = pd.DataFrame.from_dict(self.create_dictionary())
        return _df


@dataclass
class ElementFixOPEX:
    element_name: str
    opex_costs: float
    first_payment_year: int
    annuity_series: list = None
    input_parameters: OPEXFixParameters = None
    annuity: float = 0

    def get_name(self) -> str:
        """

        Returns:
            Name of the OPEX element
        """

        return self.element_name

    def get_first_payment_year(self) -> int:
        """

        Returns:
            First year of opex payment
        """

        return self.first_payment_year

    def get_interest_rate(self) -> float:
        """

        Returns:
            Interest rate for the opex element
        """

        return self.input_parameters.get_interest_rate()

    def get_opex_costs_first_payment_year(self) -> float:
        """

        Returns:
            OPEX costs in the first payment year
        """

        return self.opex_costs

    def get_annuity(self) -> float:
        """

        Returns:
            Annuity for the opex element
        """
        return self.annuity

    def create_dictionary(self) -> dict:
        _dict = {}
        for key, value in self.__dict__.items():
            if not key is self.element_name:
                if isinstance(value, OPEXFixParameters):
                    for key2, value2 in value.__dict__.items():
                        _dict[('input', key2)] = value2
                else:
                    _dict[('output', key)] = value
        return _dict

    def to_dataframe(self):
        _df = pd.DataFrame.from_dict(self.create_dictionary())
        return _df


@dataclass
class SingleStreamEconResult:
    stream_type: StreamMass = None
    input_parameters: StreamEconParameters = None
    costs: dict = field(default_factory=lambda: {})
    annuities: dict = field(default_factory=lambda: {})
    annuity: float = 0

    def get_stream_type(self):
        """

        Returns:
            Stream Type of the stream econ element
        """
        return self.stream_type

    def set_cost_parameter(self, direction: str, cost_type: str, cost_component_name: str, value: float):
        """

        Args:
            cost_type: (str): String whether its 'stream_related', 'power_related' or fixed
            direction (str) : 'in' or 'out' regarding the
            cost_component_name (str): Name of the single cost component
            value (float): Desired value that shall be set
        """

        self.extend_dictionary_if_necessary(self.costs, cost_type, direction, cost_component_name)
        self.costs[cost_type][direction][cost_component_name] = value

    def set_annuity_parameter(self, direction: str, cost_type: str, cost_component_name: str, value: float):
        """

        This function sets the annuity parameters to the output

        Args:
            cost_type: (str): String whether its 'stream_related', 'power_related' or fixed
            direction (str) : 'in' or 'out' regarding the
            cost_component_name (str): Name of the single cost component
            value (): Desired value that shall be set

        Returns:

        """

        self.extend_dictionary_if_necessary(self.annuities, cost_type, direction, cost_component_name)

        self.annuities[cost_type][direction][cost_component_name] = value

    @staticmethod
    def extend_dictionary_if_necessary(dictionary: dict, cost_type: str, direction: str,
                                       cost_component_name: str):
        """
        This function is used to add the desired keys to the dictionary

        Args:
            dictionary (dict): Dictionary which shall be checked
            cost_type: (str): String whether its 'stream_related', 'power_related' or fixed
            direction (str) : 'in' or 'out' regarding the
            cost_component_name (str): Name of the single cost component

        """
        if cost_type not in dictionary:
            dictionary[cost_type] = {}
        if direction not in dictionary[cost_type]:
            dictionary[cost_type][direction] = {}
        if cost_component_name not in dictionary[cost_type][direction]:
            dictionary[cost_type][direction][cost_component_name] = {}

    def set_sum_annuity(self):
        """
        This function is used to sum the annuities to get the sum of the single annuity components

        """
        sum_costs = 0
        for stream_type in self.annuities.values():
            for direction in stream_type.values():
                for cost_value in direction.values():
                    sum_costs += cost_value if isinstance(cost_value, float) else sum(cost_value)
        self.annuity = sum_costs

    def get_annuities(self):
        return self.annuities


@dataclass(repr=False)
class PortResult:
    from base_python.source.basic.Streamtypes import StreamDirection
    instances: ClassVar[list] = field(init=False, default=list())
    port_id: str
    sign: StreamDirection
    stream_unit: Unit
    port_type: str or None = field(default=None)
    branch_id: str or None = field(default=None)
    component_id: str or None = field(default=None)
    max_stream_in: float or None = field(init=False)
    max_stream_out: float or None = field(init=False)
    port_history: dict = field(default_factory=lambda: {})

    def __post_init__(self):
        PortResult.instances.append(self)
        try:
            self.max_stream_in = min(self.port_history[PhysicalQuantity.stream])
        except (ValueError, KeyError):
            self.max_stream_in = None
        try:
            self.max_stream_out = max(self.port_history[PhysicalQuantity.stream])
        except (ValueError, KeyError):
            self.max_stream_out = None

    @classmethod
    def get_instances(cls):
        return cls.instances

    def create_technical_results_of_port(self) -> dict:
        """Returns the technical results of one specific port as dictionary

        Returns:

        """
        _dict = dict()
        for key, value in self.port_history.items():
            if self.branch_id is None:
                branch_id = "None"
            else:
                branch_id = self.branch_id
            _dict[(branch_id, self.component_id, self.port_id, key)] = value
        return _dict

    @classmethod
    def create_technical_results_of_all_ports(cls) -> dict:
        """
        Returns ALL the technical results of every port as dictionary
        Returns:

        """
        _dict = dict()
        for instance in cls.get_instances():
            _dict.update(instance.create_technical_results_of_port())
        return _dict

    @classmethod
    def to_dataframe(cls) -> pd.DataFrame:
        """Returns the technical results of every port as Dataframe with multiindex for columns and "timeseries" for rows

        Notes:
            Lots of unnecessary infos are stored here. It is easy to filter the Dataframe
            _df.filter(like='stream')

        Returns:

        """
        data = cls.create_technical_results_of_all_ports()
        _df = pd.DataFrame.from_dict(data=data)
        _df.columns.names = ['branch_id', 'component_id', 'port_id', 'stream_type']
        _df.index.name = 'timeseries'
        return _df

    # get'n set
    def get_port_type(self):
        return self.port_type

    def get_branch_id(self):
        return self.branch_id

    def get_component_id(self):
        return self.component_id

    def get_port_id(self):
        return self.port_id

    def set_port_sign(self, sign):
        self.sign = sign

    def get_stream_history(self):
        if None not in self.port_history[PhysicalQuantity.stream]:
            return self.port_history[PhysicalQuantity.stream]
        else:
            return []

    def get_stream_history_out(self):
        return list(filter(lambda x: x > 0, self.get_stream_history()))

    def get_stream_history_in(self):
        return list(filter(lambda x: x < 0, self.get_stream_history()))

    def get_sum_stream_out_by_history(self):
        return sum(self.get_stream_history_out())

    def get_sum_stream_in_by_history(self):
        return sum(self.get_stream_history_in())

    def get_max_stream_in_by_history(self):
        stream_history_in = self.get_stream_history_in()
        if len(stream_history_in) > 0:
            return min(stream_history_in)
        else:
            return 0

    def get_max_stream_out_by_history(self):
        stream_history_out = self.get_stream_history_out()
        if len(stream_history_out) > 0:
            return max(stream_history_out)
        else:
            return 0


@dataclass
class ComponentTechnicalResults:
    size: float
    component_history: dict
    instances: ClassVar[list] = field(init=False, default=list())
    branch_id: str or None = field(default=None)
    component_id: str or None = field(default=None)

    def __post_init__(self):
        ComponentTechnicalResults.instances.append(self)

    def create_technical_result(self):
        _dict = dict()
        # _dict[(self.branch_id, self.component_id,'size')]=dict(information=self.size)
        for key, values in self.component_history.items():
            _dict[(self.branch_id, self.component_id, key)] = values
        return _dict

    @classmethod
    def create_technical_results(cls):
        _dict = dict()
        for instance in cls.instances:
            _dict.update(instance.create_technical_result())
        return _dict

    @classmethod
    def to_dataframe(cls):
        _df = pd.DataFrame.from_dict(cls.create_technical_results(), orient='index')
        _df.index = pd.MultiIndex.from_tuples(_df.index, names=['branch_id', 'component_id', 'info'])
        _df.columns.names = ['timeseries']
        return _df.T

    def get_component_id(self):
        return self.component_id

    def get_stream_annuity_by_stream_type(self, stream_type):
        for key, stream_values in self.get_streams_of_ports_divided_by_type().items():
            if key is stream_type:
                return stream_values

    def get_branch_id(self):
        return self.branch_id

    def set_branch_id(self, branch_id: str):
        self.branch_id = branch_id

    def get_component_history(self):
        return self.component_history

    def get_streams_of_ports_divided_by_type(self) -> dict:
        stream_dictionary = {}
        for port in self.ports:
            if not port.get_port_type() in stream_dictionary:
                stream_dictionary[port.get_port_type()] = (
                    port.get_sum_stream_in_by_history(), port.get_sum_stream_out_by_history())
            else:
                stream_dictionary[port.get_port_type()] = (
                    stream_dictionary[port.get_port_type()][0] + port.get_sum_stream_in_by_history(),
                    stream_dictionary[port.get_port_type()][1] + port.get_sum_stream_out_by_history())
        return stream_dictionary

    def get_max_streams_of_ports_divided_by_type(self) -> dict:
        stream_dictionary = {}
        for port in self.port_results:
            if port.get_port_type() not in stream_dictionary:
                stream_dictionary[port.get_port_type()] = (
                    port.get_max_stream_in_by_history(), port.get_max_stream_out_by_history())
            else:
                stream_dictionary[port.get_port_type()] = (
                    stream_dictionary[port.get_port_type()][0] + port.get_max_stream_in_by_history(),
                    stream_dictionary[port.get_port_type()][1] + port.get_max_stream_out_by_history())
        return stream_dictionary

    def get_max_streams_of_all_ports_divided_by_type(self) -> dict:
        """
        Returns:
            dict: Dictionary of the streams of all ports divided by their type
        """
        return self.get_max_streams_of_ports_divided_by_type()

    def get_streams_of_all_ports_divided_by_type(self) -> dict:
        """
        Returns:
            dict: Dictionary of the streams of all ports divided by their type
        """
        return self.get_streams_of_ports_divided_by_type()

    def get_component_id(self) -> str:
        """
        Returns:
            str: Name of the component
        """
        return self.component_id

    def get_branch_id(self) -> str:
        return self.branch_id


@dataclass
class ComponentEconResults:
    instances: ClassVar[list] = field(init=False, default=list())
    branch_id: str or None = field(default=None)
    component_id: str or None = field(default=None)
    component_CAPEX: List[ElementCAPEX] = field(default_factory=lambda: [])
    component_fix_OPEX: List[ElementFixOPEX] = field(default_factory=lambda: [])
    component_variable_OPEX: List[ElementVariableOPEX] = field(default_factory=lambda: [])
    component_stream_cost: List[SingleStreamEconResult] = field(default_factory=lambda: [])
    component_CAPEX_Annuity: float = 0
    component_variable_OPEX_Annuity: float = 0
    component_fix_OPEX_Annuity: float = 0
    component_stream_cost_Annuity: float = 0
    component_Annuity: float = 0

    def __post_init__(self):
        ComponentEconResults.instances.append(self)

    def set_branch_id(self, branch_id: str):
        self.branch_id = branch_id

    def set_component_id(self, component_id: str):
        self.component_id = component_id

    def get_annuity(self):
        """

        Returns:
            Overall annuity of the component
        """

        return self.component_Annuity

    def get_all_capex_elements(self) -> dict:
        """Returns all Capex ELements as Dictionary(!)
        with the element name as key and the ElementCAPEX dataclass as value

        Returns:
            All capex Elements of the component
        """
        all_elements = {}
        for single_element in self.component_CAPEX:
            all_elements[single_element.element_name] = single_element
        return all_elements

    def get_all_fixed_OPEX_elements(self) -> dict:
        """Returns all fixed opex alements as dictionary(!)
        with the element name as key and the fixedOPEX dataclass as value
        """
        all_elements = {}
        for single_element in self.component_fix_OPEX:
            all_elements[single_element.element_name] = single_element
        return all_elements

    def get_all_variable_OPEX_elements(self) -> dict:
        """Returns all variable opex elements as dictionary(!)
        with the element name as key and the variableOPEX dataclass as value

        """
        all_elements = {}
        for single_element in self.component_variable_OPEX:
            all_elements[single_element.element_name] = single_element
        return all_elements

    def get_element_by_name(self, name):
        """

        Args:
            name (str): Name of the desired capex element

        Returns:
            Desired capex element of the component
        """
        all_elements = self.get_all_capex_elements()
        if name in all_elements:
            return all_elements[name]
        else:
            return None

    def set_component_annuity(self):
        """
        Set the overall annuities for this component by adding the single annuities of each type
        """

        self.component_CAPEX_Annuity = 0
        self.component_variable_OPEX_Annuity = 0
        self.component_fix_OPEX_Annuity = 0
        self.component_stream_cost_Annuity = 0

        for element in self.component_CAPEX:
            self.component_CAPEX_Annuity += element.annuity

        for element in self.component_variable_OPEX:
            self.component_variable_OPEX_Annuity += element.annuity

        for element in self.component_fix_OPEX:
            self.component_fix_OPEX_Annuity += element.annuity

        for element in self.component_stream_cost:
            element.set_sum_annuity()
            self.component_stream_cost_Annuity += element.annuity

        self.component_Annuity = sum(
            [self.component_CAPEX_Annuity, self.component_fix_OPEX_Annuity, self.component_variable_OPEX_Annuity,
             self.component_stream_cost_Annuity])

    def create_economic_result(self):
        _dict = dict()
        # _dict[(self.branch_id, self.component_id,'size')]=dict(information=self.size)
        for key, values in self.__dict__.items():
            if not key in ['branch_id', 'component_id']:
                if isinstance(values, (int, str, float)):
                    _dict[key] = values
        return _dict

    @classmethod
    def create_economic_results(cls):
        _dict = dict()
        for instance in cls.instances:
            _dict[(instance.branch_id, instance.component_id)] = instance.create_economic_result()
        return _dict

    @classmethod
    def to_dataframe(cls):
        _df = pd.DataFrame.from_dict(cls.create_economic_results())
        _df.columns.names = ['branch_id', 'component_id']
        _df.index.name = 'parameter'
        return _df

    def to_dataframe_ElementCAPEX(self) -> pd.DataFrame:
        _df = pd.DataFrame(self.create_component_CAPEX_results())
        try:
            _df.columns.names = ['branch_id', 'component_id']
            # todo: find better names for index names
            # todo: find better namexlsxs for index names
            _df.index.names = ['Element', 'idk', 'parameter']
        except ValueError:
            pass
        return _df

    def create_component_CAPEX_results(self):
        _dict = dict()
        for instance in self.instances:
            for key, _item in instance.get_all_capex_elements().items():
                if _item.element_name:
                    #_dict[(instance.branch_id, instance.component_id, _item.element_name)] = _item.create_dictionary()
                    _dict[(instance.branch_id, instance.component_id)] = _item.create_dictionary()
        return _dict

    def create_component_fixedOPEX_results(self):
        _dict = dict()
        for instance in self.instances:
            for key, _item in instance.get_all_fixed_OPEX_elements().items():
                if _item.element_name:
                    _dict[(instance.branch_id, instance.component_id, _item.element_name)] = _item.create_dictionary()
        return _dict

    def to_dataframe_ElementfixedOPEX(self) -> pd.DataFrame:
        _df = pd.DataFrame(self.create_component_fixedOPEX_results())
        try:
            _df.columns.names = ['branch_id', 'component_id', 'element_name']
            # todo: find better names for index names
            _df.index.names = ['idk', 'parameter']
        except ValueError:
            pass
        return _df

    def create_component_variable_OPEX_results(self):
        _dict = dict()
        for instance in self.instances:
            for key, _item in instance.get_all_variable_OPEX_elements().items():
                _dict[(instance.branch_id, instance.component_id, _item.element_name)] = _item.create_dictionary()
        return _dict

    def to_dataframe_ElementvariableOPEX(self) -> pd.DataFrame:
        _df = pd.DataFrame(self.create_component_variable_OPEX_results())
        try:
            _df.columns.names = ['branch_id', 'component_id', 'element_name']
            _df.index.names = ['parameter']
        except ValueError:
            pass
        return _df

    def get_capex_element_by_name(self, name):
        """

        Args:
            name (str): Name of the capex element

        Returns:
            capex_element for the desired name of the component
        """

        return self.get_element_by_name(name)

    def get_component_annuity(self) -> float:
        """
        Returns:
            float: Total annuity of this component
        """
        return self.get_annuity()

    def get_component_id(self) -> str:
        """
        Returns:
            str: Name of the component
        """
        return self.component_id

    def get_branch_id(self) -> str:
        return self.branch_id

    def get_divided_annuity(self) -> dict:
        """
        Returns:
            dict: Annuities of the component divided in their types
        """
        return {
            'CAPEX_Annuity': self.component_CAPEX_Annuity,
            'OPEX_fix_Annuity': self.component_fix_OPEX_Annuity + self.component_variable_OPEX_Annuity,
            'OPEX_var_Annuity': self.component_stream_cost_Annuity
        }


@dataclass
class BranchInfo:
    branches: InitVar[dict]  # Init-Variable. Going to be dropped after post init
    branch_dictionary: dict = field(init=False)

    def __post_init__(self, branches: dict):
        self.branch_dictionary = dict()
        for branch_name, branch_values in branches.items():
            branch_type = branch_values.branch_type
            branch_id = branch_values.branch_id
            for component_name, component_values in branch_values.connected_components.items():
                for port_id, port_values in component_values.ports.items():
                    if branch_type == port_values.port_results.port_type:
                        self.branch_dictionary[
                            (branch_values.branch_id,
                             component_values.component_id,
                             port_id)] = dict(branch_name=branch_name,
                                              component_name=component_name,
                                              port_type=port_values.port_results.port_type,
                                              stream_type=port_values.stream_type.name,
                                              stream_unit=port_values.port_results.stream_unit,
                                              direction=port_values.port_results.sign.name
                                              )

    def get_branch_information(self):
        return self.branch_dictionary

    def to_dataframe(self):
        _df = pd.DataFrame.from_dict(data=self.branch_dictionary)
        _df.columns.names = ['branch_id', 'component_id', 'port_id']
        _df.index.name = 'information'
        return _df


@dataclass
class SystemResults:
    basic_econ_system_settings: BasicEconomicalSettings
    basic_technical_settings: BasicTechnicalSettings
    branch_information: BranchInfo

    costs_calculated: bool = False
    component_technical_results: List[ComponentTechnicalResults] = field(default_factory=lambda: [])
    component_economic_results: List[ComponentEconResults] = field(default_factory=lambda: [])
    port_results: List[PortResult] = field(default_factory=lambda: [])
    overall_annuity: float = 0

    def __post_init__(self):
        self.set_overall_annuity()

    def export_to_xlsx(self,filename: str, path:str='../../output/results/', with_timeseries: bool = True) -> None:
        # one dataframes for each sheet
        filepath = f'{path}{filename}.xlsx'
        df_basic_econ = self.basic_econ_system_settings.to_dataframe()
        df_basic_tech = self.basic_technical_settings.to_dataframe()
        df_branch_info = self.branch_information.to_dataframe()
        df_tech_results1 = self.component_technical_results[0].to_dataframe()
        df_tech_results2 = self.port_results[0].to_dataframe()
        df_econ_1 = self.component_economic_results[0].to_dataframe()
        df_econ_CAPEX = self.component_economic_results[0].to_dataframe_ElementCAPEX()
        df_econ_fixedOPEX = self.component_economic_results[0].to_dataframe_ElementfixedOPEX()
        df_econ_variableOPEX = self.component_economic_results[0].to_dataframe_ElementvariableOPEX()
        if with_timeseries:  # if a timeseries is needed -> add a timeseries
            dt_id = pd.date_range(start=datetime(year=self.basic_econ_system_settings.reference_year, month=1, day=1),
                                  periods=df_tech_results1.__len__(), freq='1H',
                                  name='TimeSeries')
            df_tech_results1.index = dt_id
            df_tech_results2.index = dt_id
        else:
            df_tech_results1.index.name = 'Steps'
            df_tech_results2.index.name = 'Steps'
        with pd.ExcelWriter(filepath) as writer:
            # use to_excel function and specify the sheet_name and index
            # to store the dataframe in specified sheet
            df_branch_info.to_excel(writer, sheet_name="Branch_Information")
            df_basic_econ.to_excel(writer, sheet_name="Economic_Settings")
            df_basic_tech.to_excel(writer, sheet_name="Technical_Settings")
            df_tech_results1.to_excel(writer, sheet_name="Technical_Component_Results")
            df_tech_results2.to_excel(writer, sheet_name="Technical_Port_Results")
            df_econ_1.to_excel(writer, sheet_name='Economical_Results_Overview')
            df_econ_CAPEX.to_excel(writer, sheet_name='CAPEX')
            df_econ_fixedOPEX.to_excel(writer, sheet_name='fixedOPEX')
            df_econ_variableOPEX.to_excel(writer, sheet_name='variableOPEX')

    def set_overall_annuity(self):
        """
        Sets the overall annuity of the system by adding the annuities of the components
        """
        self.overall_annuity = 0
        for component in self.component_economic_results:
            self.overall_annuity += component.get_annuity()

    def get_annuity_of_all_components_divided_in_type(self) -> dict:
        """
        Returns:
            dict: Annuities of all components divided by the type of annuity (e.g. CAPEX, OPEX fix etc.)
        """
        component_annuity = {}
        for component in self.component_economic_results:
            component_annuity[component.component_id] = component.get_divided_annuity()
        return component_annuity

    def get_history_of_component(self, name):
        for component in self.component_technical_results:
            if component.component_id == name:
                return component.get_component_history()

    def get_annuity_of_all_components(self) -> dict:
        """
        Returns:
            dict: Total annuities of all components
        """
        component_annuity = {}
        for component in self.component_economic_results:
            component_annuity[component.component_id] = component.component_Annuity
        return component_annuity

    def get_max_streams_of_all_components(self) -> dict:
        """
        Returns:
            dict: Streams of all components divided by stream_types
        """
        component_streams = {}
        for component in self.component_technical_results:
            component_streams[component.component_id] = component.get_max_streams_of_all_ports_divided_by_type()
        return component_streams

    def get_max_streams_of_component(self, component_name: str) -> dict:
        """

        Args:
            component_name (str): Name of the component for which the streams should be returned

        Returns:
            dict: Streams of the component divided by types
        """
        max_streams_of_all_components = self.get_max_streams_of_all_components()
        if component_name in max_streams_of_all_components:
            return max_streams_of_all_components[component_name]
        else:
            return None

    def get_streams_of_all_components(self) -> dict:
        """
        Returns:
            dict: Streams of all components divided by stream_types
        """
        component_streams = {}
        for component in self.component_economic_results:
            component_streams[component.component_id] = component.get_streams_of_all_ports_divided_by_type()
        return component_streams

    def get_streams_of_component(self, component_name: str) -> dict:
        """

        Args:
            component_name (str): Name of the component for which the streams should be returned

        Returns:
            dict: Streams of the component divided by types
        """
        streams_of_all_components = self.get_streams_of_all_components()
        if component_name in streams_of_all_components:
            return streams_of_all_components[component_name]
        else:
            return None

    def get_stream_annuities_of_all_components(self) -> dict:
        """
        Returns:
            dict: Annuities for streams of all components divided by stream_types
        """
        stream_annuities = {}
        for component in self.component_economic_results:
            single_stream_annuities = {}
            for stream_result in component.component_economic_results.component_stream_cost:
                single_stream_annuities[stream_result.stream_type] = stream_result.get_annuities()
            stream_annuities[component.component_name] = single_stream_annuities
        return stream_annuities

    def get_stream_annuity_of_component(self, component_name: str) -> dict:
        """
        Args:
            component_name (str): Name of the component

        Returns:
            dict: Annuities for streams of the component divided by stream_types
        """
        stream_annuities_of_all_components = self.get_stream_annuities_of_all_components()
        if component_name in stream_annuities_of_all_components:
            return stream_annuities_of_all_components[component_name]
        else:
            logging.warning(
                f'Trying to get stream annuity for component {component_name} which is not included in model!')

    @staticmethod
    def create_system_results(modelbase: ModelBase):
        """
        Function creates the output of the whole system and sets it to the system_result variable of the model

        """
        system_results = SystemResults(basic_econ_system_settings=modelbase.basic_economical_settings,
                                       basic_technical_settings=modelbase.basic_technical_settings,
                                       branch_information=BranchInfo(branches=modelbase.branches))
        if modelbase._costs_calculated:
            system_results.costs_calculated = True
        for component in modelbase.components.values():
            component.component_economic_results.set_component_annuity()

            component.component_technical_results.ports = []
            for port in component.ports.values():
                component.component_technical_results.ports.append(port.port_results.create_technical_results_of_port())
            #            TODO: from here?

            system_results.component_technical_results.append(component.component_technical_results)
            system_results.component_economic_results.append(component.component_economic_results)
        system_results.port_results.extend(PortResult.instances)
        system_results.set_overall_annuity()
        return system_results

    def export_pickle(self, log_file_dir: str = 'templates', file_name: str = None):
        """

        This code exports the result as pickle and json - File

        Args:
            log_file_dir (str): Directory where the files should be saved
            file_name (str): Name of the file

        """

        class NumpyEncoder(json.JSONEncoder):
            """ Special json encoder for numpy types """

            def default(self, obj):
                if isinstance(obj, np.integer):
                    return int(obj)
                elif isinstance(obj, np.floating):
                    return float(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                return json.JSONEncoder.default(self, obj)

        x = datetime.datetime.now()
        mytime = x.strftime("%y%m%d-%H%M%S")

        log_file_dir = Path(self.modeldir).parents[2].__str__() + log_file_dir

        self.create_system_results()

        export_dictionary = asdict(self.system_result)
        json_string = json.dumps(export_dictionary, cls=NumpyEncoder)
        if file_name != None:
            output_file = open(log_file_dir + os.path.sep + file_name + '.json', 'wb')
        else:
            output_file = open(log_file_dir + os.path.sep + self.modelname + '-' + mytime + '.json', 'wb')

        json.dump(self.system_result, output_file)

        output_file.close()
