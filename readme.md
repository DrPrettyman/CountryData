# M49 Codes

A map from ISO-alpha codes to UN M49 codes. Useful for Comtrade commodities data. Some other country data like region, sub-region, lat/lon is included.

## Summary

I recently dealt with some commodity export data from the UN's Comtrade database and found that the only country identifiers were M49 codes (see https://unstats.un.org/unsd/methodology/m49/overview/). Moreover, some countries in the comtrade data had different M49 codes to those found on the unstats page (France, Norway, India, Switzerland and USA).

I have created a csv file here with fields:
- `region`
- `subregion`
- `country`
- `iso2` (ISO alpha2 code)
- `iso3` (ISO alpha3 code)
- `m49` 
- `m49_comtrade` (mostly the same as m49 except for 5 countries)
- `latitude`
- `longitude`
- `ldc` (Boolean: Least Developed Country)
- `non_country_region` (Boolean)

The latitude and longitude is from the excelent Gavinr's [world-countries-centroids](https://github.com/gavinr/world-countries-centroids) github repo. I needed these for plotting using Tableau.

## Notes

#### non_country_region

The comtrade data I worked with had a few extra m49 codes:

- 899: NES
- 568: Europe, NES
- 490: Asia, NES
- 577: Africa, NES
- 837: Bunkers
- 838: Free Zones
- 839: Special Categories

where "NES" stands for "not elsewhere specified". I have included these non-countries in the csv but they can be filtered out using the boolean `non_country_region` field. 