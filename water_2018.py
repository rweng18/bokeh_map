###############################################################################
##### IMPORT PACKAGES #########################################################
###############################################################################

import geopandas as gpd
import pandas as pd
import json

from bokeh.io import show
from bokeh.models import (CDSView, ColorBar, ColumnDataSource, CustomJS,
						  CustomJSFilter, GeoJSONDataSource, HoverTool,
						  LinearColorMapper, Slider)
from bokeh.layouts import column, row, widgetbox
from bokeh.palettes import brewer
from bokeh.plotting import figure

from shapely.geometry import Point

###############################################################################
##### LOAD FILES ##############################################################
###############################################################################

contiguous_usa = gpd.read_file('data/cb_2018_us_state_20m.shp')
state_pop = pd.read_csv('data/state_pop_2018.csv')
sites_df = pd.read_csv('data/sites_2018.csv')
lead_samples = pd.read_csv('data/lead_samples_2018.csv')

###############################################################################
##### CLEAN DATA ##############################################################
###############################################################################

# Originally 43,010 sites
sites_subset = sites_df[['MonitoringLocationIdentifier', 'MonitoringLocationName',
                      'MonitoringLocationTypeName', 'LatitudeMeasure',
                      'LongitudeMeasure', 'StateCode', 'CountyCode']]

# After dropping duplicates, 42,975 sites
sites_no_dup = sites_subset.drop_duplicates('MonitoringLocationIdentifier')

# Originally 31,604 data points
lead_tests = lead_samples[['OrganizationIdentifier', 'OrganizationFormalName',
                           'ActivityIdentifier', 'ActivityTypeCode', 'ActivityMediaName', 'ActivityStartDate',
                           'MonitoringLocationIdentifier', 'ProjectIdentifier',
                           'SampleCollectionMethod/MethodIdentifier', 'SampleCollectionMethod/MethodName',
                           'CharacteristicName', 'ResultMeasureValue', 'ResultMeasure/MeasureUnitCode',
                           'ResultStatusIdentifier', 'ResultValueTypeName', 'PrecisionValue',
                           'ResultAnalyticalMethod/MethodIdentifier',
                           'ResultAnalyticalMethod/MethodIdentifierContext', 'ResultAnalyticalMethod/MethodName',
                           'DetectionQuantitationLimitTypeName', 'DetectionQuantitationLimitMeasure/MeasureValue',
                           'DetectionQuantitationLimitMeasure/MeasureUnitCode', 'ProviderName']]

# After dropping n/a 16,637 data points
lead_tests_dropna = lead_tests[pd.notnull(lead_tests['ResultMeasureValue'])]

lead_levels = []
for x in list(lead_tests_dropna['ResultMeasureValue']):
    try:
        lead = float(x)
    except ValueError:
        lead = 'Not precise'
    lead_levels.append(lead)

lead_tests_dropna['LeadValue'] = lead_levels

# Drop where there is no lead_sites, 16,260 data points
lead_found = lead_tests_dropna[lead_tests_dropna['LeadValue'] != 'Not precise']

# Drop where lead was 0 ug/l, 14,934 data points
lead_found = lead_found[lead_found['LeadValue'] > 0]

# Subset where units are ug/l or mg/l, 14,328 data points
lead_per_l = lead_found[lead_found['ResultMeasure/MeasureUnitCode'].isin(['ug/l', 'mg/l'])]

lead_ug_per_l = []
units = list(lead_per_l['ResultMeasure/MeasureUnitCode'])
levels = list(lead_per_l['LeadValue'])
for i in range(0, len(lead_per_l)):
    if units[i] == 'mg/l':
        lead_ug_per_l.append(levels[i] * 1000)
    else:
        lead_ug_per_l.append(levels[i])

lead_per_l['LeadValue_ug_l'] = lead_ug_per_l

###############################################################################
##### MERGE DATA ##############################################################
###############################################################################

pop_states = contiguous_usa.merge(state_pop, left_on = 'NAME', right_on = 'NAME')
lead_sites = lead_per_l.merge(sites_no_dup,
                              left_on = 'MonitoringLocationIdentifier',
                              right_on = 'MonitoringLocationIdentifier')

lead_sites_sorted = lead_sites.sort_values(by = 'ActivityStartDate')

# After dropping duplicates by date, 11,986 data points
lead_sites_dropdup = lead_sites_sorted.drop_duplicates(subset = ['MonitoringLocationIdentifier', 'ActivityStartDate'], keep = 'last').reset_index(drop = True)

# Drop datapoints not in contiguous contiguous_usa, 10,078 data points
lead_sites_dropdup = lead_sites_dropdup[(lead_sites_dropdup['LongitudeMeasure'] <= -60) &
                                        (lead_sites_dropdup['LongitudeMeasure'] >= -130) &
                                        (lead_sites_dropdup['LatitudeMeasure'] <= 50) &
                                        (lead_sites_dropdup['LatitudeMeasure'] >= 20)]

# Create Month column for plotting Slider
lead_sites_dropdup['Month'] = [int(x.split('-')[1]) for x in lead_sites_dropdup['ActivityStartDate']]

# Create shapely.Point objects based on longitude and latitude
geometry = []

for index, row in lead_sites_dropdup.iterrows():
    geometry.append(Point(row['LongitudeMeasure'], row['LatitudeMeasure']))

lead_sites_contig = lead_sites_dropdup.copy()
lead_sites_contig['geometry'] = geometry

# Save to dataframe
lead_sites_contig.to_csv('lead_sites_contig_2018_per_l.csv')

# Drop Alaska and Hawaii
pop_states = pop_states.loc[~pop_states['NAME'].isin(['Alaska', 'Hawaii'])]

# Save as csv
# pop_states.to_csv('contig_us_geometry.csv')

###############################################################################
##### CONVERT TO GEOJSON ######################################################
###############################################################################

# Input GeoJSON source that contains features for plotting
geosource = GeoJSONDataSource(geojson = pop_states.to_json())

# Read dataframe to geodataframe
lead_sites_crs = {'init': 'epsg:4326'}
lead_sites_geo = gpd.GeoDataFrame(lead_sites_contig,
                                  crs = lead_sites_crs,
                                  geometry = lead_sites_contig.geometry)

# Get x and y coordinates
lead_sites_geo['x'] = [geometry.x for geometry in lead_sites_geo['geometry']]
lead_sites_geo['y'] = [geometry.y for geometry in lead_sites_geo['geometry']]
p_df = lead_sites_geo.drop('geometry', axis = 1).copy()

sitesource = ColumnDataSource(p_df)

###############################################################################
##### PLOT MAP ################################################################
###############################################################################

# Define color palettes
palette = brewer['BuGn'][8]
palette = palette[::-1] # reverse order of colors so higher values have darker colors

# Instantiate LinearColorMapper that linearly maps numbers in a range, into a sequence of colors.
color_mapper = LinearColorMapper(palette = palette, low = 0, high = 40000000)

# Define custom tick labels for color bar.
tick_labels = {'0': '0', '5000000': '5,000,000',
               '10000000':'10,000,000', '15000000':'15,000,000',
               '20000000':'20,000,000', '25000000':'25,000,000',
               '30000000':'30,000,000', '35000000':'35,000,000',
               '40000000':'40,000,000+'}

# Create color bar.
color_bar = ColorBar(color_mapper=color_mapper, label_standoff=8,width = 500, height = 20,
                     border_line_color=None,location = (0,0), orientation = 'horizontal',
                     major_label_overrides = tick_labels)

# Create figure object.
p = figure(title = 'Lead Levels in Water Samples, 2018', plot_height = 600 ,
           plot_width = 950, toolbar_location = 'below',
           tools = "pan, wheel_zoom, box_zoom, reset")
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = None

# Add patch renderer to figure.
states = p.patches('xs','ys', source = geosource,
                   fill_color = {'field' :'POPESTIMATE2018', 'transform' : color_mapper},
                   line_color = 'gray', line_width = 0.25, fill_alpha = 1)

# Make a slider object to toggle the month shown
slider = Slider(title = 'Month',start = 1, end = 12, step = 1, value = 1)

# This callback triggers the filter when the slider changes
callback = CustomJS(args=dict(source=sitesource), code="""
    source.change.emit();
""")
slider.js_on_change('value', callback)

# Creates custom filter that selects the rows of the month based on the value in the slider
custom_filter = CustomJSFilter(args=dict(slider=slider, source=sitesource), code='''
var indices = [];
// iterate through rows of data source and see if each satisfies some constraint
for (var i = 0; i < source.get_length(); i++){
    if (source.data['Month'][i] == slider.value){
        indices.push(true);
    } else {
        indices.push(false);
    }
}
return indices;
''')

view = CDSView(source=sitesource, filters=[custom_filter])

# Plots the water sampling sites based on month in slider
sites = p.circle('x', 'y', source = sitesource, color = 'red',
                 size = 5, alpha = 0.3, view = view)

# Create hover tool
p.add_tools(HoverTool(renderers = [states],
                      tooltips = [('State','@NAME'),('Population', '@POPESTIMATE2018')]))
p.add_tools(HoverTool(renderers = [sites],
                      tooltips = [('Organization', '@OrganizationFormalName'),
                                  ('Location Type', '@MonitoringLocationTypeName'),
                                  ('Date', '@ActivityStartDate'),
                                  ('Lead (ug/l)', '@LeadValue_ug_l')]))
# Specify layout
p.add_layout(color_bar, 'below')

# Make a column layout of widgetbox(slider) and plot, and add it to the current document
layout = column(p, widgetbox(slider))

show(layout)
