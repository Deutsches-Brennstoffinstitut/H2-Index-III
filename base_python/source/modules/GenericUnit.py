import logging
import math
from scipy.interpolate import interp2d
from scipy import interpolate
import numpy as np
import json
import base_python.source.helper.VDI2067_Equations as VDI2067
from base_python.source.model_base.Port import Port
from base_python.source.model_base.Port_Energy import Port_Energy
from base_python.source.model_base.Dataclasses.TechnicalDataclasses import Efficiencies, Efficiency
from base_python.source.model_base.Port_Mass import Port_Mass
from base_python.source.basic.Streamtypes import StreamEnergy
from base_python.source.basic.Quantities import PhysicalQuantity, get_unit_of_quantity
from base_python.source.helper.Conversion import Time_Conversion
import base_python.source.helper.VDI2067_Equations as vdi
from base_python.source.model_base.Dataclasses.ExportDataclasses import *
from base_python.source.model_base.Dataclasses.TechnicalDataclasses import *
from enum import Enum
from strenum import StrEnum
from base_python.source.basic.Streamtypes import StreamDirection
from base_python.source.basic.CustomErrors import ComponentError
from base_python.source.helper.misc import create_id


class GenericUnit:
    COMPONENT_ID_COUNT = 0

    def __init__(self, size: float = None, technology: Enum = None, active: bool = False,
                 new_investment: bool = False, economical_parameters: EconomicalParameters = EconomicalParameters(),
                 stream_type: StreamEnergy = None, generic_technical_input: GenericTechnicalInput = None):

        """
            Basic init method of the generic unit as basis for all other components

        Args:
            size (float):           Size of the component. The unit depends on the component type
            technology (Enum):      Technology of component, which defines the investment and the efficiency loaded from
                                    database
            active (bool):          Boolean whether the component is an active or passive component
            new_investment (bool):  Boolean whether the component is a new investment or not
            economical_parameters (EconomicalParameters): Contains all economical parameters of a class
            stream_type (StreamEnergy): StreamType of the component which is only given for components which can be
                                        used with any type of stream
            pressure (dict):        Dictionary of pressure values at specific ports
            temperature (dict):     Dictionary of temperature values at specific ports
        """
        self.active = active  # True: define the whole module as active, False: Module is controlled by system
        self.component_economical_parameters = economical_parameters
        self.new_investment = new_investment
        self.size = size  # size of unit, definition varies between units)
        self.technology = technology
        self.stream_type = stream_type  # specifies the controlled port (e.g. components medium type)
        self.database_status = 0
        self.is_sub_component = False
        self.name: str = None
        self.branch_id = None
        self.component_id = self.set_id()
        self.lifecycle_database = None
        self.status = 0
        self.investment_function_database = None
        self.time_resolution = None  # length of timesteps in Minutes
        self.controlled_port = None
        self.number_of_ports = 0
        self.loop_control = None  # porttype of a loop controlled active port
        self.port_limits = None
        self.fixed_invest = False
        self.sub_components = {}

        self.port_types = {}
        self.ports = {}
        self.efficiencies = Efficiencies(
            class_name=self.__class__.__name__,
            technology=self.technology,
            all_efficiencies=[])

        if generic_technical_input is not None:
            self.pressure = generic_technical_input.get_pressures()
            self.temperature = generic_technical_input.get_temperatures()
            self.efficiencies.add_new_efficiencies(generic_technical_input.get_efficiencies())
        else:
            self.pressure = None
            self.temperature = None

        self.component_economic_results: ComponentEconResults = ComponentEconResults(branch_id=self.branch_id,
                                                                                     component_id=self.component_id)
        self.component_technical_results: ComponentTechnicalResults = ComponentTechnicalResults(
            branch_id=self.branch_id,
            component_id=self.component_id,
            size=self.size,
            component_history={'status': []})

        if self.component_economical_parameters is not None and self.component_economical_parameters.component_capex is not None:
            self.fixed_invest = True

    ###################################
    # Initialisation Methods
    ###################################
    def set_branch_id(self, branch_id: str):
        self.branch_id = branch_id
        self.component_technical_results.set_branch_id(branch_id=branch_id)
        self.component_economic_results.set_branch_id(branch_id=branch_id)

    def update_efficiency(self, medium_referenced, medium_calculated, load_values, efficiency_values):
        self.efficiencies.update_efficiency(medium_referenced, medium_calculated, load_values, efficiency_values)
        self.set_properties()

    def _reset_port_history(self):
        for port in self.ports.values():
            port.reset_history()

    def _reset_component_history(self):
        for key, value in self.component_technical_results.component_history.items():
            self.component_technical_results.component_history[key] = []

    def set_generic_properties(self):
        """
        This function is called after model initialisation to set properties which should be set for all the components
        generically

        """

        if self.pressure is not None:
            for pressure_item in self.pressure:
                port = self.get_ports_by_type_and_sign(pressure_item.get_stream_type(), pressure_item.get_direction())
                if port is None:
                    logging.warning(
                        f'Could not set pressure of Component {self.__class__.__name__} for port '
                        f'({pressure_item.get_stream_type()},{pressure_item.get_direction()})')
                else:
                    if get_unit_of_quantity(PhysicalQuantity.pressure) == pressure_item.get_unit():
                        port.set_pressure(pressure_item.get_value())
                    else:
                        logging.warning(
                            f'Given pressure unit of Component {self.__class__.__name__} for port '
                            f'({pressure_item.get_stream_type()},{pressure_item.get_direction()}) doesnt '
                            f'match {get_unit_of_quantity(PhysicalQuantity.pressure)}')

        if self.temperature is not None:
            for temperature_item in self.temperature:
                port = self.get_ports_by_type_and_sign(temperature_item.get_stream_type(),
                                                       temperature_item.get_direction())
                if port is None:
                    logging.warning(
                        f'Could not set temperature of Component {self.__class__.__name__} for port '
                        f'({temperature_item.get_stream_type()},{temperature_item.get_direction()})')
                else:
                    if get_unit_of_quantity(PhysicalQuantity.temperature) == temperature_item.get_unit():
                        port.set_temperature(temperature_item.get_value())
                    else:
                        logging.warning(
                            f'Given temperature unit of Component {self.__class__.__name__} for port '
                            f'({temperature_item.get_stream_type()},{temperature_item.get_direction()}) doesnt '
                            f'match {get_unit_of_quantity(PhysicalQuantity.temperature)}')

    def _add_port(self, component_ID: str, port_type: Enum, fixed_status: bool = False,
                  sign: StreamDirection = StreamDirection.stream_bidirectional, unit: str = None,
                  external_identifier=None) -> Port:
        """
        Basic method to add a new port to the instance of the component

        Args:
            port_type (Enum): Stream_type of the port (e.g. 'electric', 'HYDROGEN', 'MIX')
            port_type (Enum): Stream_type of the port (e.g. 'electric', 'HYDROGEN', 'MIX')
            fixed_status (bool): True if the port has fixed values based on size or profile
            sign (StreamDirection): Sign of the port whether it takes from the branch or gives to the branch
            unit (str): Unit of the port (kg, kW)

        Returns:
            Port: Port Object of the created port

        """
        port_id = create_id(letter='P', number=self.number_of_ports)
        self.number_of_ports += 1

        port = None
        if isinstance(port_type, StreamEnergy):
            port = Port_Energy(component_ID=component_ID, port_id=port_id, port_type=port_type,
                               fixed_status=fixed_status, sign=sign, unit=unit,
                               external_identifier=external_identifier)
        elif isinstance(port_type, StreamMass):
            port = Port_Mass(component_ID=component_ID, port_id=port_id, port_type=port_type, fixed_status=fixed_status,
                             sign=sign, unit=unit,
                             external_identifier=external_identifier)
        else:
            logging.critical(f'Port of {self.__class__.__name__} of type {port_type} could not be created '
                             f'due to undefined port_type')
        if port is not None:
            self.ports[port_id] = port
            if port_type in self.port_types:
                self.port_types[port_type].append(port_id)
            else:
                self.port_types[port_type] = [port_id]

        return port

    ###################################
    # GET Methods
    ###################################
    def get_types_of_all_ports(self) -> dict:
        """

        Returns:
            dict: All stream_types connected to the component
        """

        return self.port_types

    def get_technology(self):
        """

        Returns:
            Enum: Technology
        """
        return self.technology

    def get_port_by_id(self, port_id: str) -> Port:
        """
        Function to get the connected port object specified by its id

        Args:
            port_id (str): ID of the desired port

        Returns:
            Port: Port Object of the searched port by id
        """

        return self.ports[port_id]

    def get_port_by_external_identifier(self, external_identifier: Enum) -> Port:
        """
        Function to get the connected port object specified by its external identifier

        Args:
            port_id (Enum): Id of the desired port

        Returns:
            Port: Port Object of the searched port by id
        """
        for port in self.ports.values():
            if port.get_external_identifier() == external_identifier:
                return port

    def get_ports_by_type(self, port_type: Enum) -> list:
        """
        Function to get all connected port objects specifed by the stream type of the port

        Args:
            port_type (str): Stream type of the port

        Returns:
            list: List of all ports connected related to that stream type
        """

        if port_type in self.port_types:
            return [self.ports[port_id] for port_id in self.port_types[port_type]]
        else:
            return None

    def get_size(self) -> float:

        """

        Returns:
            float: Size value of the component
        """
        return self.size

    def get_status(self):
        """

        Returns:
            int: Status of the component (0 - all fine, 1 - problem occured (recalculation)
        """
        return self.status

    def _get_efficiency_dataframe(self, medium_referenced, medium_calculated):
        efficiency = self.efficiencies.get_efficiency_by_media(medium_referenced, medium_calculated)
        return efficiency.efficiencies_at_load

    def _get_efficiency(self, medium_referenced: Enum = None, medium_calculated: Enum = None) -> interpolate.interp1d:
        """
        This function is used to get a specific conversion efficiency of the component which is loaded from the database
        (e.g. Efficiency of conversion from electricity to hydrogen)
        Args:
            medium_referenced (Enum): The base medium of the conversion in example electricity
            medium_calculated (Enum): The resulting medium of conversion in example hydrogen

        Returns:
            interp1d: Interpolation of loads and conversion rates for the given media
        """
        efficiency = self.efficiencies.get_efficiency_by_media(medium_referenced, medium_calculated)
        if efficiency is not None:
            interp_funct = interpolate.interp1d(efficiency.load_range, efficiency.efficiencies_at_load)
            return interp_funct
        else:
            logging.critical(
                f'No efficiency given for component {self.__class__.__name__} for '
                f'{(medium_referenced, medium_calculated)}')
            # Check whether more than one efficiency of this type is given
            return None

    def get_ports(self) -> dict:
        """
        Returns:
            dict: Dictionary of all connected ports
        """
        return self.ports

    def get_adaptive_ports(self) -> list:
        """

        Returns:
            list: List of all adaptive ports
        """
        port_list = []
        for port_id, port in self.ports.items():
            if not port.get_fixed_status():
                port_list.append(port_id)
        return port_list

    def get_ports_by_type_and_sign(self, port_type: Enum, sign: StreamDirection, external_identifier=None) -> Port:
        """

        Args:
            port_type (Enum): stream_type of the wanted port
            sign (StreamDirection): Sign of the wanted port ( -1, 0, 1)

        Returns:
            Port: Returns list if more than one port found otherwise returns the single port
        """
        if external_identifier is not None:
            ports = self.get_port_by_external_identifier(external_identifier)
            if ports is None:
                logging.critical(
                    f'Could not find desired port of component {self.__class__.__name__} for identifier {external_identifier}')
            else:
                return ports

        if sign != StreamDirection.stream_bidirectional:
            ports = list(filter(lambda x: x.get_sign() == sign, self.ports.values())) + list(
                filter(lambda x: x.get_sign() == StreamDirection.stream_bidirectional, self.ports.values()))
        else:
            ports = list(filter(lambda x: x.get_sign() == sign, self.ports.values()))
        ports = list(filter(lambda x: x.get_type() == port_type, ports))

        if len(ports) == 1:
            return ports[0]
        elif len(ports) > 1:
            logging.warning(
                f'More than one port found for port type {port_type} and sign {sign} at component {self.__class__.__name__}. Returned first unlinked one if both are linked returning first')
            for single_port in ports:
                if single_port.get_linked_branch() is None:
                    return single_port
            return ports[0]

        else:
            return None

    ###################################
    # SET Methods
    ###################################

    def set_name(self, name: str):
        """
        Sets the name of the component
        """
        self.name = name
        self.component_result.component_name = name

    @classmethod
    def set_id(cls) -> str:
        """Class-Method to create a Unique Component_ID, based on the class-variable COMPONENT_ID_COUNT which gets
         incremented each time a new Component is created.

        Notes:
            https://mail.python.org/pipermail/python-list/2003-April/237870.html
            The Try|Except expression is needed in case the ID has to be set from the main class (Generic Unit)
            The main class is the base, so it cant orginate from a base
            The reason why it is "complicated" is, due to how inhertance works.
            https://stackoverflow.com/questions/19719767/override-class-variable-in-python#19719856
            So, in order to fix the issue with the unique IDs for components i "point" at the GenericUnit

        Returns:
            component_id: Unique String consisting of the letter "C" and two digits
        """

        try:  # if function is called from Child of GenericUnit
            cls.__mro__[-2].COMPONENT_ID_COUNT += 1 # https://mail.python.org/pipermail/python-list/2003-April/237870.html
            _ = cls.__mro__[-2].COMPONENT_ID_COUNT
        except AttributeError:  # in case of function is called from GenericUnit (It is the base, so it cant orginate from a base...)
            cls.COMPONENT_ID_COUNT += 1
            _ = cls.COMPONENT_ID_COUNT
        finally:
            component_id = create_id(letter='C', number=_)
        return component_id

    def save_state(self):
        """
        Function to save the state of the component (several attributes can be saved and printed out (e.g. status,
        pressure, temperature)

        """
        self.component_technical_results.component_history['status'].append(self.status)

    def set_sub_component(self, component: object, name=None):
        """
        Adds a sub component to the main component which can be used to do internal calculations

        Args:
            component (object): Sub-component object

        """
        if name is None:
            name = component.__class__.__name__
        else:
            name = name
        self.sub_components[name] = component
        component.make_sub_component('sub_component')

    def get_sub_components(self):
        """

        Returns:
            dict: Sub components of this component
        """
        return self.sub_components

    def make_sub_component(self, link_id):
        self.is_sub_component = True
        for port in self.ports.values():
            port.set_linked_branch(link_id)

    def set_time_resolution(self, time_resolution: int):
        """
        Sets the time resolution of the component to the models resolution

        Args:
            time_resolution (int): Time_resolution of the model

        """
        self.time_resolution = time_resolution

    def _set_fixed_port(self, port_type: Enum, port_sign: StreamDirection):
        """
        Sets the given port as a fixed port (all other ports are not influenced)

        Args:
            port_type (Enum): stream_type of the port (e.g. StreamEnergy.ELECTRIC)
            port_sign (StreamDirection): Sign of the port to define the stream direction meant (0, -1, 1)

        """

        port = self.get_ports_by_type_and_sign(port_type, port_sign)
        if isinstance(port, list):
            logging.warning('Could not set fixed status due to ports with same type and sign')
        else:
            port.set_fixed_status(True)

    def _set_adaptive_port(self, port_type: Enum, port_sign: StreamDirection):
        """
        Sets all the connected ports to fixed except the one given

        Args:
            port_type (Enum): stream_type of the port (e.g. StreamEnergy.ELECTRIC)
            port_sign (StreamDirection): Sign of the port to define the stream direction meant (0, -1, 1)

        """

        self.controlled_medium = (port_type.casefold(), port_sign)
        for port in self.ports.values():
            if port.get_sign() != port_sign or port.get_type() != port_type:
                port.set_fixed_status(True)
            else:
                port.set_fixed_status(False)

    def set_properties(self):
        """
        Calculate object specific properties, is called after model definition. This function is overwritten by
        components

        """
        return None

    def set_binary_profile_to_port(self, profile: list, port_type: Enum, port_sign: StreamDirection,
                                   external_identifier=None):
        """
        Function is used to limit the max load of the component to a specific value

        Args:
            profile (list):     Load profile of the component
            port_type (Enum):   Stream_type of the port which should get the profile (e.g. StreamEnergy.ELECTRIC)
            port_sign (StreamDirection):    Sign of the port which describes the possible direction, to define
                                            which port should get the profile (-1, 0, 1)

        """
        if external_identifier is not None:
            port = self.get_port_by_external_identifier(external_identifier)
        else:
            port = self.get_ports_by_type_and_sign(port_type, port_sign)
        port.set_port_binary_profile(profile, port_sign)

    def set_profile_to_port(self, profile: list, port_type: Enum, port_sign: StreamDirection,
                            profile_type: PhysicalQuantity, time_resolution=None, active: bool = True,
                            external_identifier=None):
        """
        Sets a profile to the component

        Args:
            port_type (Enum):               Stream_type of the port which should get the profile
                                            (e.g. StreamEnergy.ELECTRIC)
            port_sign (StreamDirection):    Sign of the port which describes the possible direction, to define
                                            which port should get the profile (-1, 0, 1)
            profile (list):                 Desired profile for the component
            profile_type(PhysicalQuantity): Type of the profile
                                            (e.g. PhysicalQuantity.stream, PhysicalQuantity.temperature)
            time_resolution (int):          Time-resolution of the profile
            active (bool):                  Decides whether the component is now active

        """
        if external_identifier is not None:
            port = self.get_port_by_external_identifier(external_identifier)
        else:
            port = self.get_ports_by_type_and_sign(port_type, port_sign)
        if port is None:
            logging.warning(
                f'Could not find the desired port of component {self.component_id} of type '
                f'{profile_type} to set profile.')
        else:
            self.controlled_port = port
            port.set_port_profile(profile_type, profile)
            self.active = active  # active components do have a profile

            if self.time_resolution is None or self.time_resolution == time_resolution:
                self.time_resolution = time_resolution
            else:
                raise ComponentError(f'Time_resolution of component {self.component_id} of type {profile_type} doesn\'t'
                                     f' match given time_resolution')

    def set_size(self, size: float):
        """
        Necessary of the size of the component changes after initialization of the model
        Args:
            size (float): Size of the component ( in kW or kg depending on stream type)
        """
        self.size = size
        self.set_properties()

    def set_controlled_active_port(self, port, value: float):
        """


        Args:
            port_type (Enum):            Stream type of the port that shall be set for loop control
            port_sign (StreamDirection): Sign of the port to define the stream direction meant
            value (float):               Loop control value that is set to the component

        """

        self.loop_control = (port, value)

    def clear_controlled_active_port(self):
        """
        Clear the loop controlled_port and the loop control value for the next runcount

        """
        self.loop_control = None

    def _set_opex_fix_invest_from_database(self, database_cursor):
        """
        Sets the investment costs of the component from database

        Args:
            database_cursor (): Database cursor given by database connection
        """

        table = 'TECHNOLOGY'
        if self.technology is not None:
            attributes = ['OPEX_SIZE_SPECIFIC']
            conditions = ["CLASS='" + str(self.__class__.__name__).upper() + "'",
                          "TECHNOLOGY='" + self.technology.name + "'"]
            database_cursor.execute("SELECT " + ", ".join(attributes) +
                                    " FROM " + table +
                                    " WHERE " + ' AND '.join(conditions))
            result = database_cursor.fetchall()

            if len(result) > 1:
                logging.warning(f'Key for opex not unique! ({str(self.__class__.__name__)} {self.technology})')
            if result:
                self.component_economical_parameters.operational_opex.set_overall_opex_in_percentage_per_year(
                    result[0][0] / 100)
            else:
                logging.warning(f'Could not get opex for: ({str(self.__class__.__name__)} {self.technology})')
                self.database_status = 1
                return None

    def _set_life_cycle_from_database(self, database_cursor):
        """
        Sets the life_cycle of the component from database

        Args:
            database_cursor (): Database cursor given by database connection
        """

        table = 'TECHNOLOGY'
        attributes = ['LIFE_CYCLE']
        if self.technology is not None:
            database_cursor.execute("SELECT " + ", ".join(attributes) +
                                    " FROM " + table +
                                    f" WHERE CLASS ='{str(self.__class__.__name__).upper()}" +
                                    f"' AND TECHNOLOGY='{self.technology.name}'")
            result = database_cursor.fetchall()
            if len(result) > 1:
                logging.warning(f'Key for life cycle not unique! ({str(self.__class__.__name__)} {self.technology})')
            if result:
                capex_elements = [i.get_name() for i in self.component_economical_parameters.component_capex]
                if not 'DATABASE' in capex_elements:
                    self.component_economical_parameters.component_capex.append(
                        CAPEXParameters(name='DATABASE', life_cycle=result[0][0]))
                else:
                    element = self.component_economical_parameters.component_capex[capex_elements.index('DATABASE')]
                    element.set_life_cycle(result[0][0])
            else:
                logging.warning(f'Could not get life cycle for: ({str(self.__class__.__name__)} {self.technology})')
                self.database_status = 1

    def _set_efficiencies_from_database(self, database_cursor):
        """
        Sets the efficiencies of the component from database. Here are all efficiencies for the
        specified class type and technology saved to the objects attribute 'efficiencies'.

        Args:
            database_cursor (): Database cursor given by database connection
        """

        if self.technology is not None:
            table = 'EFFICIENCY'
            attributes = ['*']
            conditions = [f"CLASS='{str(self.__class__.__name__).upper()}'",
                          f"TECHNOLOGY='{self.technology.name}'"]
            database_cursor.execute("SELECT " + ", ".join(attributes) +
                                    " FROM " + table +
                                    " WHERE " + ' AND '.join(conditions))
            """ Result saves all rows which contain the specified class type and technology"""

            result = database_cursor.fetchall()
            field_names = [i[0] for i in database_cursor.description]

            """ Saving indices of the columns which contain the necessary informations"""
            ref_index = field_names.index('MEDIUM_REFERENCED')
            calc_index = field_names.index('MEDIUM_CALCULATED')
            unit_calc_index = field_names.index('UNIT_CALCULATED')
            unit_ref_index = field_names.index('UNIT_REFERENCED')
            size_index = field_names.index('SIZE')
            load_index = field_names.index('LOAD')
            efficiency_index = field_names.index('EFFICIENCY')

            """ Looping over all found efficiency rows """
            for single_result in result:
                """ Key should contain the StreamTypes which stream_type is converted in another"""
                key = [None, None]
                """ Check weather length of loads equals lengths of efficiency values"""
                if len(json.loads(single_result[load_index])) == len(json.loads(single_result[efficiency_index])):
                    load_series = json.loads(single_result[load_index])
                    efficiency_series = json.loads(single_result[efficiency_index])
                    "Creating the key"
                    for key_index, key_part in enumerate([single_result[ref_index], single_result[calc_index]]):
                        key_part = key_part.upper()
                        "Transforming the StreamTypes which are given as strings in database to the desired Enums for Model"
                        if key_part in [stream_type.name for stream_type in StreamEnergy]:
                            key[key_index] = StreamEnergy[key_part]
                        elif key_part in [stream_type.name for stream_type in StreamMass]:
                            key[key_index] = StreamMass[key_part]
                    "Transform the given units(str) from database into the internal used Enums"
                    if single_result[unit_ref_index] in [single_unit.value for single_unit in Unit]:
                        unit_referenced = Unit[single_result[unit_ref_index]]
                    else:
                        unit_referenced = None
                    if single_result[unit_calc_index] in [single_unit.value for single_unit in Unit]:
                        unit_calculated = Unit[single_result[unit_calc_index]]
                    else:
                        unit_calculated = None

                    "Creating a new efficiency dataclass and store it in efficiencies of the component"
                    new_efficiency = Efficiency(
                        medium_referenced=key[0],
                        medium_calculated=key[1],
                        unit_referenced=unit_referenced,
                        unit_calculated=unit_calculated,
                        load_range=load_series,
                        efficiencies_at_load=efficiency_series
                    )
                    self.efficiencies.add_new_efficiency(new_efficiency)
                else:
                    logging.warning(f'Could not load efficiency of {str(self.__class__.__name__).upper()} '
                                    f'{self.technology} at size {single_result[size_index]} because of not '
                                    f'usable data quality.')

            "Check whether all set efficiencies have their discontinuity at the same load level"
            for single_efficiency in self.efficiencies.all_efficiencies:
                for element in single_efficiency.load_range:
                    if list(single_efficiency.load_range).count(element) > 1:
                        for sub_efficiency in self.efficiencies.all_efficiencies:
                            if not list(single_efficiency.load_range).count(element) > 1:
                                logging.critical(
                                    f'Efficiency of {str(self.__class__.__name__).upper()}{self.technology}'
                                    f'for transformation {sub_efficiency.medium_referenced, sub_efficiency.medium_calculated} does not include required discontinuity '
                                    f'of efficiency {single_efficiency.medium_referenced, single_efficiency.medium_calculated}'
                                )

    def _set_capex_funct_from_database(self, database_cursor):
        """
        Sets the capex function of the component from database

        Args:
            database_cursor (): Database cursor given by database connection
        """
        table = 'INVESTMENT'
        if self.technology is not None:
            attributes = ['*']
            conditions = ["CLASS='" + str(self.__class__.__name__).upper() + "'",
                          "TECHNOLOGY='" + self.technology.name + "'"]
            database_cursor.execute("SELECT " + ", ".join(attributes) +
                                    " FROM " + table +
                                    " WHERE " + ' AND '.join(conditions))
            result = database_cursor.fetchall()
            field_names = [i[0] for i in database_cursor.description]
            invest_index = field_names.index('YEAR_INVEST_1')
            scales = [val[field_names.index('SIZE')] for val in result]
            years = []
            values = []
            if result:
                for field_index, field_content in enumerate(field_names[invest_index:]):
                    actual_index = invest_index + field_index
                    if 'YEAR' in field_content:
                        years_single = [i[actual_index] for i in result]
                        if all(x == years_single[0] for x in years_single):
                            if years_single[0] is not None:
                                years.append(years_single[0])
                    if 'INVEST' in field_content and '_INVEST' not in field_content:
                        values_single = [i[actual_index] for i in result]
                        if values_single:
                            if not all(x is None for x in values_single):
                                if None not in values_single:
                                    values.append(values_single)
                                else:
                                    logging.warning(
                                        f'None Value found in investment costs of {str(self.__class__.__name__).upper()}'
                                        f' {self.technology.upper()} size {scales[values_single.index(None)]} in '
                                        f'year {years[-1]}')
                if values:
                    investment_function = interp2d(scales, years, values)
                    capex_elements = [i.get_name() for i in self.component_economical_parameters.component_capex]
                    if not 'DATABASE' in capex_elements:
                        self.component_economical_parameters.component_capex.append(
                            CAPEXParameters(name='DATABASE', investment_function=investment_function))
                    else:
                        element = self.component_economical_parameters.component_capex[capex_elements.index('DATABASE')]
                        element.set_investment_function(investment_function)
                else:
                    logging.warning(f'Could not get investment function for: {str(self.__class__.__name__)} ,'
                                    f' {self.technology}')
                    self.database_status = 1
            else:
                logging.warning(f'Could not get investment function for: {str(self.__class__.__name__)} ,'
                                f' {self.technology}')
                self.database_status = 1

    ###################################
    # calculation Methods
    ###################################

    def load_database(self, database_cursor: object):
        """
        Method to load all necessary values from the database

        Args:
            database_cursor (object): Database cursor given by database connection
        """

        if self.component_economical_parameters is not None:
            if self.component_economical_parameters.get_database_bool() is True:
                if self.component_economical_parameters.get_all_capex_elements() is None:
                    self.component_economical_parameters.component_capex = []
                self._set_capex_funct_from_database(database_cursor)
                self._set_life_cycle_from_database(database_cursor)

                if self.component_economical_parameters.get_operational_opex() is not None:
                    if self.component_economical_parameters.operational_opex.get_database_bool() is True:
                        self._set_opex_fix_invest_from_database(database_cursor)
                else:
                    self.component_economical_parameters.operational_opex = OPEXOperationalParameters(
                        use_database_values=True)
                    self._set_opex_fix_invest_from_database(database_cursor)
        # print(self.__class__.__name__)
        self._set_efficiencies_from_database(database_cursor)

    def _calc_control_var(self, port: Port, port_value: float):

        """
        Sets the loop controlled value to the desired controlled port

        Args:
            port (Port): ID of the port that shall be actively controlled
            port_value (float): Value that would solve the branch

        """
        # check if control strategy is temporarily changed
        loop_control = self.loop_control is not None  # if empty then we are not in loop control mode
        if loop_control:
            ports = self.loop_control[0]
            controlled_value = self.loop_control[1]
            if type(ports) == list:
                logging.warning(
                    f'Two ports of same type found for component {self.__class__.__name__} took the first one.')
                controlled_port = ports[0]
            else:
                controlled_port = ports
            self.status = 1  # add warning to output file

        else:
            controlled_port = port
            controlled_value = port_value

        return [controlled_port, controlled_value, loop_control]

    def calc_stream_economics(self, basic_economical_settings: BasicEconomicalSettings):

        """
        This function is used to calculate the costs which are caused by the energy and
        mass streams. The results are saved in self.component_economic_results

        Args:
            basic_economical_settings: Basic settings of the calculated system

        """
        self.component_economic_results.component_stream_cost = []

        def _get_price_development_until_first_payment(time_period_until_first_payment: int, price_dev_factor: float,
                                                       inflation: float) -> float:
            """
                This function is used to calculate the price development of a cost component until the first payment
                must be performed

            Args:
                time_period_until_first_payment (int):  Years until the first payment must be performed
                price_dev_factor (float):               Yearly price developement factor of the cost component
                inflation (float):                      Yearly inflation rate

            Returns:
                float: Price_developement_factor until the first payment must be performed
            """

            return (inflation + price_dev_factor) ** time_period_until_first_payment

        def _calc_annuity(value: float, annuity_factor: float, price_dyn_factor: float, discount: float) -> float:
            """
            Calculates the annuity based on the annuity_factor and the price_dynamic_factor

            Args:
                value (float):              Cost value for which the annuity shall be calculated
                annuity_factor (float):     Annuity factor based on VDI 2067
                price_dyn_factor (float):   Price dynamic factor based on VDI 2067

            Returns:
                float: Annuity value of the cost component
            """

            return value * annuity_factor * price_dyn_factor * discount

        if self.component_economical_parameters.stream_econ is not None:

            """ Loop over all stream cost components which are set for the component in the system description """

            for single_stream_econ_component in self.component_economical_parameters.stream_econ:

                """ Generate an result object and calculate annuity_factor and price_dyn_factor """

                """Time ranges"""
                total_time_period = basic_economical_settings.total_time_period
                time_period_reference_until_first_payment = single_stream_econ_component.first_payment_year - \
                                                            basic_economical_settings.reference_year
                element_time_period = basic_economical_settings.end_year - \
                                      single_stream_econ_component.first_payment_year + 1

                stream_econ_delay_time = single_stream_econ_component.first_payment_year - \
                                         basic_economical_settings.start_year

                interest_rate_factor = basic_economical_settings.basic_interest_rate_factor \
                    if single_stream_econ_component.interest_rate_factor \
                       is None else single_stream_econ_component.interest_rate_factor

                inflation = basic_economical_settings.estimated_inflation_rate if single_stream_econ_component.get_include_inflation() else 0
                price_dev_factor = single_stream_econ_component.price_dev_factor
                econ_result = SingleStreamEconResult(stream_type=single_stream_econ_component.stream_type,
                                                     input_parameters=single_stream_econ_component,
                                                     costs={})

                annuity_factor = VDI2067.annuity_factor(interest_rate_factor,
                                                        total_time_period)
                # TODO: Überprüfen was passiert, wenn eine Komponente erst später dazu kommt (z.B. Elektrolyseur), welche einen Einfluss auf die technische Berechnung hat
                price_dyn_factor = VDI2067.price_dyn_factor_b(interest_rate_factor,
                                                              price_dev_factor,
                                                              element_time_period)

                discount = 1 / (interest_rate_factor ** stream_econ_delay_time)

                price_development_until_first_payment = _get_price_development_until_first_payment(
                    time_period_reference_until_first_payment,
                    price_dev_factor, inflation)

                """ Get all ports of the component which are the same stream type as the given stream cost definition 
                and loop over these ports """

                ports = self.get_ports_by_type(single_stream_econ_component.stream_type)
                if ports is None:
                    logging.warning(f'Desired stream costs could not be set for '
                                    f'{single_stream_econ_component.stream_type} '
                                    f'at component {self.__class__.__name__}')
                for single_port in ports:

                    """ Calculation of the yearly fixed costs set in the system definition"""

                    for direction, cost_component in {
                        'in': single_stream_econ_component.yearly_fixed_costs.costs_in,
                        'out': single_stream_econ_component.yearly_fixed_costs.costs_out
                    }.items():

                        if cost_component is not None:

                            """ Loop over the defined single Cost specification such as 'Maintenance' """

                            for name_cost_component, single_cost_component in cost_component.items():

                                """Check in stream history whether this direction of the port is actually used
                                if not, no costs will be added """

                                """Calculation of price development for the single stream until first payment """

                                single_cost_component *= price_development_until_first_payment

                                sign = StreamDirection.stream_into_component if direction == 'in' else \
                                    StreamDirection.stream_out_of_component
                                abs_stream_history = single_port.get_stream_history_by_sign(sign)
                                fixed_stream_economics = 0
                                if sum(abs_stream_history) != 0:
                                    fixed_stream_economics = single_cost_component

                                """Add cost parameters to the econ_result"""

                                econ_result.set_cost_parameter(direction, 'fixed', name_cost_component,
                                                               fixed_stream_economics)
                                econ_result.set_annuity_parameter(direction, 'fixed', name_cost_component,
                                                                  _calc_annuity(fixed_stream_economics,
                                                                                annuity_factor, price_dyn_factor,
                                                                                discount))

                    """ Calculation of the amount related costs which are related to the absolute amount of energy 
                    in kWh or the amount of mass in kg. These costs can be given as list or as float. If a list is 
                    given the profile must have the same length as the profiles of the system """

                    for direction, cost_component in {
                        'in': single_stream_econ_component.amount_related_costs.costs_in,
                        'out': single_stream_econ_component.amount_related_costs.costs_out
                    }.items():
                        if cost_component is not None:

                            """ Looping over the single amount_related cost components given for this stream 
                            (e.g. commodity price)"""

                            for name_cost_component, single_cost_component in cost_component.items():

                                """Calculation of price development for the single stream until first payment """

                                single_cost_component *= price_development_until_first_payment

                                sign = StreamDirection.stream_into_component if direction == 'in' else \
                                    StreamDirection.stream_out_of_component
                                abs_stream_history = list(map(abs, single_port.get_stream_history_by_sign(sign)))

                                """Energy streams are given in kW instead of kWh so they have to be converted from 
                                power to energy"""
                                energy_conversion_factor = 1.0 if not isinstance(single_port.get_stream_type(),
                                                                                 StreamEnergy) else \
                                    Time_Conversion.resolution2hour(self.time_resolution)
                                abs_stream_history = np.array(abs_stream_history) * energy_conversion_factor

                                """Checking whether the price is given as list and if this list has the desired length. 
                                If not, the mean value of the costs will be used."""

                                if isinstance(single_cost_component, list) or isinstance(single_cost_component, set):
                                    if not len(single_cost_component) == len(abs_stream_history):
                                        logging.critical(
                                            f'Cost component {name_cost_component} of component '
                                            f'{self.__class__.__name__}'
                                            f'does not match profile lengths with length {len(single_cost_component)}'
                                            f'calculated costs with mean value')
                                        amount_related_costs = np.mean(single_cost_component) * sum(abs_stream_history)
                                    else:
                                        amount_related_costs = np.array(single_cost_component) * abs_stream_history
                                else:
                                    amount_related_costs = single_cost_component * abs_stream_history

                                """Add costs parameter to the econ_result"""

                                econ_result.set_cost_parameter(direction, 'amount_related', name_cost_component,
                                                               amount_related_costs)
                                econ_result.set_annuity_parameter(direction, 'amount_related', name_cost_component,
                                                                  _calc_annuity(sum(amount_related_costs),
                                                                                annuity_factor, price_dyn_factor,
                                                                                discount))

                    """ Calculation of the costs which are related to the maximum power stream of the port in 
                    the desired direction (e.g. power price of electricity) """

                    for direction, cost_component in {
                        'in': single_stream_econ_component.power_related_costs.costs_in,
                        'out': single_stream_econ_component.power_related_costs.costs_out
                    }.items():
                        if cost_component is not None:

                            """ Loop over the single components in the power_related_costs dictionary """

                            for name_cost_component, single_cost_component in cost_component.items():

                                """Calculation of price development for the single stream until first payment """

                                single_cost_component *= price_development_until_first_payment

                                sign = StreamDirection.stream_into_component if direction == 'in' else \
                                    StreamDirection.stream_out_of_component
                                max_stream = single_port.get_max_stream_by_sign(sign)
                                power_related_costs = 0

                                """ For power related costs no price profiles are allowed, so an error will be thrown"""

                                if isinstance(single_cost_component, list) or isinstance(single_cost_component, set):
                                    logging.critical(f'Power related costs must be given as integer or float, '
                                                     f'a profile is not allowed!')
                                else:
                                    power_related_costs = single_cost_component * abs(max_stream)

                                """Add costs parameter to the econ_result"""

                                econ_result.set_cost_parameter(direction, 'power_related', name_cost_component,
                                                               power_related_costs)
                                econ_result.set_annuity_parameter(direction, 'power_related', name_cost_component,
                                                                  _calc_annuity(power_related_costs,
                                                                                annuity_factor, price_dyn_factor,
                                                                                discount))

                """ Add the new econ result to the list of all econ results for this component """
                self.component_economic_results.component_stream_cost.append(econ_result)

    def calc_capex(self, basic_economical_settings: BasicEconomicalSettings):
        """

        Args:
            basic_economical_settings:

        Returns:

        """

        """ get basic economical settings"""
        base_year = basic_economical_settings.start_year
        end_year = basic_economical_settings.end_year
        total_time_period = basic_economical_settings.total_time_period
        inflation = basic_economical_settings.estimated_inflation_rate
        interest_rate = basic_economical_settings.basic_interest_rate

        component_capex = None

        self.component_economic_results.component_CAPEX = []
        self.component_economic_results.component_variable_OPEX = []

        """ check if input parameters are given"""
        if self.component_economical_parameters is not None:
            component_capex = self.component_economical_parameters.component_capex

            database_capex_element = self.component_economical_parameters.get_capex_element_by_name('DATABASE')
            if self.component_economical_parameters.get_database_bool() is True:
                capex_elements = [database_capex_element]
            else:
                capex_elements = self.component_economical_parameters.get_all_capex_elements()
                if database_capex_element is not None:
                    capex_elements.remove(database_capex_element)

                """loop through all elements of one component"""
            if (capex_elements != None) & (capex_elements[0] != None):
                for capex_element in capex_elements:

                    """get element input parameters"""
                    element_name = capex_element.get_name()
                    investment_cost = capex_element.get_investment_costs()
                    investment_function = capex_element.get_investment_function()
                    funding = capex_element.get_funding_volume()
                    lifecycle = capex_element.get_life_cycle()
                    price_dev_factor = capex_element.get_price_dev_factor()
                    risk_factor = capex_element.get_risk_surcharge_factor()
                    if capex_element.interest_rate_factor is None:
                        interest_rate = basic_economical_settings.basic_interest_rate_factor
                        """-1 because interest_rate_factor is in basic settings, but interest rate has to be given to capex_element"""
                        capex_element.set_interest_rate(interest_rate - 1)
                    else:
                        interest_rate = capex_element.interest_rate_factor

                    """define timeframes"""
                    reference_year = capex_element.get_reference_year() if capex_element.get_reference_year() is not None \
                        else basic_economical_settings.get_basic_reference_year()
                    if capex_element.get_investment_year() is None:
                        investment_year = base_year
                        capex_element.set_investment_year(base_year)
                    else:
                        investment_year = capex_element.get_investment_year()
                    project_delay_time = base_year - reference_year
                    element_time_period = end_year - investment_year + 1
                    element_delay_time = investment_year - base_year
                    total_delay_time = investment_year - reference_year

                    price_dev_with_inflation = price_dev_factor + inflation

                    """adjust the costs for the first investment for the year of investment"""
                    if investment_cost is not None:
                        first_investment = investment_cost * price_dev_with_inflation ** (
                            total_delay_time) * risk_factor
                        funded_first_investment = (investment_cost - funding) * price_dev_with_inflation ** (
                            total_delay_time) * risk_factor
                    elif investment_function is not None and self.size is not None:
                        first_investment = float(investment_function(self.size, total_delay_time)) * self.size
                        funded_first_investment = (first_investment - funding * price_dev_with_inflation ** (
                            total_delay_time)) * risk_factor
                    else:
                        first_investment = 0
                        logging.warning(
                            f'Could not calculate CAPEX for {self.__class__.__name__, self.technology} of element {element_name}')

                    """-------------calculate annuities as described in VDI 2067-----------------"""
                    all_investments_element = []
                    all_investments_not_discounted = []
                    all_investments_not_discounted.append(funded_first_investment)
                    all_investments_element.append(funded_first_investment)

                    if lifecycle != 0:
                        """calculate annuity for elements which have a lifecycle e.g. electrolysis stacks"""

                        """calculate number costs for replacements"""
                        number_replacements = math.floor(element_time_period / lifecycle)

                        if number_replacements >= 1:
                            for replacement in range(1, number_replacements + 1):
                                if investment_cost is not None:
                                    replacement_invest = float(
                                        first_investment * price_dev_with_inflation ** (replacement * lifecycle))
                                elif investment_function is not None and self.size is not None:
                                    replacement_invest = float(investment_function(self.size,
                                                                                   total_delay_time + (
                                                                                           replacement * lifecycle)) * self.size)
                                else:
                                    replacement_invest = 0

                                replacement_invest_discounted = replacement_invest / (
                                        interest_rate ** (replacement * lifecycle))

                                all_investments_not_discounted.insert(replacement, replacement_invest)
                                all_investments_element.insert(replacement, replacement_invest_discounted)

                        """calculate remain value
                        -> discounting remain value to element invest_year"""

                        remain_value_element = all_investments_not_discounted[-1] * \
                                               ((number_replacements + 1) * lifecycle - element_time_period) / \
                                               lifecycle * \
                                               interest_rate ** (-element_time_period)

                        """ ------------------------ calculate annuity of capex ----------------------------------"""
                        annuity_factor = vdi.annuity_factor(interest_rate, total_time_period)
                        total_investment_element = sum(all_investments_element)

                        capex_annuity_element = (total_investment_element - remain_value_element) * \
                                                annuity_factor * interest_rate ** -element_delay_time

                    else:
                        remain_value_element = 0
                        """calculation for elements which have no lifecycle e.g. research & development"""
                        capex_annuity_element = first_investment / total_time_period

                    element_capex = ElementCAPEX(element_name=element_name, all_investments=all_investments_element,
                                                 input_parameters=capex_element,
                                                 annuity=capex_annuity_element, remain_value=remain_value_element)
                    """write capex_Data in ExportDataclass"""
                    self.component_economic_results.component_CAPEX.append(element_capex)

                    """ ----------------------calculate variable opex annuity (VDI 2067)--------------------------- """
                    if self.component_economical_parameters.get_operational_opex() is not None:
                        variable_opex_in_percent_of_invest = self.component_economical_parameters.operational_opex.get_operational_percentage()
                        if variable_opex_in_percent_of_invest is not None:
                            opex_first_payment_year = self.component_economical_parameters.operational_opex.get_first_payment_year()
                            if self.component_economical_parameters.operational_opex.get_inflation_bool():
                                opex_price_dev = price_dev_factor + inflation
                            else:
                                opex_price_dev = price_dev_factor

                            price_dynamic_factor = vdi.price_dyn_factor_b(interest_rate, opex_price_dev,
                                                                          element_time_period)
                            var_opex_at_first_investment_year = first_investment * variable_opex_in_percent_of_invest

                            if opex_first_payment_year is not None:
                                var_opex_at_first_payment_year = var_opex_at_first_investment_year * inflation ** (
                                        opex_first_payment_year - reference_year)
                            else:
                                var_opex_at_first_payment_year = var_opex_at_first_investment_year

                            """Calculate opex at the time of first payment year"""
                            var_opex_annuity_element = var_opex_at_first_payment_year * price_dynamic_factor * annuity_factor

                            var_opex_annuity_element = var_opex_annuity_element * interest_rate ** -element_delay_time

                            """write var_opex_data in ExportDataclass"""
                            element_var_opex = ElementVariableOPEX(element_name=element_name,
                                                                   first_investment=first_investment,
                                                                   percentage_of_invest=variable_opex_in_percent_of_invest,
                                                                   annuity=var_opex_annuity_element)
                            self.component_economic_results.component_variable_OPEX.append(element_var_opex)

    def calc_opex(self, basic_economical_settings: BasicEconomicalSettings):
        """
        calculate Annuities for fix OPEX

        Args:
            basic_economical_settings:


        """

        """get basic economical parameters"""
        base_year = basic_economical_settings.start_year
        end_year = basic_economical_settings.end_year
        total_time_period = end_year - base_year + 1
        inflation = basic_economical_settings.estimated_inflation_rate

        self.component_economic_results.component_fix_OPEX = []

        component_fix_opex = None
        if self.component_economical_parameters is not None:
            component_fix_opex = self.component_economical_parameters.fixed_opex

        if component_fix_opex is not None:

            """loop through all elements of one component"""
            for fix_opex_element in component_fix_opex:
                """get timeframes"""
                this_year = basic_economical_settings.reference_year
                first_payment_year = fix_opex_element.first_payment_year if fix_opex_element.first_payment_year \
                                                                            is not None else \
                    basic_economical_settings.start_year
                runout_year = fix_opex_element.runout_year if fix_opex_element.runout_year is not None else end_year

                project_delay_time = base_year - this_year
                element_time_period = runout_year - first_payment_year + 1
                element_delay_time = first_payment_year - base_year
                total_delay_time = first_payment_year - this_year

                """get input parameters"""
                name = fix_opex_element.name
                yearly_fixed_opex = fix_opex_element.yearly_fixed_opex
                interest_rate = fix_opex_element.interest_rate_factor if fix_opex_element.interest_rate_factor is \
                                                                         not None else \
                    basic_economical_settings.basic_interest_rate_factor

                """assumption: only the inflation influences the future price"""
                if fix_opex_element.get_include_inflation():
                    price_dev_with_inflation = inflation + 1
                else:
                    price_dev_with_inflation = 1

                """calculate annuities for fix OPEX (VDI 2067)"""
                price_dynamic_factor = vdi.price_dyn_factor_b(interest_rate, price_dev_with_inflation,
                                                              element_time_period)
                annuity_factor = vdi.annuity_factor(interest_rate, total_time_period)
                fix_opex_first_payment_year = yearly_fixed_opex * price_dev_with_inflation ** total_delay_time
                """ Calculation of annuity at first payment year of opex"""
                fix_opex_annuity_element = fix_opex_first_payment_year * \
                                           price_dynamic_factor * annuity_factor

                """Discounting of the opex to the project start year"""
                fix_opex_annuity_element = fix_opex_annuity_element * interest_rate ** -element_delay_time

                """write results in ExportDataclass"""
                element_fix_opex = ElementFixOPEX(element_name=name, opex_costs=fix_opex_first_payment_year,
                                                  first_payment_year=first_payment_year,
                                                  input_parameters=fix_opex_element, annuity=fix_opex_annuity_element)
                self.component_economic_results.component_fix_OPEX.append(element_fix_opex)

    # def reset_costs(self):
    #     """reset results for grid-search"""
    #     self.component_economic_results: ComponentEconResults = ComponentEconResults()
    #     self.component_technical_results: ComponentTechnicalResults = ComponentTechnicalResults(self.size,
    #                                                                                             self.component_technical_results.component_history)

    def calc_costs(self, basic_economical_settings: BasicEconomicalSettings):
        if self.component_economical_parameters is not None:
            self.calc_stream_economics(basic_economical_settings)
            self.calc_capex(basic_economical_settings)
            self.calc_opex(basic_economical_settings)
            self.component_economic_results.set_component_annuity()
