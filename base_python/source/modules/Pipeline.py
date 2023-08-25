from base_python.source.modules.GenericUnit import GenericUnit
from base_python.source.helper.Conversion import Unit_Conversion as uc, basic_calculations as bc, \
    Time_Conversion as tc
import logging
import cProfile
import numpy as np
from numpy import sqrt as sqrt
from numpy import log as log
import pandas as pd
# ___REFRPROP___
import os
import sys
from ctREFPROP.ctREFPROP import REFPROPFunctionLibrary
import CoolProp.CoolProp as CoolProp
from CoolProp import AbstractState
from enum import Enum, auto
from base_python.source.basic.Streamtypes import StreamDirection
from base_python.source.model_base.Dataclasses.TechnicalDataclasses import GenericTechnicalInput

root = os.environ['RPPREFIX']
R = REFPROPFunctionLibrary(root)
R.SETPATHdll(root)


class Pipeline(GenericUnit):
    class Technology(Enum):
        ONSHORE_UNDERGROUND = auto()

    """Pipelinemodule to calculate the pressure drop and temperature in- or decrease of a pipeline which consists of
    one or more pipeline-segments.

    """

    def __init__(self, technology=None, stream_type='HYDROGEN', new_investment=None, economical_parameters=None,
                 fixed_opex=0, save_file=False, generic_technical_input: GenericTechnicalInput = None):
        """

        Args:
            controlled_medium(tuple):
            technology(str):
            new_investment(bool):
            investment_costs(float):
            fixed_opex(float):
            save_file(bool): Bool value. If True the results are saved as xlsx-file.
        """

        super().__init__(technology=technology,
                         new_investment=new_investment,
                         economical_parameters=economical_parameters,
                         stream_type=stream_type,
                         generic_technical_input=generic_technical_input
                         )  # Initializing the Generic Unit
        if self.stream_type is not None:
            self.mass_ports = {}
            self.mass_ports['in'] = self._add_port(port_type=self.stream_type,
                                                   fixed_status=False,
                                                   sign=StreamDirection.stream_into_component)  # Inlet of the Pipelinesegment
            self.mass_ports['out'] = self._add_port(port_type=self.stream_type,
                                                    fixed_status=True,
                                                    sign=StreamDirection.stream_out_of_component)  # Outlet of the Pipelinesegment
            self.fluid = self.mass_ports['in'].port_properties

        # empty variables
        self.dimensional_data = None
        self.material_data = None
        self.geo_data = None
        # Basic values. good enough for buried pipelines.
        self.lambda_pipeline = 40
        self.lambda_insulation = 0.036
        self.lambda_soil = 1.2

        self.save_file = save_file  # Bool variable to skip the export of the excel file if it is not wanted.

        self.heat_flux_iteration = False  # Iterating the heat flux is by default False. The Function
        # "init_heat_flux_iteration" sets the Variable to True
        self.t_environment = 20  # Temperature of the environment in [°C] | Default = 20 °C but doesnt matter,
        # if heat_flux_iteration is False.
        # By Default there is no difference in altitude - perfectly  horizontal pipeline
        # Initializing the Pipelineparameters
        self.save_path = 'Pipeline_output.xlsx'

    @classmethod
    def init_blank(cls, m_dot: float = 100, fluid: str = 'CO2', inlet_pressure_in_Pa: float = 500000,
                   inlet_temperature_in_C: float = 20, save_file=False):
        """CLASSMETHOD to intialize pipelineclass pretty much blank, without initializing branches, a system, etc.

        Args:
            m_dot(float): Massflow in [kg/s]
            fluid(str): REFPROP-fluid as string
            inlet_pressure_in_Pa(float): Pressure at the Inlet of very first Pipeline-Segment in [Pa]
            inlet_temperature_in_C(float): Temperature of the fluid at the Inlet of the ery first Pipeline-Segment in [°C]

        Returns: alternative initialized Pipeline-Class

        """
        ppln_cls = Pipeline(save_file=save_file)
        ppln_cls.massflow = m_dot
        ppln_cls.fluid = fluid
        ppln_cls.p_input = inlet_pressure_in_Pa
        ppln_cls.t_input = inlet_temperature_in_C
        ppln_cls._blank_fluid(fluid_string=fluid)
        ppln_cls.time_resolution = 60
        return ppln_cls

    def _blank_fluid(self, fluid_string=None):
        """Initializes the REFPROP-Fluid with its "abstractState"-Class. This method is needed for a blank
        initialization due to the fact that the fluid properties get initialized somewhere else in a simulation of an
        energy system.

        Args:
            fluid_string(str): REFPROP-fluid as string

        """

        if fluid_string is not None:
            self.fluid = AbstractState("REFPROP", fluid_string)

    def load_dimensional_data(self, inner_diameter_in_m, roughness_in_mm):
        """Initialize the very basic parameters to simulate a pipeline without heat-losses

        Args:
            inner_diameter_in_m(float): Inner Diameter of the Pipeline in [m]
            roughness_in_mm(float): Roughness of the inner Surface of the Pipeline in [mm]

        Returns:

        """
        self.inner_diameter = inner_diameter_in_m  # Inner Diameter of the Pipeline in [m]
        self.roughness = roughness_in_mm  # Roughness of the inner pipeline surface in [mm]
        self.area = bc.diameter2area(self.inner_diameter)  # Area of the inner Diameter in [m²]

    def load_geo_data(self,
                      excel_filename: str = r'T:\Mitarbeiter\Fischer_Frank\Literatur\Pipelines\Pipelines.xlsx',
                      sheet_name='Jaenschwalde-Rotterdamm'):
        """Loads an excel-file with predefined header and data
        todo:
            Create an Excel-File-Template.
        Args:
            excel_filename(str): Filename of the Excel-File
            sheet_name(str): Sheetname of the Excel-File

        Returns: Dataframe with the excel-sheet's data.

        """
        df = pd.read_excel(excel_filename, sheet_name=sheet_name)
        self.geo_data = df

    def init_parameters_buried_pipeline(self, outer_diameter: float, insulation_thickness: float = 0, depht: float = 1):
        """An Optional Method to initialize the temperature correction

            Args:
                temp_environment: Temperature of the environment [°C] (probably soil temperature?)
                outer_diameter(float): Outer Diameter of the Pipeline in [m]
                insulation_thickness(float): Thickness of the insulation [m]
                pipeline_material(str): Material of the Pipeline (must be available in ht, heat transfer, module)
                insulation_material(str): Material of the Insulation (must be available in ht, heat transfer, module)
            Returns:

        """
        self.heat_flux_iteration = True  # activating the heat flux calculation

        self.outer_diameter = outer_diameter  # Outer Diameter of the Pipeline in [m]
        self.insulation_diameter = self.outer_diameter + 2 * insulation_thickness  # Outer Diameter of the Insulation in [m]
        # The Inner Diameter of the Insulation equals the Outer Diameter of the Pipeline.
        self.imaginary_diameter = 4 * depht  # the thought diameter of the soil surrounding the pipeline. [m]
        # e.g. if the pipeline is buried 1m deep, the thoguht diameter is 4 times the depht.

    def run(self, port_id, branch_information, runcount=0):
        """Method to integrate the pipelinemodule in the simulation.

        Args:
            port_id:
            branch_information:
            runcount:

        Returns:

        todo:

            replace 'print-outputs' with logging.info
        """
        ### Init run-method ###

        [controlled_port, port_value, loop_control] = self._calc_control_var(port_id, branch_information[
            PhysicalQuantity.stream])

        port_mass_in = self.mass_ports['in']
        port_mass_out = self.mass_ports['out']

        if loop_control:
            port_mass_in.set_stream(runcount, abs(port_value) * port_mass_in.get_sign())
        else:
            if self.get_port_by_id(controlled_port) != port_mass_in:
                logging.critical(
                    'Branch connected port of pipeline does not match input port. Rearrange branch calculation order!')
            port_mass_in.set_pressure(branch_information[PhysicalQuantity.pressure])
            port_mass_in.set_temperature(branch_information[PhysicalQuantity.temperature])
            port_mass_in.set_stream(runcount, branch_information[PhysicalQuantity.stream])

        self.p_input = port_mass_in.get_pressure()  # Pa
        self.t_input = uc.K2C(port_mass_in.get_temperature())  # °C
        self.massflow = abs(
            port_mass_in.get_stream() / tc.resolution2second(self.time_resolution))  # [kg/timeresolution] -> [kg/s]

        # In the case, if the massflow is 0, input equals output and the function is stopped. (After Loopcontrol etc.
        # and before the iteration
        if self.massflow == 0:
            # todo: the pipeline does not function as storage yet. which means, that a consumer wont get a massflow from the pipeline if the massflow is 0 which is not true
            port_mass_out.set_pressure(self.p_input)
            port_mass_out.set_temperature(uc.C2K(self.t_input))
            port_mass_out.set_stream(runcount, self.massflow / tc.second2resolution(self.time_resolution))
            return

        # ___STATIC_SIMULATION_OF_THE_PIPELINE_HAPPENS_HERE!___
        p2, t2, m_dot = self.pipeline()

        port_mass_out.set_pressure(p2)
        port_mass_out.set_temperature(uc.C2K(t2))
        port_mass_out.set_stream(runcount, m_dot / tc.second2resolution(self.time_resolution))

    def pipeline(self):
        """Function to calculate one pipeline segment one after another.

        Note:
            The input values are from the init-function and/or an excel-file

        Returns: the outlet pressure, massflow and outlet temperature as information for the branch.

        """
        first = True
        data_dict = dict()
        m_dot = self.massflow

        for segment in self.geo_data[1:].iterrows():  # loop starting at the 2nd Element of the List
            if first:  # first loop has to be different from the others.
                inlet_segment = self.geo_data.iloc[0]
                outlet_segment = segment[1]
                p1 = self.p_input
                t1 = self.t_input
                first = False

            else:
                inlet_segment = outlet_segment
                outlet_segment = segment[1]
                p1 = p2
                t1 = t2

            z1 = inlet_segment['Höhe [m]']
            z2 = outlet_segment['Höhe [m]']
            l = abs(inlet_segment['Strecke [km]'] - outlet_segment['Strecke [km]']) * 1000  # km->m
            try:
                self.t_environment = inlet_segment[
                    'Umgebungstemperatur [°C]']  # Environmental Temperature in [°C] | can
                # be air temperature or
            except KeyError:
                if self.heat_flux_iteration != True:
                    self.t_environment = t1
                else:
                    pass

            try:
                self.lambda_soil = inlet_segment['Wärmeleitfähigkeit_Boden [W/(mK)]']
            except KeyError:
                logging.warning(
                    f'No HeatConductionValue for Soil available => Using standard value of {self.lambda_soil} [W/(mK)]')
            try:
                self.lambda_pipeline = inlet_segment['Wärmeleitfähigkeit_Pipeline [W/(mK)]']
            except KeyError:
                logging.warning(
                    f'No HeatConductionValue for Pipeline available => Using standard value of {self.lambda_pipeline} [W/(mK)]')
            try:
                self.lambda_insulation = inlet_segment['Wärmeleitfähigkeit_Isolierung [W/(mK)]']
            except KeyError:
                logging.warning(
                    f'No HeatConductionValue for Insulation available => Using standard value of {self.lambda_insulation} [W/(mK)]')

            # temperature of the soil. Depends on pipeline
            p2, t2, m_dot, l, v1, v2, w1, w2 = self.pipeline_segment(p1=p1, t1=t1, m_dot=m_dot, l=l, z1=z1,
                                                                     z2=z2)
            if self.save_file:
                data_dict[segment[0]] = {'S0 [km]': inlet_segment['Strecke [km]'],
                                         'Z1 [m ü. NN.]': z1,
                                         'm_dot [kg/s]': m_dot,
                                         'v1 [m/s]': w1,
                                         'P1 [Pa]': p1 / 100000,
                                         'T1 [°C]': t1,
                                         'rho1 [t/m³]': 0.001 / v1,
                                         }
        if self.save_file:
            pd.DataFrame(data_dict).T.to_excel(self.save_path)

        return p2, t2, m_dot  # anything the energymodel needs in the end...

    def pipeline_segment(self, p1, t1, m_dot, l, z1, z2, zeta=0):
        """Function to calculate one pipeline segment

        Args:
            p1(float): pressure at the inlet of the pipeline segment in [Pa]
            t1(float): temperature at the inlet of the pipeline segment in [°C]
            m_dot(float): Massflow through the pipeline segment in [kg/s]
            l(float): length of the pipeline segment in [m]
            z1(float): Altitude at the inlet of the pipeline segment in [m. ü.NN.]
            z2(float): Altitude at the outlet of the pipelnine segment in [m. ü.NN.]
            zeta(float): additional flow resistance of the pipeline segment in [-]

        Returns: The Values at the outlet for the next pipeline segment

        """
        length = l

        cp = self._REFPROP_set_cp(pressure_in_Pa=p1,
                                  temperature_in_C=t1
                                  )  # [J/kgK] Heat Capcity of the Fluid

        # Initial Guesses: Depending on the chosen values it could speed up the simulation or slow it down.
        # Change it if you know what you are doing. Otherwise, leave them as they are.
        p2 = 0.95 * p1  # [Pa] Guess of the outlet_pressure
        t2 = t1  # [°C] Guess of the outlet_temperature
        tm = t1  # [°C] Guess of the mean_temperature
        p2I = p2  # [Pa] Pre-Initialized Variable
        delta_pII = 0  # [Pa] Pre-Initialized Variable

        v1 = self._REFPROP_calc_specific_volume(temperature=t1,
                                                pressure=p1
                                                )  # [m³/kg] Specific Volume @ Inlet
        w1 = self._calc_velocity(massflow=m_dot,
                                 specific_volume=v1
                                 )  # [m/s] Velocity of the Fluid @ Inlet

        ### Start with calculations
        go_on_1 = True
        while go_on_1:
            v2 = self._REFPROP_calc_specific_volume(temperature=t2,
                                                    pressure=p2
                                                    )  # [m³/kg] Specific Volume @ Outlet
            w2 = self._calc_velocity(massflow=m_dot,
                                     specific_volume=v2
                                     )  # [m/s] Velocity of the Fluid @ Outlet

            if w2 > 150:  # [m/s] todo: Limit based on fluid (at the moment: half speed of sound)
                # A compressible medium can only reach the speed of sound (MACH 1) at the outlet.
                # Common Values: NG:<10m/s, H2: <30m/s, liquid-CO2: ~1m/s
                # If the fluid flows with the speed of sound it reached the so-called "Lavalgeschwindigkeit"
                # https://de.wikipedia.org/wiki/Laval-Zahl
                # The Pipeline simulation is neither intended to work with such high fluid velocities nor would it work at all.
                # First test, if the basic parameters are "possible", if not, break out of while loop
                logging.critical(
                    f'The outlet-velocity of {w2} m/s exceeds the limit of 150 m/s! Increase the diameter by 2 Inches(50.8 mm)!')
                break

            pm = self._calc_mean_pressure(inlet_pressure_in_Pa=p1,
                                          outlet_pressure_in_Pa=p2
                                          )  # [Pa] mean Pressure
            vm = self._calc_mean_specific_volume(inlet_pressure_in_Pa=p1,
                                                 outlet_pressure_in_Pa=p2,
                                                 inlet_specific_volume=v1,
                                                 outlet_specific_volume=v2
                                                 )  # [m³/kg]
            Sm = self._calc_mean_stagnation_pressure(inlet_velocity_in_ms=w1,
                                                     outlet_velocity_in_ms=w2,
                                                     inlet_specific_volume=v1,
                                                     outlet_specific_volume=v2
                                                     )  # [Pa] mean stagnation Pressure (mittlerer Staudruck)
            viscosity = self._REFPROP_calc_viscosity(mean_pressure=pm,
                                                     mean_temperature=tm
                                                     )  # [ms/kg] mean dynamic Viscosity
            reynolds_number = self._calc_reynolds_number(m_dot=m_dot,
                                                         viscosity=viscosity
                                                         )  # [-]

            # ---- FRICTION LOSS COEFFICIENT ----
            # friction loss coefficient: lambda || flc = 1/ lambda²
            flc, friction_loss_coefficient = self._calc_friction_loss_coefficient(reynolds_number=reynolds_number)

            KE = self._calc_kinetic_energy_correction(reynolds_number=reynolds_number, flc=flc)

            # ---- CALCULATE PRESSURE DROP ----
            delta_pV = self._calc_pressure_drop(friction_loss_coefficient=friction_loss_coefficient,
                                                segment_length=length,
                                                zeta=zeta,
                                                stagnation_pressure=Sm
                                                )
            delta_w_square = self._calc_velocity_adjustment(KE=KE,
                                                            inlet_velocity=w1,
                                                            outlet_velocity=w2
                                                            )
            delta_pI = self._calc_pressure_drop_from_energy_equation(delta_w_square=delta_w_square,
                                                                     inlet_pressure=p1,
                                                                     outlet_pressure=p2,
                                                                     pressure_difference=delta_pV,
                                                                     mean_specific_volume=vm,
                                                                     inlet_altitude=z1,
                                                                     outlet_altitude=z2,
                                                                     )

            # _____TEMP-CORRECTION____
            delta_tII = 0
            t2I = t2
            # ___
            go_on_2 = True  # if broken out of innerloop, has to be reset again...
            while go_on_2:
                # todo: inside _calc_specific_heat_flux_buried replace a function
                fluid_conductivity = self._REFPROP_calc_conductivity(pressure_in_Pa=pm,
                                                                     temperature_in_C=tm)
                prandtl_number = self._calc_prandtlnumber(dynamic_viscosity=viscosity,
                                                          specific_heatcapacity=cp,
                                                          thermal_conductivity=fluid_conductivity)
                nusselt_number = self._calc_nusselt_number(reynolds_number=reynolds_number,
                                                           prandtl_number=prandtl_number,
                                                           segment_length=length,
                                                           )
                specific_heat_flux = self._calc_specific_heat_flux_buried(length=length,
                                                                          nusselt_number=nusselt_number,
                                                                          fluid_conductivity=fluid_conductivity)
                heat_flux = self._calc_heat_flux(mean_temperature=tm,
                                                 specific_heat_flux=specific_heat_flux,
                                                 heat_flux_iteration=self.heat_flux_iteration
                                                 )

                if t1 == self.t_environment:  # inlet temperature equals temperature of the environment
                    # obviously tiny effects happen.
                    delta_tI = self._calc_temperature_loss(inlet_temperature=t1, outlet_temperature=t2,
                                                           heat_flux=heat_flux, inlet_altitude=z1, outlet_altitude=z2,
                                                           delta_w_square=delta_w_square, massflow=m_dot, cp=cp)
                else:
                    max_heat_flux = m_dot * cp * (t1 - self.t_environment)
                    if abs(heat_flux) < abs(max_heat_flux):  # If Heatflux is bigger than max. possible Heatflux
                        delta_tI = self._calc_temperature_loss(inlet_temperature=t1, outlet_temperature=t2,
                                                               heat_flux=heat_flux, inlet_altitude=z1,
                                                               outlet_altitude=z2, delta_w_square=delta_w_square,
                                                               massflow=m_dot, cp=cp)
                    else:
                        t2 = self._guess_new_outlet_temperature(outlet_temperature=t2)
                        tm = self._guess_new_mean_temperature(inlet_temperature=t1, outlet_temperature=t2)
                        go_on_2 = False
                        continue
                        # --- RERUN_OUTER_LOOP---

                # ---- SET_NEW_OUTLET_TEMPERATURE ----
                if abs(delta_tI) < 0.1:  # criteria how accurate temperature has to be, the lower, the more iterations!
                    if abs(delta_pI) < 2.0:  # criteria how accurate pressure has to be, the lower, the more iterations!
                        go_on_1 = False
                        go_on_2 = False
                        continue
                        # ---END_OF_LOOP---
                    else:  # If delta_pI is bigger than 2.0, a new outlet pressure has to be set.
                        if delta_pII == 0:  # that's the case during the very first iteration. p2II isn't set either.
                            p2 = 0.95 * p2
                        else:  # Newton-Iteration(?)
                            p2 = p2II - delta_pII * (p2II - p2I) / (
                                    delta_pII - delta_pI)
                        p2II = p2I
                        delta_pII = delta_pI
                        p2I = p2

                        if p2 < 5 * 10 ** 5:  # practical limit: shouldn't ever be the case in Pipelines
                            logging.warning(f'Diameter too small! outlet_pressure reached {p2} bar(a)!')
                            go_on_1 = False
                            go_on_2 = False
                            continue
                            # ---END_OF_LOOP---
                        else:  # if the new outlet_pressure is valid the inner loop runs again.
                            go_on_2 = False
                            continue
                            # ---RERUN_INNER_LOOP---
                else:  # In case delta_tI is bigger than 0.1 a new outlet_temperature has to be set.
                    # ---Calculate new Outputtemperature
                    if delta_tII == 0:  # That's the case during the first iteration. t2II isn't set either.
                        t2 = 0.99 * t2
                        if t1 != self.t_environment:  # Very first iteration
                            t2 = t2 + 0.01 * self.t_environment
                    else:  # Newton Iteration(?)
                        t2 = t2II - delta_tII * ((t2II - t2I) / (delta_tII - delta_tI))

                t2II = t2I
                delta_tII = delta_tI
                t2I = t2
                tm = self._calc_mean_temperature(inlet_temperature_in_C=t1,
                                                 outlet_temperature_in_C=t2
                                                 )
                continue
                # ---RERUN_INNER_LOOP ---

        return p2, t2, m_dot, l, v1, v2, w1, w2

    def _REFPROP_set_gas_const(self):
        """ Calculates and returns the specific gas constant of the fluid

        Returns(float):
            specific Gasconstant [J/kgK]

        """
        molar_mass = self.fluid.molar_mass()  # molar mass in [kg/mol]  (should be SI units)
        gasconst = self.fluid.gas_constant()  # gas constant in [J/molK] (should be SI units)
        return gasconst / molar_mass  # [J/ kgK]

    def _REFPROP_set_cp(self, pressure_in_Pa, temperature_in_C):
        """ Calculates and returns the specific heat value of the fluid at a certain pressure and temperature

        Returns(float):
            specific heat capacity [J/kgK]
        """
        self.fluid.update(CoolProp.PT_INPUTS, pressure_in_Pa, uc.C2K(temperature_in_C))
        return self.fluid.cpmass()

    def _REFPROP_calc_viscosity(self, mean_pressure: float, mean_temperature: float):
        """ Updates the Fluid plus Calculates and returns the viscosity of the fluid at set pressure and temperature.

        Args:
            mean_pressure(float): mean Pressure in [Pa]
            mean_temperature(float): mean Temperature in [°C]

        Returns(float):
            Viscosity of the fluid in [kg/ms]
        Note:
            it does not have to be the mean temperature and pressure. It s a hint to clarify where the function is used.
        """
        self.fluid.update(CoolProp.PT_INPUTS, mean_pressure, uc.C2K(mean_temperature))
        viscosity = self.fluid.viscosity()
        return viscosity  # kg/(m*s)

    def _REFPROP_calc_specific_volume(self, temperature: float, pressure: float):
        """Calculate the specific volume (density**-1) with temperature and pressure

        Args:
            temperature(float): Temperature in [°C]
            pressure(float): Pressure in [Pa]

        Returns:
            specific_volume(float) in [m³/kg]

        """

        self.fluid.update(CoolProp.PT_INPUTS, pressure, uc.C2K(temperature))

        return 1 / self.fluid.rhomass()

    def _REFPROP_calc_conductivity(self, pressure_in_Pa, temperature_in_C):
        """
        todo:
            document this function
        Args:
            pressure_in_Pa:
            temperature_in_C:

        Returns:

        """
        self.fluid.update(CoolProp.PT_INPUTS, pressure_in_Pa, uc.C2K(temperature_in_C))
        return self.fluid.conductivity()

    def _calc_specific_heat_flux_buried(self, length, nusselt_number, fluid_conductivity):
        """
        todo:
            slightly more detailed (e.g. add density and heatcapacity of soil, etc.
            DIN EN ISO 6946:2018-03
            plausible value for alpha_air needed!
        Args:
            mean_temperature(float):
            length(float): Length of the pipeline segment [m]
            nusselt_number(float): the dimensionless nusselt number [-]
            fluid_conductivity: Conductivity of the fluid [W/(m*K)]
        Returns (float): Heat flux of a buried pipeline.

        """
        if self.heat_flux_iteration:
            numerator = length * np.pi

            _alpha_fluid = self._calc_heat_transfer_coefficient(nusselt_number=nusselt_number,
                                                                thermal_conductivity=fluid_conductivity
                                                                )
            ht_fluid2inner_surface = 1 / _alpha_fluid

            hc_pipeline = (1 / 2 * self.lambda_pipeline) * np.log10(self.outer_diameter / self.inner_diameter)

            if self.insulation_diameter != self.outer_diameter:  # Pipeline has an insulation
                hc_insulation = (1 / 2 * self.lambda_insulation) * np.log10(
                    self.insulation_diameter / self.outer_diameter)
            else:  # Non-insulated Pipeline
                hc_insulation = 0

            if self.imaginary_diameter != self.insulation_diameter:  # Pipeline is buried
                hc_soil = (1 / 2 * self.lambda_soil) * np.log10(self.imaginary_diameter / self.insulation_diameter)
                _alpha_air = 1000  # different alpha for buried pipeline (air on ground is "cooling" the soil)
            else:  # Pipline is above the ground
                hc_soil = 0
                _alpha_air = 1000  # air on insulation is "cooling" the pipeline)
            ht_soil2air = 1 / _alpha_air  # not implemented. just a guess so far. probably very wrong

            denominator = ht_fluid2inner_surface + 0.6 * hc_pipeline + hc_insulation + hc_soil
            return numerator / denominator
        else:
            return 0

    def _calc_heat_transfer_coefficient(self, nusselt_number: float, thermal_conductivity: float):
        """ Calculates the heat transfer coefficient of fluid within a pipeline based on the fluids flow properties (nusselt number), its thermal conductivity and the characteristic length (diameter of the Pipe in this case)

        Args:
            nusselt_number: Dimensionless number to describe the heat_flux between a fluid and surface from the
            point of view of the fluid (biot-number from surface) [-]
            thermal_conductivity: thermal conductivity of the fluid [W/(m*K)]

        Returns: Heat transfer coefficient alpha [W/(m²*K)]

        """
        return nusselt_number * thermal_conductivity / self.inner_diameter

    def _calc_heat_flux(self, mean_temperature, specific_heat_flux, heat_flux_iteration: bool):
        """Calculates the heatflux between fluid within the pipeline segmant and pipeline segment.

        Args:
            mean_temperature: Mean Temperature of a pipeline segment [°C]
            specific_heat_flux: The specific heat flux per Kelvin [W/(s*K)] (or something like that)
            heat_flux_iteration: bool value to iterate heatflux or not.

        Returns:

        """

        if heat_flux_iteration:
            return specific_heat_flux * (self.t_environment - mean_temperature)
        else:
            return 0

    def _calc_velocity(self, massflow, specific_volume):
        """ Calculates the velocity of the fluid based on the massflow, specific volume and area

        Args:
            massflow(float): Massflow in [kg/s]
            specific_volume(float): Specific Volume of the Fluid in [m³/kg]

        Returns:
            velocity(float): Flow Velocity of the Fluid in [m/s]
        """
        velocity = massflow * specific_volume / self.area  # [m/s] velocity of the fluid

        return velocity

    def _calc_friction_loss_coefficient(self, reynolds_number):
        """Calculate the Friction Factor based on reynolds_number and the roughness of the pipeline. Depending on the
        roughness of the inner surface of a pipe the pipe can be described as "hydraulically smooth", "hydraulic
        rough" or as "transitioning between hydraulic smooth and hydraulic rough". Depending on those 3
        classifications different empirical formulas are chosen to calculate the frictioin factor.
        Args:
            reynolds_number: dimensionless number to describe the turbulence of a flow (within a pipe in this case) [-]

        Returns: the friction loss coefficient [-] and its squared and inversed value

        """
        laminar_boundary = 2320
        transition_boundary = 10 ** 5
        turbulent_boundary = 10 ** 6
        if reynolds_number * self.roughness / (1000 * self.inner_diameter) < 65:  # Hydraulically smooth pipe
            if reynolds_number <= laminar_boundary:  # laminar flow in Hydraulic smooth pipe
                friction_loss_coefficient = 64 / reynolds_number

            elif reynolds_number > laminar_boundary and reynolds_number <= transition_boundary:
                # Hydraulic Smooth pipe with flow with neither laminar nor turbulent flow (transition)
                friction_loss_coefficient = 0.3164 * reynolds_number ** -0.25

            elif reynolds_number > transition_boundary and reynolds_number <= turbulent_boundary:
                # Hydraulic Smooth pipe with flow with neither laminar nor turbulent flow(transition)
                friction_loss_coefficient = 0.0032 + 0.221 * reynolds_number ** -0.237
            else:
                # Turbulent flow in hydraulic smooth pipe
                friction_loss_coefficient = 10
                _flc = 11
                while abs(friction_loss_coefficient - _flc) > 0.0001:
                    _flc = friction_loss_coefficient
                    friction_loss_coefficient = (1 / (2 * np.log10(reynolds_number * np.sqrt(_flc)) - 0.8)) ** 2

        elif reynolds_number * self.roughness / (1000 * self.inner_diameter) > 1300:  # Hydraulic rough pipe
            friction_loss_coefficient = 10
            _flc = 11
            while abs(friction_loss_coefficient - _flc) > 0.0001:
                _flc = friction_loss_coefficient
                friction_loss_coefficient = (1 / (
                        -2 * np.log10(self.roughness / (3.7065 * 1000 * self.inner_diameter)))) ** 2

        else:  # r*k/d >65 and r*k/d < 1300 == Transition between smooth and rough
            friction_loss_coefficient = 1
            _flc = 1.1
            while abs(friction_loss_coefficient - _flc) > 0.0001:
                _flc = friction_loss_coefficient
                friction_loss_coefficient = (1 / (-2 * np.log10((2.5226 / (reynolds_number * np.sqrt(_flc))) + (
                        self.roughness / (3.7065 * self.inner_diameter * 1000))))) ** 2

        flc = (friction_loss_coefficient ** 2) ** -1
        return flc, friction_loss_coefficient

    def _calc_KE(self, flc):
        """Calculates the K_E value which is a dimensionless factor to correct the average flow speed of a fluid
        within a pipeline based on its profile. The profile is e.g. parabolic if the flow is laminar (Re <2320) or a
        clinched parabola if the flow is turbulent(Re >2320)
        todo:
            Add source where this witchcraft comes from
        Args:
            flc: flc = 1/(friction_loss_coefficient)² [-]

        Returns:

        """
        KE = 0.25 * ((((1 / flc) + 2) ** 3) * (((1 / flc) + 1) ** 3)) / (((3 / flc) + 1) * ((3 / flc) + 2))
        return KE

    def _calc_mean_pressure(self, inlet_pressure_in_Pa, outlet_pressure_in_Pa):
        """Calculates the mean pressure of a pipeflow based on its pressures at the in- and outlet.

        Note:
            The unit of the pressures don't really matter as long as the variables have the same units!

        Args:
            inlet_pressure_in_Pa: Pressurelevel at the inlet of a pipeline segment in [Pa]
            outlet_pressure_in_Pa: Pressure level at the outlet of a pipelien segment in [Pa]

        Returns: mean pressure level of the pipeline segment in [Pa]
        """
        PI = self._calc_pressure_factor(inlet_pressure_in_Pa=inlet_pressure_in_Pa,
                                        outlet_pressure_in_Pa=outlet_pressure_in_Pa
                                        )  # [-]

        try:
            pm = inlet_pressure_in_Pa * (2 / 3) * ((1 - PI ** 3) / (
                    1 - PI ** 2))  # [Pa] The term on the the righthand side would cause a ZeroDivisionError.
        except ZeroDivisionError:
            pm = inlet_pressure_in_Pa  # [Pa]
        return pm

    def _calc_mean_specific_volume(self, inlet_pressure_in_Pa, outlet_pressure_in_Pa, inlet_specific_volume,
                                   outlet_specific_volume):
        """ Calculates the mean specific volume of the fluid within a pipeline segment.

        Note:
            The specific volume equals the inverse density of a fluid.

        Args:
            inlet_pressure_in_Pa: Inlet Pressure in [Pa]
            outlet_pressure_in_Pa: Outlet Pressure in [Pa]
            inlet_specific_volume: Specific Volume at the inlet in [m³/kg]
            outlet_specific_volume: Specific Volume at the outlet in [m³/kg]

        Returns: The specific mean volume of a fluid within a pipeline segment in [m³/kg]

        """
        PI = self._calc_pressure_factor(inlet_pressure_in_Pa=inlet_pressure_in_Pa,
                                        outlet_pressure_in_Pa=outlet_pressure_in_Pa
                                        )
        v1 = inlet_specific_volume
        v2 = outlet_specific_volume

        try:
            vm = sqrt(v1 * v2) * (log(PI)) / (sqrt(PI) - (1 / sqrt(
                PI)))  # [m³/kg] The term on the righthand side would cause a ZeroDivisionError:
        except ZeroDivisionError:
            vm = sqrt(v1 * v2)  # [m³/kg]
        return vm

    def _calc_pressure_factor(self, inlet_pressure_in_Pa, outlet_pressure_in_Pa):
        """Calculates the ratio between out- and inlet pressure

        Note:
            unit doesnt matter as long as it is the same unit

        Args:
            inlet_pressure_in_Pa: Inlet Pressure in [Pa]
            outlet_pressure_in_Pa: Outlet Pressure in [Pa]

        Returns: dimensionless pressure ratio in [-]

        """
        return outlet_pressure_in_Pa / inlet_pressure_in_Pa

    def _calc_mean_stagnation_pressure(self, inlet_velocity_in_ms, outlet_velocity_in_ms, inlet_specific_volume,
                                       outlet_specific_volume):
        """Calculates the stagnation pressure within a pipeline segment

        Args:
            inlet_velocity_in_ms: flow velocity of the fluid at the inlet of the pipeline segment in [m/s]
            outlet_velocity_in_ms: flow velocity of the fluid at the outlet of the pipeline segment in [m/s]
            inlet_specific_volume: specific volume of the fluid at the inlet of the pipeline in [m³/kg]
            outlet_specific_volume: specific volume of the fluid at the outlet of the pipeline in [m³/kg]

        Returns: Stagnation Pressure in [Pa]

        """
        return inlet_velocity_in_ms * outlet_velocity_in_ms / (
                inlet_specific_volume + outlet_specific_volume)  # mean stagnation Pressure (mittlerer Staudruck)

    def _calc_mean_temperature(self, inlet_temperature_in_C, outlet_temperature_in_C):
        """Function to calculate the next mean temperature based on inlet- and outlet temperature if the current mean_temperature is not accurate enough
        Note:
            Should work for Temperatures in [K] as well, as long as all Temperatures are in [K] (which is not the case because the environmental temperature is in [°C])
        Args:
            inlet_temperature_in_C: Temperature at the inlet of the Segment in [°C]
            outlet_temperature_in_C: Temperature at the outlet of the Segment in [°C]

        Returns: Mean-Temperature in [°C]

        """
        try:  # Error has to be cached if t2 equals t_environment, which means "t2==self.t_environment" is True already!
            _val = (inlet_temperature_in_C - self.t_environment) / (outlet_temperature_in_C - self.t_environment)
        except ZeroDivisionError:
            _val = -1

        if inlet_temperature_in_C == self.t_environment or outlet_temperature_in_C == self.t_environment or inlet_temperature_in_C == outlet_temperature_in_C or _val < 0:
            return (inlet_temperature_in_C + outlet_temperature_in_C) / 2
        else:
            return self._guess_new_mean_temperature(inlet_temperature=inlet_temperature_in_C,
                                                    outlet_temperature=outlet_temperature_in_C)

    def _calc_reynolds_number(self, m_dot, viscosity):
        """Calculates the Reynoldsnumber for cylindric pipes.

        Args:
            m_dot: Massflow in [kg/s]
            viscosity: dynamic Viscosity of the fluid in [kg/(m*s)]

        Returns: The dimensionless reynoldsnumber [-]

        """
        reynolds = 4 * m_dot / (self.inner_diameter * viscosity * np.pi)  # [kg/s] / ([m]*[m/(kg*s
        return reynolds

    def _calc_nusselt_number(self, reynolds_number: float, prandtl_number: float, segment_length: float):
        """Calculates the nusselt number based on the length of the pipeline segment, reynolds number and prandtl number
        todo:
            more research to do on heatflux from surface to fluid /fluid to surface
            more research to do on gas, liquid, dense phase...

        Note:
            The nusselt number is independent of the viscosity of the fluid, because beta = Re *Pr *l/L

        Args:
            reynolds_number: dimensionless number to describe the turbulence of the pipeflow (in this case)
            prandtl_number: dimensionless number to describe the relationship between viscosity and thermal conductivity of a fluid.
            segment_length: length of the pipeline_segment in [m]

        Returns:

        """
        _beta = reynolds_number * prandtl_number * segment_length * self.inner_diameter
        if reynolds_number <= 2320:  # laminare Strömung
            _nu = 49.371 + (1.615 * _beta ** (1 / 3) - 0.7) ** 3
            if self.inner_diameter * 100 <= segment_length:  # nicht ausgebildete laminare Strömung bei konstanter Wandtemperatur
                # todo: Faktor nochmal überprüfen
                return (_nu + (2 / (1 + 22 * prandtl_number)) * _beta ** 3) ** (1 / 3)
            else:  # voll ausgebildete laminare Strömung bei konstanter Wandtemperatur
                return _nu ** (1 / 3)
        else:  # turbulente Strömung unabh. von konst. Wandtemperatur oder konstanter Wärmestromdichte.
            # Keine unterscheidung zwischen vollständig und nicht vollst. ausgebildeten Strömungsprofil
            _zeta = (1.82 * np.log10(reynolds_number) - 1.62) ** -2
            numerator = (_zeta / 8) * (reynolds_number - 1000) * prandtl_number
            denumerator = 1 + 12.7 * (_zeta / 8) ** 0.5 * (prandtl_number ** (2 / 3) - 1)
            term = (1 + (self.inner_diameter / segment_length) ** (2 / 3))
            return term * (numerator / denumerator)

    def _calc_prandtlnumber(self, dynamic_viscosity: float, specific_heatcapacity: float, thermal_conductivity: float):
        """The Prandtl-Number describes the relationship betwen the viscosity and thermal conductivity of a fluid.

        Args:
            dynamic_viscosity: Dynamic Viscosity of a fluid in [kg/(m*s)]
            specific_heatcapacity: Heat capacity of a fluid in [J/(kg*K)] || [Ws/(kg*K)]
            thermal_conductivity: Thermal conductivity of a fluid in [W/(m*K)]

        Returns: dimensionless prandtl-number [-]

        """
        return dynamic_viscosity * specific_heatcapacity / thermal_conductivity  # [-] = [kg/(m*s)]*[J/(kg*K)]/[W/(m*K)]

    def _calc_kinetic_energy_correction(self, reynolds_number, flc):
        """instead of using the "average velocity of the fluid" the integration over the inner surface of a circle (
        as a function of the avg. velocity)is used. The difference between laminar and turbulent flow is also taken
        into account.

        todo:
            mathematical in-depth-theory behind this factor and the formula would be cool


        Args:
            reynolds_number: dimensionless number to describe the turbulence of a flow in [-]
            flc: flc = 1/(friction_loss_coefficient²) in [-]

        Returns:

        """
        if reynolds_number <= 2320:  # otherwise it is
            return 2  # the distribution of fluid velocities in the pipeline has a "perfect" parabolic curve. therefore KE = 2
        else:
            return self._calc_KE(flc)

    def _calc_pressure_drop(self, friction_loss_coefficient, segment_length, zeta, stagnation_pressure):
        """Calculates the pressure loss within a pipeline segment.

        Args:
            friction_loss_coefficient: friction based on roughness of the inner pipeline surface [-]
            segment_length: length of the pipeline segment in [m]
            zeta: Pressure losses based on bents, valves and other installations within the segment [-]
            stagnation_pressure: Stagnation Pressure (ger.: Staudruck) in [Pa]

        Returns: Pressure loss within the Pipeline Segement in [Pa]

        """
        return (friction_loss_coefficient * segment_length / self.inner_diameter + zeta) * stagnation_pressure

    def _calc_velocity_adjustment(self, KE, inlet_velocity, outlet_velocity):
        """Adjusts the squared velocity by the factor KE

        todo:
            describe KE again
        Args:
            KE:
            inlet_velocity: flow velocity at the inlet of a pipeline segment in [m/s]
            outlet_velocity: flow velocity at the outlet of a pipeline segment in [m/s]

        Returns: the corrected squared velocity in [m²/s²]

        """
        return (outlet_velocity ** 2 - inlet_velocity ** 2) * KE  # adjustment of the squared velocity-change

    def _calc_pressure_drop_from_energy_equation(self, delta_w_square,
                                                 inlet_pressure, outlet_pressure, pressure_difference,
                                                 mean_specific_volume,
                                                 inlet_altitude, outlet_altitude
                                                 ):
        """
        todo:
            document the function

        Args:
            delta_w_square:
            inlet_pressure:
            outlet_pressure:
            pressure_difference:
            mean_specific_volume:
            inlet_altitude:
            outlet_altitude:

        Returns:

        """
        p2star = inlet_pressure - delta_w_square / (
                2 * mean_specific_volume) - pressure_difference  # ___Pressure from Energy-Equation
        if inlet_altitude != outlet_altitude:
            p2star = p2star - (9.81 / mean_specific_volume) * (outlet_altitude - inlet_altitude)  # altitude differences
        delta_pI = p2star - outlet_pressure
        return delta_pI

    def _calc_temperature_loss(self, inlet_temperature, outlet_temperature, heat_flux,
                               inlet_altitude, outlet_altitude,
                               delta_w_square, massflow, cp):
        """
        todo:
            document the function
        Args:
            inlet_temperature:
            outlet_temperature:
            heat_flux:
            inlet_altitude:
            outlet_altitude:
            delta_w_square:
            massflow:
            cp:

        Returns:

        """
        t2star = inlet_temperature + heat_flux / (massflow * cp) - delta_w_square / (
                2 * cp)

        t2star = t2star - (9.81 / cp) * (outlet_altitude - inlet_altitude)  # altitude differences
        delta_tI = t2star - outlet_temperature
        return delta_tI

    def _guess_new_outlet_temperature(self, outlet_temperature):
        """Guesses a new Temperature at the outlet based on the current outlet temperature and the environmental
        temperature.

        Args:
            outlet_temperature: outlet temperature of a pipeline segment in [°C]

        Returns: a new outlet temperature of the pipelinesegment in [°C]

        """
        return (outlet_temperature + self.t_environment) * 0.5

    def _guess_new_mean_temperature(self, inlet_temperature, outlet_temperature):
        """Guesses a new mean temperature of a pipeline segment based on its in- and outlet temperature and the
        temperature of the environment values.

        Args:
            inlet_temperature: inlet temperature of a pipeline segment in [°C]
            outlet_temperature: outlet temperature of a pipeline segment in [°C]

        Returns: a new mean temperature of the pipeline segment in [°C]

        """
        _val = (inlet_temperature - self.t_environment) / (outlet_temperature - self.t_environment)
        if np.isneginf(_val):
            value = self.t_environment + (inlet_temperature - outlet_temperature) / (np.log10(_val))
        else:
            # todo: überprüfen ob das so richtig sein kann
            value = (inlet_temperature + self.t_environment) / 2

        return value


if __name__ == '__main__':
    # sleipner: diameter = 0.509
    # rotterdamm: diameter = 0.4636
    # sleipner: Outer_dia = 0.559
    # rotterdamm: Outer_dia = 0.5096
    ppln = Pipeline.init_blank(m_dot=168.08,
                               inlet_pressure_in_Pa=181 * 10 ** 5,
                               inlet_temperature_in_C=50,
                               fluid='CO2',
                               save_file=True
                               )
    ppln.load_dimensional_data(inner_diameter_in_m=0.4636,
                               roughness_in_mm=0.0417
                               )
    ppln.init_parameters_buried_pipeline(outer_diameter=0.5096,
                                         insulation_thickness=0.0,
                                         depht=(2 / 2) - 0.5096
                                         )

    ppln.load_geo_data(sheet_name='Jaenschwalde-Rotterdamm')

    ppln.save_path = "../../../use_cases/21_Bad_Lauchstaedt/doc/Pipeline_output.xlsx"

    cProfile.run("ppln.pipeline()", sort='cumtime')
