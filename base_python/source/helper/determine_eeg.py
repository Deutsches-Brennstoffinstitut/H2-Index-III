def get_eeg_costs(model):
    for comp in model.self_energy_components['Excluded Consumers']:
        consumer_ports = model.components[comp].get_ports_by_type(StreamEnergy.ELECTRIC)
        if len(consumer_ports) > 1:
            logging.critical(
                'Self energy component {} has more than one port. Could not define specific port'.format(comp))
        else:
            consumer_port = consumer_ports[0]
            if self_energy_streams == []:
                self_energy_streams = array(consumer_port.get_stream_history())
            else:
                self_energy_streams -= abs(array(consumer_port.get_stream_history()))
