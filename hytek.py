"""Module for reading and processing HyTek meet results files."""

import sqlalchemy as sa
import sqlalchemy_access as sa_a  # type: ignore
import sqlalchemy_access.pyodbc as sa_a_pyodbc  # type: ignore
import pandas as pd
import pyodbc  # type: ignore
from pathlib import Path
from typing import Optional
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import URL
from version import HYTEK_DB_PASSWORD

class HyTekReader:
    """Class to handle reading and processing of HyTek meet database files."""

    # Class constants
    DEFAULT_DRIVER = '{Microsoft Access Driver (*.mdb, *.accdb)}'


    def __init__(self, db_path: str, password: str, driver: Optional[str] = None):
        """Initialize HyTekReader with database path and credentials.

        Args:
            db_path: Path to the Access database file
            password: Database password
            driver: Optional database driver override
        """
        self.db_path = Path(db_path)
        self.password = password
        self.driver = driver or self.DEFAULT_DRIVER
        self.engine: Optional[Engine] = None
        self.meet_info: Optional[pd.DataFrame] = None
        self.entries_info: Optional[pd.DataFrame] = None


    def connect(self) -> None:
        """Establish connection to the database."""
        connection_string = (
            f"DRIVER={self.driver};"
            f"DBQ={self.db_path};"
            f"PWD={self.password};"
            "ExtendedAnsiSQL=1;"
        )
        connection_url = sa.engine.URL.create(
            "access+pyodbc", 
            query={"odbc_connect": connection_string}
        )
        self.engine = sa.create_engine(connection_url)

    def read_data(self, query: str) -> pd.DataFrame:
        """Read data from database using specified query.

        Args:
            query: Optional SQL query string. Uses DEFAULT_SQL if not provided.

        Returns:
            pandas DataFrame containing query results
        """
        if not self.engine:
            self.connect()
        
        if self.engine is None:
            raise RuntimeError("Failed to establish database connection")
            
        self.df = pd.read_sql(query, con=self.engine)
        

        
        return self.df

    def read_meet_info(self) -> pd.DataFrame:
        """Read meet information from the database."""

        MEET_INFO_SQL = """
            SELECT 
                TRIM(M.Meet_name1) AS Meet_name, 
                M.Meet_start,
                M.Meet_end,
                M.Calc_date,
                M.course_order,
                M.EntryEligibility_date
            FROM 
                Meet AS M;
        """
        if not self.engine:
            self.connect()
        self.meet_info = self.read_data(MEET_INFO_SQL)
        return self.meet_info
    
    def read_entries_info(self) -> pd.DataFrame:
        """Read entries information from the database."""

        ENTRIES_SQL = """
            SELECT 
                TRIM(T.Team_abbr) AS Team_abbr, 
                TRIM(A.Last_name) AS Last_name, 
                TRIM(A.First_name) AS First_name, 
                A.Reg_no,
                A.Ath_Sex, 
                A.Birth_date, 
                A.Ath_age, 
                E.Event_no, 
                E.Ind_rel, 
                CInt(IIF(E.Event_dist IS NULL, 0, E.Event_dist)) AS Event_dist,
                E.Event_stroke, 
                E.Low_age, 
                E.Event_Type, 
                EN.ActSeed_course, 
                CLng(IIF(EN.ActualSeed_time IS NULL, 0, EN.ActualSeed_time * 100)) AS ActualSeed_time,
                EN.ConvSeed_course, 
                CLng(IIF(EN.ConvSeed_time IS NULL, 0, EN.ConvSeed_time * 100)) AS ConvSeed_time,
                EN.Scr_stat, 
                EN.Bonus_event, 
                TRIM(EN.Pre_exh) AS Pre_exh, 
                TRIM(EN.Fin_exh) AS Fin_exh
            FROM 
                ((Athlete AS A 
                INNER JOIN Team AS T ON A.Team_no = T.Team_no)
                INNER JOIN Entry AS EN ON A.Ath_no = EN.Ath_no)
                INNER JOIN Event AS E ON EN.Event_ptr = E.Event_ptr;
        """
        if not self.engine:
            self.connect()
        self.entries_info = self.read_data(ENTRIES_SQL)
                # Ensure integer types for specific columns
        int_columns = ['Event_dist', 'ActualSeed_time', 'ConvSeed_time']
        for col in int_columns:
            if col in self.entries_info.columns:
                self.entries_info[col] = self.entries_info[col].fillna(0).astype(int)

        return self.entries_info

    def export_csv(self, df: pd.DataFrame, output_path: str) -> None:
        """Export the current DataFrame to CSV.

        Args:
            output_path: Path where CSV file should be saved
        """
        if df is None:
            raise ValueError("No data has been read. Call read_data() first.")
        df.to_csv(output_path, index=False)

    @staticmethod
    def list_drivers() -> list:
        """List available ODBC drivers.

        Returns:
            List of available ODBC drivers
        """
        return pyodbc.drivers()


def main():
    """Main function to demonstrate HyTekReader usage."""
    # Example usage
    db_file = 'C:/Projects/TimeValidate/WRChamps.mdb'
    password = HYTEK_DB_PASSWORD
    
    # Create reader instance
    reader = HyTekReader(db_file, password)
    
    # Optional: List available drivers
    print("Available ODBC drivers:", reader.list_drivers())
    
    # Read data
    meet_info = reader.read_meet_info()
    entries_info = reader.read_entries_info()

    print("\nData preview:")
    print(meet_info)
    print(entries_info)
    
    # Export to CSV
    reader.export_csv(meet_info, 'meet_info.csv')
    reader.export_csv(entries_info, 'entries_info.csv')
    print("\nData exported to meet_info.csv and entries_info.csv")


if __name__ == "__main__":
    main()

