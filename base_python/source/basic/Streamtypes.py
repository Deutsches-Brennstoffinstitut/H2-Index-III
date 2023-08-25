from strenum import StrEnum
from enum import Enum, auto
from itertools import chain
from base_python.source.basic.Units import Unit


class StreamDirection(Enum):
    stream_into_component = -1
    stream_out_of_component = 1
    stream_bidirectional = 0


class StreamTypes(Enum):
    power = auto()
    energy = auto()
    mass = auto()


class StreamMass(StrEnum):
    HYDROGEN = 'HYDROGEN'
    WATER = 'WATER'
    OXYGEN = 'OXYGEN'
    NITROGEN = 'NITROGEN'
    CO2 = 'CO2'
    METHANE = 'METHANE'
    ETHANE = 'ETHANE'
    PROPANE = 'PROPANE'
    BUTANE = 'BUTANE'
    PENTANE = 'PENTANE'
    HEXANE = 'HEXANE'

    # TODO: Mixturen evtl extra in eine Klasse, wird aber mit dem Suchen danach dadurch schwieriger
    AIR = 'AIR'
    METHANE_10 = 'METHANE_10'
    MIX_GAS = 'MIX_GAS'
    NG_RUSSIA_H = 'NG_RUSSIA_H'


class StreamEnergy(StrEnum):
    ELECTRIC = 'ELECTRIC'
    HEAT = 'HEAT'


stream_units = {
    StreamEnergy.ELECTRIC: Unit.kW,
    StreamEnergy.HEAT: Unit.kW,
    StreamMass.HYDROGEN: Unit.kg,
    StreamMass.WATER: Unit.kg,
    StreamMass.OXYGEN: Unit.kg,
    StreamMass.CO2: Unit.kg
}

stream_types = {
    StreamEnergy.ELECTRIC: StreamTypes.power,
    StreamEnergy.HEAT: StreamTypes.power,
    StreamMass.HYDROGEN: StreamTypes.mass,
    StreamMass.WATER: StreamTypes.mass,
    StreamMass.OXYGEN: StreamTypes.mass,
    StreamMass.CO2: StreamTypes.mass}


def get_stream_unit(port_type):
    return stream_units.get(port_type)


def get_stream_type(port_type):
    return stream_types.get(port_type)
