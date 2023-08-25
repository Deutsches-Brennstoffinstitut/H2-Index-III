# import variable name declarations in order to enable syntax check in programming environment
import logging
import sys
from base_python.source.basic.CustomErrors import BranchConnectionError

class Mixin:
    def __init__(self):
        self.branch_calculation_order = None

    def build_branches(self):
        """
        This function is used to build the branches of the model and sorts them regarding dependencies
        """


        branches_split = {}
        for branch_name, branch in self.branches.items(): # Loop over all Branches
            branch_id = branch.get_id()
            branch_split = {'fixed': {}, 'adaptive': {}}
            for component in branch.connections: # Loop over all Components of a Branch
                link_set = False
                name = component[0]
                sign = component[1]

                #todo: ??? keine Ahnung warum Q_Q das da ist (FFi)
                if len(component) == 3:
                    external_identifier = component[2]
                    port = self.components[name].get_port_by_external_identifier(external_identifier)
                    ports = {port.get_id: port}
                else:
                    ports = self.components[name].get_ports()

                for port_id, single_port in ports.items(): # Loop over all Ports of a Component
                    if single_port.get_linked_branch() is None:  # check whether already branch connected
                        if single_port.get_sign() == sign:
                            if single_port.get_type() == branch.get_type():
                                link_set = True
                                port_id = single_port.get_id()
                                branch.add_port_connection(name, self.components[name], single_port)
                                self.components[name].ports[port_id].set_linked_branch(branch_id)
                                self.components[name].set_branch_id(branch_id=branch_id)

                                if single_port.get_fixed_status():
                                    answer = branch_split['fixed'].setdefault(name, [port_id])
                                    if answer != [port_id]:
                                        branch_split['fixed'][name].append(port_id)
                                else:
                                    answer = branch_split['adaptive'].setdefault(name, [port_id])
                                    if answer != [port_id]:
                                        branch_split['adaptive'][name].append(port_id)
                                break
                if not link_set:
                    raise BranchConnectionError(f'Could not set branch connection of {component} at branch {branch_id}')
            branches_split[branch_name] = branch_split

        # throw error if a branch contains no fixed part
        missing_fixed = None
        for name, branch_split in branches_split.items():
            if len(branch_split['fixed']) == 0:
                missing_fixed = name
        if missing_fixed is not None:
            raise BranchConnectionError(f'Branch {missing_fixed} is missing a fixed component! DUMP: {branches_split[missing_fixed]}')

        # --- sort adaptive branch ports according priorityRules ---
        for i, branch_split in branches_split.items():
            branch_split_sort = {'fixed': branch_split['fixed'], 'adaptive': {}}

            # iterate trough rules
            for rule in self.passive_priorityRules:
                if rule in branch_split['adaptive']:
                    branch_split_sort['adaptive'][rule] = branch_split['adaptive'][rule]
                    branch_split['adaptive'].pop(rule)

            # add missing connections which where not part of priorityRules
            branch_split_sort['adaptive'].update(branch_split['adaptive'])
            branches_split[i] = branch_split_sort

        # --- compute dependencies in branches and sort accordingly ---
        # build ist of dependent objects name:[adaptive_ports]
        dependencies = {}
        for name, component in self.components.items():
            my_ports = component.get_adaptive_ports()
            if len(my_ports) > 0:
                # my_dependencies = [name + ':' + x for x in my_port_names ]
                dependencies[name] = my_ports

        logging.debug('sort branches by dependency within the branches, printing computing order:')
        branches_split_left = branches_split.copy()
        branches_split_sort = {}
        count = 0
        while (len(branches_split_left) > 0) and (count < len(list(self.components.keys())) + 1):
            # iterate through names until all elements have been scanned
            count += 1

            # find components which have no dependencies
            # generate list of names that are already computed, by iterating though list of open branches
            names_no_dependencies = list(self.components.keys()).copy()
            for name, port_ids in dependencies.items():
                for branch in branches_split_left.values():
                    if (branch['adaptive'].get(name) in port_ids) and (name in names_no_dependencies):
                        names_no_dependencies.remove(name)

            # find branches that have no open dependencies
            for branch_ID, branch in branches_split_left.items():
                all_satisfied = True
                for key in branch['fixed'].keys():  # return open dependencies
                    all_satisfied &= key in names_no_dependencies

                if all_satisfied:  # this is the next computable branch
                    logging.debug(f'branch {len(branches_split_sort)}: fixed components {list(branch["fixed"].keys())} '
                                  f'-> adaptive components {list(branch["adaptive"].keys())}')
                    branches_split_sort[branch_ID] = branch
                    branches_split_left.pop(branch_ID)
                    break

        # throw error if count is exceeded
        if len(branches_split_left) > 0:
            raise BranchConnectionError('No straight forward way for the model solution '
                                        'could be found! Maybe there is an indirect loop? No Starting point found?')

        for branch_name, branch in self.branches.items():
            branch.set_fixed_ports(branches_split_sort[branch_name]['fixed'])
            branch.set_adaptive_ports(branches_split_sort[branch_name]['adaptive'])
            if branch_name in self.loop_control_rules:
                branch.set_loop_control_rules(self.loop_control_rules[branch_name])
        self.branch_calculation_order = branches_split_sort
