import logging
from base_python.source.model_base.Port import Port
from base_python.source.basic.Streamtypes import *
from base_python.source.basic.Quantities import PhysicalQuantity
from base_python.source.basic.Units import Unit
from base_python.source.basic.Streamtypes import StreamDirection
from base_python.source.basic.CustomErrors import PortEnergyError

class Port_Energy(Port):
    def __init__(self, component_ID:str, port_id: str, port_type: StreamEnergy, sign: StreamDirection, unit: Unit = None,
                 fixed_status: bool = False, external_identifier=None):
        """
        Args:
            port_id (str):              Id of the port
            port_type (StreamEnergy):   Type of the port (e.g. electric, heat)
            sign (StreamDirection):     Sign of the port which defines the possible flow direction of the port based on
                                        the general conventions
            unit (Unit):                Unit of the ports stream
            fixed_status (bool):        Defines whether the port is a fixed one or not based on general conventions
        """
        super().__init__(component_ID=component_ID,port_id=port_id, sign=sign, unit=unit, fixed_status=fixed_status,
                         external_identifier=external_identifier)

        self.set_type_and_unit(port_type, unit)
        self.port_results.port_history.setdefault(PhysicalQuantity.stream, [])

    def reset_history(self):
        super().reset_history()
        self.port_results.port_history.setdefault(PhysicalQuantity.stream, [])

    def set_type_and_unit(self, port_type: StreamEnergy, unit: Unit = None):
        """
        This method sets the type of the port and based on this also the unit and the stream_type

        Args:
            port_type (StreamEnergy):   Type of the port (e.g. StreamEnergy.ELECTRIC, StreamEnergy.HEAT)
            unit (Unit):                Unit of the stream (e.g. Unit.kW)

        Returns:

        """
        if self.port_results.port_type is None:
            if unit is not None and unit != get_stream_unit(port_type):
                logging.critical(f'Given stream unit {unit} of type {port_type} does not match model convention')
            else:

                self.port_results.port_type = port_type
                self.stream_type = get_stream_type(port_type)
                self.port_results.stream_unit = get_stream_unit(port_type)
        else:
            logging.warning(f'Trying to change Port Type of port {self.port_results.port_id}')

    def save_state(self):
        """
        Safes the actual stream value in the value history so it is possible to read the history later

        """
        super().save_state()
        self.port_results.port_history[PhysicalQuantity.stream].append(self.stream)

    def set_all_properties(self, runcount: int, port: Port):
        """
        This function sets all properties compared to another given port. For Energy ports this is for now only
        the stream value
        Args:
            runcount (int): Actual runcount for which the properties shall be set to checkup against a profile which
                            is given to the port whether the new value exceeds the profile value.
            port (Port):    Port which contains the information that shall be used for this port

        """

        self.set_stream(runcount, port.get_stream())

    def get_all_properties(self) -> dict:
        """
        Returns:
            dict: All properties which describe the actual state of the port
        """

        resulting_dictionary = {}
        resulting_dictionary[PhysicalQuantity.stream] = self.get_stream()
        return resulting_dictionary
