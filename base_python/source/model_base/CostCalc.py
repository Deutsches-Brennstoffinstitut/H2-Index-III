import logging
from base_python.source.basic.Streamtypes import StreamEnergy
from numpy import array


class Mixin:

    def calculate_costs(self):
        """
        Main method for cost calculation of the model which calls all the sub functions for each of the components

        """
        self._costs_calculated = True
        for name, component in self.components.items():
            component.calc_costs(basic_economical_settings=self.basic_economical_settings)

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
                        self_energy_streams = array(self_energy_port.get_stream_history())
                    else:
                        self_energy_streams += abs(array(self_energy_port.get_stream_history()))

            for comp in self.self_energy_components['Excluded Consumers']:
                consumer_ports = self.components[comp].get_ports_by_type(StreamEnergy.ELECTRIC)
                if len(consumer_ports) > 1:
                    logging.critical(f'Self energy component {comp} has more than one port. Could not define specific port')
                else:
                    consumer_port = consumer_ports[0]
                    if not self_energy_streams:
                        self_energy_streams = array(consumer_port.get_stream_history())
                    else:
                        self_energy_streams -= abs(array(consumer_port.get_stream_history()))
            self_energy_streams[self_energy_streams < 0] = 0
            return self_energy_streams
