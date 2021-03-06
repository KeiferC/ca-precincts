"""
extract.py
==========

Provides
    - A python class, ``ExtractTable`` (pronounced "extractable") for 
      extracting subtables from given tabular data. Can manage filetypes 
      .csv, .xlsx, .geojson, .shp, etc.

    - A commandline script that can be used to

        1. convert input filetype to output filetype (ex. .shp -> .csv);
        2. output tabular data reindexed with a specified column label; or
        3. output subtables from input tabular data

Metadata
--------

:Filename:      `extract.py <https://github.com/keiferc/extract-table>`_
:Author:        `@KeiferC <https://github.com/keiferc>`_
:Date:          06 July 2020
:Version:       0.0.1
:Description:   Script and module to extract subtables from given tabular data
:Dependencies:  

                - ``geopandas``
                - ``numpy``

Documentation
-------------

Documentation for the ``extract`` module can be found as docstrings. 
Run ``import modules.extract; help(modules.extract)`` to view documentation.
::

    $ python
    >>> import modules.extract; help(modules.extract)

Additionally, documentation can be found on `Read the Docs 
<https://extract-table.readthedocs.io>`_.

Script Usage 
------------

To get help on using the ``extract.py`` script, run ``extract.py -h``.
::

    $ python extract.py -h

"""
import argparse
import geopandas as gpd
import numpy as np
import os.path
import pandas as pd
import pathlib
import shapely.wkt
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
    For extracting tabular data. Run ``help(ExtractTable)`` to view docs.

    
    Specifying `outfile` determines the filetype of the output table. 
    Specifying `column` uses given column as output's index. Specifying 
    `value` isolates output to rows that contain values in specified column.
    

    Attributes
    ----------
    infile : Optional[str]
        Name/path of input file of tabular data to read
    outfile : Optional[pathlib.Path]
        Path of output file for writing
    column : Optional[str]
        Label of column to use as index for extracted table
    value : Optional[Union[str, List[str]]]
        Value(s) of specified column in rows to extract
    
    """

    #===========================================+
    # Constructors                              |
    #===========================================+

    def __init__(self, 
                 infile:    Optional[Union[str, 
                                           gpd.GeoDataFrame,
                                           pd.DataFrame]] = None, 
                 outfile:   Optional[str] = None, 
                 column:    Optional[str] = None, 
                 value:     Optional[Union[str, List[str]]] = None):
        """
        ExtractTable initializer.

        Parameters
        ----------
        infile : str | gpd.GeoDataFrame | pd.DataFrame | None, optional
            Name/path of input file of tabular data to read or geopandas
            GeoDataFrame or pandas DataFrame. Default is None.
        outfile : str | None, optional
            Name/path of output file for writing. Default is None.
        column : str | None, optional
            Label of column to use as index for extracted table. Default 
            is None
        value : str | List[str] | None, optional
            Value(s) of specified column in rows to extract. Default is None
        
        Returns
        -------
        extract.ExtractTable

        See Also
        --------
        extract.ExtractTable.read_file

        Examples
        --------
        >>> et1 = ExtractTable()

        >>> et2 = ExtractTable('example/input.shp')

        >>> et3 = ExtractTable('example/file.csv', column='ID')

        >>> et4 = ExtractTable('input.xlsx', 'output.md')

        >>> et5 = ExtractTable('in.csv', 'out.tex', 'ID', '01')

        >>> et6 = ExtractTable('in.csv', column='ID', value=['01', '03'])

        >>> et7 = ExtractTable('in.shp', outfile='out', column='X', value='y')

        >>> et8 = ExtractTable(gpd.GeoDataFrame())

        >>> et9 = ExtractTable(pd.DataFrame())

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
            Name/path of input file of tabular data to read. Default is None
        column : str | None, optional
            Label of column to use as index for extracted table. Default 
            is None
        value : str | List[str] | None, optional
            Value(s) of specified column in rows to extract. Default is None

        Returns
        -------
        extract.ExtractTable

        Examples
        --------
        >>> et1 = ExtractTable.read_file('example/input.shp')

        >>> et2 = ExtractTable.read_file('example/file.csv', column='ID')

        >>> et3 = ExtractTable.read_file('in.shp', column='foo', value='bar')

        >>> et4 = ExtractTable.read_file('in.csv', column='X', value=['1','3'])

        """
        return self(filename, None, column, value)
    

    def __sanitize_init(self,
                        infile:     Optional[Union[str, 
                                             gpd.GeoDataFrame,
                                             pd.DataFrame]], 
                        outfile:    Optional[str], 
                        column:     Optional[str], 
                        value:      Optional[Union[str, List[str]]]):
        """
        Safely initializes attributes using setters.

        Parameters
        ----------
        infile : str | gpd.GeoDataFrame | pd.DataFrame | None, optional
            Name/path of input file of tabular data to read or geopandas
            GeoDataFrame or pandas DataFrame
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
        """
        Returns a GeoPandas GeoDataFrame containing extracted subtable.

        Returns
        -------
        gpd.GeoDataFrame

        Raises
        ------
        RuntimeError
            Raised if trying to extract from non-existent tabular data
        
        See Also
        --------
        extract.ExtractTable.extract_to_file

        Examples
        --------
        >>> et = ExtractTable.read_file('input.csv')
        >>> df1 = et.extract()
        >>> print(df1.head())
        field_1 col1 col2 geometry
        0    asdf    a    b     None
        1    fdsa    c    d     None
        2    lkjh    c    3     None

        >>> et.column = 'col1'
        >>> print(et.extract().head())
            field_1 col2 geometry
        col1                      
        a       asdf    b     None
        c       fdsa    d     None
        c       lkjh    3     None

        >>> et.value = 'c'
        >>> print(et.extract().head())
            field_1 col2 geometry
        col1                      
        c       fdsa    d     None
        c       lkjh    3     None

        """
        if self.__table is None:
            raise RuntimeError("Unable to find tabular data to extract")
        elif self.column:
            return self.__reindex()
        else:
            return self.__table
            

    def extract_to_file(self, outfile: Optional[str] = None,
                        driver: Optional[str] = None) -> NoReturn:
        """
        Writes the tabular extracted data to a file. 
        
        Given an optional Fiona support OGR driver, writes to file using the 
        driver. If outfile is None, data is printed as plaintext to stdout.

        Parameters
        ----------
        outfile: str | None, optional
            Name of file to write extracted data. Default is None
        driver: str | None, optional
            Name of Fiona supported OGR drivers to use for file writing.
            Default is None
        
        Raises
        ------
        RuntimeError
            Raised if unable to extract to output file

        See Also
        --------
        extract.ExtractTable.extract

        Examples
        --------
        >>> et1 = ExtractTable.read_file('input.csv', 'col2', ['b', 'd'])
        >>> et1.extract_to_file()
             field_1 col1
        col2                      
        b       asdf    a
        d       fdsa    c

        >>> et1.outfile = 'output.xlsx'
        >>> et1.extract_to_file()

        >>> et2 = ExtractTable('input.shp', 'output', 'column1', 'square')
        >>> et2.extract_to_file('ESRI Shapefile')

        """
        gdf = self.extract()
        is_geometric = self.__has_spatial_data(gdf)

        if outfile is None:
            filename = self.outfile
        else:
            filename = outfile

        if filename is None:
            if is_geometric:
                gdf.to_string(buf=sys.stdout)
            else:
                pd.DataFrame(gdf).drop(
                        columns='geometry').to_string(buf=sys.stdout)

        else:
            ext = self.__get_extension(filename)
            try: 
                if is_geometric and ext == '.shp':
                    gdf.to_file(filename)
                elif is_geometric and ext == '.geojson':
                    gdf.to_file(filename, driver='GeoJSON')
                elif is_geometric and ext == '.gpkg':
                    gdf.to_file(filename, driver='GPKG')
                elif is_geometric and driver is not None:
                    gdf.to_file(filename, driver=driver)
                elif is_geometric:
                    self.__extract_to_inferred_file(
                            pd.DataFrame(gdf), filename, ext)
                else:
                    self.__extract_to_inferred_file(
                            pd.DataFrame(gdf).drop(columns='geometry'), 
                            filename, ext)
            except Exception as e:
                raise RuntimeError("Extraction failed:", e)


    def list_columns(self) -> np.ndarray:
        """
        Returns a list of all columns in the initialized source tabular data.

        Returns
        -------
        np.ndarray

        Raises
        ------
        RuntimeError
            Raised if trying to list columns from non-existent tabular data
        
        See Also
        --------
        extract.ExtractTable.list_values
        
        Examples
        --------
        >>> et = ExtractTable.read_file('input.csv)
        >>> print(et.list_columns())
        ['field_1' 'col1' 'col2']

        """
        if self.__table is None:
            raise RuntimeError("Unable to find tabular data to extract")
        elif self.__has_spatial_data(self.__table):
            return self.__table.columns.values
        else:
            return self.__table.columns.values[
                        self.__table.columns.values != 'geometry']


    def list_values(self, 
                    column: Optional[str] = None,
                    unique: Optional[bool] = False) -> \
            Union[np.ndarray, gpd.array.GeometryArray]:
        """
        Returns a list of values in the initialized column (default).
        
        Returns a list of values in the given column (if specified).
        Returns a list of unique values (if specified)

        Parameters
        ----------
        column : str | NoneType, optional
            Name of the column whose values are to be listed. If None,
            lists the values of the initialized column. Defaults to None
        unique : bool, optional
            If True, function lists only unique values. Defaults to False

        Returns
        -------
        np.ndarray | gpd.array.GeometryArray

        Raises
        ------
        RuntimeError
            Raised if trying to list values from non-existent tabular data
        KeyError
            Raised if column does not exist in tabular data
        RuntimeError
            Raised if trying to list values from non-existent column
        
        See Also
        --------
        extract.ExtractTable.list_columns
        
        Examples
        --------
        >>> et = ExtractTable.read_file('input.csv', 'col2')
        >>> print(et.list_values)
        ['b' 'd' '3' '5' '10']

        >>> print(et.list_values('col1'))
        ['a' 'c' 'c' 'c' 'b']
        
        >>> print(et.list_values('col1', unique=True))
        ['a' 'c' 'b']

        """
        if self.__table is None:
            raise RuntimeError("Unable to find tabular data to extract")

        elif column is not None: 
            try:
                if unique:
                    return self.__table[column].unique()
                else:
                    return self.__table[column].values
            except:
                raise KeyError("Unable to find column '{}'".format(column))

        elif column is None and self.column is not None:
            if unique:
                return self.__table[self.column].unique()
            else:
                return self.__table[self.column].values

        else:
            raise RuntimeError("No initialized column exists")
            

    #===========================================+
    # Private Helper Methods                    |
    #===========================================+

    def __reindex(self) -> gpd.GeoDataFrame:
        if self.value:
            return self.__extracted.set_index(self.column)
        else:
            return self.__table.set_index(self.column)


    def __get_extension(self, filename: str) -> str:
        (_, extension) = os.path.splitext(filename)
        return extension.lower()


    def __read_file(self, filename: str) -> Tuple[str, gpd.GeoDataFrame]:
        """
        Given a filename, returns a tuple of a tabular file's name and 
        a GeoDataFrame containing tabular data.

        """
        ext = self.__get_extension(filename)

        if ext != '.zip':
            try:
                return (filename, gpd.read_file(filename))
            except: # gpd's read uses pd's init, which has recursion depth cap
                return (filename, self.__geometrize_gdf(
                        gpd.GeoDataFrame(self.__read_inferred(filename, ext))))
        else:
            return self.__read_zip(filename)


    def __read_zip(self, filename: str) -> Tuple[str, gpd.GeoDataFrame]:
        """
        Helper to self.__read_file. Recursively unzips given zipfiles.
        Unlike gpd, can handle relative paths and doesn't require
        'zip:///' prepend.

        """
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
        

    def __unzip(self, filename: str) -> List[str]:
        """
        Given a zipfile filename, returns a list of filenames in the 
        unzipped directory.

        """
        cwd = os.path.splitext(filename)[0]
        with zipfile.ZipFile(filename, 'r') as zipped:
            zipped.extractall(cwd)
            
        if os.path.isdir(cwd) is None:
            raise IOError("Directory \'{}\' not found.".format(cwd))
        else:
            (_, _, files) = next(os.walk(cwd))
            return [os.path.join(cwd, file) for file in files]


    def __has_spatial_data(self, gdf: gpd.GeoDataFrame) -> bool:
        return not gdf['geometry'].isna().all()


    def __read_inferred(self, filename: str, ext: str) -> pd.DataFrame:
        if ext == '.csv':
            return pd.read_csv(filename)
        elif ext == '.pkl' or ext == '.bz2' or ext == '.zip' or \
             ext == '.gzip' or ext == '.xz':
            return pd.read_pickle(filename)
        elif ext == '.xlsx':
            return pd.read_excel(filename)
        elif ext == '.html':
            return pd.read_html(filename)
        elif ext == '.json':
            return pd.read_json(filename)
        else:
            raise FileNotFoundError('Cannot read {}'.format(filename))


    def __extract_to_inferred_file(self, 
                                   df: Union[gpd.GeoDataFrame, pd.DataFrame], 
                                   filename: pathlib.Path, 
                                   ext: str) -> NoReturn:
        has_index = self.column is not None

        if ext == '.csv':
            df.to_csv(path_or_buf=filename, index=has_index)
        elif ext == '.pkl' or ext == '.bz2' or ext == '.zip' or \
             ext == '.gzip' or ext == '.xz':
            df.to_pickle(filename)
        elif ext == '.xlsx':
            df.to_excel(filename, index=has_index)
        elif ext == '.html':
            df.to_html(buf=filename, index_names=has_index)
        elif ext == '.json':
            df.to_json(path_or_buf=filename)
        elif ext == '.tex':
            df.to_latex(buf=filename, index=has_index)
        else:
            with open(filename, 'w') as out:
                if ext == '.md':
                    out.write(df.to_markdown())
                else:
                    out.write(df.to_string())
    

    def __geometrize_gdf(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        try:
            geometry = gdf['geometry'].map(shapely.wkt.loads)
            geometrized = gdf.drop(columns='geometry')
            return gpd.GeoDataFrame(geometrized, geometry=geometry)
        except:
            return gdf


    #===========================================+
    # Getters and Setters                       |
    #===========================================+

    @property
    def infile(self) -> str:
        """
        {str} 
            Name/path of input file of tabular data to read
        
        """
        return self.__infile

    @infile.setter
    def infile(self, 
               infile: Optional[Union[str, 
                                      gpd.GeoDataFrame,
                                      pd.DataFrame]]) -> NoReturn:
        if infile is not None:
            try:
                (self.__infile, self.__table) = self.__read_file(infile)
            except:
                try:
                    self.__infile = None
                    self.__table = gpd.GeoDataFrame(infile)
                except Exception as e:
                    raise FileNotFoundError(
                            '{} not found. {}'.format(infile, e))


    @property
    def outfile(self) -> Optional[pathlib.Path]:
        """
        {pathlib.Path | None}
            Path of output file for writing. Defaults to stdout

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
           Label of column to use as index for extracted table
        
        """
        return self.__column

    @column.setter
    def column(self, column: Optional[str]) -> NoReturn:
        if column is not None:
            try:
                self.__coldata = self.__table[column]
            except Exception as e:
                raise KeyError("Column not found: {}".format(e))

            self.__column = column


    @property
    def value(self) -> Optional[Union[str, List[str]]]:
        """ 
        {str | List[str] | None}
           Value(s) of specified column in rows to extract 

        """
        return self.__value

    @value.setter
    def value(self, value: Optional[Union[str, List[str]]]) -> NoReturn:
        if value is not None and self.__table is None:
            raise KeyError("Cannot set value without specifying tabular data")

        elif value is not None and self.column is None:
            raise KeyError("Cannot set value without specifying column")

        elif value is not None:
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

If no outfile is specified, outputs plaintext to stdout. If no column is 
specified, outputs filetype converted input. If no value is specified, 
outputs table indexed with given column (required). If value and column 
are specified, outputs subtable indexed with given column and containing 
only rows equal to given value(s).

supported input filetypes:
    .csv .geojson .shp .xlsx .zip

supported output filetypes:
    .bz2 .csv .geojson .gpkg .gzip .html .json .md .pkl .tex .xlsx .zip 
    all other extensions will contain output in plaintext
"""
    
    examples = """examples:
    python extract.py input.xlsx -c ID > output.csv
    python extract.py foo.csv -o bar.csv -c "state fips" -v 01
    python extract.py input.csv -o ../output.csv -c Name -v "Rick Astley"
    python extract.py in.csv -o out.csv -c NUM -v 0 1 2 3"""

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

