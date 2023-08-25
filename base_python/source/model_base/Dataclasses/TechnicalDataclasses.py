from dataclasses import dataclass, field
from base_python.source.basic.Units import Unit
from base_python.source.basic.Quantities import *
from base_python.source.basic.Streamtypes import StreamEnergy, StreamMass
from base_python.source.basic.Streamtypes import StreamDirection
from typing import List
from enum import Enum
from scipy import interpolate
import collections
import logging


@dataclass
class Pressure:
    stream_type_of_port: StreamMass
    stream_direction_of_port: StreamDirection
    pressure_value: float
    unit: Unit
    physical_quantity = PhysicalQuantity.pressure

    def get_stream_type(self) -> StreamMass:
        """

        Returns:
            StreamMass: Stream type for which the pressure value shall be set
        """

        return self.stream_type_of_port

    def get_direction(self) -> StreamDirection:
        """

        Returns:
            StreamDirection: Direction for which the pressure value shall be set
        """
        return self.stream_direction_of_port

    def get_value(self) -> float:
        """

        Returns:
            float: Pressure value that shall be set
        """
        return self.pressure_value

    def get_unit(self) -> Unit:
        """

        Returns:
            Unit: Unit of the pressure value
        """
        return self.unit

    def __post_init__(self):
        if not self.get_unit() == get_unit_of_quantity(self.physical_quantity):
            logging.critical(
                f'Unit {self.get_unit()} of given pressure {self.get_value()} does not match internal unit for this property'
                f'({get_unit_of_quantity(self.physical_quantity)})')


@dataclass
class Temperature:
    stream_type_of_port: StreamMass
    stream_direction_of_port: StreamDirection
    temperature_value: float
    unit: Unit
    physical_quantity = PhysicalQuantity.temperature

    def get_stream_type(self) -> StreamMass:
        """

        Returns:
            StreamMass: Stream type for which the temperature value shall be set
        """

        return self.stream_type_of_port

    def get_direction(self) -> StreamDirection:
        """

        Returns:
            StreamDirection: Direction for which the temperature value shall be set
        """
        return self.stream_direction_of_port

    def get_value(self) -> float:
        """

        Returns:
            float: temperature value that shall be set
        """
        return self.temperature_value

    def get_unit(self) -> Unit:
        """

        Returns:
            Unit: Unit of the temperature value
        """
        return self.unit

    def __post_init__(self):
        if not self.get_unit() == get_unit_of_quantity(self.physical_quantity):
            logging.critical(
                f'Unit {self.get_unit()} of given temperature {self.get_value()} does not match internal unit for this property'
                f'({get_unit_of_quantity(self.physical_quantity)})')


@dataclass
class Efficiency:
    medium_referenced: StreamMass
    unit_referenced: Unit
    medium_calculated: StreamMass
    unit_calculated: Unit
    load_range: List[int]
    efficiencies_at_load: List[float]
    interpolation_function = None

    def get_medium_referenced(self):
        """

        Returns:
            StreamMass: Referenced stream_type of efficiency
        """
        return self.medium_referenced

    def get_medium_calculated(self):
        """

        Returns:
            StreamMass: Calculated stream_type of efficiency
        """
        return self.medium_calculated

    def get_interpolation_function(self):
        """

        Returns:
            Interpolation function of efficiency and load for this Class
        """
        return self.interpolation_function

    def set_efficiency(self, load_values, efficiency_values):
        """
        Sets new efficiency values to the class
        Args:
            load_values (list): Values of load for this class
            efficiency_values (list): Values of efficiency for this class

        Returns:

        """
        if len(load_values) == len(efficiency_values):
            self.load_range = load_values
            self.efficiencies_at_load = efficiency_values
        self.check_length()

    def set_interpolation_function(self):
        self.interpolation_function = interpolate.interp1d(self.load_range, self.efficiencies_at_load)

    def check_length(self):
        if not len(self.load_range) == len(self.efficiencies_at_load):
            logging.critical(f'Could not create efficiency for '
                             f'calculating {self.medium_calculated} from {self.medium_referenced}')
        else:
            self.set_interpolation_function()

    def __post_init__(self):
        self.check_length()


@dataclass
class Efficiencies:
    class_name: str
    technology: Enum
    all_efficiencies: List[Efficiency] = field(default_factory=lambda: [])

    def check_if_efficiency_not_included(self, medium_referenced: StreamMass, medium_calculated: StreamMass) -> bool:
        """
        Checks whether an efficiency of this medium_referenced / medium_calculated combination is already included
        Args:
            medium_referenced (StreamMass): Reference medium of the efficiency dataset
            medium_calculated (StreamMass): Calculation medium of the efficiency dataset

        Returns:

        """
        if self.get_efficiency_by_media(medium_referenced, medium_calculated) is None:
            return True
        else:
            return False


    def get_efficiencies_at_load(self):
        for single_efficiency in self.all_efficiencies:
            efficiencies_at_load = single_efficiency.efficiencies_at_load
        return efficiencies_at_load

    def get_efficiency_by_media(self, medium_referenced: StreamMass, medium_calculated: StreamMass) -> Efficiency:
        """
        This function is used to get a specific efficiency by the given media combination
        Args:
            medium_referenced (StreamMass): Reference medium of the efficiency dataset
            medium_calculated (StreamMass): Calculation medium of the efficiency dataset

        Returns:
            Efficiency: Single efficiency dataset
        """
        list_of_matched_efficiencies = []
        for single_efficiency in self.all_efficiencies:
            if single_efficiency.get_medium_referenced() == medium_referenced and \
                    single_efficiency.get_medium_calculated() == medium_calculated:
                list_of_matched_efficiencies.append(single_efficiency)

        if len(list_of_matched_efficiencies) > 1:
            logging.critical(f'More than one efficiency given for calculation of {medium_calculated}'
                             f' from {medium_referenced} ({self.class_name}, {self.technology}).')
            return list_of_matched_efficiencies[0]
        elif len(list_of_matched_efficiencies) == 1:
            return list_of_matched_efficiencies[0]

    def add_new_efficiencies(self, list_of_efficiencies: List[Efficiency]):
        """
        Adds several efficiency datasets to the dataclass
        Args:
            list_of_efficiencies (list): List of single efficiencies

        """
        for single_efficiency in list_of_efficiencies:
            self.add_new_efficiency(single_efficiency)

    def update_efficiency(self, medium_referenced, medium_calculated, load_values, efficiency_values):

        efficiency_object = self.get_efficiency_by_media(medium_referenced=medium_referenced,
                                                         medium_calculated=medium_calculated)
        if efficiency_object is not None:
            efficiency_object.set_efficiency(load_values=load_values, efficiency_values=efficiency_values)
        else:
            logging.critical(
                f'Could not find desired efficiency object of {self.class_name} {self.technology} for calculation of {medium_referenced} from {medium_calculated} to update efficiency')

    def add_new_efficiency(self, efficiency_object: Efficiency):
        """
        Adds one single efficiency to the dataclass
        Args:
            efficiency_object (Efficiency): Efficiency object which is defined by the Efficiency dataclass

        """

        if self.check_if_efficiency_not_included(efficiency_object.get_medium_referenced(),
                                                 efficiency_object.get_medium_calculated()):
            self.all_efficiencies.append(efficiency_object)
        else:
            logging.warning(
                f'Could not add efficiency of {efficiency_object.get_medium_referenced()} to {efficiency_object.get_medium_calculated()}'
                f' for {self.class_name}, {self.technology}, because efficiency of this stream conversion already loaded')


@dataclass
class GenericTechnicalInput:
    temperatures: List[Temperature] = None
    pressures: List[Pressure] = None
    efficiencies: List[Efficiency] = field(default_factory=lambda: [])

    def get_temperatures(self):
        """

        Returns:
            list: List of temperatures
        """

        return self.temperatures

    def get_pressures(self):
        """

        Returns:
            list: List of pressures
        """

        return self.pressures

    def get_efficiencies(self):
        """

        Returns:
            list: List of efficiencies
        """

        return self.efficiencies
