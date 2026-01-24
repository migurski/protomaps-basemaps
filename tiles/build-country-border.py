#!/usr/bin/env python3
import csv
import sys
import functools
import geopandas
import shapely.wkt

def main():
    df = geopandas.read_file("country-polygons.csv")
    print(df, file=sys.stderr)

    geometry = geopandas.GeoSeries.from_wkt(df.geometry)
    gdf = geopandas.GeoDataFrame(data=df, geometry=geometry)
    pov_borders: dict[tuple[int, int], set[int]] = {}
    iso3_neighbors: set[tuple[str, str]] = set()

    for pov in set(gdf.iso3.values):
        print("POV:", pov, file=sys.stderr)
        gdf_pov = gdf[gdf.perspective.str.contains(pov)]
        for i, row in geopandas.sjoin(gdf_pov, gdf_pov, predicate="touches").iterrows():
            i1, i2 = (min(i, row.index_right), max(i, row.index_right))
            iso3a, iso3b = gdf.loc[i1].iso3, gdf.loc[i2].iso3
            iso3_neighbors.add((iso3a, iso3b))
            if (i1, i2) in pov_borders:
                pov_borders[(i1, i2)].add(pov)
            else:
                pov_borders[(i1, i2)] = {pov}
        print(pov_borders, file=sys.stderr)

    with open("country-disputes.csv", mode="w") as file:
        rows = csv.DictWriter(file, fieldnames=("iso3a", "iso3b", "disputed_border", "agreed_border"))
        rows.writeheader()

        print(iso3_neighbors, file=sys.stderr)
        for iso3a, iso3b in iso3_neighbors:
            gdf1 = gdf[(gdf.iso3 == iso3a) & (gdf.perspective.str.contains(iso3a))]
            gdf2 = gdf[(gdf.iso3 == iso3b) & (gdf.perspective.str.contains(iso3b))]
            geom1, geom2 = gdf1.iloc[0].geometry, gdf2.iloc[0].geometry
            disputed_geom = geom1.intersection(geom2)

            if disputed_geom.is_empty or disputed_geom.area == 0:
                print("SAME", iso3a, iso3b)
                continue
            print("DIFFERENT", iso3a, iso3b, round(disputed_geom.area, 3))

            agreed_geom1 = geom1.difference(disputed_geom)
            agreed_geom2 = geom2.difference(disputed_geom)
            agreed_line = agreed_geom1.intersection(agreed_geom2)
            if disputed_geom.type == 'GeometryCollection':
                dpolygons = [p for p in disputed_geom.geoms if 'Polygon' in p.type]
                disputed_geom = functools.reduce(lambda g1, g2: g1.union(g2), dpolygons)
            disputed_line = disputed_geom.boundary

            row = dict(iso3a=iso3a, iso3b=iso3b)
            print("Writing", row, file=sys.stderr)
            rows.writerow({
                **row,
                "disputed_border": shapely.wkt.dumps(disputed_line),
                "agreed_border": shapely.wkt.dumps(agreed_line),
            })

    with open("country-borders.csv", mode="w") as file:
        rows = csv.DictWriter(file, fieldnames=("iso3a", "iso3b", "perspectives", "geometry"))
        rows.writeheader()

        for (i1, i2), povs in pov_borders.items():
            iso3a, iso3b = gdf.loc[i1].iso3, gdf.loc[i2].iso3
            geom1, geom2 = gdf.loc[i1].geometry, gdf.loc[i2].geometry
            linestring = geom1.intersection(geom2)

            row = dict(iso3a=iso3a, iso3b=iso3b, perspectives=",".join(sorted(povs)))
            print("Writing", row, file=sys.stderr)
            rows.writerow({**row, "geometry": shapely.wkt.dumps(linestring)})

if __name__ == "__main__":
    exit(main())
