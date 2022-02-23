#!/usr/bin/env python3

from lib2to3.refactor import get_fixers_from_package
import streamlit as st
import pandas as pd
import numpy as np
import subprocess
import seaborn as sns
import matplotlib.pyplot as plt
import glob
import pydeck
import meshio
import streamlit.components.v1 as components
import open3d as o3d
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
    # fig.update_xaxes(matches='x')
    # fig.data = [t for t in fig.data if t.mode == "lines"]
    # fig.update_traces(showlegend=True) #trendlines have showlegend=False by default

    if save == True:
        py.plot(fig, filename=filename, auto_open=False)
        fig.show()
    else:
        fig.show()


## Data organization

# df = pd.read_csv("season10_rgb_flir_psii_3d.csv")

# df["date"] = pd.to_datetime(df["date"])
# df["date"] = [d.date() for d in df["date"]]

# df = df.sort_values(by=["date", "treatment", "genotype"])

# df = df[df["treatment"] != "border"]

final_merged_df = pd.read_csv(
    "https://data.cyverse.org/dav-anon/iplant/projects/phytooracle/season_10_lettuce_yr_2020/level_4/scanner3DTop/season10_rgb_flir_psii_3d.csv"
)
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
    page_icon="chart_with_upwards_trend",
    layout="wide",
)

# Markdowns for navigation bar
st.markdown(
    '<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous">',
    unsafe_allow_html=True,
)
st.markdown(
    """
<nav class="navbar fixed-top navbar-expand-lg navbar-dark" style="background-color: #3498DB;">
<a class="navbar-brand" href="/">
      <div class="logo-image">
            <img src="/Volumes/SEB_USB/Season_10/NAPPN/Streamlit/UA.png">
      </div>
</a>
  <a class="navbar-brand" href="" target="_blank">NAPPN Phytooracle Workshop</a>
  <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
    <span class="navbar-toggler-icon"></span>
  </button>
  <div class="collapse navbar-collapse" id="navbarNav">
    <ul class="navbar-nav">
      <li class="nav-item active">
        <a class="nav-link disabled" href="#">Home <span class="sr-only">(current)</span></a>
      </li>
      <li class="nav-item">
        <a class="nav-link" href="https://github.com/phytooracle/automation/blob/main/README.md/" target="_blank">Documentation</a> 
      </li>
    </ul>
  </div>
</nav>
""",
    unsafe_allow_html=True,
)


# def season10_menu():
#     genoIn = st.sidebar.selectbox("Genotype", (df["genotype"].unique()))
#     plantIn = st.sidebar.selectbox(
#         "Plant Number",
#         (
#             df[df["plant_name"].str.contains(genoIn) == True]["plant_name"]
#             .sort_values()
#             .unique()
#         ),
#     )
# geno1 = st.sidebar.checkbox("Iceberg")
# geno2 = st.sidebar.checkbox("Aido")
# geno3 = st.sidebar.checkbox("Xanadu")

# return plantIn, genoIn  # , geno1, geno2, geno3

# st.markdown writes text onto the page
st.markdown("# Phytooracle Products")
st.markdown("***")

## Populating the Sidebar
st.sidebar.image("Pauli_Logo.png", use_column_width=True)

# plantIn, genoIn = season10_menu()
genoIn = st.sidebar.selectbox("Genotype", (df["genotype"].unique()))

## ------------------------- Individual Graph Bounding Area --------------------------------
st.markdown("")
st.markdown(f"### {genoIn} RGB")

## Make graph
ind_df = df[df["genotype"] == genoIn]

fig = px.line(
    ind_df,
    x="date",
    y="bounding_area_m2",
    title=f"{genoIn} Bounding Area (m2)",
    # width=600,
    # height=400,
)
# fig.add_vline(x=pd.to_datetime(f"{dateIn}"), line_dash="dash", line_color="red")

## Add graph to streamlit
st.plotly_chart(fig, use_column_width=True)

## ------------------------- Individual Graph Median Temp --------------------------------

st.markdown(f"### {genoIn} Thermal")

## Make graph
ind_df = df[df["genotype"] == genoIn]

fig_temp = px.line(
    ind_df,
    x="date",
    y="median",
    title=f"{genoIn} Plant Canopy Temperature (Kelvin)",
    # width=600,
    # height=400,
)
# fig_temp.add_vline(
#     x=pd.to_datetime(f"{dateIn}"), line_dash="dash", line_color="red"
# )

## Add graph to streamlit
st.plotly_chart(fig_temp, use_column_width=True)

## -------------------------------------- PS2 Graph ----------------------------------------
# st.markdown("### PS2")
st.markdown(f"### {genoIn} PS2")

## Make graph
ind_df = df[df["genotype"] == genoIn].sort_values(by="date")

fig_fluor = px.line(ind_df, x="date", y="FV/FM", title=f"{genoIn} Fv/Fm")

## Add graph to streamlit
st.plotly_chart(fig_fluor, use_column_width=True)

## ---------------------------------- Emmanuel's Plotly Graphs ---------------------------------

scatter_plot_lowess_plotly(
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

# scatter_plot_lowess_plotly(df=grouped_df[grouped_df['bounding_area_m2'].isna()==False],#[grouped_df['genotype'].isin(crit)],
#                            x='date',
#                            y='bounding_area_m2',
#                            color='genotype',
#                            facet_col='treatment',
#                            sort_values=['genotype', 'treatment'],
#                            title='Bounding Area Growth Curves (LOWESS)',
#                            filename='s11_plantgrowth_ww_wl_sig_diff_4',
#                         #    save=True,
#                            frac=1.0)

# scatter_plot_lowess_plotly(df=grouped_df[grouped_df['height'].isna()==False],#[grouped_df['genotype'].isin(crit)],
#                            x='date',
#                            y='height',
#                            color='genotype',
#                            facet_col='treatment',
#                            sort_values=['genotype', 'treatment'],
#                            title='Convex Hull Growth Curves (LOWESS)',
#                            filename='s11_plantgrowth_3d_ww_wl_sig_diff_4',
#                         #    save=True,
#                            frac=1.0)

# scatter_plot_lowess_plotly(df=grouped_df[grouped_df['median'].isna()==False],#[grouped_df['genotype'].isin(crit)],
#                            x='date',
#                            y='median',
#                            color='genotype',
#                            facet_col='treatment',
#                            sort_values=['genotype', 'treatment'],
#                            title='Canopy Temperature Depression',
#                            filename='s11_ctd_ww_wl_sig_diff_4',
#                         #    save=True,
#                            frac=1.0)

## ------------------------------- Bottom half of the streamlit app ----------------------------

## ----------------------------------- Rotating GIFs (static) ----------------------------------


## New Columns
# st.markdown(f"## Season Level Data")

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

