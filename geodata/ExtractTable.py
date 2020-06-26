"""
ExtractTable
============

Provides
    - A python class for extracting subtables from given tabular data. 
      Can manage filetypes .csv, .xlsx, .geojson, .shp, etc.
    - A command-line script that can be used to
        1. convert input filetype to output filetype (ex. .shp -> .csv);
        2. output tabular data reindexed with a specified column label
        3. output subtables from input tabular data

Metadata
--------
filename:       ExtractTable.py
author:         @KeiferC
date:           26 June 2020
version:        0.0.1
description:    Script and module to extract subtables from given tabular data
dependencies:   geopandas
                numpy

Documentation
-------------
Documentation for the ExtractTable module can be found as docstrings. 
Run `import ExtractTable; help(ExtractTable)` to view documentation.

Usage
-----
usage: ExtractTable.py [-h] [-o OUTFILE] [-c COLUMN] [-v VALUE [VALUE ...]]
                       INFILE

Script to extract tabular data. 

If no outfile is specified, outputs plaintext to stdout.
If no column is specified, outputs filetype converted input. 
If no value is specified, outputs table indexed with given column (required).
If value and column are specified, outputs subtable indexed with given column
and containing only rows equal to given value(s).

supported input filetypes:
    .csv .geojson .shp .xlsx .zip

supported output filetypes:
    .bz2 .csv .geojson .gpkg .gzip .html .json .md .pkl .tex .xlsx .zip 
    all other extensions will contain output in plaintext

positional arguments:
  INFILE                name/path of input file of tabular data to read

optional arguments:
  -h, --help            show this help message and exit
  -o OUTFILE, --output OUTFILE
                        name/path of output file for writing
  -c COLUMN, --column COLUMN
                        label of column to use as index for extracted table
  -v VALUE [VALUE ...], --value VALUE [VALUE ...]
                        value(s) of specified column in rows to extract

examples:
    
    python ExtractTable.py input.xlsx -c ID > output.csv; ls
    python ExtractTable.py foo.csv -o bar.csv -c "state fips" -v 01
    python ExtractTable.py input.csv -o ../output.csv -c Name -v "Rick Astley"
    python ExtractTable.py in.csv -o out.csv -c NUM -v 0 1 2 3

"""
import argparse
import geopandas as gpd
import numpy as np
import os.path
import pandas as pd
import pathlib
import sys
import zipfile

from typing import List, NoReturn, Optional, Tuple, Union
import warnings; warnings.filterwarnings(
    'ignore', 'GeoSeries.isna', UserWarning)



#########################################
#                                       #
#       Class Definition                #
#                                       #
#########################################

class ExtractTable:
    """
    For extracting tabular data. Run `help(ExtractTable)` to view docs.

    Specifying `column` uses given column as output's index. Specifying 
    `value` isolates output to rows that contain values in specified column.
    Specifying `outfile` determines the filetype of the output table. 

    Attributes
    ----------
    infile : str
        Name/path of input file of tabular data to read
    outfile : pathlib.Path
        Path of output file for writing
    column : str
        Label of column to use as index for extracted table
    value : str | List[str]
        Value(s) of specified column in rows to extract

    Class Methods
    -------------
    __init__(Optional[str], Optional[str], Optional[str], 
             Optional[Union[str, List[str]]) -> ExtractTable
        `ExtractTable initializer
    read_file(str, Optional[str], Optional[Union[str, List[str]]])
            -> ExtractTable
        Returns an ExtractTable instance with a specified input filename
    
    Public Instance Methods
    -----------------------
    extract() -> gpd.GeoDataFrame
        TODO
    extract_to_file(Optional[str]) -> NoReturn
        TODO
    list_columns() -> np.ndarray
        TODO
    list_values(Optional[str], bool) -> 
            Union[np.ndarray, gpd.array.GeometryArray]
        TODO

    """

    #===========================================+
    # Constructors                              |
    #===========================================+

    def __init__(self, infile:  Optional[str] = None, 
                 outfile:       Optional[str] = None, 
                 column:        Optional[str] = None, 
                 value:         Optional[Union[str, List[str]]] = None):
        """
        ExtractTable initializer.

        Parameters
        ----------
        infile : str | None, optional
            Name/path of input file of tabular data to read
        outfile: str | None, optional
            Name/path of output file for writing
        column: str | None, optional
            Label of column to use as index for extracted table
        value: str | List[str] | None, optional
            Value(s) of specified column in rows to extract
        
        Returns
        -------
        ExtractTable

        See Also
        --------
        read_file(str, Optional[str], Optional[Union[str, List[str]]]) 
                -> ExtractTable

        Examples
        --------
        >>> et1 = ExtractTable()
        >>> et2 = ExtractTable('example/input.shp')
        >>> et3 = ExtractTable('example/file.csv', column='ID')
        >>> et4 = ExtractTable('input.xlsx', 'output.md')
        >>> et5 = ExtractTable('in.csv', 'out.tex', 'ID', '01')
        >>> et6 = ExtractTable('in.csv', column='ID', value=['01', '03'])
        >>> et7 = ExtractTable('in.shp', outfile='out', column='X', value='y')

        """
        # Encapsulated attributes
        self.__infile =     None
        self.__outfile =    None
        self.__column =     None
        self.__value =      None

        # Protected attributes
        self.__table =      None
        self.__coldata =    None
        self.__foundval =   False
        self.__extracted =  None

        self.__sanitize_init(infile, outfile, column, value)


    @classmethod
    def read_file(self, filename: str, 
                  column:         Optional[str] = None, 
                  value:          Optional[Union[str, List[str]]] = None):
        """
        Returns an ExtractTable instance with a specified input filename.

        Parameters
        ----------
        filename : str
            Name/path of input file of tabular data to read
        column : str | None, optional
            Label of column to use as index for extracted table
        value : str | List[str] | None, optional
            Value(s) of specified column in rows to extract

        Returns
        -------
        ExtractTable

        Examples
        --------
        >>> et1 = ExtractTable.read_file('example/input.shp')
        >>> et2 = ExtractTable.read_file('example/file.csv', column='ID')
        >>> et3 = ExtractTable.read_file('in.shp', column='foo', value='bar')
        >>> et4 = ExtractTable.read_file('in.csv', column='X', value=['1','3'])

        """
        return self(filename, None, column, value)
    

    def __sanitize_init(self, infile:   Optional[str], 
                        outfile:        Optional[str], 
                        column:         Optional[str], 
                        value:          Optional[Union[str, List[str]]]):
        """
        Safely initializes attributes using setters.

        Parameters
        ----------
        infile : str | None, optional
            Name/path of input file of tabular data to read
        outfile: str | None, optional
            Name/path of output file for writing
        column: str | None, optional
            Label of column to use as index for extracted table
        value: str | List[str] | None, optional
            Value(s) of specified column in rows to extract
        
        Raises
        ------
        AttributeError
            Raised if setter throws an error

        """
        try:
            self.infile = infile
            self.outfile = outfile
            self.column = column
            self.value = value

        except Exception as e:
            raise AttributeError("Initialization failed. {}".format(e))


    #===========================================+
    # Public Instance Methods                   |
    #===========================================+

    def extract(self) -> gpd.GeoDataFrame:
        '''
        Returns a GeoPandas GeoDataFrame containing extracted subtable.

        Returns
        -------
        GeoDataFrame
        
        '''
        if self.__table is None:
            raise RuntimeError("Unable to find tabular data to extract")
        elif self.column:
            return self.__reindex()
        else:
            return self.__table
            

    def extract_to_file(self, driver: Optional[str] = None) -> NoReturn:
        '''
        Writes the tabular extracted data to a file. Given an optional Fiona 
        support OGR driver, writes to file using the driver. If outfile 
        is None, data is printed as plaintext to stdout

        Parameters
        ----------
        driver: str | None
            Name of Fiona supported OGR drivers
        '''

        # TODO: test
        filename = self.outfile
        gdf = self.extract()
        is_geo = self.__has_spatial_data(gdf) # TODO: finish

        if not filename:
            if is_geo:
                gdf.to_string(buf=sys.stdout)
            else:
                pd.DataFrame(gdf).to_string(buf=sys.stdout)

        else:
            ext = self.__get_extension(filename)

            if is_geo and ext == '.shp':
                gdf.to_file(filename)
            elif is_geo and ext == '.geojson':
                gdf.to_file(filename, driver='GeoJSON')
            elif is_geo and ext == '.gpkg':
                gdf.to_file(filename, driver='GPKG')
            elif is_geo and driver:
                gdf.to_file(filename, driver=driver)
            elif is_geo:
                self.__extract_to_inferred_file(gdf, filename, ext)
            else:
                self.__extract_to_inferred_file(pd.DataFrame(gdf), 
                                                filename, ext)


    def list_columns(self) -> np.ndarray:
        '''
        Returns a list of all columns in the initialized source table

        Returns
        -------
        np.ndarray
        '''
        if self.__table is None:
            raise RuntimeError("Unable to find tabular data to extract")
        else:
            return self.__table.columns.values


    def list_values(self, 
                    column: Optional[str] = None,
                    unique: bool = False) -> \
            Union[np.ndarray, gpd.array.GeometryArray]:
        """
        Returns a list of values in the initialized column (default).
        Returns a list of values in the given column (if specified).
        Returns a list of unique values (if specified)

        Parameters
        ----------
        column : str | NoneType
            Name of the column whose values are to be listed. If None,
            lists the values of the initialized column. Defaults to None
        unique : bool, optional
            If True, function lists only unique values. Defaults to False

        Returns
        -------
        np.ndarray | gpd.array.GeometryArray

        Raises
        ------
        KeyError
            TODO
        RuntimeError
            TODO
        RuntimeError
            TODO

        """
        if self.__table is None:
            raise RuntimeError("Unable to find tabular data to extract")

        elif column: 
            try:
                if unique:
                    return self.__table[column].unique()
                else:
                    return self.__table[column].values
            except:
                raise KeyError("Unable to find column '{}'".format(column))

        elif not self.column:
            raise RuntimeError("No default column exists")

        else:
            if unique:
                return self.__table[self.column].unique()
            else:
                return self.__table[self.column].values
            

    #===========================================+
    # Private Helper Methods                    |
    #===========================================+

    def __reindex(self) -> gpd.GeoDataFrame:
        if self.value:
            return self.__extracted.set_index(self.column)
        else:
            return self.__table.set_index(self.column)


    def __read_file(self, filename: str) -> Tuple[str, gpd.GeoDataFrame]:
        """
        Given a filename, returns a tuple of a tabular file's name and 
        a GeoDataFrame containing tabular data.

        """
        if self.__get_extension(filename) != '.zip':
            return (filename, gpd.read_file(filename))

        else: # Recursively handles relative paths to zip files
            (name, gdf) = (None, None)
            for file in self.__unzip(filename):
                try:
                    (name, gdf) = self.__read_file(file)
                    break
                except:
                    continue

            if gdf is None:
                raise FileNotFoundError("No file found".format(name))
            else:
                return (name, gdf)


    def __get_extension(self, filename: str) -> str:
        (_, extension) = os.path.splitext(filename)
        return extension.lower()
        

    def __unzip(self, filename: str) -> List[str]:
        """
        Given a zipfile filename, returns a list of filenames in the 
        unzipped directory.

        """
        cwd = os.path.splitext(filename)[0]
        with zipfile.ZipFile(filename, 'r') as zipped:
            zipped.extractall(cwd)
            
        if not os.path.isdir(cwd):
            raise IOError("Directory \'{}\' not found.".format(cwd))
        else:
            (_, _, files) = next(os.walk(cwd))
            return [os.path.join(cwd, file) for file in files]


    def __has_spatial_data(self, gdf: gpd.GeoDataFrame) -> bool:
        True # TODO: check if all geometries are empty


    def __extract_to_inferred_file(self, 
                                   df: Union[gpd.GeoDataFrame, pd.DataFrame], 
                                   filename: pathlib.Path, 
                                   ext: str) -> NoReturn:
        # TODO: test each

        if ext == '.csv':
            df.to_csv(path_or_buf=filename)
        elif ext == '.pkl' or ext == '.bz2' or ext == '.zip' or \
             ext == '.gzip' or ext == '.xz':
            df.to_pickle(filename)
        elif ext == '.xlsx':
            df.to_excel(filename)
        elif ext == '.html':
            df.to_html(buf=filename)
        elif ext == '.json':
            df.to_json(path_or_buf=filename)
        elif ext == '.tex':
            df.to_latex(buf=filename)
        else:
            with open(filename, 'w') as out:
                if ext == '.md':
                    print(type(df))
                    out.write(df.to_markdown())
                else:
                    out.write(df.to_string())


    #===========================================+
    # Getters and Setters                       |
    #===========================================+

    @property
    def infile(self) -> str:
        """
        {str} 
            Path to tabular data file containing tables to extract
        
        """
        return self.__infile
    @infile.setter
    def infile(self, filename: Optional[str]) -> NoReturn:
        if filename:
            (self.__infile, self.__table) = self.__read_file(filename)


    @property
    def outfile(self) -> Optional[pathlib.Path]:
        """
        {pathlib.Path | None}
            Path to output csv file containing extracted table. 
            Defaults to stdout

        """
        return self.__outfile
    @outfile.setter
    def outfile(self, filename: Optional[str] = None) -> NoReturn:
        try:
            self.__outfile = pathlib.Path(filename)
        except:
            self.__outfile = None


    @property
    def column(self) -> str:
        """
        {str}
            Name of column in source table to use as index for extracted table.
        
        """
        return self.__column
    @column.setter
    def column(self, column: Optional[str]) -> NoReturn:
        if column:
            try:
                self.__coldata = self.__table[column]
            except Exception as e:
                raise KeyError("Column not found: {}".format(e))

            self.__column = column


    @property
    def value(self) -> Union[str, List[str], None]:
        """ 
        {str | List[str] | None}
            Value in column in source table to use as filter for extracting 
            subtable. If not specified, output file is a reindexed table.

        """
        return self.__value
    @value.setter
    def value(self, value: Union[str, List[str], None]) -> NoReturn:
        if value and (self.__table is None):
            raise KeyError("Cannot set value without specifying tabular data")

        elif value and (not self.column):
            raise KeyError("Cannot set value without specifying column")

        elif value:
            try: # value is a singleton
                self.__extracted = \
                    self.__table[self.__table[self.column] == value]
            except: # value is a list
                self.__extracted = \
                    self.__table[self.__table[self.column].isin(value)]

            if self.__extracted.empty:
                raise KeyError(
                    "Column '{}' has no value '{}'".format(self.column, value))
            else:
                self.__value = value


#########################################
#                                       #
#       Command-Line Parsing            #
#                                       #
#########################################

def parse_arguments() -> argparse.Namespace:
    """
    Parses command-line arguments and returns a Namespace of input values.

    Returns
    -------
    An argparse Namespace object

    """
    infile_help = "name/path of input file of tabular data to read"
    column_help = "label of column to use as index for extracted table"
    value_help = "value(s) of specified column in rows to extract"
    outfile_help = "name/path of output file for writing"

    description = """Script to extract tabular data. 

If no outfile is specified, outputs plaintext to stdout.
If no column is specified, outputs filetype converted input. 
If no value is specified, outputs table indexed with given column (required).
If value and column are specified, outputs subtable indexed with given column
and containing only rows equal to given value(s).

supported input filetypes:
    .csv .geojson .shp .xlsx .zip

supported output filetypes:
    .bz2 .csv .geojson .gpkg .gzip .html .json .md .pkl .tex .xlsx .zip 
    all other extensions will contain output in plaintext
"""
    
    examples = """examples:
    
    python ExtractTable.py input.xlsx -c ID > output.csv; ls
    python ExtractTable.py foo.csv -o bar.csv -c "state fips" -v 01
    python ExtractTable.py input.csv -o ../output.csv -c Name -v "Rick Astley"
    python ExtractTable.py in.csv -o out.csv -c NUM -v 0 1 2 3
"""

    parser = argparse.ArgumentParser(
                description=description,
                epilog=examples,
                formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
                'infile',
                metavar='INFILE', 
                help=infile_help)
    parser.add_argument(
                '-o', 
                '--output', 
                dest='outfile',
                metavar='OUTFILE', 
                type=str, 
                help=outfile_help)
    parser.add_argument(
                '-c', 
                '--column', 
                dest='column', 
                metavar='COLUMN', 
                type=str, 
                help=column_help)
    parser.add_argument(
                '-v', 
                '--value', 
                dest='value',
                metavar='VALUE', 
                type=str,
                nargs='+',
                help=value_help)

    return parser.parse_args()



#########################################
#                                       #
#               Main                    #
#                                       #
#########################################

def main() -> NoReturn:
    """Validates input, parses command-line arguments, runs script."""
    args = parse_arguments()
    infile = args.infile
    outfile = args.outfile
    column = args.column
    value = args.value

    try:
        et = ExtractTable(infile, outfile, column, value)

        # debug - testing
        print('infile = ', et.infile)
        print('outfile = ', et.outfile)
        print('column = ', et.column)
        print('value = ', et.value)

        et.extract_to_file()

    except Exception as e:
        print(e)

    sys.exit()



#########################################
#                                       #
#           Function Calls              #
#                                       #
#########################################

if __name__ == "__main__":
    main()

