
import sys
import pvlib
import numpy as np
import logging

from base_python.source.helper.geocoding import get_coordinates


class RE_System_Wind():

    def __init__(self,
                 location_name: str = None,
                 latitude: float = None,
                 longitude: float = None,
                 altitude: float = None,
                 #wind_profile: list = None,
                 surface_roughness: float = 0.245,
                 hub_height: float = 120,
                 rotor_diameter: float = 135,
                 cut_in_wind_speed: float = 3.0,
                 cut_out_wind_speed: float = 20,
                 rated_wind_speed: float = 9.3,
                 power_rating: float = 3000):
        """
        collection of methods aimed towards preprocessing of Wind Power production curves
        credit to Frank Fischer for most of the algorithms
        initial values represent Myse 3.0-135 from here: www.myse.com.cn/uploadfiles/2019/05/20190515013101793.pdf
        for more data see: https://nozebra.ipapercms.dk/Vestas/Communication/4mw-platform-brochure/?page=16

        Args:
            location_name: string of city name
            latitude: locations coordinate lat
            longitude: locations coordinate lon
            altitude: [m] height difference between sea-level and soil-level. used to calculate the pressure-level
            (not implemented) wind_profile: [m/s] list containing wind speed values
            surface_roughness: exponent decribing landcape characteristic (see _wspd_correction for details)
            hub_height: [m] height of tower
            rotor_diameter: [m]
            cut_in_winds_peed: [m/s] start wind speed for wind power production
            cut_out_wind_speed: [m/s] shut down wind speed
            rated_wind_speed: [m/s] wind speed where nominal power is reached
            power_rating: [kw] power output at rated wind speed
        """
        if location_name is None and (latitude is None or longitude is None):
            logging.critical('not enough info (location) for Wind Power production')
            sys.exit()

        # get coordinates from location name if needed (at least one coordinate missing):
        if location_name is not None and (latitude is None or longitude is None):
            tmp = get_coordinates(location_name)
            latitude = tmp.latitude
            longitude = tmp.longitude

        self.location_name = location_name
        self.latitude = latitude
        self.longitude = longitude
        self.hub_height = hub_height
        self.rotor_diameter = rotor_diameter
        self.cut_in_wind_speed = cut_in_wind_speed
        self.cut_out_wind_speed = cut_out_wind_speed
        self.rated_wind_speed = rated_wind_speed
        self.power_rating = power_rating
        self.surface_roughness = surface_roughness


        self._set_weather_TMY()  # TMY: typical meterological year, sets self.weather_df
        self.wind_profile = np.array(self.weather_df['wind_speed'].tolist())
        self.own_wind_profile_set = False

        if altitude is not None:
            self.altitude = altitude
        else:
            self.altitude = self.weather_location['location']['elevation']

        self._calc_density_profile()

        self.rotor_area = 0.25 * np.pi * self.rotor_diameter ** 2


    def _set_weather_TMY(self):
        """
        normalized weather and radiation data from
        https://joint-research-centre.ec.europa.eu/pvgis-photovoltaic-geographical-information-system_en
        """
        AllData = pvlib.iotools.get_pvgis_tmy(self.latitude, self.longitude, map_variables=True)
        self.weather_location = AllData[2]
        self.weather_df = AllData[0]
        self.weather_df.index.name = "utc_time"

    def get_weather_TMY(self):
        """
        normalized weather and radiation data from
        https://joint-research-centre.ec.europa.eu/pvgis-photovoltaic-geographical-information-system_en

        Returns:
            weather_df: dataframe with normalized weather data, hourly , 1 year
        """
        return self.weather_df

    def get_power_profile(self):
        """

        Returns:
            profile of power production [kWh] of wind power plant at given location
        """
        if not self.own_wind_profile_set:  # wind comes from 10m data and has to be adjusted for hub height
            w1 = self._wspd_correction()
        else:
            w1 = self.wind_profile

        w1[w1 < self.cut_in_wind_speed] = 0
        w1[w1 >= self.cut_out_wind_speed] = 0
        w1[w1 >= self.rated_wind_speed] = self.rated_wind_speed
        #w1 = w1.apply(lambda x: self.rated_wind_speed if x >= self.rated_wind_speed else x)
        w2 = w1*(2/3)
        density = self.density_profile
        wind_power = 1e-3 * 0.25 * self.rotor_area * (density * ((w1 ** 2 - w2 ** 2) * (w1 + w2.T))).T
        wind_power[wind_power >= self.power_rating] = self.power_rating
        return np.array(wind_power.tolist())

    def get_normalized_production(self):
        """
        normalizes the production profile (power) to the nominal power output ( power rating) of the wind power plant
        :return:
        """

        normalized_production_profile = self.get_power_profile()/self.power_rating
        return normalized_production_profile

    def _wspd_correction(self):
        """
        Roughnessclass  Landscape characteristic                                            Exponent (k)
        0               Water surface                                                       0.0
        0.5             Completely open terrain with soft surface as runways at airports,   0.12
                        mowed grass, etc
        1.0             Open agricultural land with single buildings                        0.245
        1.5             Agricultural land with separate buildings and 8 meter fences at     0.275
                        a distance of >>1250 m
        2.0             Agricultural land with separate buildings and 8 meter fences at     0.30
                        a distance of >>500 m
        2.5             Agricultural land with groups of buildings and 8 meter fences at    0.335
                        a deistance of >>250 m
        3.0             Villages, small towns, agricultural land with separate buildings    0.37
                        and high fences, forest and rugged terrain
        3.5             Big cities with tall buildings                                      0.405
        4.0             Very big cities with tall buildings and skyscrapers                 0.44

        Returns:
            for turbulence corrected wind speed profile at hub height
        """
        return self.wind_profile * (self.hub_height / 10) ** self.surface_roughness # 10 is fixed parameter for measurement height of wind speed (as is in PVGIS tmy data)

    def _temp_in_K(self, temp_in_C):
        return temp_in_C + 273.15

    def _saturated_vapor_pressure_magnus(self, temp_in_C):
        # Magnus-Formel nach Sonntag 1990.
        # Gilt für den Temperaturbereich von -45°C <= temp_in_C <= 60°C
        # http://cires1.colorado.edu/~voemel/vp.html
        # Result in [mbar]
        return 6.112 * np.e ** ((17.62 * temp_in_C) / (243.12 + temp_in_C))

    def _calc_gas_const_humid_air(self, pres_in_mbar, temp_in_C, rhum_in_percent):

        svp = self._saturated_vapor_pressure_magnus(temp_in_C)
        R_dryair = 287.05  # J/kgK
        R_vapor = 461.523  # J/kgK
        if rhum_in_percent == 0:
            return R_dryair
        else:
            return R_dryair / (1 - 0.01 * rhum_in_percent * svp / pres_in_mbar * (1 - R_dryair / R_vapor))

    def _calc_single_density(self, pres_in_bar, temp_in_C, rhum_in_percent):
        # p*V = m * R_s * T
        # p/(R_s*T) = m/V = rho
        # [mbar]/([J/(kgK)]*[K]) = [kg]/[m³]
        # Konvertierung von Einheiten: 1 mbar = 100 Pa || 1 Pa = 1 N/m²  || 1 J = 1 Nm
        # [N/m²)]/([Nm/(kg)])
        # [N/m²] * [kg/Nm]
        # [kg*N]/[m² *Nm]
        # [kg/m³]
        temp_in_Kelvin = self._temp_in_K(temp_in_C)
        R_humid_air = self._calc_gas_const_humid_air(pres_in_bar, temp_in_C,
                                                     rhum_in_percent)
        rho = pres_in_bar / (R_humid_air * temp_in_Kelvin)

        return rho

    def _calc_density_profile(self):
        """
        todo: write function to calc density!
        Returns:

        """
        density_profile = []

        for (p, t, h) in zip(self.weather_df['pressure'], self.weather_df['temp_air'], self.weather_df['relative_humidity']):
            density_profile.append(self._calc_single_density(p, t, h))
        self.density_profile = density_profile

    def get_v_min_hours(self):
        """
        Returns:
            Number of hours spend <= vMin
        """
        wspd = self._wspd_correction()
        hours = wspd[wspd <= self.cut_in_wind_speed].size
        return hours

    def get_v_max_hours(self):
        """

        Returns:
            Number of hours spend >= vMax
        """
        wspd = self._wspd_correction()
        hours = wspd[wspd >= self.cut_out_wind_speed].size
        return hours


if __name__ == '__main__':
    import matplotlib.pyplot as plt
    location = 'Leipzig'
    print('Location = ' + location)
    Instance = RE_System_Wind(location_name=location)
    this = Instance.get_power_profile()

    my_wind_profile = [range(0, 25, 8760)]
    Instance = RE_System_Wind(location_name=location)
    this = Instance.get_power_profile()
    print(Instance.get_normalized_production())

    Instance = RE_System_Wind(location_name='Flensburg')
    print(sum(Instance.get_normalized_production()))

    Instance = RE_System_Wind(location_name='Munchen')
    print(len(Instance.get_normalized_production()))
