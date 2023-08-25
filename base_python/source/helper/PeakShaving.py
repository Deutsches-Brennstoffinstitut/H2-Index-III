import logging, sys
from scipy.optimize import brentq
from base_python.source.helper._FunctionDef import range_limit


class Mixin:

    def calc_full_hours_of_use(self, component_name: str, port_type: str):
        """
        :param component_name:  specify the component the calculation is carried out for
        :param port_type:       specify the port
        :return:                the full hours of use (Vollbenutzungsstunden) of the system
        """

        grid_energy_drain = 0
        max_grid_drain = 0

        if component_name in self.components:

            # check if model has been run in advance (at least once)
            if self.systemvars is None:
                self.run()

            # calculate: overall grid sum, maximum
            for step in self.systemvars:
                val = step['ports'][component_name][port_type]
                grid_energy_drain += val * self.time_resolution / 60
                if val > max_grid_drain:
                    max_grid_drain = val

            # calculate the full hours of use value
            return grid_energy_drain / max_grid_drain

        else:
            logging.critical('system.full_hours_of_use: The required component "{}" is not part of the model.'.format(
                component_name))
            sys.exit()

    def _find_grid(self, limited_grid, grid_medium):
        if limited_grid is None:
            grid_names = self.get_sources(grid_medium,
                                          'grid')  # get all storages of the model using the designated technology
            if len(grid_names) == 0:
                logging.critical(
                    'Peak shaving: No source (e.g. grid) with the given technology "{}" was found.'.format(grid_medium))
                sys.exit()
            elif len(grid_names) == 1:
                return grid_names[0]  # return the found grid
            elif len(grid_names) > 1:
                logging.warning(
                    'Peak shaving: Multiple sources of type "{}" found: {} - taking the first one.'.format(grid_medium,
                                                                                                           grid_names))
                return grid_names[0]  # take the first found grid
        elif limited_grid in self.names:
            return limited_grid
        else:
            logging.critical('Peak shaving: The required source {} is not part of the model.'.format(limited_grid))
            sys.exit()

    def _find_storage(self, used_storage, storage_medium):
        if used_storage is None:
            storage_names = self.get_storages(
                storage_medium)  # get all storages of the model using the designated technology
            if len(storage_names) == 0:
                logging.critical(
                    'Peak shaving: No storage with the given technology "{}" was found.'.format(storage_medium))
                sys.exit()
            elif len(storage_names) == 1:
                return storage_names[0]  # return the found storage
            elif len(storage_names) > 1:
                logging.warning(
                    'Peak shaving: Multiple storages of type "{}" found, taking the first one.'.format(storage_medium))
                return storage_names[0]  # return the first found storage
        elif used_storage in self.names:
            return used_storage
        else:
            logging.critical('Peak shaving: The required storage {} is not part of the model.'.format(used_storage))
            sys.exit()
