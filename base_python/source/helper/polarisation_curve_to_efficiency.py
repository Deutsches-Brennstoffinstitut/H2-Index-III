# Code initially written by Martin Heckner (Former student)
# Rework and commenting ongoing by FFi
# https://sci-hub.se/10.1016/j.jpowsour.2019.227350

import logging

import numpy as np
import pandas as pd


class ElectrolyserEff():
    OFFSET = 0.000001  #

    def __init__(self,
                 lower_currentdensity: float, upper_currentdensity: float,
                 lower_voltage: float, upper_voltage: float,
                 number_of_stacks: int):
        """Class to calculate polarisation and efficiency curves for electrolysers based on cell voltages and current densities

        Notes:
            Reversible and Thermoneutral Voltage are pre-defined and not calculated yet!
            The minimum load of the electrolyser is calculated via the minimum working range of a single stack. this  might be wrong in some cases!

        Args:
            lower_currentdensity(float): Lower Current Density [A/cm²]
            upper_currentdensity(float): Upper Current Density [A/cm²]
            lower_voltage(float): Lower Voltage [V]
            upper_voltage(float): Upper Voltage [V]
            number_of_stacks(int): Number of Stacks of the Electrolyser
        """
        self.working_range = (lower_currentdensity, upper_currentdensity)
        self.rest_range = (0, lower_currentdensity - self.OFFSET)
        self.voltage_range = (lower_voltage, upper_voltage)

        self.amount_of_stacks = number_of_stacks

        self.minimum_load_stack = self.working_range[0] / self.working_range[1]
        # todo: not sure if i make a mistake here by assuming ely load is based on stack load.
        self.minimum_load_electrolyser = self.minimum_load_stack / self.amount_of_stacks
        # ToDo: calculate these voltages
        self.voltage_reversible: float = 1.23
        self.voltage_thermoneutral: float = 1.48

        self.df = self.calculate_efficiency_curves()

    def result(self):
        """Returns a Dataframe with all necessary values of the calculated electrolyser
        Notes:
            I recommend to use the plotly backend in order to plot the Dataframe as shown in the if name = main below.

        Returns:
            A pandas Dataframe

        """
        return self.df

    def func_Utn(self, temperature_in_K) -> float:
        """Funktion zur Temperaturabhängigen bestimmung der thermoneutralen Zellspannung

        Todo:
            not implemented yet

        Notes:
            U_tn(T) = 1.485-1.49*10^-4 * (T-T_0) -9.84*10^-8*(T-T_0)^2
            mit T_0 = 273.15 K
            aus Martins Masterarbeit (S. 33 Gl. 26)

        Returns:

        """
        T_0 = 273.15
        if temperature_in_K <= T_0 + 100:
            U_tn = lambda T: 1.485 - 1.49 * 1e-4 * (T - T_0) - 9.84 * 1e-8 * (T - T_0) ** 2
        else:
            raise NotImplementedError(f'No function to calculate the thermoneutral Current for temperatures >'
                                      f' {temperature_in_K + 100} [K] implemented yet!')
        return U_tn(temperature_in_K)

    def func_Urev(self, pressure_H2: float, pressure_O2: float, pressureH2O: float) -> float:
        """Funktion Nernst-Gleichung zur Druckabhängigen berechnung der reversiblen Zellspannung

        Todo:
            Not implemented yet

        Args:
            pressure_H2(float): Partialdruck Wasserstoff
            pressure_O2(float): Partialdruck Sauerstoff
            pressureH2O(float): Partialdruck Wasser

        Notes:
            U_rev = U_rev_0 + (R*T)/ (2*F) * ln( ((p_O2)^0.5)*p_H2/(p_H2O) )
            mit U_rev_0 = 1.229 V (Reversible Zellspannung unter Standardbedingungen
            R = Universelle Gaskonstante (R = 8.314472 kJ/kmolK)
            p_x = Drücke der Produkte und Edukte
            aus Martins Masterarbeit( S.34 Gl. 27)

        Returns:
            reversible Zellspannung

        """
        raise NotImplementedError("Function to calc reversible Cell Voltage not implemented yet!")

    def calculate_efficiency_curves(self) -> pd.DataFrame:
        """Calculate the efficiency_curves for the single stack and electrolyser which consists of multiple stacks of the same Type

        Notes:
            Calculating the single stack is obsolete,since you can calculate an electrolyser which consists of a single stack aswell.
            It might be useful in order to understand the code.

        Returns:
            Pandas Dataframe with the results
        """

        # Stack
        # arr_polarisation_curve_stack = self.create_polarisation_curve4single_stack()
        # polarisation_curve_stack = pd.DataFrame(data=arr_polarisation_curve_stack[1:2])
        # self.stack_efficiency_curve = self.polarisation_curve2efficiency_curve(polarisation_curve=polarisation_curve_stack)

        # Electrolyser(multiple Stacks)
        polarisation_curve_electrolyser = self.create_polarisation_curve4electrolyser()
        electrolyser_efficiency_curve = self.polarisation_curve2efficiency_curve(
            polarisation_curve=polarisation_curve_electrolyser)
        return self.efficiency_curve2dataframe(efficiency_curve=electrolyser_efficiency_curve)

    def efficiency_curve2dataframe(self, efficiency_curve: np.array) -> pd.DataFrame:
        """Parses the efficiency curve, which is a numpy array to a Dataframe (pandas)

        Args:
            efficiency_curve(np.array):  Numpy-Array 4xn

        Returns:
            Dataframe with axis description
        """
        df = pd.DataFrame._from_arrays(arrays=efficiency_curve[1:, :], columns=[0, 1, 2], index=efficiency_curve[0, :]*100)
        df.index.name = 'load_of_elctrolyser [%]'
        df.columns = ['load_of_stacks_at_load [%]',
                      'stack_efficiency_at_load_of_electrolyser [kWh_H2/kWh_el]',
                      'stack_efficiency_at_load_of_electrolyser [kg/kWh_el]']
        return df

    def create_polarisation_function(self):
        """Creates a function for the voltage based on current density

        x = Current Densities
        y = f(x) = Voltages
        y = f(x) = m*x+t if current density in working range, else 0
        Returns: lambda function

        """

        x0 = self.working_range[0]
        x1 = self.working_range[1]
        y0 = self.voltage_range[0]
        y1 = self.voltage_range[1]
        m = (y1 - y0) / (x1 - x0)
        t = y0 - m * x0

        y = lambda x: 0 if x < x0 else m * x + t
        return y

    def create_polarisation_curve4single_stack(self) -> np.array:
        """ Creates a polarisation-Curve for a single Stack

        Returns:
            numpy-array with 3 x 4 values
            plotted, it should look like a single sawtooth
        """

        # working_range -> arange of current_densities (x-Axis in [A/cm²])
        y = self.create_polarisation_function()
        current_densities = np.array([self.rest_range[0],
                                      self.rest_range[1],
                                      self.working_range[0],
                                      self.working_range[1]])

        # linear interpolation for known current densities -> f(x) = m*x+t (y-Axis in [V])
        cell_voltages = np.array([y(val) for val in current_densities])
        linsp = current_densities / max(current_densities)
        # x-Values | y-Values -> (x|y)-Pairs
        polarisation_curve = np.row_stack([linsp, current_densities, cell_voltages])
        return polarisation_curve

    def create_polarisation_curve4electrolyser(self) -> np.array:
        """Pretty much the same as "create_polarisation_curve4single_stack, but for multpiple stacks stacked on each other, which is why it is a bit more complex

        Returns:
            numpy-array with 3 x N values
            plotted, it should look like multiple sawtooths
        """

        y = self.create_polarisation_function()
        for stack in np.linspace(1, self.amount_of_stacks, self.amount_of_stacks):
            if stack == 1:  # first Stack
                load = np.array([0, 1, 1, 2]) * self.minimum_load_electrolyser
                current_densities = np.array([self.rest_range[0],
                                              self.rest_range[1],
                                              self.working_range[0],
                                              self.working_range[1] - self.OFFSET])
                cell_voltages = np.array([y(val) for val in current_densities])
            elif stack == self.amount_of_stacks:  # last Stack
                load2append = np.array([stack * self.minimum_load_electrolyser, 1])

                current_densities2append = [self.working_range[0], self.working_range[1]]
                voltages2append = np.array([y(val) for val in current_densities2append])
                load = np.append(*[load, load2append], axis=0)
                current_densities = np.append(*[current_densities, current_densities2append], axis=0)
                cell_voltages = np.append(*[cell_voltages, voltages2append], axis=0)
            else:  # stacks inbetween
                load2append = np.array([stack, stack + 1]) * self.minimum_load_electrolyser
                current_densities2append = [self.working_range[0],
                                            (self.working_range[0] + (self.working_range[1] - self.working_range[
                                                0]) / stack) - self.OFFSET]
                voltages2append = np.array([y(val) for val in current_densities2append])
                load = np.append(*[load, load2append], axis=0)
                current_densities = np.append(*[current_densities, current_densities2append], axis=0)
                cell_voltages = np.append(*[cell_voltages, voltages2append], axis=0)

        polarisation_curve = np.row_stack([load, current_densities, cell_voltages, load])
        return polarisation_curve

    def polarisation_curve2efficiency_curve(self, polarisation_curve) -> np.array:
        """Merges Rest-Range and Working-Range (Polarisation_Curve) and divides the Thermoneutral Voltage with
        the load-dependent Current_Densities

        Args:
            polarisation_curve:

        Returns:
            Numpy Array with 4 rows [load, load of stack, efficieny in kWh_H2/kWh_el, efficiency in kg/kWh_el
        """
        # Efficiency from 0 [%] to 100 [%]
        _arr = polarisation_curve

        # https://stackoverflow.com/questions/48696344/numpy-where-and-division-by-zero/48696660#48696660
        with np.errstate(divide='ignore'):  # np.where throws div-by-zero-error, due to how the function works
            _x_axis = _arr[1] / self.working_range[1]  # Conversion from 0-to-working-load [A/cm²] to 0-to-1 [%]
            _y_axis = np.where(_arr[2] == 0, 0,  # 0 [V] if Cell_Voltage is 0
                               self.voltage_thermoneutral * np.ones(_arr[2].size) / _arr[2]).T

            # if != 0 -> thermoneutral_voltage / cell_voltages
        efficiency_curve = np.row_stack(
            [_arr[0], _x_axis, _y_axis, _y_axis * 1 / 39.41])  # 39.41 kWh_H2/kg_H2= kWh_H2/kWh_el -> kg/kWh_el
        return efficiency_curve


if __name__ == '__main__':
    eff_PEM = ElectrolyserEff(upper_currentdensity=2,  # [A/cm²]
                              lower_currentdensity=0.5,  # [A/cm²]
                              upper_voltage=2,  # [V]
                              lower_voltage=1.65,  # [V]
                              number_of_stacks=10,  # [-]
                              )  # [-]
    eff_AEL = ElectrolyserEff(
        upper_currentdensity=0.4,
        lower_currentdensity=0.2,
        upper_voltage=2.2,
        lower_voltage=1.8,
        number_of_stacks=4,
    )

    pd.options.plotting.backend = "plotly"
    df_PEM = eff_PEM.result()
    df_AEL = eff_AEL.result()

    fig_PEM = df_PEM.plot(title='PEM')
    fig_AEL = df_AEL.plot(title='AEL')
    axis = dict(title='Efficiency in [kWh_H2/kWh_el] <br> Efficiency in [kg/kWh_el]')
    fig_PEM.update_layout(yaxis=axis)
    fig_AEL.update_layout(yaxis=axis)
    fig_PEM.show()
    fig_AEL.show()
