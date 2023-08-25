# Bibliothek Import

import pickle
import logging
import sys
import math
import inspect
import numpy as np
import pandas as pd
import CoolProp.CoolProp as CP
from copy import copy
from copy import deepcopy
from scipy.interpolate import interp1d, interp2d

# Model Base Import

from base_python.source.basic.Streamtypes import StreamMass, StreamEnergy, StreamDirection
from base_python.source.basic.Settings import *
from base_python.source.basic.Quantities import PhysicalQuantity, get_unit_of_quantity
from base_python.source.basic.Units import Unit
from base_python.source.basic.CustomErrors import *
# Helper function Imports

from base_python.source.helper.initialize_logger import initialize_logger, LoggingLevels

# component imports
from base_python.source.modules import *
from base_python.source.modules import GenericUnit, Converter, Consumer, Grid

# import model includes

from base_python.source.model_base.Branches import Branch
from base_python.source.model_base.Dataclasses.EconomicalDataclasses import *
from base_python.source.model_base.Dataclasses.TechnicalDataclasses import *
from base_python.source.model_base.Dataclasses.ExportDataclasses import SystemResults, PortResult, ComponentTechnicalResults, ComponentEconResults
import base_python.source.model_base.Connections2Branches as Connections2Branches

import base_python.source.model_base.database_connection as database_connection


class ModelBase(database_connection.Mixin, Connections2Branches.Mixin):

    def __init__(self, database_name: str, db_location='server', logging_level: LoggingLevels = LoggingLevels.CRITICAL):

        """
        Initializes the Model with all necessary attributes

        Args:
            database_name: Name of the database in HeidiSQL
            db_location: either "server" or "local"
            logging_level: Logging Level as Enum of logging levels to describe the logging output
        """
        ## reset Branch and Component IDs
        self.reset_IDs()

        # create variable structure definition
        self.overall_status = 0
        self.modelname = self.__class__.__name__  # name of the calling child (= system model Name)
        self.system_results: SystemResults = None
        self.basic_technical_settings: BasicTechnicalSettings = None
        self.basic_economical_settings: BasicEconomicalSettings = None
        self._costs_calculated = False
        self.profile_len = None
        self.database_cursor = None

        self.self_energy_components = []
        self.passive_priorityRules = []

        self.components = {}
        self.ports = {}  # unit definition: electric=kW, H2=kW
        self.connections = {}
        self.loop_control_rules = {}
        self.status = {}
        self.input_media_costs = {}
        self.output_media_costs = {}
        self.electricity_costs = {}
        self.costs = {}
        self.branches = {}
        self.settings = {}

        initialize_logger(level=logging_level)
        if db_location == 'server' and database_name is not None:
            self.connect_to_server_database(database_name)
            self.load_basic_database()
        elif db_location == 'local' and database_name is not None:
            self.connect_to_local_database(database_name)
            self.load_basic_database()
        else:
            logging.warning('Missing Information, please provide a valid database name')

    ###################################
    # Initialisation Methods
    ###################################
    @staticmethod
    def reset_IDs():
        '''
        tries to reset all possible Components ID's for
        :return:
        '''
        Branch.BRANCH_ID_COUNT = 0
        GenericUnit.GenericUnit.COMPONENT_ID_COUNT = 0
        # clear all possible componentes here:
        # TODO: find a much more elegant way to do that
        PortResult.instances.clear()
        ComponentTechnicalResults.instances.clear()
        ComponentEconResults.instances.clear()

        #Burner.COMPONENT_ID_COUNT = 0
        #CHP_Plant.COMPONENT_ID_COUNT = 0
        Compressor.COMPONENT_ID_COUNT = 0
        Consumer.COMPONENT_ID_COUNT = 0
        Converter.Converter.COMPONENT_ID_COUNT = 0
        Electrolyser.COMPONENT_ID_COUNT = 0
        Grid.COMPONENT_ID_COUNT = 0
        Investment.COMPONENT_ID_COUNT = 0
        Pipeline.COMPONENT_ID_COUNT = 0
        Pipeline_Segment.COMPONENT_ID_COUNT = 0
        Source.COMPONENT_ID_COUNT = 0
        Storage.COMPONENT_ID_COUNT = 0
        #Storage_Electrical.COMPONENT_ID_COUNT = 0
        Storage_Gas.COMPONENT_ID_COUNT = 0

    def init_structure(self):
        """
        Loads the database and builds all necessary branches of the model

        """
        self.set_time_resolution(self.basic_technical_settings.time_resolution)
        self.add_sub_components_to_list()
        self.load_database()
        self.set_properties_of_components()
        for comp_name, component in self.components.items():
            self.ports[comp_name] = component.get_ports()

        self.build_branches()  # build model branches

    def add_branch(self, branch_name: str, branch_type: StreamEnergy, port_connections: list):
        """
        Adds a new branch to the model which will be calculated
        Args:
            branch_name (str): Desired name of the branch
            branch_type (str): Stream type of the branch. Possible stream types are given in documentation
            port_connections (list): List of tuples which define the branch connections. First item is connected
                                     component and second item the sign of the port connected.
            e.g. ('Electrolyser, -1)

        """

        if branch_type is None:
            raise BranchError(f'Branch type of branch {branch_name} not given. Please define a type')

        if not isinstance(port_connections, list):
            raise BranchError(f'Datatype of Port_Connections of branch "{branch_name}" is '
                              f'"{type(port_connections).__name__}" not {type([]).__name__}')

        if not all([isinstance(ii, tuple) for ii in port_connections]):
            for ii in port_connections:
                _ = []
                _2 = []
                if not isinstance(ii, tuple):
                    _.append(str(ii))
                    _2.append(type(ii).__name__)
                raise BranchConnectionError(f'Type Error in Branch "{branch_name}" of Type "{branch_type}":'
                                            f'{len(_)} Port Connections have the wrong Type -  {str(", ").join(ii)} '
                                            f'have the types {str(", ").join(_2)} instead of {type(tuple).__name__}')

        for port_connection in port_connections:
            if port_connection[0] not in self.components:
                raise BranchConnectionError(f'Component {port_connection[0]} given in branch {branch_name} not '
                                            f'part of the system. Check spelling!')

        self.branches[branch_name] = Branch(branch_type=branch_type, port_connections=port_connections,
                                            basic_technical_settings=self.basic_technical_settings, branch_name=branch_name)

    def add_sub_components_to_list(self):
        """
        This function is used to add sub components of a specific main component to the component list. It is necessary
        to generate the desired model output

        """
        sorted_list = []
        new_component_list = {}
        new_component_list.update(self.components)
        for component_name, component in self.components.items():
            sorted_list.append(component_name)
            if component.sub_components != {}:
                for sub_component_name, sub_component in component.sub_components.items():
                    new_component_list[component_name + '_' + sub_component_name] = sub_component
                    sorted_list.append(component_name + '_' + sub_component_name)
        self.components = {}
        for item in sorted_list:
            self.components[item] = new_component_list[item]

    ###################################
    # SET Methods
    ###################################
    def set_properties_of_components(self):

        """
        Sets all component specific properties to the components

        """

        for component_name in self.components:
            self.components[component_name].set_generic_properties()
            self.components[component_name].set_properties()

    def set_time_resolution(self, time_resolution: int = None):

        """
        Sets the time resolution of the model

        Args:
            time_resolution (int): Value of time resolution should be a divisor of 60 min
        """

        if time_resolution is None:
            time_resolution = self.basic_technical_settings.time_resolution
            logging.critical('No time resolution given! Use "model.set_time_resolution(time)" at model definition')
        if 60 % time_resolution != 0:
            logging.critical('Time resolution must be a common factor of 60 Minutes')
        self.basic_technical_settings.time_resolution = time_resolution
        for name, component in self.components.items():
            component.set_time_resolution(time_resolution)
            for sub_component in component.sub_components.values():
                sub_component.set_time_resolution(time_resolution)

    def add_profile_to_component_port(self, component_name: str, port_stream_type: StreamMass,
                                      port_stream_direction: StreamDirection, profile: pd.Series,
                                      profile_type: PhysicalQuantity,
                                      time_resolution: int = None, active: bool = True, binary=False,
                                      external_identifier=None):
        """
        Add a load profile to a specified model component

        Args:
           port_stream_type (StreamMass):           Desired Port stream_type which should get the profile
           port_stream_direction (StreamDirection): Desired Stream Direction for which the profile should be set
           component_name (str):                    name of the specified component
           profile (pd.Series):                     dataset as pandas Series
           profile_type(PhysicalQuantity):          Defines which property should get a profile e.g. 'pressure',
                                                    'temperature'
           time_resolution (int):                   Value of time resolution should be a divisor of 60 min
           active (bool):                           Active status of component
           binary (bool):                           Defines whether its a binary profile

        """

        # Check for shortest profile
        if self.profile_len is None:
            self.profile_len = len(profile)
        elif len(profile) < self.profile_len:
            logging.warning(
                f'Profile length of type {profile_type} from component {component_name} at port {port_stream_type} is with '
                f'{len(profile)} steps shorter than given length of {self.profile_len}\n'
                f'Profile length of all components cropped to {len(profile)}.')
            self.profile_len = len(profile)
        elif len(profile) > self.profile_len:
            logging.warning(
                f'Profile length of type {profile_type} from component {component_name} at port {port_stream_type}\nis with '
                f'{len(profile)} steps longer than calculated length of {self.profile_len}.')
        # check the time resolution consistency

        if time_resolution is not None:
            if self.basic_technical_settings.time_resolution is None:
                self.basic_technical_settings.time_resolution = time_resolution
            elif time_resolution != self.basic_technical_settings.time_resolution:
                raise ComponentError(f'ERROR while adding a profile to component "{component_name}": the desired time '
                                     f'resolution of {time_resolution} differs from the models resolution of '
                                     f'{self.basic_technical_settings.time_resolution}')
            # else both resolutions are equivalent, so nothing to do
        else:  # no time_resolution given, so use model's one
            time_resolution = self.basic_technical_settings.time_resolution

        if component_name in self.components.keys():
            if binary:
                self.components[component_name].set_binary_profile_to_port(profile, port_stream_type,
                                                                           port_stream_direction, external_identifier)
            else:
                self.components[component_name].set_profile_to_port(profile=profile, port_type=port_stream_type,
                                                                    port_sign=port_stream_direction,
                                                                    profile_type=profile_type,
                                                                    time_resolution=time_resolution,
                                                                    active=active,
                                                                    external_identifier=external_identifier)
        else:
            raise ComponentError(f'ERROR while adding a profile to component "{component_name}": The Component_Name '
                                 f'is not part of the model!')

    def convert_profile_time_resolution(self, stream_type: StreamEnergy, profile: list,
                                        profile_time_resolution: int) -> list:

        """

        Args:
            stream_type (StreamEnergy):     Type of the stream for which the profile should be converted
                                            (StreamEnergy.ELECTRIC)
            profile (list):                 List of the profile for the stream
            profile_time_resolution (int):  Time resolution of the given profile

        Returns:
            list: Profile in desired Model time resolution
        """
        #todo: Ganz bestimmt effizienter lösbar - 2022.07.21 - FFi
        created_index_col = pd.date_range(f"{str(self.basic_economical_settings.start_year)}-01-01",
                                          periods=len(profile), freq=f'{profile_time_resolution}T')
        pd_series = pd.Series(index=created_index_col, data=profile)
        pd_series = pd_series.reindex(pd_series.index.union(pd_series.index.shift(profile_time_resolution, 'T')))
        if stream_type in StreamEnergy:
            pd_series = pd_series.resample(f'{self.basic_technical_settings.time_resolution}T', closed='left').mean()
            pd_series = pd_series.drop(pd_series.index[-1])
            if profile_time_resolution > self.basic_technical_settings.time_resolution:
                pd_series = pd_series.interpolate(method='polynomial', order=1)
        else:
            pd_series = pd_series.resample(f'{self.basic_technical_settings.time_resolution}T', closed='left').sum()
        pd_series = pd_series.fillna(method='ffill')
        profile = pd_series.values

        return profile

    def add_limited_binary_profile_to_component(self, component_name: str, port_stream_type: StreamMass,
                                                port_stream_direction: StreamDirection, time_resolution: int,
                                                activation_function, compare_profile: list, active: bool = True):

        """
        Add a binary profile to a port limited by the activation function and the compare profile

        Args:
           port_stream_type (StreamMass):           Desired Port stream_type which should get the profile
           port_stream_direction (StreamDirection): Desired Stream Direction for which the profile should be set
           component_name (str):                    name of the specified component
           time_resolution (int):                   Value of time resolution should be a divisor of 60 min
           compare_profile (list):                  Base profile which is used with the activation function to create a
                                                    desired binary profile
           activation_function (function):          If this function is boolean true the value of the compare profile
                                                    is set to 1 in the resulting binary profile, all other values are 0
           active (bool):                           Active status of component

        """

        if activation_function is None:
            logging.critical(
                f'Set activation function for {component_name} binary profile to define which values of binary '
                f'profile are set to 1')
        else:
            if compare_profile is None:
                compare_profile = self.get_stream_profile_of_port(component_name, port_stream_type,
                                                                  port_stream_direction)
        if compare_profile is not None:
            binary_profile = list(np.array(list(map(activation_function, compare_profile))).astype(int))
            self.add_binary_stream_profile_to_port(component_name, port_stream_type, port_stream_direction,
                                                   binary_profile, time_resolution=time_resolution, active=active)
        else:
            logging.critical(f'Could not set binary_profile to {port_stream_type, port_stream_direction} '
                             f'of component {component_name}.')

    def add_binary_stream_profile_to_port(self, component_name: str, port_stream_type: StreamMass,
                                          port_stream_direction: StreamDirection, profile: pd.Series = None,
                                          time_resolution: int = None, active: bool = True, external_identifier=None):
        """
        Add a binary profile to the desired port

        Args:
           port_stream_type (StreamMass):           Desired Port stream_type which should get the profile
           port_stream_direction (StreamDirection): Desired Stream Direction for which the profile should be set
           component_name (str):                    name of the specified component
           time_resolution (int):                   Value of time resolution should be a divisor of 60 min
           profile (list):                          List of binary values which is set to the port as profile
           active (bool):                           Active status of component

        """

        if time_resolution != self.basic_technical_settings.time_resolution:
            logging.critical(f'Binary profile of component {component_name} does not have desired time_resolution of '
                             f'{time_resolution}. Not considered!')
        else:
            self.add_profile_to_component_port(component_name=component_name, port_stream_type=port_stream_type,
                                               port_stream_direction=port_stream_direction, profile=profile,
                                               profile_type=PhysicalQuantity.stream,
                                               time_resolution=time_resolution, active=active, binary=True,
                                               external_identifier=external_identifier)

    def add_stream_profile_to_electrical_port_IN(self, component_name: str, profile: pd.Series = None):
        """
        wrapper for add_stream_profile_to_port without the enums
        """

        self.add_stream_profile_to_port(component_name=component_name,
                                        port_stream_type=StreamEnergy.ELECTRIC,
                                        port_stream_direction=StreamDirection.stream_into_component,
                                        profile=profile)
    def add_stream_profile_to_electrical_port_OUT(self, component_name: str, profile: pd.Series = None):
        """
        wrapper for add_stream_profile_to_port without the enums
        """

        self.add_stream_profile_to_port(component_name=component_name,
                                        port_stream_type=StreamEnergy.ELECTRIC,
                                        port_stream_direction=StreamDirection.stream_out_of_component,
                                        profile=profile)

    def add_stream_profile_to_H2_port_IN(self, component_name: str, profile: pd.Series = None):
        """
        wrapper for add_stream_profile_to_port without the enums
        """
        #profile = np.array(profile)
        self.add_stream_profile_to_port(component_name=component_name,
                                        port_stream_type=StreamMass.HYDROGEN,
                                        port_stream_direction=StreamDirection.stream_into_component,
                                        profile=profile)

    def add_stream_profile_to_H2_port_OUT(self, component_name: str, profile: pd.Series = None):
        """
        wrapper for add_stream_profile_to_port without the enums
        """

        self.add_stream_profile_to_port(component_name=component_name,
                                        port_stream_type=StreamMass.HYDROGEN,
                                        port_stream_direction=StreamDirection.stream_out_of_component,
                                        profile=profile)

    def add_stream_profile_to_port(self, component_name: str, port_stream_type: StreamMass,
                                   port_stream_direction: StreamDirection, profile: pd.Series = None,
                                   time_resolution: int = None, unit: Unit = None, active: bool = True):
        """
        Is used to add a profile to a specific port of a component. If the component is active, it is controlled by
        this profile

        Args:
            component_name (str): Name of the component
            port_stream_type (StreamMass):           Desired Port stream_type which should get the profile
            port_stream_direction (StreamDirection): Desired Stream Direction for which the profile should be set
            profile (pd.Series): Profile which should be set to the port
            unit (Unit): Unit of the profile values
            time_resolution (int): Time resolution of the profile in minutes
            active (bool): Sets the active status of the component, default is active

        """

        stream_type = port_stream_type
        if unit is None:
            logging.warning(f'Please specify unit for profile of {component_name}!')
        elif (stream_type in StreamEnergy and unit != get_unit_of_quantity(PhysicalQuantity.power_stream)) or \
                (stream_type in StreamMass and unit != get_unit_of_quantity(PhysicalQuantity.mass_stream)):
            logging.critical(
                f'Unit of given profile for {component_name} does not match internal unit for this type of stream')

        if time_resolution is not None and time_resolution != self.basic_technical_settings.time_resolution:
            profile = self.convert_profile_time_resolution(stream_type, profile, time_resolution)
            time_resolution = self.basic_technical_settings.time_resolution
        else:
            profile = profile

        self.add_profile_to_component_port(component_name=component_name, port_stream_type=port_stream_type,
                                           port_stream_direction=port_stream_direction, profile=profile,
                                           profile_type=PhysicalQuantity.stream,
                                           time_resolution=time_resolution, active=active, binary=False)

    ###################################
    # GET Methods
    ###################################

    def get_full_hours_of_use(self, component_name: str, port_type: str) -> float:
        """
        Returns the the full load hours of a specific port of a defined component

        Args:
            component_name (str):  specify the component the calculation is carried out for
            port_type (str):       Type of the port

        Returns:
            float: Full load hours of use
        """

        grid_energy_drain = 0
        max_grid_drain = 0

        if component_name in self.components:
            #todo: removed systemvars: if systemvars were none -> run, so a new if exprssion has to be found
            self.run()

            # calculate: overall grid sum, maximum
            ports = self.components[component_name].get_ports_by_type(port_type)
            if len(ports) > 1:
                raise ComponentError(f'Component {component_name} has {len(ports)} ports of same type! '
                                     f'Calculation of full-load-hours not possible.')
            else:
                port = ports[0]
            values = port.get_stream_history()
            for val in values:
                if val > 0:
                    grid_energy_drain += val * self.basic_technical_settings.time_resolution / 60
                if val > max_grid_drain:
                    max_grid_drain = val

            # calculate the full hours of use value
            return grid_energy_drain / max_grid_drain

        else:
            raise ComponentError(f'The required component "{component_name}" is not part of the model. Full-Load-Hours'
                                 f' can\'t be calculated!')

    def get_stream_profile_of_port(self, component_name: str, port_type: StreamMass, sign: StreamDirection) -> list:

        """
        Returns the stream profile of a specific port of a component

        Args:
            component_name (str): Name of the component
            port_type (StreamMass): Type of the port
            sign (int): Sign of the port which defines the direction (-1, 0 ,1)

        Returns:
            list: Profile of the port
        """

        port = None
        component = self.components.get(component_name)
        if component is not None:
            port = component.get_port_by_type_and_sign(port_type, sign)
        return port

    def get_components(self) -> dict:
        """

        Returns:
            dict: Dictionary of all system components with names as keys and component objects as values
        """
        return copy.deepcopy(self.components)


    ###################################
    # calculation Methods
    ###################################

    def run(self):
        """
        Run the system by solving the model for all timesteps by calling the
        pre-defined branches and solve these by calling the single run methods of the components

        """

        """Reset the histories of components to prevent wrong results"""

        for component in self.components.values():
            component._reset_component_history()
            component._reset_port_history()

        self.overall_status = 0

        """Check whether profile length and time resolution are given. If not only one step will be calculated"""

        if self.profile_len is None:
            if self.basic_technical_settings.time_resolution is None:
                iteration_count = 1
            else:
                iteration_count = int(8760 / self.basic_technical_settings.time_resolution * 60)
        else:
            iteration_count = self.profile_len

        logging.debug('### Starting run of model "{}" with {} steps ###'.format(self.modelname, str(iteration_count)))

        for runcount in range(iteration_count):
            logging.debug('- New run {} -'.format(runcount))

            """Run the model for the runcount using the solve method"""
            self.solve(runcount=runcount)
            if -1 in self.status.values():
                self.overall_status = -1
            self._print_error()

            """Saving the state """
            for component in self.components.values():
                component.save_state()
                for port in component.ports.values():
                    port.save_state()

        logging.debug('### run completed ###')

    def solve(self, runcount) -> int:
        """
        Solves one single runcount of the model and calls the branches to solve itself
        Args:
            runcount (int): Actual timestep of the model

        Returns:
            int: Status of the runcount
        """

        if self.basic_technical_settings.time_resolution is None:
            raise ModelError("Solver: TimeResolution is not set! ")
        else:
            """Set limits of the iteration"""

            """Set pre-default values which are necessary for the calculation"""

            status = 0
            loop_controlled_components = []
            timeout = 0
            rerun = False

            """Run every single branch and process the results"""

            names_already_run = {}

            """ Run the code as long not all branches have the attribute calculated true and the timeout value 
            did not reach the maximum timeout value.
            """
            while not all([branch.calculated is True for branch in self.branches.values()]) and (timeout < self.basic_technical_settings.timeout_max):
                timeout += 1
                """ Loop over all branches in the model regarding the pre-defined branch_calculation_order"""
                for branch_name in self.branch_calculation_order:
                    if not self.branches[branch_name].calculated:

                        """Run method of the branch is started and the information whether the branch has been looped
                        (rerun) and the other branches has to be recalculated (reset)"""
                        rerun, names_already_run, reset = self.branches[branch_name].run(names_already_run, runcount,
                                                                                         rerun)
                        loop_controlled_components.extend(self.branches[branch_name].get_loop_controlled_components())
                        if reset:
                            """ If Reset is true all branches except the one which raised the rerun True parameter
                            has to be recalcuated and get the attribute calculated = False"""
                            for name, branch in self.branches.items():
                                if branch_name != name:
                                    branch.calculated = False
                            break

            """ Resets any loop control values to prepare the model for the next runcount"""

            for branch in self.branches.values():
                branch.calculated = False
                branch.set_loop_controlled_components_empty()
            for name in loop_controlled_components:
                self.components[name].clear_controlled_active_port()
            # reset port properties
            for component in self.components.values():
                for port in component.ports.values():
                    port.set_status_calculated()

            """Check whether all branch could be solved or not. If not an error occures"""
            for branch_name, branch in self.branches.items():
                balance = branch.get_stream_balance()
                if abs(balance) >= self.basic_technical_settings.absolute_model_error:
                    logging.warning(f'Integrity check: system dissipates stream within {branch_name} of type'
                                    f' "{branch.get_type()}" with a rate of {balance} at runcount: {runcount}')

            """Write all status variables of the components for this runcount into a dictionary"""
            self.status = {}
            for name, component in self.components.items():
                self.status[name] = component.get_status()
            return status
    def create_results(self) -> SystemResults:
        """Creates SystemResults as Export

        Returns: SystemResults Class

        """
        return SystemResults.create_system_results(self)  #  import SystemResults in header
    def _print_error(self):
        """Print a warning for each component with status <> 0"""

        for name, component in self.components.items():
            component_status = component.get_status()
            err_str = f'Unit {name} returned status: {component_status}'
            if component_status > 0:
                logging.warning(err_str)
            elif component_status:
                logging.critical(err_str)

    def calculate_costs(self):
        """
        Main method for cost calculation of the model which calls all the sub functions for each of the components

        """
        self._costs_calculated = True
        for name, component in self.components.items():
            component.calc_costs(basic_economical_settings=self.basic_economical_settings)

        """Calculation of eeg levy"""
        # TODO: EEG-Umlagen wieder in das Modell einfügen wenn notwendig
        self_energy_streams = self.get_eeg()
        if self_energy_streams is not None:
            eeg_levy_for_self_generated_power = self.basic_economical_settings.eeg_levy_for_use_of_self_generated_power \
                                                * sum(self_energy_streams)


        self.system_results = self.create_results()

    def get_eeg(self) -> list:
        """
        Calculation of eeg-levy of components in system which produce renewable energy and have to pay eeg_levy.
        Some consumers can be excluded from the levy(e.g. Electrolyser). This has to be defined in
        self_energy_components.

        Returns:
            list: Self energy streams resulting from the calculation
        """
        if self.self_energy_components:
            self_energy_streams = []
            for key in self.self_energy_components['Sources']:
                self_energy_ports = self.components[key].get_ports_by_type(StreamEnergy.ELECTRIC)
                if len(self_energy_ports) > 1:
                    logging.critical(
                        f'Self energy component {key} has more than one port. Could not define specific port')
                else:
                    self_energy_port = self_energy_ports[0]
                    if not self_energy_streams:
                        self_energy_streams = np.array(self_energy_port.get_stream_history())
                    else:
                        self_energy_streams += abs(np.array(self_energy_port.get_stream_history()))

            for comp in self.self_energy_components['Excluded Consumers']:
                consumer_ports = self.components[comp].get_ports_by_type(StreamEnergy.ELECTRIC)
                if len(consumer_ports) > 1:
                    logging.critical(f'Self energy component {comp} has more than one port. Could not define specific port')
                else:
                    consumer_port = consumer_ports[0]
                    if not self_energy_streams:
                        self_energy_streams = np.array(consumer_port.get_stream_history())
                    else:
                        self_energy_streams -= abs(np.array(consumer_port.get_stream_history()))
            self_energy_streams[self_energy_streams < 0] = 0
            return self_energy_streams
