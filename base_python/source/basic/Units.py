from strenum import StrEnum
import logging

"""
This file contains the units which are used for internal calculations of the model.
The Linke between Quantities and Units are performed in the Quantities.py"""


class Unit(StrEnum):
    kg = 'kg'
    kW = 'kW'
    m = 'm'
    m_cubic = 'm³'
    norm_cubic_meters = 'Nm³'
    kWh = 'kWh'
    K = 'K'
    Pa = 'Pa'
    kWh_per_kg = 'kWh/kg'
    g_per_mol = 'g/mol'
    kg_per_cubic_meter = 'kg/m³'
    kg_per_norm_cubic_meter = 'kg/m³'
    dimensionless = ''

    euro_per_year = '€/a'
    euro_per_kW = '€/kW'
    euro_per_kg = '€/kg'
    euro_per_kWh = '€/kWh'
    euro_per_norm_cubic_meter = '€/Nm³'
