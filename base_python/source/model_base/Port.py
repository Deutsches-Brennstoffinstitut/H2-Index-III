import logging
from base_python.source.helper.range_limit import range_limit
from base_python.source.basic.Quantities import PhysicalQuantity
from base_python.source.basic.Units import Unit
from base_python.source.basic.CustomErrors import PortError
from base_python.source.basic.Streamtypes import StreamDirection, StreamMass
import numpy as np
from enum import Enum
from base_python.source.model_base.Dataclasses.ExportDataclasses import PortResult


class Port:
    def __init__(self, component_ID: str, port_id: str, sign: StreamDirection, unit: Unit = None,
                 fixed_status: bool = False, external_identifier=None):
        """
        Args:
            port_id (str):          Id of the port
            sign (StreamDirection): Sign of the port which defines the possible flow direction of the port based on the
                                    general conventions
            unit (Unit):            Unit of the ports stream
            fixed_status (bool):    Defines whether the port is a fixed one or not based on general conventions
        """
        self.port_results: PortResult = PortResult(
            branch_id=None,
            component_id=component_ID,
            port_id=port_id,
            port_type=None,
            sign=sign,
            stream_unit=unit,
            port_history={})
        self.fixed_status = fixed_status
        self.externalport_type = None
        self.external_identifier = external_identifier
        self.stream = None
        self.stream_type = None
        self.stream_value_split_by_direction = {StreamDirection.stream_into_component: [],
                                                StreamDirection.stream_out_of_component: []}
        self.max_stream_value = {StreamDirection.stream_into_component: 0,
                                 StreamDirection.stream_out_of_component: 0}
        self.value_profiles = {}
        self.binary_profile = {}
        self.value_limits = {
            PhysicalQuantity.stream: (),
            PhysicalQuantity.pressure: (),
            PhysicalQuantity.temperature: (),
            PhysicalQuantity.mass_fraction: {}
        }

    def reset_history(self):
        self.port_results.port_history = {}
        self.stream_value_split_by_direction = {StreamDirection.stream_into_component: [],
                                                StreamDirection.stream_out_of_component: []}
        self.max_stream_value = {StreamDirection.stream_into_component: 0,
                                 StreamDirection.stream_out_of_component: 0}
    def save_state(self):
        """
        This function will be extended by the sub classes
        """
        if self.stream is not None:
            if self.stream < 0:
                self.stream_value_split_by_direction[StreamDirection.stream_into_component].append(self.stream)
                self.stream_value_split_by_direction[StreamDirection.stream_out_of_component].append(0)
                if self.stream < self.max_stream_value[StreamDirection.stream_into_component]:
                    self.max_stream_value[StreamDirection.stream_into_component] = self.stream
            elif self.stream > 0:
                self.stream_value_split_by_direction[StreamDirection.stream_into_component].append(0)
                self.stream_value_split_by_direction[StreamDirection.stream_out_of_component].append(self.stream)
                if self.stream > self.max_stream_value[StreamDirection.stream_out_of_component]:
                    self.max_stream_value[StreamDirection.stream_out_of_component] = self.stream
            else:
                self.stream_value_split_by_direction[StreamDirection.stream_into_component].append(0)
                self.stream_value_split_by_direction[StreamDirection.stream_out_of_component].append(0)

    ###################################
    # SET Methods
    ###################################

    def set_status_calculated(self):
        """
        Overwritten by port functions - Sets the status of the port whether it has been calculated

        """
        pass

    def set_port_binary_profile(self, profile: list, sign: int):
        """
        Sets a binary profile to the port in a desired direction

        Args:
            profile (list): List of binary values which is used as the profile
            sign (int):     Sign of the profile to determine the direction the binary profile is working
        """
        self.binary_profile[sign] = profile

    def set_port_profile(self, property_type: PhysicalQuantity, profile: list):
        """
        This function is used to set a profile to a specific property type of the port (e.g. stream, pressure etc.)

        Args:
            property_type (PhysicalQuantity):    Type of the profile that shall be set
            profile (list):                      Profile values that shall be set to the port
        """
        if all([step <= 0 for step in profile]) or all([step >= 0 for step in profile]):
            if all([step <= 0 for step in profile]) and self.port_results.sign.value <= 0:
                self.value_profiles[StreamDirection.stream_into_component] = {}
                self.value_profiles[StreamDirection.stream_into_component][property_type] = profile
            elif all([step >= 0 for step in profile]) and self.port_results.sign.value >= 0:
                self.value_profiles[StreamDirection.stream_out_of_component] = {}
                self.value_profiles[StreamDirection.stream_out_of_component][property_type] = profile
            elif all([step <= 0 for step in
                      profile]) and self.port_results.sign == StreamDirection.stream_out_of_component:
                logging.critical(
                    f'Port {self.port_results.port_id} of type {self.port_results.port_type} got an negative profile, '
                    f'while sign is positive (out of component).')
            elif all([step >= 0 for step in
                      profile]) and self.port_results.sign == StreamDirection.stream_into_component:
                logging.critical(
                    f'Port {self.port_results.port_id} of type {self.port_results.port_type} got an positive profile, '
                    f'while sign is negative (into component).')
        elif self.get_sign() == StreamDirection.stream_bidirectional:
            self.value_profiles[StreamDirection.stream_bidirectional][property_type] = profile
        else:
            logging.critical(
                f'The profile of Port {self.port_results.port_id} of type {self.port_results.port_type} does not have a consistent sign')

    def set_sign(self, sign: int):
        """
        Sets the sign of the port
        Args:
            sign (int): Desired sign of the port which defines possible stream directions (0, 1, -1)

        """
        self.port_results.sign = self.port_results.set_port_sign(sign=sign)

    def set_fixed_status(self, fixed_status: bool):
        """
        Defines whether the port is fixed or adaptive, which describes how the component is handled while calculating
        it in the branch module

        Args:
            fixed_status (bool): Boolean whether the port is a fixed port
        """
        self.fixed_status = fixed_status

    def set_maximum_stream(self, runcount: int) -> float:
        """
        Sets the maximum stream value to the port after checking it against the value_limits

        Args:
            runcount (int): The actual runcount for which the stream value shall be changed

        Returns:
            float: Resulting stream value of the port
        """
        stream = self.value_limits[PhysicalQuantity.stream][1]
        self.set_stream(runcount, stream)
        return self.stream

    def set_stream(self, runcount: int, stream: float) -> float:
        """
        Sets a stream value to the port after checking it against the value_limits

        Args:
            runcount (int): The actual runcount for which the stream value shall be changed
            stream (float): Stream value which should be set to the port

        Returns:
            float: Resulting stream value of the port
        """
        self.stream = self.check_port_value(PhysicalQuantity.stream, stream, runcount)
        return self.stream

    def set_profile_stream(self, runcount: int):
        """
        Sets a stream value to the port after checking it against the value_limits

        Args:
            runcount (int): Runcount for which the profile values should be set

        Returns:
            float: Resulting stream value of the port
        """
        self.stream = self.check_port_value(PhysicalQuantity.stream,
                                            self.get_profile_values(runcount)[PhysicalQuantity.stream], runcount)
        return self.stream

    def update_stream_limit(self, limit: tuple):
        """
        Sets a limit for the stream, which will be checked when setting a stream value

        Args:
            limit (tuple): Tuple of lowest and highest value for the stream (min_val, max_val)
        """
        limit = (float(limit[0]), float(limit[1]))

        if abs(limit[0]) > abs(limit[1]):
            limit = sorted(limit, reverse=True)
        self.value_limits[PhysicalQuantity.stream] = limit

    def reset_stream_limits(self):
        self.value_limits[PhysicalQuantity.stream] = ()

    def set_stream_limit(self, limit: tuple):
        """
        Sets a limit for the stream, which will be checked when setting a stream value

        Args:
            limit (tuple): Tuple of lowest and highest value for the stream (min_val, max_val)
        """
        limit = (float(limit[0]), float(limit[1]))

        if self.value_limits[PhysicalQuantity.stream] != ():
            logging.critical('Cannot add more than one couple of value limits.')
        else:
            if abs(limit[0]) > abs(limit[1]):
                limit = sorted(limit, reverse=True)
            self.value_limits[PhysicalQuantity.stream] = limit

    def set_linked_branch(self, branch_id: str):
        """
        Connects the port with a desired branch

        Args:
            branch_id (str): ID of the branch that should be connected
        """

        self.port_results.branch_id = branch_id

    def set_all_properties(self, port):
        """
        Empty function used for child classes
        """
        pass

    ###################################
    # GET Methods
    ###################################

    def get_type(self):
        """

        Returns:
            PhysicalQuantity: Type of the port (e.g. mass, power)
        """
        return self.port_results.port_type

    def get_profile_values(self, runcount: int, sign: int = None) -> dict:
        """

        Args:
            runcount (int): current runcount of the model
            sign (int):     defines the direction for which the profile values should be returned
                            1: OUT, 0: bidirectional, -1: IN

        Returns:
            dict:           Dictionary of the profile values for this runcount and direction which may include
                            stream, pressure, temperature depending on port type
        """
        answer = {}
        if sign is not None:
            for key, item in self.value_profiles[sign].items():
                answer[key] = item[runcount]
        elif self.port_results.sign != 0:  # not bidirectional
            if self.port_results.sign in self.value_profiles:
                for key, item in self.value_profiles[self.port_results.sign].items():
                    answer[key] = item[runcount]
            else:
                answer = None
        else:
            if len(self.value_profiles.keys()) == StreamDirection.stream_out_of_component:
                for key, item in self.value_profiles[self.value_profiles.keys()[0]].items():
                    answer[key] = item[runcount]
            else:
                logging.critical(
                    f'Could not get the profile value of port {self.port_results.port_id} of type {self.port_results.port_type}, '
                    f'because two profiles are given and no port sign defined')
        return answer

    def get_stream_limits(self) -> tuple:
        """

        Returns:
            tuple: Tuple of the stream limits by value type
        """
        return self.get_value_limits().get(PhysicalQuantity.stream)

    def get_external_identifier(self) -> Enum:
        """

        Returns:
            Enum: Enum of the external identifier or None
        """
        return self.external_identifier

    def get_value_limits(self) -> dict:
        """

        Returns:
            dict: Dictonary of the value limits by value type
        """
        value_limits = {}
        for key, limit in self.value_limits.items():
            if limit not in [(), {}, [], None]:
                value_limits[key] = limit
        return value_limits

    def get_id(self) -> str:
        """

        Returns:
            str: ID of the port
        """
        return self.port_results.port_id

    def get_stream(self) -> float:
        """

        Returns:
            float: Actual value of the ports stream
        """
        return self.stream
    def get_max_stream_by_sign(self, sign: int) -> float:
        """

        Args:
            sign (int): Direction (sign) for which the maximum stream value shall be returned

        Returns:
            float: Maximum Stream value
        """

        if sign in self.max_stream_value:
            return self.max_stream_value[sign]
        else:
            return None
    def get_stream_type(self) -> StreamMass:
        """

        Returns:
            StreamMass: Type of the stream (e.g. mass, power, energy)
        """
        return self.stream_type

    def get_stream_history(self) -> list:
        """

        Returns:
            list: List of the history of the stream from start to actual runcount
        """
        if PhysicalQuantity.stream in self.port_results.port_history.keys():
            return self.port_results.port_history[PhysicalQuantity.stream]
        else:
            return None

    def get_stream_history_by_sign(self, sign) -> list:
        """

        Args:
            sign (int): Sign for which the history of streams shall be returned

        Returns:
            list: History of the port separated by the direction regarding given sign
        """
        if sign in self.stream_value_split_by_direction:
            return self.stream_value_split_by_direction[sign]
        else:
            return None

    def get_stream_limited_value(self, value: float) -> float:
        """

        Args:
            value (float): Desired value which shall be checked against the stream limits of the port

        Returns:
            float: Value which has been checked against the stream limits of the port
        """
        return_value = value

        if PhysicalQuantity.stream in self.value_limits:
            '''
            first: the normal cases:
            higher than maximum is handled by "range limit", 
            also if bidirectional possible, the limits in "range_limit" make sense'''
            return_value = range_limit(value, sorted(self.value_limits[PhysicalQuantity.stream])[0],
                                       sorted(self.value_limits[PhysicalQuantity.stream])[1])

            if np.sign(value) > 0: # going IN
                if np.sign(value) == np.sign(sorted(self.value_limits[PhysicalQuantity.stream])[0]):
                    '''if the desired load/value points in the same direction (positive) as the minimal load/value'''
                    if np.abs(value) < np.abs(sorted(self.value_limits[PhysicalQuantity.stream])[0]):
                        ''' AND the desired load/value is smaller than the minimal load/value (e.g. Electrolyzer min load) '''
                        return_value = 0 # set load to zero

            if np.sign(value) < 0:  # going OUT
                if np.sign(value) == np.sign(sorted(self.value_limits[PhysicalQuantity.stream])[1]):
                    '''if the desired load/value points in the same direction (negative) as the minimal load/value'''
                    if np.abs(value) < np.abs(sorted(self.value_limits[PhysicalQuantity.stream])[1]):
                        ''' AND the desired load/value is smaller than the minimal load/value (e.g. something cannot handle  less than x output) '''
                        return_value = 0

        return return_value

    def get_port_history(self) -> dict:
        """

        Returns:
            dict: History of all the port values
        """
        return self.port_results.port_history

    def get_stream_unit(self) -> Unit:
        """

        Returns:
            Unit: Unit of the stream for this port
        """
        return self.port_results.stream_unit

    def get_sign(self) -> StreamDirection:
        """

        Returns:
            int: Sign of the port which describes the possible flow directions (-1, 0 or 1)
        """
        return self.port_results.sign

    def get_fixed_status(self) -> bool:
        """

        Returns:
            bool: Returns whether the port is a fixed one or not
        """
        return self.fixed_status

    def get_linked_branch(self) -> str:
        """

        Returns:
            str: ID of the linked branch to this port
        """
        return self.port_results.branch_id

    ###################################
    # CALCULATION Methods
    ###################################

    def check_port_value(self, property_type: PhysicalQuantity, value: float, runcount: int = None) -> float:
        """
        This method checks the given value against the set value limits of this specific property. If the value is
        not in the range limit given by the value_limits the value will be changed to meet the requirements of the
        limits and afterwards returned

        Args:
            property_type (PhysicalQuantity): The property the value should be checked whether its in the range (e.g.
                                              stream, pressure)
            value (float): The value that should be checked
            runcount (int): The runcount for which the port value shall be checked

        Returns:
            float: The value after checking whether it is in the range. If not the value will be limited to the nearest
            border value
        """

        if abs(value) == 0:
            return_value = 0
        elif value * self.port_results.sign.value < 0:
            ''' 
            - negative if value and port direction do not match, 
            - zero if sign value is bidirectional (0)'''
            return_value = 0
        elif not self.value_limits[property_type] in [{}, (), [], None]:  # value limits have been set and are not empty
            if self.port_results.sign != StreamDirection.stream_bidirectional:
                return_value = self.get_stream_limited_value(value)
            else:  # if port can be bidirectional
                return_value = range_limit(value, self.value_limits[property_type][0],
                                           self.value_limits[property_type][1])
        else:
            return_value = value

        """Check whether the port has a binary profile in the direction of the value given"""
        if return_value != 0:
            sign = int(np.sign(return_value))
            if sign == 1:
                stream_direction = StreamDirection.stream_out_of_component
            else:
                stream_direction = StreamDirection.stream_into_component

            if stream_direction in self.binary_profile.keys():
                return_value = return_value if self.binary_profile[stream_direction][runcount] == 1 else 0

        return return_value
