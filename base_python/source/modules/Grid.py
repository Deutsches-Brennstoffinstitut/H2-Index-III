#  imports
from base_python.source.modules.GenericUnit import GenericUnit
from base_python.source.model_base.Dataclasses.EconomicalDataclasses import *
from base_python.source.basic.Quantities import PhysicalQuantity
from base_python.source.basic.Streamtypes import StreamDirection
from base_python.source.model_base.Dataclasses.TechnicalDataclasses import GenericTechnicalInput
import numpy as np
import math
import logging


class Grid(GenericUnit):
    """
    Create an object with output=electric
    """

    def __init__(self, size=None, technology=None, unit=None, economical_parameters: EconomicalParameters = None,
                 stream_type=None, active=False, sign: StreamDirection = StreamDirection.stream_bidirectional,
                 new_investment=False, generic_technical_input: GenericTechnicalInput = None):
        """
        :param size:            float, installed capacity, None == infinite
        :param controlled_medium:    string, set the port_type ('electric', 'heat', 'natural_gas', 'H2')
        :param unit:            string, unit descriptor for the port ("")
        :param active:          boolean, define whether the component controls the system
        :param sign:            integer, allowed direction of input
                                0, both directions
                                1, output only
                                -1 , input only
        """

        super().__init__(size=size, active=active, technology=technology, new_investment=new_investment,
                         economical_parameters=economical_parameters,
                         stream_type=stream_type,
                         generic_technical_input=generic_technical_input)  # initialize class generic unit
        self.sign = sign
        self.streams_split_by_direction_and_type = {}
        self.max_stream_by_direction_and_type = {}
        self.economical_parameters = economical_parameters
        self._add_port(port_type=stream_type, component_ID=self.component_id,fixed_status=False, sign=sign, unit=unit)

        if self.size != None:
            self.ports[self.port_types[self.stream_type][0]].set_stream_limit((-self.size, self.size))
        else:
            self.ports[self.port_types[self.stream_type][0]].set_stream_limit((-math.inf, math.inf))

    def run(self, port_id, branch_information, runcount=0):
        """ runs the module, sets values of output ports
        :param myInputs: placeholder for input parameters
        :param runcount: Step Index (runtime = runcount * resolution)
        """

        self.status = 0  # set default status with 0:ok; >0:warning; <0:error

        # check whether a connected port has a stream profile

        if self.controlled_port != None:
            port = self.controlled_port
        else:
            port = self.get_port_by_id(port_id)

        # check if control strategy is temporarily changed
        [controlled_port, port_value, loop_control] = self._calc_control_var(port, branch_information[
            PhysicalQuantity.stream])

        if self.active & (not loop_control):
            if PhysicalQuantity.stream not in controlled_port.get_profile_values(runcount):
                controlled_port.set_stream(runcount,
                                           0) if controlled_port.get_stream_limits() is None else controlled_port.set_stream(
                    runcount, controlled_port.get_stream_limits()[1])
            else:
                controlled_port.set_profile_stream(runcount)
        else:
            if loop_control:
                controlled_port.set_stream(runcount, port_value)
            else:
                self.get_port_by_id(port_id).set_stream(runcount, port_value)

    #############################
    # Module specific functions #
    #############################

    def set_properties(self):
        """
        Calculate object specific properties
        :return: self
        """

        if self.size is not None:
            switch_list = {
                0: {self.stream_type: {'min': -1 * self.size, 'max': self.size}},
                1: {self.stream_type: {'min': 0, 'max': self.size}},
                -1: {self.stream_type: {'min': -1 * self.size, 'max': 0}},
            }
        else:
            switch_list = {
                0: {self.stream_type: {'min': -math.inf, 'max': math.inf}},
                1: {self.stream_type: {'min': 0, 'max': math.inf}},
                -1: {self.stream_type: {'min': -math.inf, 'max': 0}},
            }

        self.port_limits = switch_list.get(self.sign)

        return self
        # Return Self: https://stackoverflow.com/questions/43380042/purpose-of-return-self-python

    def set_basic_grid_economical_settings(self, basic_economical_settings):

        self.economical_parameters.set_annuity_factor(basic_economical_settings.total_time_period)
        self.economical_parameters.set_price_dyn_factor(basic_economical_settings.total_time_period)

        # Calculate the costs for balance streams over system border

    def _get_fixed_grid_costs(self):
        return self.economical_parameters.yearly_fixed_costs

    def _get_power_related_grid_costs(self):
        power_related_costs = {}
        for direction in ['in', 'out']:
            if direction == 'in':
                if self.economical_parameters.power_related_costs.costs_in is not None:
                    costs_from_component = self.economical_parameters.power_related_costs.costs_in
                else:
                    costs_from_component = None
            else:
                if self.economical_parameters.power_related_costs.costs_out is not None:
                    costs_from_component = self.economical_parameters.power_related_costs.costs_out
                else:
                    costs_from_component = None
            power_related_costs[direction] = {}
            if costs_from_component is not None:
                for key, value in costs_from_component.items():
                    if isinstance(value, list) or isinstance(value, tuple):
                        if len(value) == len(self.input_streams):
                            power_related_costs[direction][key] = sum(
                                np.array(value) * np.array(self.stream_split_by_direction[direction]))
                        else:
                            logging.critical(f'Length of cost profile for {key} in grid component {self.component_id}\n'
                                             f'does not match model profile length')
                    elif isinstance(value, float) or isinstance(value, int):
                        power_related_costs[direction][key] = value * self.max_power[direction]
                    else:
                        logging.warning(
                            f'Datatype of {key} costs of grid component {self.component_id} does not match required datatype')
        return power_related_costs

    def _get_amount_related_stream_costs(self):
        amount_related_costs = {}
        for direction in ['in', 'out']:
            costs_from_component = self.economical_parameters.amount_related_costs.costs_out if direction == 'out' \
                else self.economical_parameters.amount_related_costs.costs_in
            amount_related_costs[direction] = {}
            for key, value in costs_from_component:
                if isinstance(value, list) or isinstance(value, tuple):
                    if len(value) == len(self.input_streams):
                        amount_related_costs[direction][key] = sum(
                            np.array(value) * np.array(self.stream_split_by_direction[direction]))
                    else:
                        logging.critical(f'Length of cost profile for {key} in grid component {self.component_id}\n'
                                         f'does not match model profile length')
                elif isinstance(value, float):
                    amount_related_costs[direction][key] = value * self.stream_split_by_direction[direction]
                else:
                    logging.warning(
                        f'Datatype of {key} costs of grid component {self.component_id} does not match required datatype')
        return amount_related_costs

    def _get_overall_grid_costs(self):
        grid_related_cost = {}
        self.set_grid_streams_and_loads()
        grid_related_cost['fixed_grid_costs'] = self._get_fixed_grid_costs()
        grid_related_cost.update(self._get_power_related_grid_costs())
        grid_related_cost.update(self._get_amount_related_grid_costs())
        return grid_related_cost

    def get_grid_costs_and_annuities(self, basic_economical_settings):

        self.set_basic_grid_economical_settings(basic_economical_settings)
        grid_related_costs = self._get_overall_grid_costs()


#
#
#
#     for direction in ['in', 'out']:
#         grid_related_costs[f'energy_{direction}_related_costs'] = {}
#         for key, value in self.energy_related_costs[f'{direction}'].items():
#             grid_related_costs[f'energy_{direction}_related_costs'][key] = value * energy
#
#     if basic_economical_settings['electricity_calculation'] == 'contract':
#
#
#             if StreamEnergy.ELECTRIC in input_streams[component].keys():
#                 electricity_stream = input_streams[component][StreamEnergy.ELECTRIC]
#                 self.electricity_costs.update(self.get_electricity_costs(input_media_costs,component, electricity_stream, annuity_factor))
#                 input_media_costs['costs'][StreamEnergy.ELECTRIC] = sum([sum(i.values()) for i in [y for y in self.electricity_costs['costs'].values()]])
#                 input_media_costs['total_annuities'][StreamEnergy.ELECTRIC] = sum([sum(i.values()) for i in [y for y in self.electricity_costs['total_annuities'].values()]])
#                 input_media_costs['amount'][StreamEnergy.ELECTRIC] = self.electricity_costs['amount']['energy']
#                 if input_media_costs['amount'][StreamEnergy.ELECTRIC] != 0:
#                     input_media_costs['media_costs'][StreamEnergy.ELECTRIC] = input_media_costs['costs'][StreamEnergy.ELECTRIC] / input_media_costs['amount'][StreamEnergy.ELECTRIC]
#                 else:
#                     input_media_costs['media_costs'][StreamEnergy.ELECTRIC] = 0
#     elif self.settings['electricity_calculation']=='market'.casefold():
#         #TODO: Other calculation methods
#         pass
#     # Calculate other input streams
#     for component, component_values in input_streams.items():
#         for type, stream_value in component_values.items():
#             if type != StreamEnergy.ELECTRIC or (type == StreamEnergy.ELECTRIC and self.settings['electricity_calculation'].casefold() =='fix'.casefold()):
#                 if sum(list(array(input_streams[component][type]))) != 0:
#                     input_media_costs['amount'].setdefault(type,0)
#                     if type == StreamEnergy.ELECTRIC:
#                         input_media_costs['amount'][type] = self.power_to_energy(sum(list(array(input_streams[component][type]))))
#                     else:
#                         input_media_costs['amount'][type] += sum(list(array(input_streams[component][type])))
#                     if type in input_media_costs['media_costs'].keys():
#                         if isinstance(input_media_costs['media_costs'][type], float):
#                                 input_media_costs['costs'][type]= sum(list(array(input_streams[component][type])*array(input_media_costs['media_costs'][type])))
#                                 input_media_costs['total_annuities'][type] = input_media_costs['costs'][type]*annuity_factor*input_media_costs['price_dyn_factor'][type]
#                         else:
#                             logging.critical('The cost time series of {} doesn\'t match the input stream'.format(type))
#                     else:
#                         logging.warning('No input media costs for {} found.'.format(type))
#
#     # Alle ausgehenden Stoff- und Energieströme betrachten
#     for component, component_values in output_streams.items():
#         for type, stream_value in component_values.items():
#             if sum(list(array(output_streams[component][type]))) != 0:
#                 output_media_costs['amount'].setdefault(type, 0)
#                 if type == StreamEnergy.ELECTRIC:
#                     output_media_costs['amount'][type] = self.power_to_energy(sum(list(array(output_streams[component][type]))))
#                 else:
#                     output_media_costs['amount'][type] += sum(list(array(output_streams[component][type])))
#                 if type in output_media_costs['media_costs'].keys():
#                     if isinstance(output_media_costs['media_costs'][type], float) and isinstance(output_media_costs['price_dyn_factor'][type], float):
#                         output_media_costs['costs'][type]=abs(output_media_costs['amount'][type])*output_media_costs['media_costs'][type]
#                         output_media_costs['total_annuities'][type]=output_media_costs['costs'][type]*annuity_factor*output_media_costs['price_dyn_factor'][type]
#                     else:
#                         logging.critical('The cost time series of {} doesn\'t match the output stream'.format(type))
#                 else:
#                     logging.warning('No output media costs for {} found.'.format(type))

if __name__ == '__main__':
    print('T E S T: RE - Plant')
