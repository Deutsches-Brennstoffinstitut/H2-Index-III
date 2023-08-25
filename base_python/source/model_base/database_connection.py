import logging
import os
import sqlite3

from base_python.source.basic import ModelSettings
from base_python.source.basic.Quantities import PhysicalQuantity, EconomicalQuantities, get_unit_of_quantity
from base_python.source.basic.Streamtypes import StreamMass, StreamEnergy
import sqlite3 as sql  # installed as pysqlite3
import mysql.connector


class Mixin:
    def __init__(self):
        self.database_connection = None
        self.database_cursor = None

    @staticmethod
    def _server_connection(database_name: str):
        """
        Contains the main information to connect the model to the database
        returns connector object for alter access to content
        """
        config = {
            'host': '',
            'user': '',
            'password': '',
            'database': database_name
        }
        try:
            c = mysql.connector.connect(**config)
            return c
        except:
            raise ConnectionError(f'No Connection to Database "{database_name}" possible. Check if VPN is enabled or'
                                  f'if the name is correct.')

    @staticmethod
    def _local_connection(database_name: str):
        path_str = f'data/{database_name}.sqlite'
        path = os.path.abspath(path_str)

        while True:
            try:
                c = sql.connect(path)
                break
            except sqlite3.OperationalError:
                pass
            finally:
                path_str = '../' + path_str
                path_old = path
                path = os.path.abspath(path_str)

            if path == path_old:
                raise ConnectionError(f'No Connection to local Database "{database_name}" possible. Check if '
                                      f'name or location (data\\{database_name}.sqlite) is correct.')

        return c

    def connect_to_server_database(self, database_name: str):
        """
        Connects the model with the MySQL database and raises an error if the connection was not successfull
        Returns:
        """
        self.database_connection = self._server_connection(database_name)
        self.database_cursor = self.database_connection.cursor()

    def connect_to_local_database(self, database_name: str):
        """
        Connects the model to a local sqlite database file and raises an error if the connection was not successfull
        Returns:
        """
        self.database_connection = self._local_connection(database_name)
        self.database_cursor = self.database_connection.cursor()

    def load_basic_database(self):
        """
        Loads the basic information from the database, which contain stream types, stream properties

        """
        # GET STREAMS FROM DATABASE
        # TODO: Wie gehen wir mit der Variable stream_types um, die übergreifend von allen Modulen erreichbar sein muss
        if self.database_cursor is not None:
            ModelSettings.stream_types = {}

            attributes = ['*']
            table = 'STREAM_TYPES'
            self.database_cursor.execute("SELECT " + ", ".join(attributes) +
                                         " FROM " + table)
            result = self.database_cursor.fetchall()
            field_names = [i[0] for i in self.database_cursor.description]
            for single_result in result:

                ModelSettings.stream_types[StreamMass[single_result[0]]] = {}
                ModelSettings.stream_types[StreamMass[single_result[0]]][PhysicalQuantity.mass_fraction] = {}
                for index, mass_fraction in enumerate(single_result):
                    if index > 0:
                        if mass_fraction is not None:
                            ModelSettings.stream_types[StreamMass[single_result[0]]][PhysicalQuantity.
                            mass_fraction][StreamMass[field_names[index]]] = mass_fraction

            # GET STREAM PROPERTIES
            attributes = ['*']
            table = 'STREAM_PROPERTIES'
            self.database_cursor.execute("SELECT " + ", ".join(attributes) +
                                         " FROM " + table)
            result = self.database_cursor.fetchall()
            field_names = [i[0] for i in self.database_cursor.description]
            for single_result in result:
                for index, value in enumerate(single_result):
                    if index > 0:
                        if StreamMass[single_result[0]] in ModelSettings.stream_types:
                            if 'unit' in field_names[index].casefold():
                                if value is not None:
                                    field_name = field_names[index][5:].casefold()
                                    unit_preferred = get_unit_of_quantity(PhysicalQuantity[field_name])
                                    unit_given = value
                                    if not unit_given == unit_preferred.value:
                                        logging.critical(f'Unit {unit_given} of value {str(field_names[index][5:])} '
                                                         f'does not match the preferred unit of {unit_preferred}')
                            else:
                                ModelSettings.stream_types[StreamMass[single_result[0]]][PhysicalQuantity[
                                    field_names[index].casefold()]] = value
                        else:
                            logging.warning(f'Property of stream {StreamMass[single_result[0]]} given but no fractions.'
                                            f'\nCheck Database!')
                            ModelSettings.stream_types[StreamMass[single_result[0]]] = {}

    def load_database(self):
        """
        Loads the values for the connected components from the database

        """
        # GET COMPONENT KPI
        if self.database_cursor is not None:
            for component in self.components.values():
                component.load_database(self.database_cursor)
            self.close_database_connection()

    def close_database_connection(self):
        """
        Closes the database connection and disconnects database and model

        """
        if self.database_cursor is not None:
            self.database_cursor.close()
            self.database_connection.close()
