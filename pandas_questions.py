import pandas as pd
import geopandas as gpd


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------
def load_data():
    referendum = pd.read_csv(
        "data/referendum.csv",
        sep=";",
        encoding="utf-8",
        engine="python"
    )

    regions = pd.read_csv(
        "data/regions.csv",
        sep=",",
        encoding="utf-8",
        engine="python"
    )

    departments = pd.read_csv(
        "data/departments.csv",
        sep=",",
        encoding="utf-8",
        engine="python"
    )

    return referendum, regions, departments


# --------------------------------------------------
# MERGE REGIONS AND DEPARTMENTS
# --------------------------------------------------
def merge_regions_and_departments(regions, departments):
    regions = regions.rename(columns={
        "code": "code_reg",
        "name": "name_reg"
    })

    departments = departments.rename(columns={
        "region_code": "code_reg",
        "code": "code_dep",
        "name": "name_dep"
    })

    merged = departments.merge(
        regions[["code_reg", "name_reg"]],
        on="code_reg",
        how="left"
    )

    return merged[["code_reg", "name_reg", "code_dep", "name_dep"]]


# --------------------------------------------------
# MERGE REFERENDUM AND AREAS
# --------------------------------------------------
def merge_referendum_and_areas(referendum, regions_and_departments):
    referendum.columns = referendum.columns.str.strip()

    referendum = referendum.rename(columns={
        "Department code": "code_dep"
    })

    referendum["code_dep"] = referendum["code_dep"].astype(str)
    regions_and_departments["code_dep"] = regions_and_departments["code_dep"].astype(str)

    df = referendum.merge(
        regions_and_departments,
        on="code_dep",
        how="left"
    )

    # Remove DOM-TOM / COM / abroad voters
    df = df[~df["code_dep"].str.contains("Z", na=False)]

    return df


# --------------------------------------------------
# COMPUTE REFERENDUM RESULTS BY REGION
# --------------------------------------------------
def compute_referendum_result_by_regions(referendum_and_areas):
    grouped = (
        referendum_and_areas
        .groupby(["code_reg", "name_reg"], as_index=False)
        .agg({
            "Registered": "sum",
            "Abstentions": "sum",
            "Null": "sum",
            "Choice A": "sum",
            "Choice B": "sum",
        })
    )

    return grouped


# --------------------------------------------------
# PLOT REFERENDUM MAP
# --------------------------------------------------
def plot_referendum_map(referendum_result_by_regions):
    geo = gpd.read_file("data/regions.geojson")

    # GeoJSON uses 'code' as region identifier
    geo = geo.rename(columns={"code": "code_reg"})

    geo["code_reg"] = geo["code_reg"].astype(str)
    referendum_result_by_regions["code_reg"] = (
        referendum_result_by_regions["code_reg"].astype(str)
    )

    gdf = geo.merge(
        referendum_result_by_regions,
        on="code_reg",
        how="left"
    )

    gdf["ratio"] = (
        gdf["Choice A"] /
        (gdf["Choice A"] + gdf["Choice B"])
    )

    # Plot (no plt.show() here, required by tests)
    gdf.plot(
        column="ratio",
        cmap="RdBu",
        legend=True,
        edgecolor="black"
    )

    return gdf
