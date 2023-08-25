import random
import cProfile
from ctREFPROP.ctREFPROP import REFPROPFunctionLibrary
import CoolProp.CoolProp as CoolProp
from CoolProp import AbstractState
from base_python.source.basic import Database
import logging
from functools import lru_cache


def create_fluid(mass_fraction, temperature=None, pressure=None):
    """
    Creates the Refprop fluid using the saved properties in the stream

    """
    components_string = ""
    components = [component.name for component in mass_fraction.keys()]
    fractions = []
    if mass_fraction is not {}:
        components_string = '&'.join(components)
        fractions = list(mass_fraction.values())
    else:
        logging.warning('No mass fraction given for Fluid')
    my_abstract_state = AbstractState("REFPROP", components_string)
    my_abstract_state.set_mass_fractions(
        fractions)  # note: mass fractions can be set after creation with: my_abstract_state.set_mass_fractions(fractions)
    if temperature != None and pressure != None:
        update_fluid(my_abstract_state, temperature, pressure, mass_fraction)
    return my_abstract_state


def update_fluid(fluid, temperature=None, pressure=None, mass_fraction=None):
    """
    Updates the ports properties when fraction, temperature or pressure changed

    """

    if (mass_fraction != {}):
        fluid.set_mass_fractions(list(mass_fraction.values()))

    if (temperature != None) and (pressure != None):
        fluid.update(CoolProp.PT_INPUTS, pressure, temperature)


def get_specific_gas_constant(fluid):
    return Database.general_gas_constant / fluid.molar_mass()
