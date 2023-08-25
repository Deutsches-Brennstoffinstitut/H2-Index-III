################################################
# Test B - Basic_Consumption_H2                #
################################################

from base_python.source.model_base.ModelBase import *


class Model_B(ModelBase):

    def __init__(self, database_name='dbi_mat', db_location='local',
                 logging_level: LoggingLevels = LoggingLevels.CRITICAL):
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
            ports[name] = {'electric':0, 'H2':0} - transcript the copmonents ports to the model
        """

        name = 'Grid'
        self.components[name] = Grid(stream_type=StreamEnergy.ELECTRIC,
                                     new_investment=False)

        name = 'Ely'
        self.components[name] = Electrolyser(size=150,
                                             technology=Electrolyser.Technology.ALKALY,
                                             active=True,
                                             new_investment=True,
                                             economical_parameters=EconomicalParameters(
                                                 use_database_values=True)
                                             )
        # --> will get some binary profile later

        name = 'Storage_H2'
        self.components[name] = Storage_Gas(size=550000,
                                            technology=Storage_Gas.Technology.TANK_U100BAR,
                                            stream_type=StreamMass.HYDROGEN,
                                            initial_value=0,
                                            new_investment=True,
                                            economical_parameters=EconomicalParameters(
                                            use_database_values=True)
                                           )

        # HYDROGEN Dump:
        name = "Grid_H2"
        self.components[name] = Grid(stream_type=StreamMass.HYDROGEN)

        name = 'Consumer_H2'
        self.components[name] = Consumer(stream_type=StreamMass.HYDROGEN,
                                         size=100,
                                         active=True)

        self.add_branch(branch_name='El', branch_type=StreamEnergy.ELECTRIC,
                        port_connections=[
                            ('Grid', StreamDirection.stream_bidirectional),
                            ('Ely', StreamDirection.stream_into_component)])

        self.add_branch(branch_name='H2', branch_type=StreamMass.HYDROGEN,
                        port_connections=[
                            ('Ely', StreamDirection.stream_out_of_component),
                            ('Consumer_H2', StreamDirection.stream_into_component),
                            ('Storage_H2', StreamDirection.stream_out_of_component),
                            ('Storage_H2', StreamDirection.stream_into_component),
                            ('Grid_H2', StreamDirection.stream_bidirectional),
                            ])

        self.set_time_resolution(60)
        # define operation rules
        self.passive_priorityRules.extend(['Ely', 'dump_electric'])
        self.passive_priorityRules.extend(['Consumer_H2', 'Ely', 'Storage_H2', 'Grid_H2'])

        # --- do automated declaration processing ---
        self.init_structure()  # init names, ports, branches

    def report(self):
        for name in list(self.components.keys()):
            logging.info('ports of ' + name + ': {}'.format(self.ports[name]))


def run_local(logging_level: LoggingLevels):
    my_system_model = Model_B(database_name='dbi_mat', db_location='local', logging_level=logging_level)
    my_system_model.run()
    my_system_model.calculate_costs()
    model1_results = my_system_model.create_results()

    df_basic_econ = model1_results.basic_econ_system_settings.to_dataframe()
    df_basic_tech = model1_results.basic_technical_settings.to_dataframe()
    df_branch_info = model1_results.branch_information.to_dataframe()
    df_status_report = model1_results.component_technical_results[0].to_dataframe()
    df_port_profiles = model1_results.port_results[0].to_dataframe()
    df_econ_main = model1_results.component_economic_results[0].to_dataframe()
    df_econ_CAPEX = model1_results.component_economic_results[0].to_dataframe_ElementCAPEX()
    df_econ_fixedOPEX = model1_results.component_economic_results[0].to_dataframe_ElementfixedOPEX()
    df_econ_variableOPEX = model1_results.component_economic_results[0].to_dataframe_ElementvariableOPEX()
    print('done')


if __name__ == '__main__':
    run_local(LoggingLevels.CRITICAL)
