from enum import Enum, auto
from strenum import StrEnum
from base_python.source.basic.Units import Unit
import logging

"""
This file is used to implement different Quantities in the model each of the quantity
has a preferred unit which can be get by using get_unit_of_quantity
The Units are set in Units.py
"""


class EconomicalQuantities(Enum):
    price_dev_factor = auto()
    media_costs = auto()


class PhysicalQuantity(StrEnum):
    stream = 'stream'
    mass_stream = 'mass_stream'
    power_stream = 'power_stream'
    pressure = 'pressure'
    temperature = 'temperature'
    mass_fraction = 'mass_fraction'
    higher_heating_value = 'higher_heating_value'
    lower_heating_value = 'lower_heating_value'
    molar_mass = 'molar_mass'
    norm_density = 'norm_density'


economical_quantity_units = {
    EconomicalQuantities.media_costs: (Unit.euro_per_kg, Unit.euro_per_kWh, Unit.euro_per_norm_cubic_meter)
}

physical_quantity_units = {
    PhysicalQuantity.pressure: Unit.Pa,
    PhysicalQuantity.temperature: Unit.K,
    # Todo: Massenstrom wird mit welcher einheit belegt?
    PhysicalQuantity.mass_stream: Unit.kg,
    PhysicalQuantity.power_stream: Unit.kW,
    PhysicalQuantity.higher_heating_value: Unit.kWh_per_kg,
    PhysicalQuantity.lower_heating_value: Unit.kWh_per_kg,
    PhysicalQuantity.molar_mass: Unit.g_per_mol,
    PhysicalQuantity.norm_density: Unit.kg_per_norm_cubic_meter
}


def get_unit_of_quantity(quantity):
    if quantity in physical_quantity_units:
        unit = physical_quantity_units.get(quantity)
    elif quantity in economical_quantity_units:
        unit = economical_quantity_units.get(quantity)
    else:
        unit = None
        logging.warning(f'Could not get unit for quantity {quantity}')
    return unit
