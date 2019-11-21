# Project: Interactive Map Basics Using bokeh and GeoPandas

## Goal
* Build an interactive map using bokeh and GeoPandas packages in Python

## Method
* Use water quality data, specifically regarding positive lead levels measured in ug/l, and state population for 2018 to create an interactive map

## Data
* [Census Bureau](https://www.census.gov/geographies/mapping-files/time-series/geo/carto-boundary-file.html)
  * Shapefile for geometry describing the contiguous US States
  * 2018 state population estimates
* [Water Quality Data](https://www.waterqualitydata.us/)
  * Locations of water testing sites throughout the contiguous US for 2018
  * Lead test results from all sites throughout the contiguous US in 2018
  
## Documents
* [Walkthrough: Mapping Basics with bokeh and GeoPandas in Python](https://towardsdatascience.com/walkthrough-mapping-basics-with-bokeh-and-geopandas-in-python-43f40aa5b7e9)
  * A Medium post I wrote that was picked up by *Towards Data Science* that explains in prose why and how I created the map
  * Includes links to resources that I used and found along the way
* map_builder_notebook.ipynb
  * Jupyter Notebook version of code for more line-by-line understanding of how the code functions
  * Breaks down according to Medium blog post (basic to more complex map)
* map_builder_script.py
  * Script that creates the map
  * Depends on various packages including GeoPandas and bokeh
      * Recommended: conda installation (see blog post)
