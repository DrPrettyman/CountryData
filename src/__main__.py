import pandas as pd
import requests
import os
from bs4 import BeautifulSoup
from io import StringIO


def fetch_centroids() -> pd.DataFrame:
    """Fetch country centroids from a CSV file.
    
    We want the centroids of countries for plotting purposes.
    There is a good CSV file available from gavinr's 
    world-countries-centroids repo.
    """
    # Download the CSV file from the URL
    centroids_df_raw = pd.read_csv(
        "https://cdn.jsdelivr.net/gh/gavinr/world-countries-centroids@v1/dist/countries.csv",
        keep_default_na=False,
    )

    # Some ISO codes are repeated in the CSV file becuase some small
    # territories are listed separately, but we want to
    # exclude these and just keep the main country centroids.
    _exclude_rows = pd.DataFrame([
        {'ISO': 'TF', 'COUNTRY': 'Juan De Nova Island'},
        {'ISO': 'TF', 'COUNTRY': 'Glorioso Islands'},
        {'ISO': 'BQ', 'COUNTRY': 'Saba'},
        {'ISO': 'BQ', 'COUNTRY': 'Saint Eustatius'},
        {'ISO': 'ES', 'COUNTRY': 'Canarias'}
    ])
    _merge = centroids_df_raw.merge(
        _exclude_rows, on=['ISO', 'COUNTRY'], how='left', indicator=True
    )
    centroids_df = _merge[_merge['_merge'] == 'left_only'].drop(
        '_merge', axis=1
    )

    # Finally just a few tweaks to the DataFrame
    centroids_df['ISO'] = centroids_df['ISO'].str.strip()
    centroids_df['COUNTRY'] = centroids_df['COUNTRY'].str.strip()
    centroids_df = centroids_df.sort_values('ISO').reset_index(drop=True).drop(
        columns=['COUNTRYAFF', "AFF_ISO"]
    ).rename(
        columns={
            'ISO': 'iso',
            'COUNTRY': 'country'
        }
    )

    # There are also some missing regions which do appear in the comtrade database
    _missing_lat_lon = pd.DataFrame(
        [
            {
                "country": "Hong Kong",
                "iso": "HK",
                "latitude": 22.3964,
                "longitude": 114.1095
            },
            {
                "country": "Macau",
                "iso": "MO",
                "latitude": 22.2109,
                "longitude": 113.5525
            },
            {
                "country": "Åland Islands",
                "iso": "AX",
                "latitude": 60.25,
                "longitude": 20.0
            },
            {
                "country": "Western Sahara",
                "iso": "EH",
                "latitude": 24.5,
                "longitude": -13
            }
        ]
    )

    # Add the missing regions
    centroids_df = pd.concat([centroids_df, _missing_lat_lon])
    
    return centroids_df.reset_index(drop=True)
    
    
def fetch_un_data():
    # Get a lookup table of M49 codes
    # and country names from the UN M49 page

    response = requests.get(
        "https://unstats.un.org/unsd/methodology/m49/overview/"
    )
    response.raise_for_status()

    # Extract the table from the response content
    soup = BeautifulSoup(response.content, 'html.parser')
    table = soup.find('table', {'id': 'downloadTableEN'})
    
    # Convert the HTML table to a DataFrame
    df = pd.read_html(StringIO(str(table)), keep_default_na=False)[0]

    # The LDC column indicates whether a country is a least developed country
    # There is a string "x" if true, and an empty string if false.
    # We convert this to a boolean column for easier filtering later.
    df['ldc'] = df['Least Developed Countries (LDC)'].apply(
        lambda x: True if x == 'x' else False
    )

    df = df.rename(
        columns={
            'Country or Area': 'country',
            'M49 Code': 'm49',
            'Region Name': 'region',
            'Sub-region Name': 'subregion',
            'ISO-alpha3 Code': 'iso3',
            'ISO-alpha2 Code': 'iso2',
        }
    )

    return df[[
        'region', 'subregion', 'm49', 'iso3', 'iso2', 'ldc'
    ]].copy()


if __name__ == "__main__":
    # Fetch the country centroids and UN data
    centroids = fetch_centroids()
    un_data = fetch_un_data()

    # Merge the two DataFrames on the 'iso' column
    merged = pd.merge(
        un_data, 
        centroids, 
        left_on='iso2', 
        right_on='iso', 
        how='outer'
    ).drop(columns=['iso'])
    
    # If using UN Comtrade data, some m49 codes are different 
    # so we will create a new column for the Comtrade codes
    alternate_comtrade_m49_codes = {
        251: "France",
        579: "Norway",
        699: "India",
        757: "Switzerland",
        842: "United States",
    }

    merged['m49_comtrade'] = merged['m49']
    # Update the M49 codes based on the alternate Comtrade codes
    for m49_code, country_name in alternate_comtrade_m49_codes.items():
        if country_name not in merged["country"].values:
            print(f"Country {country_name} not found in merged.")
            continue
        merged.loc[merged["country"] == country_name, "m49_comtrade"] = m49_code

    merged['non_country_region'] = False

    m49_non_country = [
        (899, None, "NES"),
        (568, "Europe", "NES"),
        (490, "Asia", "NES"),
        (577, "Africa", "NES"),
        (837, None, "Bunkers"),
        (838, None, "Free Zones"),
        (839, None, "Special Categories")
    ]

    _non_country_df = pd.DataFrame(
        m49_non_country,
        columns=["m49", "region", "country"]
    )
    _non_country_df['m49_comtrade'] = _non_country_df['m49']
    _non_country_df['ldc'] = False
    _non_country_df['non_country_region'] = True

    merged = pd.concat([merged, _non_country_df], ignore_index=True)
    merged["m49_comtrade"] = merged["m49_comtrade"].astype(int)
    merged = merged.sort_values(by="country").reset_index(drop=True)

    merged[[
        'region', 'subregion', 
        'country',
        'iso2', 'iso3',
        'm49', 'm49_comtrade',
        'latitude', 'longitude',
        'ldc', 'non_country_region'
    ]].to_csv(
        os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            "countries.csv"
        ),
        index=False
    )

    print("Country data has been fetched and saved to 'countries.csv'.")
    print("You can now use this data in your application.")