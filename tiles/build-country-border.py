#!/usr/bin/env python3
import csv
import sys
import geopandas
import shapely.wkt

def main():
    df = geopandas.read_file("country-polygons.csv")
    print(df, file=sys.stderr)

    geometry = geopandas.GeoSeries.from_wkt(df.geometry)
    gdf = geopandas.GeoDataFrame(data=df, geometry=geometry)
    borders = {}

    for pov in set(gdf.iso3.values):
        print("POV:", pov, file=sys.stderr)
        gdf_pov = gdf[gdf.perspective.str.contains(pov)]
        for i, row in geopandas.sjoin(gdf_pov, gdf_pov, predicate="touches").iterrows():
            index_pair = (min(i, row.index_right), max(i, row.index_right))
            if index_pair in borders:
                borders[index_pair].add(pov)
            else:
                borders[index_pair] = {pov}
        print(borders, file=sys.stderr)

    with open("country-borders.csv", mode="w") as file:
        rows = csv.DictWriter(file, fieldnames=("iso3a", "iso3b", "perspectives", "geometry"))
        rows.writeheader()

        for (i1, i2), povs in borders.items():
            iso3a, iso3b = gdf.loc[i1].iso3, gdf.loc[i2].iso3
            geom1, geom2 = gdf.loc[i1].geometry, gdf.loc[i2].geometry
            linestring = geom1.intersection(geom2)

            row = dict(iso3a=iso3a, iso3b=iso3b, perspectives=",".join(sorted(povs)))
            print("Writing", row, file=sys.stderr)
            rows.writerow({**row, "geometry": shapely.wkt.dumps(linestring)})

if __name__ == "__main__":
    exit(main())
