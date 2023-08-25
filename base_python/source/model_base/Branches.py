import copy
import logging
import sys
import math

# Model Base Import
from base_python.source.basic.Settings import BasicTechnicalSettings
from base_python.source.basic.Quantities import PhysicalQuantity
from base_python.source.basic.CustomErrors import BranchError
from base_python.source.model_base.Port_Mass import Port_Mass
from base_python.source.model_base.Port import Port
from base_python.source.basic.Streamtypes import StreamDirection

# Component Import
from base_python.source.modules.GenericUnit import GenericUnit
from base_python.source.helper.range_limit import *
from base_python.source.helper.misc import create_id

class Branch:
    BRANCH_ID_COUNT = 0  # counter for branch IDs, nececcary to set unique branch IDs

    def __init__(self, branch_type, branch_name, port_connections, basic_technical_settings: BasicTechnicalSettings):
        """
        Initializes a Branch of a specific type with connected components. The branch can be solved by itself
        and interacts with the model.

        Args:
            branch_type (Enum):          The type of the branch which must match the types of the connected ports
            port_connections (list):    Dictionary of the linked ports and their components
        """

        self.connections = port_connections
        self.branch_type = branch_type
        self.branch_name = branch_name
        self.runcount = 0
        self.branch_id = self.set_id()
        self.basic_technical_settings = basic_technical_settings
        self.calculated = False

        self.loop_control_rules = []
        self.loop_controlled_components = []

        self.connected_components = {}
        self.fixed_ports = {}
        self.temp_fixed_ports = {}
        self.adaptive_ports = {}
        self.temp_adaptive_ports = {}
        self.ports_connected = {}
        self.balance = {}

    ###################################
    # SET Methods
    ###################################
    @classmethod
    def set_id(cls) -> str:
        """Class-Method to create a Unique Branch_ID, based on the class-variable BRANCH_ID_COUNT which gets
         incremented each time a new Branch is created.

        Notes:
            https://mail.python.org/pipermail/python-list/2003-April/237870.html
            the Try Except is, in case a child of branch is ever used same as the set_id function for components.
        Returns:
            Branch_ID: Unique String consisting of the letter "B" and two digits
        """

        branch_id = create_id(letter='B', number=cls.BRANCH_ID_COUNT)
        #
        try:
            cls.__mro__[-2].BRANCH_ID_COUNT += 1
        except AttributeError:
            cls.BRANCH_ID_COUNT += 1
        return branch_id

    def set_fixed_ports(self, components_dict: dict):
        """
        Saves the fixed ports of the branch in a seperate dictionary

        Args:
            components_dict (dict): Dictionary of Components and fixed ports of the branch

        """

        self.fixed_ports = copy.deepcopy(components_dict)

    def set_adaptive_ports(self, components_dict: dict):
        """
        Saves the adaptive ports of the branch in a seperate dictionary

        Args:
            components_dict (dict): Dictionary of components and adaptive ports of the branch

        """
        self.adaptive_ports = copy.deepcopy(components_dict)

    def set_loop_control_rules(self, rules: list):
        """
        Saves the loop control rules of the branch (contain which component shall be loop controlled) in a dictionary

        Args:
            rules (list): List of components in the branch which should be loop controlled

        """
        self.loop_control_rules = rules

    def set_loop_controlled_components_empty(self):
        """
        Deletes all components in the loop controlled list, to prepare the branch for the next runcount

        """
        self.loop_controlled_components.clear()

    def add_port_connection(self, component_name: str, component: GenericUnit, port: Port):
        """
        Create a new branch - port connection

        Args:
            component_name (str): Name of the component that will be connected
            component (GenericUnit): The Object of the component that will be connected
            port (Port): The Object of the port that will be connected

        """
        self.connected_components[component_name] = component
        self.ports_connected.setdefault(component_name, {})
        self.ports_connected[component_name][port.get_id()] = port

    def set_balance(self, component_name: str, port_id: str):
        """
        Sets the balance of the stream to a new level

        Args:
            component_name (str): component from which the balance should be set
            port_id (str): Port ID from which the balance should be set

        """

        self.balance[PhysicalQuantity.stream] = self.ports_connected[component_name][port_id].get_stream()
        if type(self.ports_connected[component_name][port_id]) == Port_Mass:
            self.balance[PhysicalQuantity.pressure] = self.ports_connected[component_name][port_id].get_pressure()
            self.balance[PhysicalQuantity.temperature] = self.ports_connected[component_name][port_id].get_temperature()
            self.balance[PhysicalQuantity.mass_fraction] = self.ports_connected[component_name][
                port_id].get_mass_fraction()

    ###################################
    # GET Methods
    ###################################

    def get_id(self) -> str:
        """

        Returns:
            str:    Returns ID of the branch
        """
        return self.branch_id

    def get_stream_balance(self) -> float:
        """

        Returns:
            dict: Returns the actual balance of the branch balance (e.g. stream, pressure, temperature)
        """
        return self.balance[PhysicalQuantity.stream]

    def get_type(self) -> str:
        """

        Returns:
            str: Returns stream type of the branch
        """
        return self.branch_type

    def get_fixed_components(self) -> dict:
        """

        Returns:
            dict: Returns all components and their related fixed ports
        """
        return self.fixed_ports

    def get_values_of_connected_port(self, component_name: str, port_id: str) -> float:
        """
        Method returns the actual port values of a branch connected port

        Args:
            component_name (str):    Name of the Component
            port_id (str):      ID of the connected port

        Returns:
            float:              Returns the value of the branch connected port
        """

        return self.ports_connected[component_name][port_id].get_values()

    def get_loop_controlled_components(self) -> list:
        """

        Returns:
            list: A list of all components which has been loop_controlled by this branch in this runcount
        """
        return self.loop_controlled_components

    def get_port_limited_value(self, port: Port, value: float) -> float:
        """
        Calculates the limited value of a specific port

        Args:
            port (object):  Port which should be checked regarding the limits
            value (float):  Value which should be checked whether its in the ports limits

        Returns:
            float:          Limited value, which is set to the limit if the actual value has been outside the limits
        """

        limits = port.get_value_limits()
        possible_value = value
        for key in limits:
            if key == PhysicalQuantity.stream:
                if port.get_sign() != 0:
                    possible_value = range_limit(value, sorted(limits[key])[0], sorted(limits[key])[1])
                else:
                    possible_value = value
                    # TODO: Port limits für beidseitige Ports anschauen
            else:
                possible_value = range_limit(value, sorted(limits[key])[0], sorted(limits[key])[1])
        return possible_value

    def get_ports_of_connected_component(self, component_name: str) -> list:
        """
        Finds the port of a component which is connected to the branch

        Args:
            component_name (str): Name of the component

        Returns:
            list:            ID of the connected port of a component
        """
        if component_name in self.ports_connected:
            ports = list(self.ports_connected[component_name].values())
        else:
            raise BranchError(f'Defined component {component_name} of loop control rules not connected to branch!')
        return ports

    def get_stream_of_connected_component(self, component_name) -> float:
        """
        Returns the stream of the port of a component which is connected to the branch

        Args:
            component_name (str):    Name of the component

        Returns:
            float:              Stream value of the specified port
        """
        connections = []

        if component_name in self.adaptive_ports:
            connections.append(self.adaptive_ports[component_name])
        if component_name in self.fixed_ports:
            connections.append(self.fixed_ports[component_name])

        if len(connections) > 1:
            logging.warning(f'Component {component_name} is connected twice to branch {self.branch_id}')
        else:
            connections = str(connections[0])

        return self.connected_components[component_name].ports[connections].get_stream()

    ###################################
    # CALCULATION Methods
    ###################################

    def run(self, names_already_run: list, runcount: int, rerun: bool) -> (bool, list, bool):
        """
        Run method of the single branch:
        In this method the whole branch will be solved. Therefore all active and passive components which
        are part of this branch will be run and the branch balance should be zero afterwards
        Otherwise the branch calls a loop control, controls one or more elements actively and reruns
        all branches starting with this one.

        Args:
            names_already_run (list): List of names that has already been run
            runcount (int): The Timestep of the model that is solved at this moment
            rerun (bool): Boolean value whether its the first run of this runcount or a rerun due to loop control

        """
        logging.debug('################################################')
        logging.debug(f' BRANCH: {self.branch_id} of branch type "{self.branch_type}"')

        """Set some default values for calculation"""
        self.balance = {}
        self.calculated = False
        self.runcount = runcount
        reset = False
        run_again = True
        timeout = 0
        timeout_max = self.basic_technical_settings.timeout_max
        "Loop the branch until the run_again value is false or the timeout reached the maximum to prevent endless loops"
        while run_again and timeout < timeout_max:
            timeout += 1
            if rerun:
                """
                4) If the branch has been "run" already and is in a rerun mode:
                 - the temporary adaptive ports are set to model adaptive ports 
                 - if they are not already set by the loop control. 
                And the status of the components change to calculated. 
                That is necessary for the status of the refprop calculation               
                """
                # TODO: find out what that has to do with refprop
                if self.temp_adaptive_ports == {}:
                    self.temp_adaptive_ports = self.adaptive_ports.copy() #Note: The ".copy()" is necessary. otherwise it would only be a "pointer"
                    #from adaptive_ports to temp_adaptive_ports, but it has to be a copy, since in Line 470 there is a ".pop()"
                if self.temp_fixed_ports == {}:
                    self.temp_fixed_ports = self.fixed_ports.copy()
                self.balance = {}
                for component in self.ports_connected.values():
                    for port in component.values():
                        port.set_status_calculated()
            else:
                self.temp_adaptive_ports = self.adaptive_ports.copy()
                self.temp_fixed_ports = self.fixed_ports.copy()

            """
            ----- ALREADY RUN COMPONENTS ----
            Check for already run components. If some components which are connected to this branch have already
            been run by another branch, this branch only takes the values of the connected port and adds them
            to its own balance."""

            for name in names_already_run:
                if name in [*self.connected_components.keys()]:
                    if name in self.temp_fixed_ports:
                        for port_id in self.temp_fixed_ports.get(name):
                            if self.balance == {}:
                                self.set_balance(name, port_id)
                            else:
                                self.balance = self.check_balance_validity(name, port_id)
                    elif name in self.temp_adaptive_ports:
                        for port_id in self.temp_adaptive_ports.get(name):
                            if self.balance == {}:
                                self.set_balance(name, port_id)
                            else:
                                self.balance = self.check_balance_validity(name, port_id)
            """
            ----- 1) FIXED COMPONENTS ----
            Running the branch connected components which are connected by an fixed port. Active ports use 
            a desired profile value or their maximum port value (set by size) to set the flow/ input/output. 
            The branch must and will accept the stream values which are given or taken by an active component
            """
            for name, ports in self.temp_fixed_ports.items():
                if name not in names_already_run:
                    port_id = ports[0]
                    required_port_value = self.balance.copy()
                    if required_port_value != {}:
                        required_port_value[PhysicalQuantity.stream] = -required_port_value[
                            PhysicalQuantity.stream]
                    else:
                        required_port_value[PhysicalQuantity.stream] = 0

                    "Running the component"
                    self.connected_components[name].run(port_id, required_port_value, runcount)  # run component
                    names_already_run[name] = True
                    """Setting the balance based on the new results after component run"""
                    for port_id in ports:
                        if self.balance == {}:
                            self.set_balance(name, port_id)
                        else:
                            self.balance = self.check_balance_validity(name, port_id)

            """
            ----- 2) ADAPTIVE COMPONENTS ----
            Running the connected (to the branch) components which are passive (active=False) to the branch.
            The branch gives these ports a desired stream value and tries to equalize its internal branch balance to zero.
            If the first passive component is not able to take all the necessary stream to equalize the branch balance
            the branch tries to give the rest of the stream to the next component. 
            The order is defined by the "passive priority rules" of this branch. 
            """
            for name, ports in self.temp_adaptive_ports.items():
                # usually only one port connected to branch, BUT: Storage can have two (into+out of component!!)
                if name not in names_already_run:
                    required_port_value = self.balance.copy()  # we try to dump the full balance onto this port
                    component_ran_already = False
                    for port_id in ports:  # usually only one, but storage can have two, hence the loop
                        """Check whether port is able to equalize the balance regarding the sign (flow direction) of the port 
                        -1  - into component, out of branch
                         0  - both directions (grid) 
                         1  - out of component (into grid ) 
                        """
                        if self.check_port_sign(self.ports_connected[name][port_id],
                                                self.balance[PhysicalQuantity.stream]):  # check if current port has the right sign
                            required_port_value[PhysicalQuantity.stream] = -required_port_value[
                                PhysicalQuantity.stream]
                            self.connected_components[name].run(port_id, required_port_value, runcount)
                            component_ran_already = True  # if one port has been found with the right direction, the component is finished
                            break
                    """If component is not able to equalize balance theoretically (by its sign), 
                    the component is run with value of 0 to prevent errors"""
                    if not component_ran_already:
                        required_port_value[PhysicalQuantity.stream] = 0
                        self.connected_components[name].run(ports[0], required_port_value, runcount)

                    """Setting the balance based on the new results after component run (or skip if port signs did not match)"""
                    for port_id in ports:
                        if self.balance == {}:
                            self.set_balance(name, port_id)
                        else:
                            self.balance = self.check_balance_validity(name, port_id)
                    names_already_run[name] = True

            """ 3) Check whether after run of all branch connected (fixed and adaptive) components the branch balance is
            equalized to 0. If not: a loop control is necessary which actively sets the values of some components 
            which are defined in the loop "control rules" for this branch"""

            if abs(self.balance[PhysicalQuantity.stream]) > self.basic_technical_settings.absolute_model_error:
                rerun = self.loop_control(self.balance[PhysicalQuantity.stream], timeout)
                reset = True
                names_already_run = {}
            else:
                self.calculated = True
                run_again = False

        if timeout == timeout_max:
            raise BranchError(f'Could not find solution for Branch {self.branch_id} at runcount {runcount}\n'
                              f"Component {name}'s Port {port_id} has a balance of {self.balance}")

        return rerun, names_already_run, reset

    def loop_control(self, balance_value: float, timeout: int) -> bool:
        """
        This method uses the balance value if the branch could not be solved and tries to actively
        control the components specified in self.loop_control_rules to get an result for the branch

        Args:
            balance_value (float): Stream value of the branch that has to be balanced
            timeout (int): Variable which defines whether code should quit to prevent endless loop
        """

        "Loop over all components which are defined in loop control rules"
        for component_name in self.loop_control_rules:
            if abs(balance_value) <= self.basic_technical_settings.absolute_model_error:
                break
            "Get all ports of the component which are connected to this branch"

            component_ports = self.get_ports_of_connected_component(component_name)
            component_value = 0
            "Loop over the connected ports to find the port which can be used to equalize the balance"
            for component_port in component_ports:
                component_value = component_port.get_stream()
                if component_value * balance_value < 0:
                    break

            "Calculate the new value which can be set to the port to equalize the branch balance"
            component_value_new = component_value - balance_value

            "Check whether the new port value is in the limits of the port stream limits"
            limited_value = self.get_port_limited_value(component_port, component_value_new)
            if not component_value_new == 0 and timeout == 1:
                component_value_new = limited_value
            elif limited_value != component_value_new and timeout > 1:
                component_value_new = 0

            """Check whether an change in the sign of the stream occurs, if it is true and port sign is not 0 the 
            new value is set to 0"""
            if not self.check_port_sign_change_validity(component_port, component_value_new):
                component_value_new = 0

            """Determine the new balance value and set the calculated component value to the port"""
            balance_value -= (component_value - component_value_new)
            self.connected_components[component_name].set_controlled_active_port(component_port,
                                                                            component_value_new)

            """Add the component to the list of components which are actively controlled by loop control"""
            self.loop_controlled_components.append(component_name)

        """Recheck the balance value whether it should be lower than the tolerated absolute model error, if true 
        rerun the model"""
        if balance_value <= self.basic_technical_settings.absolute_model_error or timeout > 1:
            rerun = True
            for component_name in self.loop_controlled_components:
                if component_name not in self.temp_fixed_ports:
                    self.temp_fixed_ports[component_name] = [port.get_id() for port in
                                                        self.get_ports_of_connected_component(component_name)]
                    if component_name in self.temp_adaptive_ports:
                        self.temp_adaptive_ports.pop(component_name) # That's the Reason, why in Line 300-320 has to be a .copy()
            for component in self.loop_controlled_components:
                if component not in self.temp_fixed_ports:
                    self.temp_fixed_ports[component] = [port.get_id() for port in
                                                        self.get_ports_of_connected_component(component)]
                    if component in self.temp_adaptive_ports:
                        self.temp_adaptive_ports.pop(component)
                    logging.warning(f'branch integrity check failed; trying to rerun branch {self.branch_id} with'
                                    f' active controlled components {self.loop_controlled_components}')
        else:
            rerun = False
        return rerun

    def check_port_sign_change_validity(self, port: Port, value: float) -> bool:
        """
        This method is used to check whether an port sign change occurs and if yes whether its valid

        Args:
            port (Port): Desired port which should be checked
            value (float): Stream value that should be checked for the port

        Returns:
            bool: Boolean whether the change of port sign is valid
        """

        port_sign = port.get_sign()
        if port_sign == StreamDirection.stream_bidirectional:
            return True
        if port_sign.value * value <= 0:
            return False
        else:
            return True

    def check_port_sign(self, port: Port, balance: float) -> bool:
        """
        This method is used to check whether a port is able to equalize the balance given

        Args:
            port (object): Object of the port that should be checked
            balance (float): Balance value which should be checked against port sign

        Returns:
            bool: Boolean answer, whether sign of the given port is zero or opposite to balance value
        """
        port_sign = port.get_sign()
        if port_sign == StreamDirection.stream_bidirectional:
            return True
        if port_sign.value * balance <= 0:
            return True
        else:
            return False

    def check_balance_validity(self, component_name: str, port_id: str) -> dict:
        """
        This method checks whether the values of a port match with the properties of the branch balance
        if properties (like temperature, pressure, fraction) do not match an error will be raised. If the
        branch does not have balance values (math.inf). The balance of the branch will be set to the
        property values of the connected port.

        Args:
            component_name (str): Name of the component which contains the port that should be checked
            port_id (str): Id of the port that should be checked against the branch balance

        Returns:
             dict: Dictionary of the balance of the branch
        """

        for key, value in self.balance.items():
            """Loop over the property items set to the branch balance and check for the properties"""
            if key == PhysicalQuantity.temperature:
                """ Check whether branch balance temperature is equal to port temperature of connected components"""
                if not self.balance[key] == self.ports_connected[component_name][port_id].get_temperature():
                    """ If temperature values do not match perform check whether the port already has 
                    a set temperature """
                    if abs(self.ports_connected[component_name][port_id].get_temperature()) != math.inf and \
                            self.ports_connected[component_name][port_id].get_temperature_status() == 0:
                        """ If the port has a temperature, check will be performed if the branch does not have a set 
                        temperature. If a temperature is already set and different from port temperature an error will 
                        be raised."""
                        if self.balance[key] is None or abs(self.balance[key]) == math.inf:
                            self.balance[key] = abs(self.ports_connected[component_name][port_id].get_temperature())
                        else:
                            # todo: 3 times the Same Error Message. Better solution?
                            raise BranchError(f'Error in {key} of branch {self.branch_id} at runcount {self.runcount}. '
                                              f'Add mixer class to prevent error.')
                    else:
                        self.ports_connected[component_name][port_id].set_temperature(self.balance[key])
            elif key == PhysicalQuantity.pressure:
                """ Check whether branch balance pressure is equal to port temperature of connected components"""
                if not (self.balance[key] == self.ports_connected[component_name][port_id].get_pressure()):
                    """ If pressure values do not match perform check whether the port already has 
                    a set pressure """
                    if abs(self.ports_connected[component_name][port_id].get_pressure()) != math.inf and \
                            self.ports_connected[component_name][port_id].get_pressure_status() == 0:
                        """ If the port has a pressure, check will be performed if the branch does not have a set 
                        pressure. If a pressure is already set and different from port temperature an error will 
                        be raised."""
                        if self.balance[key] is None or abs(self.balance[key]) == math.inf:
                            self.balance[key] = abs(self.ports_connected[component_name][port_id].get_pressure())
                        else:
                            # same Error Message_________________________________
                            raise BranchError(f'Error in {key} of branch {self.branch_id} at runcount {self.runcount}. '
                                              f'Add mixer class to prevent error.')
                    else:
                        self.ports_connected[component_name][port_id].set_pressure(self.balance[key])
            elif key == PhysicalQuantity.mass_fraction:
                """If no mass fraction is set for the branch the mass fractions of the connected port will be 
                transferred to the balance of the model"""
                if self.balance[key] == {}:
                    self.balance[key] = self.ports_connected[component_name][port_id].get_mass_fraction().items()
                else:
                    """If mass fraction is already set for the branch the mass fractions of each component will be
                    compared with the branches mass fraction. If a discrepancy of the mass fractions differ more than
                    1e-10 an error will be raised."""
                    for mass_key, mass_val in self.ports_connected[component_name][port_id].mass_fraction.items():
                        if not abs(mass_val) - abs(self.balance[key][mass_key]) <= 1e-10:
                            # same Error Message____________________
                            raise BranchError(f'Error in {key} of branch {self.branch_id} at runcount {self.runcount}. '
                                              f'Add mixer class to prevent error.')
            elif key == PhysicalQuantity.stream:
                """Stream property value of the port will be added to the stream property value of the branch."""
                self.balance[key] += self.ports_connected[component_name][port_id].get_stream()

        return self.balance
