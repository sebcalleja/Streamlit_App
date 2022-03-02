#!/usr/bin/env python3

from lib2to3.refactor import get_fixers_from_package
import streamlit as st
import pandas as pd
import numpy as np
import subprocess
import matplotlib.pyplot as plt
import glob
import pydeck
import streamlit.components.v1 as components
from pathlib import Path
import sys
import plotly.express as px
import plotly.graph_objects as go
import os
import base64
import pingouin as pg
import re
from datetime import datetime
import itertools
import warnings
import chart_studio
import chart_studio.plotly as py
import plotly.io as pio
import requests
import io

## ------------------------------------- Data Organization Data ---------------------------------

## functions
def find_drop_outliers(df, phenotype_column):

    df["outlier"] = pg.madmedianrule(df[phenotype_column])
    df = grouped_df[df["outlier"] == False]

    return df.drop("outlier", axis=1)


def scatter_plot_lowess_plotly(
    df,
    x,
    y,
    facet_col,
    color,
    title,
    sort_values,
    filename,
    frac=0.1,
    save=False,
    marginal_y="histogram",
):

    fig = px.scatter(
        df.sort_values(sort_values),
        x=x,
        y=y,
        facet_col=facet_col,
        color=color,
        title=title,
        trendline="lowess",
        facet_col_spacing=0.04,
        width=1100,
        height=500,
        # marginal_y=marginal_y,
        # orientation='v',
        trendline_options=dict(frac=frac),
    )

    return fig


def scatter_plot_lowess_plotly_indiv(
    df,
    x,
    y,
    facet_col,
    color,
    title,
    sort_values,
    filename,
    frac=0.1,
    save=False,
    marginal_y="histogram",
):

    fig = px.scatter(
        df[df["genotype"] == genoIn].sort_values(sort_values),
        x=x,
        y=y,
        facet_col=facet_col,
        color=color,
        title=title,
        trendline="lowess",
        facet_col_spacing=0.04,
        width=1100,
        height=500,
        # marginal_y=marginal_y,
        # orientation='v',
        trendline_options=dict(frac=frac),
    )
    return fig

## Data Organization

url = "https://data.cyverse.org/dav-anon/iplant/projects/phytooracle/season_10_lettuce_yr_2020/level_4/scanner3DTop/season10_rgb_flir_psii_3d_div.csv"
s = requests.get(url).content
final_merged_df = pd.read_csv(io.StringIO(s.decode("utf-8")))

final_merged_df["date"] = pd.to_datetime(final_merged_df["date"])

grouped_df = (
    final_merged_df.groupby(by=["genotype", "treatment", "date"]).median().reset_index()
)

## Setting up the criteria for the plots
crit = ["Iceberg", "Aido", "Xanadu"]

map_dict = {
    "border": "Border",
    "treatment 1": "Well Watered",
    "treatment 2": "Moderately Water Limited",
    "treatment 3": "Water Limited",
}

grouped_df["treatment"] = grouped_df["treatment"].map(map_dict)

grouped_df = grouped_df[
    ~grouped_df["treatment"].isin(["Border", "Moderately Water Limited"])
]

grouped_df = find_drop_outliers(grouped_df, "FV/FM")
grouped_df = find_drop_outliers(grouped_df, "bounding_area_m2")
grouped_df = find_drop_outliers(grouped_df, "oriented_bounding_box")
grouped_df = find_drop_outliers(grouped_df, "median")

grouped_df = grouped_df[~grouped_df["genotype"].str.contains("GRxI")]

grouped_df["height"] = grouped_df["max_z"] - grouped_df["min_z"]


## -------------------------------------- Streamlit Visuals ----------------------------------------

# page_config sets up the title of the page (this mainly affects the
# text that appears on the browser tab as far as I know)
# icon makes the icon on the browser tab into a chart emoji
st.set_page_config(
    page_title="NAPPN Phytooracle Workshop",
    page_icon="https://avatars.githubusercontent.com/u/70173404?s=200&v=4",
    layout="wide",
)

# Markdowns for navigation bar
st.markdown(
    '<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous">',
    unsafe_allow_html=True,
)
st.markdown(
    """
<nav class="navbar fixed-top navbar-expand-lg navbar-dark" style="background-color: #6e6e70;">
<a class="navbar-brand" href="/">
</a>
  <a class="navbar-brand" href="" style="color:white;">NAPPN Phytooracle Workshop</a>
  <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
    <span class="navbar-toggler-icon"></span>
  </button>
  <div class="collapse navbar-collapse" id="navbarNav">
    <ul class="navbar-nav">
      <li class="nav-item active">
        <a class="nav-link" href="https://github.com/phytooracle/automation/blob/main/README.md/" style="color:white;">Documentation</a> 
      </li>
    </ul>
    <img class="logo-img" src="https://www.colorhexa.com/6e6e70.png" width="40" height="40">
    <img class="logo-img" src="https://brand.arizona.edu/sites/default/files/styles/uaqs_medium/public/ua_horiz_rgb_4.png?itok=T7TcQ02k" width="180" height="40">
    <img class="logo-img" src="https://www.colorhexa.com/6e6e70.png" width="40" height="40">
    <img class="logo-img" src="https://avatars.githubusercontent.com/u/70173404?s=200&v=4" width="40" height="40">
  </div>
</nav>
""",
    unsafe_allow_html=True,
)

# st.markdown writes text onto the page

st.markdown("# Phytooracle Products")
st.markdown("***")

## Populating the Sidebar
st.sidebar.image(
    "https://2mszru2giiozvn5btmb0gsig-wpengine.netdna-ssl.com/wp-content/uploads/2019/12/DU_LogoDesign_Final_Horizontal-min.png",
    use_column_width=True,
)

geno_list = ["Aido", "Iceberg", "Xanadu"]

genoIn = st.sidebar.selectbox("Genotype", geno_list)

## ------------------------- Individual Graph Bounding Area --------------------------------

fig_rgb = scatter_plot_lowess_plotly_indiv(
    df=grouped_df[
        grouped_df["bounding_area_m2"].isna() == False
    ],  # [grouped_df['genotype'].isin(crit)],
    x="date",
    y="bounding_area_m2",
    color="genotype",
    facet_col="treatment",
    sort_values=["genotype", "treatment"],
    title="Bounding Area Growth Curves (LOWESS)",
    filename="s11_plantgrowth_ww_wl_sig_diff_4",
    #    save=True,
    frac=1.0,
)
st.plotly_chart(fig_rgb, use_column_width=True)

## ------------------------- Individual Graph Median Temp --------------------------------

fig_temp = scatter_plot_lowess_plotly_indiv(
    df=grouped_df[
        grouped_df["median"].isna() == False
    ],  # [grouped_df['genotype'].isin(crit)],
    x="date",
    y="median",
    color="genotype",
    facet_col="treatment",
    sort_values=["genotype", "treatment"],
    title="Canopy Temperature Depression",
    filename="s11_ctd_ww_wl_sig_diff_4",
    #    save=True,
    frac=1.0,
)
st.plotly_chart(fig_temp, use_column_width=True)

## -------------------------------------- PS2 Graph ----------------------------------------

fig_fluor = scatter_plot_lowess_plotly_indiv(
    df=grouped_df[
        grouped_df["FV/FM"].isna() == False
    ],  # [grouped_df['genotype'].isin(crit)],
    x="date",
    y="FV/FM",
    color="genotype",
    facet_col="treatment",
    sort_values=["genotype", "treatment"],
    title="Photochemical efficiency of PSII",
    filename="s11_fvfm_ww_wl_sig_diff_4",
    #    save=True,
    frac=1.0,
)
st.plotly_chart(fig_fluor, use_column_width=True)

## ---------------------------------- Emmanuel's Plotly Graphs ---------------------------------

plotly_fluor = scatter_plot_lowess_plotly(
    df=grouped_df[
        grouped_df["FV/FM"].isna() == False
    ],  # [grouped_df['genotype'].isin(crit)],
    x="date",
    y="FV/FM",
    color="genotype",
    facet_col="treatment",
    sort_values=["genotype", "treatment"],
    title="Photochemical efficiency of PSII",
    filename="s11_fvfm_ww_wl_sig_diff_4",
    #    save=True,
    frac=1.0,
)
st.plotly_chart(plotly_fluor, use_column_width=True)

plotly_rgb = scatter_plot_lowess_plotly(
    df=grouped_df[
        grouped_df["bounding_area_m2"].isna() == False
    ],  # [grouped_df['genotype'].isin(crit)],
    x="date",
    y="bounding_area_m2",
    color="genotype",
    facet_col="treatment",
    sort_values=["genotype", "treatment"],
    title="Bounding Area Growth Curves (LOWESS)",
    filename="s11_plantgrowth_ww_wl_sig_diff_4",
    #    save=True,
    frac=1.0,
)
st.plotly_chart(plotly_rgb, use_column_width=True)

plotly_height = scatter_plot_lowess_plotly(
    df=grouped_df[
        grouped_df["height"].isna() == False
    ],  # [grouped_df['genotype'].isin(crit)],
    x="date",
    y="height",
    color="genotype",
    facet_col="treatment",
    sort_values=["genotype", "treatment"],
    title="Convex Hull Growth Curves (LOWESS)",
    filename="s11_plantgrowth_3d_ww_wl_sig_diff_4",
    #    save=True,
    frac=1.0,
)
st.plotly_chart(plotly_height, use_column_width=True)

plotly_temp = scatter_plot_lowess_plotly(
    df=grouped_df[
        grouped_df["median"].isna() == False
    ],  # [grouped_df['genotype'].isin(crit)],
    x="date",
    y="median",
    color="genotype",
    facet_col="treatment",
    sort_values=["genotype", "treatment"],
    title="Canopy Temperature Depression",
    filename="s11_ctd_ww_wl_sig_diff_4",
    #    save=True,
    frac=1.0,
)
st.plotly_chart(plotly_temp, use_column_width=True)

## _____________________________ Bottom half of the streamlit app ______________________________

## ----------------------------------- Rotating GIFs (static) ----------------------------------


## New Columns

col1, col2, col3 = st.columns(3)

with col1:

    st.markdown(
        "<center>Iceberg_230 Early Season</center>", unsafe_allow_html=True,
    )
    st.image("GIFs/Iceberg_230_soil_segmentation_1.gif")

    st.markdown(
        "<center>Aido_38 Early Season</center>", unsafe_allow_html=True,
    )
    st.image("GIFs/Aido_38_soil_segmentation_1.gif")

    st.markdown(
        "<center>Xanadu_143 Early Season</center>", unsafe_allow_html=True,
    )
    st.image("GIFs/Xanadu_143_soil_segmentation_1.gif")


with col2:

    st.markdown(
        "<center>Iceberg_230 Mid Season</center>", unsafe_allow_html=True,
    )
    st.image("GIFs/Iceberg_230_soil_segmentation_2.gif")

    st.markdown(
        "<center>Aido_38 Mid Season</center>", unsafe_allow_html=True,
    )
    st.image("GIFs/Aido_38_soil_segmentation_2.gif")

    st.markdown(
        "<center>Xanadu_143 Mid Season</center>", unsafe_allow_html=True,
    )
    st.image("GIFs/Xanadu_143_soil_segmentation_2.gif")

with col3:

    st.markdown(
        "<center>Iceberg_230 Late Season</center>", unsafe_allow_html=True,
    )
    st.image("GIFs/Iceberg_230_soil_segmentation_3.gif")

    st.markdown(
        "<center>Aido_38 Late Season</center>", unsafe_allow_html=True,
    )
    st.image("GIFs/Aido_38_soil_segmentation_3.gif")

    st.markdown(
        "<center>Xanadu_143 Late Season</center>", unsafe_allow_html=True,
    )
    st.image("GIFs/Xanadu_143_soil_segmentation_3.gif")

