import numpy as np
from datetime import timedelta


class Time_Conversion:
    """Class to convert time-intervalls which are given by profiles or exterior sources to basic SI-units the models
    work with.

    Note:
        mass and energy flows usually are given in [kg/h], [kWh/h], [kg/15-minutes] or [kWh/15-minutes]. On the
        other hand, internal calculations within the modules use SI-Units, e.g. [kg/s] or [kWh/s]. Therefore it is
        needed to dynamically calculate the new divisor.

    Example:
        60 Minute Resolution to 1s Resolution: 1 kg/h = 1kg/3600s => (1/3600)kg/s
    """
    delta_second = timedelta(seconds=1)  # timedelta 1 second
    delta_hour = timedelta(hours=1)  # timedelta 1 hour

    def __init__(self):
        pass

    @staticmethod
    def resolution2second(system_resolution: float):
        """Converts the given time_resolution into the resolution a model works with

        Returns:
            divisor(float): a new divisor based on the old time resolution.

        """

        divisor = timedelta(minutes=system_resolution) / Time_Conversion.delta_second  # float
        return divisor

    @staticmethod
    def second2resolution(system_resolution: float):
        """Converts the for the module needed time_resolution back to the time_resolution of the system.

        Returns:
            divisor(float): a new divisor based on the old time resolution.
        """
        divisor = Time_Conversion.delta_second / timedelta(minutes=system_resolution)
        return divisor

    @staticmethod
    def resolution2hour(system_resolution: float):
        """Converts the time_resolution of the module to an hourly resolution.

        Returns:
            divisor(float): a new divisor based on the old time resolution.

        """
        divisor = timedelta(minutes=system_resolution) / Time_Conversion.delta_hour
        return divisor

    @staticmethod
    def hour2resolution(system_resolution: float):
        """Converts the for the module needed time_resolution back to the time_resolution of the system.

        Returns:
            divisor(float): a new divisor based on the old time resolution.

        """
        divisor = Time_Conversion.delta_hour / timedelta(minutes=system_resolution)
        return divisor


class conv:
    dictionary_with_factors = dict()

    def __init__(self):
        pass

    @classmethod
    def _call(cls, from_to: str):
        """calls the proper lambda-function

        Args:
            from_to(str): The String must be part of CONVERSION_FACTORS

        Returns:
            Returns the needed lambda-function from CONVERSION_FACTORS

        """
        return cls.dictionary_with_factors[from_to]


class Unit_Conversion(conv):
    """Class to convert units.

    """
    dictionary_with_factors = {'K2C': lambda x: x - 273.15,
                               'C2K': lambda x: x + 273.15,
                               'Pa2bar': lambda x: x * 10 ** -5,
                               'bar2Pa': lambda x: x * 10 ** 5
                               }

    def __init__(self):
        """Initializes a list of factors to convert units

        Note:
            The list can be expanded on demand. The point of the list is to see all available conversion factors at
            once w.o. scrolling through messy code.
        todo:
            add conversion_factors on demand
        """
        super().__init__()

    @staticmethod
    def K2C(temp_in_Kelvin):
        """Converts Temperatures in Kelvin to Temperatures in Celsius

        Args:
            temp_in_Kelvin: [K]can be float or lists of floats

        Returns:
            a temperature, or a list of temperatures in °C
        """
        return Unit_Conversion._call('K2C')(temp_in_Kelvin)  # [°C]

    @staticmethod
    def C2K(temp_in_Celsius):
        """Converts Temperatures in °Celsius to Temperatures in Kelvin

        Args:
            temp_in_Celsius: [°C] can be float or lists of floats

        Returns:
            a temperature, or list of temperatures in K
        """
        return Unit_Conversion._call('C2K')(temp_in_Celsius)  # [K]

    @staticmethod
    def Pa2bar(pressure_in_Pascal):
        """Converts Pressures in Pascal to Pressures in bar

        Args:
            pressure_in_Pascal: [Pa] can be float or list of floats

        Returns:
            a pressure, or list of pressures in bar
        """
        return Unit_Conversion._call('Pa2bar')(pressure_in_Pascal)  # [bar]

    @staticmethod
    def bar2Pa(pressure_in_bar):
        """Converts Pressures i bar to Pressures in Pascal

        Args:
            pressure_in_bar: [bar] can be float or list of floats

        Returns:
            a pressure, or list of pressures in Pascal

        """
        return Unit_Conversion._call('bar2Pa')(pressure_in_bar)  # [Pa]


class basic_calculations(conv):
    """Helper-Class to do basic or trivial calculations which are generally needed anywhere.

    """

    dictionary_with_factors = {'diameter2area': lambda y: 0.25 * np.pi * y ** 2,
                               'diameter2circumference': lambda y: np.pi * y,
                               'radius2area': lambda y: np.pi * y ** 2,
                               'radius2circumference': lambda y: 2 * np.pi * y,
                               'H2mass2H2volume': lambda z: z / 0.08988,
                               'H2volume2H2mass': lambda z: z * 0.08988
                               }

    def __init__(self):
        """Initializes a list of functions which are basically anywhere needed
        Note:
            this might be too lazy.
        """
        super().__init__()

    @staticmethod
    def diameter2area(diameter):
        return basic_calculations._call('diameter2area')(diameter)

    @staticmethod
    def diameter2circumference(diameter):
        return basic_calculations._call('diameter2circumference')(diameter)

    @staticmethod
    def radius2area(radius):
        return basic_calculations._call('radius2area')(radius)

    @staticmethod
    def radius2circumference(radius):
        return basic_calculations._call('radius2circumference')(radius)

    @staticmethod
    def H2mass2volume(mass_in_kg):
        return basic_calculations._call('H2mass2H2volume')(mass_in_kg)


if __name__ == '__main__':
    import numpy as np

    celsius = 22  # °C
    kelvin = Unit_Conversion.C2K(celsius)
    print(kelvin)

    bar = 22  # bar
    pascal = Unit_Conversion.bar2Pa(bar)
    print(pascal)

    bar_range = np.linspace(0, 420, 11)
    pascal_range = Unit_Conversion.bar2Pa(bar_range)
    print(pascal_range)

    res = 60.0
    new_divisor = Time_Conversion.resolution2second(res)
    print(res, "Minutes are", new_divisor, "seconds")

    res = 15.0
    new_divisor = Time_Conversion.resolution2second(res)
    print(res, "Minutes are", new_divisor, "seconds.")

    res = 60.0
    new_divisor = Time_Conversion.second2resolution(res)
    print(1, "second equals", new_divisor, "Hours.")


    def printfunc(mass, v_in, v_out):
        print(mass, '\t[kg_H2/h]\t', round(basic_calculations().H2mass2volume(mass)),
              "\t[Nm³_H2/h]\t", v_in, "\t[m/s]_in\t", v_out, "\t[m/s]_out")


    res = 60.0
    kg_H2_per_60_minutes = 142000  # massenstrom limit Bad Lauchstädt:
    v_inlet = 55.1
    v_outlet = 110.3
    printfunc(kg_H2_per_60_minutes, v_inlet, v_outlet)

    kg_H2_per_60_minutes = 100000  # massenstrom limit Bad Lauchstädt:
    v_inlet = 38.8
    v_outlet = 48.8
    printfunc(kg_H2_per_60_minutes, v_inlet, v_outlet)

    kg_H2_per_60_minutes = 70000  # massenstrom limit Bad Lauchstädt:
    v_inlet = 27.2
    v_outlet = 30.0
    printfunc(kg_H2_per_60_minutes, v_inlet, v_outlet)

    kg_H2_per_60_minutes = 60000  # massenstrom limit Bad Lauchstädt:
    v_inlet = 23.3
    v_outlet = 25.0
    printfunc(kg_H2_per_60_minutes, v_inlet, v_outlet)

    kg_H2_per_60_minutes = 50000  # massenstrom limit Bad Lauchstädt:
    v_inlet = 19.4
    v_outlet = 20.4
    printfunc(kg_H2_per_60_minutes, v_inlet, v_outlet)
