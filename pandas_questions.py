import pandas as pd
import geopandas as gpd


# --------------------------------------------------
# UTILS
# --------------------------------------------------
def _normalize_dep_code(s: pd.Series) -> pd.Series:
    s = s.astype(str).str.strip()
    s = s.str.replace(r"\.0$", "", regex=True)
    s = s.apply(lambda x: x.zfill(2) if x.isdigit() and len(x) < 2 else x)
    return s


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------
def load_data():
    referendum = pd.read_csv(
        "data/referendum.csv",
        sep=";",
        encoding="utf-8",
        engine="python",
        dtype={"Department code": str, "Town code": str},
    )

    regions = pd.read_csv(
        "data/regions.csv",
        sep=",",
        encoding="utf-8",
        engine="python",
        dtype={"code": str},
    )

    departments = pd.read_csv(
        "data/departments.csv",
        sep=",",
        encoding="utf-8",
        engine="python",
        dtype={"code": str, "region_code": str},
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

    departments["code_dep"] = _normalize_dep_code(departments["code_dep"])
    departments["code_reg"] = departments["code_reg"].astype(str).str.strip()
    regions["code_reg"] = regions["code_reg"].astype(str).str.strip()

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
    referendum = referendum.copy()
    regions_and_departments = regions_and_departments.copy()

    referendum.columns = referendum.columns.str.strip()

    referendum["code_dep"] = _normalize_dep_code(referendum["Department code"])
    regions_and_departments["code_dep"] = _normalize_dep_code(
        regions_and_departments["code_dep"]
    )

    df = referendum.merge(
        regions_and_departments,
        on="code_dep",
        how="left"
    )

    # Remove DOM-TOM / COM / abroad voters
    df = df[~df["code_dep"].str.contains("Z", na=False)]

    # Tests require NO NaN
    df = df.dropna()

    return df


# --------------------------------------------------
# COMPUTE REFERENDUM RESULTS BY REGION
# --------------------------------------------------
def compute_referendum_result_by_regions(referendum_and_areas):
    grouped = (
        referendum_and_areas
        .groupby("name_reg", as_index=False)
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

    # Le GeoJSON utilise 'nom' pour le nom de la région
    geo = geo.rename(columns={"nom": "name_reg"})

    gdf = geo.merge(
        referendum_result_by_regions,
        on="name_reg",
        how="left"
    )

    gdf["ratio"] = (
        gdf["Choice A"] /
        (gdf["Choice A"] + gdf["Choice B"])
    )

    gdf.plot(
        column="ratio",
        cmap="RdBu",
        legend=True,
        edgecolor="black"
    )

    return gdf


