################################################
# Test 1 - Basic_Production_H2                 #
################################################

from base_python.source.model_base.ModelBase import *

class Model_A(ModelBase):

    def __init__(self, database_name='dbi_mat', db_location='local', logging_level: LoggingLevels = LoggingLevels.CRITICAL):
        # init
        super().__init__(database_name, db_location, logging_level)
        self.modeldir = inspect.getfile(self.__class__)

        self.basic_technical_settings = BasicTechnicalSettings(time_resolution=60,
                                                               absolute_model_error=1e-10)

        self.basic_economical_settings = BasicEconomicalSettings(reference_year=2023,
                                                                 start_year=2023,
                                                                 end_year=2030,
                                                                 basic_interest_rate=0.03,
                                                                 estimated_inflation_rate=0
                                                                 )
        # --------------------------
        # --- declare components ---
        # --------------------------
        # insert your code here
        """ description of objects
            name = "any unique text string you like"
            components[name]  = model class     - create instance of class member
            connections[name] = [ a list of tuples of connection, where each tuple consists of a pair of tuples  ]
                                [ ((source definition), (target definition)) ]
                                [ ((name, 'electric'), ('mySource1', 'electric')), ((name, 'H2'), ('mySource2', 'special H2')) ]

            # automatic processing #
            names.append(name)                   - insert object into the list of known objects
            ports[name] = {'electric':0, 'H2':0} - transcript the components ports to the model
        """

        name = 'RE_Wind'
        self.components[name] = Source(stream_type=StreamEnergy.ELECTRIC, size=10,
                                       technology=Source.Technology.WIND_ONSHORE, active=True,
                                       new_investment=True,
                                       economical_parameters=EconomicalParameters(
                                           use_database_values=True)
                                       )
        name = 'RE_PV'
        self.components[name] = Source(stream_type=StreamEnergy.ELECTRIC, size=10,
                                       technology=Source.Technology.PV_OPEN_AREA, active=True,
                                       new_investment=True,
                                       economical_parameters=EconomicalParameters(
                                           use_database_values=True)
                                       )

        name = "dump_electric"
        self.components[name] = Consumer(stream_type=StreamEnergy.ELECTRIC)

        name = 'Ely'
        self.components[name] = Electrolyser(size=100,
                                             technology=Electrolyser.Technology.PEM,
                                             new_investment=True,
                                             economical_parameters=EconomicalParameters(
                                                 use_database_values=True)
                                             )

        name = 'Consumer_H2'
        self.components[name] = Consumer(stream_type=StreamMass.HYDROGEN)

        name = 'Grid_H2'
        self.components[name] = Grid(stream_type=StreamMass.HYDROGEN)

        branch_name = 'El'
        self.add_branch(branch_name,
                        branch_type=StreamEnergy.ELECTRIC,
                        port_connections=[('RE_Wind', StreamDirection.stream_out_of_component),
                                          ('RE_PV', StreamDirection.stream_out_of_component),
                                          ('Ely', StreamDirection.stream_into_component),
                                          ('dump_electric', StreamDirection.stream_into_component),
                                          ]
                        )

        branch_name = 'H2'
        self.add_branch(branch_name,
                        branch_type=StreamMass.HYDROGEN,
                        port_connections=[('Ely', StreamDirection.stream_out_of_component),
                                          ('Consumer_H2', StreamDirection.stream_into_component),
                                          ('Grid_H2', StreamDirection.stream_bidirectional)
                                          ]
                        )

        self.loop_control_rules.update({'El': ['RE_Wind', 'RE_PV', 'Ely', "dump_electric"],
                                        'H2': ['Consumer_H2', 'Ely']
                                        })

        self.set_time_resolution(60)
        # self.add_stream_profile_to_port(component_name='RE_Wind',
        #                                 port_stream_type=StreamEnergy.ELECTRIC,
        #                                 port_stream_direction=StreamDirection.stream_out_of_component,
        #                                 profile=[10] * 8760)
        self.profile_len = 8760
        # define operation rules

        # --- do automated declaration processing ---
        self.init_structure()  # init names, ports, branches


def run_local(logging_level: LoggingLevels):
    my_system_model = Model_A(database_name='dbi_mat', db_location='local', logging_level=logging_level)


    ## not enough power for Electrolyzer:
    my_system_model.add_stream_profile_to_port(component_name="Consumer_H2",
                                               port_stream_type=StreamMass.HYDROGEN,
                                               port_stream_direction=StreamDirection.stream_into_component,
                                               profile=[-1000] * 8760)

    my_system_model.add_stream_profile_to_port(component_name='RE_Wind',
                                    port_stream_type=StreamEnergy.ELECTRIC,
                                    port_stream_direction=StreamDirection.stream_out_of_component,
                                    profile=[1] * 8760)

    my_system_model.components['RE_PV'].new_investment = True
    my_system_model.components['RE_Wind'].new_investment = True


    my_system_model.components['Ely'].set_size(size=20)
    my_system_model.run()
    my_system_model.calculate_costs()
    model1_results = my_system_model.create_results()

    df_basic_econ        = model1_results.basic_econ_system_settings.to_dataframe()
    df_basic_tech        = model1_results.basic_technical_settings.to_dataframe()
    df_branch_info       = model1_results.branch_information.to_dataframe()
    df_status_report     = model1_results.component_technical_results[0].to_dataframe()
    df_port_profiles     = model1_results.port_results[0].to_dataframe()

    # this = pd.DataFrame(df_port_profiles.values,
    #              index=df_port_profiles.index.droplevel(0),
    #              columns=df_port_profiles.columns)

    df_econ_main         = model1_results.component_economic_results[0].to_dataframe()
    df_econ_CAPEX        = model1_results.component_economic_results[0].to_dataframe_ElementCAPEX()
    df_econ_fixedOPEX    = model1_results.component_economic_results[0].to_dataframe_ElementfixedOPEX()
    df_econ_variableOPEX = model1_results.component_economic_results[0].to_dataframe_ElementvariableOPEX()

    my_system_model.components['RE_PV'].new_investment = False
    my_system_model.components['RE_Wind'].new_investment = False
    my_system_model.run()
    my_system_model.calculate_costs()
    model1_results = my_system_model.create_results()
    df_econ_CAPEX        = model1_results.component_economic_results[0].to_dataframe_ElementCAPEX()


    print('Done')


if __name__ == '__main__':
    run_local(LoggingLevels.CRITICAL)