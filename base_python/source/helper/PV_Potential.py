import pvlib
import sys
import numpy as np
import pandas as pd
from scipy.optimize import minimize
import logging

from base_python.source.helper.geocoding import get_coordinates

class RE_System_PV():

    def __init__(self,
                 location_name: str = None,
                 latitude: float = None,
                 longitude: float = None,
                 altitude: float = None,
                 tilt: float = 35,
                 azimuth: float = 180,
                 power_rating: float = 220):
        """
        collection of methods aimed towards preprocessing of PV production curves
        credit to PVLib for most of the algorithms: https://pvpmc.sandia.gov/

        Args:
            location_name: string of city name
            latitude: locations coordinate lat
            longitude: locations coordinate lon
            altitude: locations elevation from ground
            tilt: tilt of solar panels
            azimuth: orientation of solar panel in degree (180 = south)
            power_rating: power output at 1000 w/m² irradiance
        """

        if location_name is None and (latitude is None or longitude is None):
            logging.critical('not enough info for PV location')
            sys.exit()

        # get coordinates from location name if needed (at least one coordinate missing):
        if location_name is not None and (latitude is None or longitude is None):
            tmp = get_coordinates(location_name)
            latitude = tmp.latitude
            longitude = tmp.longitude

        self.location_name = location_name
        self.latitude = latitude
        self.longitude = longitude
        self.tilt = tilt
        self.azimuth = azimuth
        self.weather_df = pd.DataFrame

        ## initialize parameters for the system
        # ToDo: make system setting available in a method
        sandia_modules = pvlib.pvsystem.retrieve_sam('SandiaMod')
        sapm_inverters = pvlib.pvsystem.retrieve_sam('cecinverter')
        # this one has a nominal power of: "http://www.solardesigntool.com/components/module-panel-solar/Canadian-Solar-Inc./832/CS5P-220M/specification-data-sheet.html"
        self.module = sandia_modules['Canadian_Solar_CS5P_220M___2009_']
        self.power_rating = power_rating  # W

        self.inverter = sapm_inverters['ABB__MICRO_0_25_I_OUTD_US_208__208V_']
        self.system = {'module': self.module,
                       'inverter': self.inverter,
                       'surface_tilt': self.tilt,
                       'surface_azimuth': self.azimuth}

        # weather, solar position for the location
        # ToDo: some sort of update function if location is changed
        self.temperature_model_parameters = pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS['sapm'][
            'open_rack_glass_glass']
        self._set_weather_TMY()
        if altitude is not None:
            self.altitude = altitude
        else:
            self.altitude = self.weather_location['location']['elevation']
        self._set_solar_position()



    def set_orientation(self, tilt, azimuth):
        self.tilt = tilt
        self.azimuth = azimuth
        self.system = {'module': self.module,
                       'inverter': self.inverter,
                       'surface_tilt': self.tilt,
                       'surface_azimuth': self.azimuth}

    def get_optimal_orientation(self):
        """
        optimum is the orientation with highest yield per normalized year

        Returns:
            dict with keys: "tilt", "azimuth"
        """

        # store old orientation:
        tmp_tilt = self.tilt
        tmp_azimuth = self.azimuth

        # set boundary conditions
        bnds = ((0, 90), (0, 360))
        starting_values = (35, 180)
        # cons = ({'type': 'ineq', 'fun': lambda x: x[0] - 2 * x[1] + 2},
        #         {'type': 'ineq', 'fun': lambda x: -x[0] - 2 * x[1] + 6},
        #         {'type': 'ineq', 'fun': lambda x: -x[0] + 2 * x[1] + 2})

        # find solution
        solution = minimize(self._blackbox_fcn, starting_values, method='SLSQP', bounds=bnds, tol=1e-6)

        # restore old orientation
        self.set_orientation(tmp_tilt, tmp_azimuth)
        return {'tilt': solution.x[0], 'azimuth': solution.x[1]}

    def _blackbox_fcn(self, x):
        """
        returns negative sum of produced AC for minimization routine
        Args:
            x[0] = tilt: float [°] orientation of solar panel resp. ground
            x[1] = azimuth:  float [°] orientation of panel resp. North

        Returns:
            negative sum of produced AC
        """
        tilt = x[0]
        azimuth = x[1]

        self.set_orientation(tilt, azimuth)
        return -self.get_sum_production_ac()

    def get_normalized_production(self):
        """
        create normalized production curve of PV system, calculations and weather data based on location.
        credit to PVLib for the algorithms: https://pvpmc.sandia.gov/
        production curves are returned normalized to kW Peak production

        Returns:
            production_norm: numpy array, normalized production profile

        """

        production = self.get_production_ac()
        production_norm = production / self.power_rating
        production_norm[production_norm < 0] = 0
        return production_norm

    def get_sum_production_ac(self):
        """
        Returns:
            production_sum_ac: float, sum of production profile

        """
        production = self.get_production_ac()
        production_sum_ac = np.sum(production)
        return production_sum_ac

    def get_production_ac(self):
        """
        create production curve of PV system, calculations and weather data based on location.
        credit to PVLib for the algorithms: https://pvpmc.sandia.gov/
        production curve is NOT normalized - the technical System is used from
        https://pvlib-python.readthedocs.io/en/stable/introtutorial.html

        Return:
             ac output numpy array of photovoltaic system in Wh
        """
        dni_extra = pvlib.irradiance.get_extra_radiation(self.weather_df.index)
        airmass = pvlib.atmosphere.get_relative_airmass(self.solpos['apparent_zenith'])
        pressure = pvlib.atmosphere.alt2pres(self.altitude)
        am_abs = pvlib.atmosphere.get_absolute_airmass(airmass, pressure)
        aoi = pvlib.irradiance.aoi(
            self.system['surface_tilt'],
            self.system['surface_azimuth'],
            self.solpos["apparent_zenith"],
            self.solpos["azimuth"],
        )

        total_irradiance = pvlib.irradiance.get_total_irradiance(
            self.system['surface_tilt'],
            self.system['surface_azimuth'],
            self.solpos['apparent_zenith'],
            self.solpos['azimuth'],
            self.weather_df['dni'],
            self.weather_df['ghi'],
            self.weather_df['dhi'],
            dni_extra=dni_extra,
            model='haydavies',
        )

        cell_temperature = pvlib.temperature.sapm_cell(
            total_irradiance['poa_global'],
            self.weather_df["temp_air"],
            self.weather_df["wind_speed"],
            **self.temperature_model_parameters,
        )

        effective_irradiance = pvlib.pvsystem.sapm_effective_irradiance(
            total_irradiance['poa_direct'],
            total_irradiance['poa_diffuse'],
            am_abs,
            aoi,
            self.module,
        )
        dc = pvlib.pvsystem.sapm(effective_irradiance, cell_temperature, self.module)
        production_ac = pvlib.inverter.sandia(dc['v_mp'], dc['p_mp'], self.inverter)
        # remove inverter power creep:
        production_ac = production_ac + min(production_ac)
        return production_ac.to_numpy()

    def _set_solar_position(self):
        """
        from normalized weather dataframe
        https://pvlib-python.readthedocs.io/en/stable/generated/pvlib.location.Location.get_solarposition.html#pvlib.location.Location.get_solarposition
        Returns:

        """
        self.solpos = pvlib.solarposition.get_solarposition(
            time=self.weather_df.index,
            latitude=self.latitude,
            longitude=self.longitude,
            altitude=self.altitude,
            temperature=self.weather_df["temp_air"],
            pressure=pvlib.atmosphere.alt2pres(self.altitude),
        )

    def get_solar_position(self):
        """
        from normalized weather dataframe
        https://pvlib-python.readthedocs.io/en/stable/generated/pvlib.location.Location.get_solarposition.html#pvlib.location.Location.get_solarposition
        Returns:
            solpos: DataFrame
        """
        return self.solpos

    def _set_weather_TMY(self):
        """
        normalized weather and radiation data from
        https://joint-research-centre.ec.europa.eu/pvgis-photovoltaic-geographical-information-system_en
        """
        AllData = pvlib.iotools.get_pvgis_tmy(self.latitude,
                                              self.longitude,
                                              map_variables=True,
                                              url='https://re.jrc.ec.europa.eu/api/v5_2/',
                                              )
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

    def get_wind_speed(self):
        """
        mainly for use with Matlab calls
        :return: ndarray of wind speed values
        """
        column_name = 'wind_speed'
        return self.weather_df.loc[:, column_name].values


if __name__ == '__main__':
    import matplotlib.pyplot as plt

    location = 'Leipzig'
    Instance = RE_System_PV(location_name=location)
    norm_production = Instance.get_normalized_production()  # normalized production curve
    print('Location = ' + location)
    print('Coordinates (lat,lon)= ' + str(Instance.latitude) + '  ' + str(Instance.longitude))
    tmy = pvlib.iotools.get_pvgis_tmy(latitude=39.80306525333696,
                                      longitude=18.356299228070274,
                                      map_variables=True,
                                      url='https://re.jrc.ec.europa.eu/api/v5_1/',
                                      )

    WeatherData = Instance.get_weather_TMY()
    column_name = 'wind_speed'
    py_column = WeatherData.loc[:, column_name].values


    print(tmy[0].head(10).to_string())
    print("MaxWSPD:", tmy[0]['wind_speed'].max())

    # norm_production = Instance.get_normalized_production() # normalized production curve
    # print('yearly production = ' + str(Instance.get_sum_production_ac()) + ' Wh')
    optimal_orientation = Instance.get_optimal_orientation()
    print('optimal tilt: ' + str(optimal_orientation['tilt']))
    print('optimal azimuth: ' + str(optimal_orientation['azimuth']))

    # AllData = pvlib.iotools.get_pvgis_tmy(Instance.latitude, Instance.longitude, map_variables=True, url='https://re.jrc.ec.europa.eu/api/v5_2/')
    # print(AllData)
    # location = 'Leipzig'
    # print('Location = ' + location)
    # Instance = RE_System_PV(location_name=location)
    # norm_production = Instance.get_normalized_production()  # normalized production curve
    # print('yearly production = ' + str(Instance.get_sum_production_ac()) + ' Wh')
    # optimal_orientation = Instance.get_optimal_orientation()
    # print('optimal tilt: ' + str(optimal_orientation['tilt']))
    # print('optimal azimuth: ' + str(optimal_orientation['azimuth']))
    #print('this')

