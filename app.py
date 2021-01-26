import os
import psycopg2
import pandas as pd
import pandas.io.sql as sqlio
import numpy as np
import datetime
import plotly.express as px
import dash
import dash_auth
import dash_table
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

# Keep this out of source code repository - save in a file or a database
VALID_USERNAME_PASSWORD_PAIRS = {
    'marshall': 'ilovecake49!',
    'flip': 'Falcons2!'
}

conn = psycopg2.connect(
    host='ec2-34-236-215-156.compute-1.amazonaws.com',
    port=5432,
    dbname='d9t6p6b3r2ltpn',
    user='dgsdhgvrctjiiz',
    password='97a055b10996937a403c46df5c0f60f36a6c15495db3d5554da5c6fc5d7c4ead'
    )

sql = "select * from aged_inventory;"
invDf = sqlio.read_sql_query(sql, conn)
invDf.columns = ['PRC', 'Part', 'Receipt', 'Bin', 'Primary Bin', 'Loc', 'Bin Qty', 'Bin Cost', 'Bin Ext Value', 'Shelf Qty', 'Created On', 'Date Code', 'Lot Code', 'Receipt Date', 'Written Off']
invDf['Bin Ext Value'] = (invDf['Bin Ext Value'].replace( '[\$,)]','', regex=True ).replace( '[(]','-',   regex=True ).astype(float))
invDf['Receipt Date'] = pd.to_datetime(invDf['Receipt Date'])

sql = "select * from parts;"
partsDf = sqlio.read_sql_query(sql, conn)
partsDf.columns = ['Prcpart', 'Description', 'Active', 'QOH', 'QR', 'QOO', 'Shelf Life', 'Default Cost', 'RoHS', 'Pref Manufacturer', 'Non-Inventory?', 'Std Pack Qty', 'Packaging', 'MSL', 'Created On']

conn = None

# Merge parts info to inventory data
invDf["Prcpart"] = invDf["PRC"].astype(str) + invDf["Part"].astype(str)
mergedDf = invDf.merge(partsDf, how='left', on='Prcpart')
del invDf
del partsDf

# Create list of Dates for range slider
dateRange = mergedDf.copy()
# dateRange = sorted(dateRange['Receipt Date'].dt.to_period("M").unique().strftime('%m-%Y'))
dateRange = sorted(dateRange['Receipt Date'].dt.to_period("M").unique().to_timestamp())

# Create list of Mfgs sorted
mergedDf['Pref Manufacturer'] = mergedDf['Pref Manufacturer'].str.upper()
mfgs = mergedDf['Pref Manufacturer'].unique().tolist()
for i in range(len(mfgs)):
    mfgs[i] = str(mfgs[i])
mfgs = sorted(mfgs)
mfgs = list(dict.fromkeys(mfgs))    # remove duplicates

# Build App
app = dash.Dash(__name__)
auth = dash_auth.BasicAuth(
    app,
    VALID_USERNAME_PASSWORD_PAIRS
)
server = app.server
app.layout = html.Div(
    [
        html.H1("Flip Dashboard"),
        html.H3("Note: Due to database limits, the following data is not correct."),
        html.Div(
            [
                html.Div(
                    [
                        html.P(
                            "Filter by top X MFGs (type value for X)",
                            className="control_label",
                        ),
                        dcc.Input(
                            id='mfgs-top',
                            placeholder='Enter a value...',
                            type='text',
                            value='10',
                            className='dcc_control'
                        ),
                        html.P(
                            "Select MFGs",
                            className="control_label",
                        ),
                        dcc.Dropdown(
                            id='mfgs-dropdown', clearable=False,
                            value=['CYPRESS SEMICONDUCTOR'], multi=True,
                            options=[
                                {'label': m, 'value': m}
                                for m in mfgs
                            ],
                            className='dcc_control'
                        ),
#                         html.P(
#                             "Select Date Range: ",
#                             className="control_label",
#                             id='output-container-range-slider'
#                         ),
#                         dcc.RangeSlider(
#                             id='date-slider',
#                             min=0,
# #                             max=len(dateRange) - 1,
#                             max=44,
# #                             step=None,
# #                             marks={k: v for k, v in enumerate(dateRange)},
# #                             value=[0, len(dateRange) - 1],
#                             value=[0, 44],
#                             updatemode='drag',
# #                             tooltip={'always_visible':False, 'placement':'topLeft'}
# #                             dots=False,
#                             className='dcc_control'
#                         ),
                        html.P(
                            "Select date range (or select range in graph)",
                            className="control_label",
                        ),
                        dcc.DatePickerRange(
                            id='date-picker-range',
                            min_date_allowed=dateRange[0],
                            max_date_allowed=dateRange[len(dateRange) - 1],
                            start_date=dateRange[0],
                            end_date=dateRange[len(dateRange) - 1],
                            display_format='MMM, YY',
                            className='dcc_control'
                        ),
                        html.P(
                            "Total aged inventory (in months)",
                            className="control_label",
                        ),
                        dcc.Input(
                            id='age-input',
                            placeholder='e.g. 6-12',
                            type='text',
                            value='12',
                            className='dcc_control'
                        ),
                    ],
                    id="cross-filter-options",
                    className="pretty_container four columns",
                ),
                html.Div(
                    [dcc.Graph(id="graph")],
#                     id="countGraphContainer",
#                     className="pretty_container",
                    id="right-column",
#                     className="eight columns",
                    className='pretty_container eight columns'
                ),
#                 html.Div(
#                     [
#                         html.Div(
#                             [dcc.Graph(id="graph")],
#                             id="countGraphContainer",
#                             className="pretty_container",
#                         ),
#                     ],
#                     id="right-column",
#                     className="eight columns",
#                 ),
            ],
            className="row flex-display",
        ),
##        html.Div(
##            [
##                html.Div(
##                    [dcc.Graph(id="graph2")],
##                    className='pretty_container six columns'
##                ),
##                html.Div(
##                    [dcc.Graph(id="graph3")],
##                    className='pretty_container six columns'
##                ),
##            ],
##            className="row flex-display",
##        ),
##        html.Div(
##            [
##                html.Div(
##                    [dcc.Graph(id="graph4")],
##                    className='pretty_container twelve columns'
##                ),
##            ],
##            className="row flex-display",
##        ),
    ],
    id="mainContainer",
    style={"display": "flex", "flex-direction": "column"},
)

# Define callback to update mfg dropdown
@app.callback(
    Output('mfgs-dropdown', 'value'),
    [Input("mfgs-top", "value")]
)
def update_mfg_dropdown(top):
    if top != '':
        topMfgs = mergedDf.groupby('Pref Manufacturer').agg({'Bin Ext Value':'sum'}).reset_index().sort_values('Bin Ext Value', ascending=True).tail(int(top))['Pref Manufacturer']
        return topMfgs.tolist()
    else:
        return []

# Define callback to update graph
@app.callback(
    Output('graph', 'figure'),
    [Input("mfgs-dropdown", "value"),
     Input("age-input", "value"),
     Input("date-picker-range", "start_date"),
     Input("date-picker-range", "end_date")]
)
def update_figure(mfg, age, startDate, endDate):
    
    # Total
    totalDf = mergedDf.copy()
    totalDf = totalDf[['Bin Ext Value', 'Receipt Date']]
    totalDf.columns = ['Value', 'Date']
    totalDf['Mfg'] = 'Total'
    totalDf.set_index("Date", inplace=True)
    totalDf.sort_values("Date", inplace=True)
    totalDf = totalDf.groupby([pd.Grouper(freq='M'), 'Mfg']).agg({'Value':'sum'}).cumsum().reset_index()
    
    # Mfg
    mfgDf = mergedDf.loc[mergedDf['Pref Manufacturer'].isin(mfg)]
    mfgDf = mfgDf[['Pref Manufacturer', 'Bin Ext Value', 'Receipt Date']]
    mfgDf.columns = ['Mfg', 'Value', 'Date']
    mfgDf.set_index("Date", inplace=True)
    mfgDf.sort_values("Date", inplace=True)
    mfgDf = mfgDf.groupby([pd.Grouper(freq='M'), 'Mfg']).agg({'Value':'sum'}).groupby('Mfg').cumsum().reset_index()
    
    # Aged
    agedDf = mergedDf.copy()
    agedDf = agedDf[['Bin Ext Value', 'Receipt Date']]
    agedDf.columns = ['Value', 'Date']
    agedDf['Mfg'] = 'Total Aged Inventory'
    agedDf.set_index("Date", inplace=True)
    agedDf.sort_values("Date", inplace=True)
    try:
        agedDf = agedDf.groupby([pd.Grouper(freq='M'), 'Mfg']).agg({'Value':'sum'}).shift(int(age), fill_value=0).cumsum().reset_index()
    except Exception as e:
        print(e)
    
    # Final
    finalDf = pd.concat([totalDf, agedDf, mfgDf], axis=0, ignore_index=True, sort=False)
    finalDf.sort_values('Date', inplace=True)
#     finalDf = finalDf.loc[(finalDf['Date'] > dateRange[date[0]]) & (finalDf['Date'] < dateRange[date[1]])]
    finalDf = finalDf.loc[(finalDf['Date'] > startDate) & (finalDf['Date'] < endDate)]

#     outDateStr = 'Select Date Range: ' + dateRange[date[0]].strftime('%B %Y') + ' to ' + dateRange[date[1]].strftime('%B %Y')

    return px.line(finalDf, x='Date', y='Value', color='Mfg', title='Inventory Trends')

### Define callback to update graph
##@app.callback(
##    Output('graph2', 'figure'),
##    [Input("mfgs-dropdown", "value")]
##)
##def update_figure2(val):
##    df = salesDf.copy()
##
##    #Assign spreadsheet to a dataframe.
##    il = df['Invoiced Lines'].loc[:, ['Customer', 'Invoice Date', 'Inside Sales','Prcpart','Qty','Cost','Ext Cost','Resale','Ext Resale', 'GM', 'Mfg']]
##    il['Profit Margin'] = il['Ext Resale'] - il['Ext Cost']
##    
##    #Sum Profit Margin and create a new dataframe
##    dff = il.groupby('Mfg').agg({'Profit Margin':'sum'}).reset_index()
##    new_df = dff.sort_values(by='Profit Margin',ascending =False)
##
##    #Bar graph of the top 10 manufacturers by profit margin
##    return px.bar(new_df.head(10), x='Mfg' , y='Profit Margin', title='Top 10 Manufacturers by Profit Margin')
##
### Define callback to update graph
##@app.callback(
##    Output('graph3', 'figure'),
##    [Input("mfgs-dropdown", "value")]
##)
##def update_figure3(val):
##    df = salesDf.copy()
##    
##    #Assign spreadsheet to a dataframe.
##    il = df['Invoiced Lines'].loc[:, ['Customer', 'Invoice Date', 'Inside Sales','Prcpart','Qty','Cost','Ext Cost','Resale','Ext Resale', 'GM', 'Mfg']]
##    il['Profit Margin'] = il['Ext Resale'] - il['Ext Cost']
##    
##    #Sort Profit Margin by Inside Sales
##    dfff = il.groupby('Inside Sales').agg({'Profit Margin':'sum'}).reset_index()
##    new_dff = dfff.sort_values(by='Profit Margin',ascending =False)
##    
##    #Bar graph of top 5 Inside Sales by Profit Margin
##    return px.bar(new_dff.head(), x='Inside Sales' , y='Profit Margin', title='Top 5 Inside Sales by Profit Margin')
##
### Define callback to update graph
##@app.callback(
##    Output('graph4', 'figure'),
##    [Input("mfgs-dropdown", "value")]
##)
##def update_figure4(val):
##    df = salesDf.copy()
##
##    #Assign spreadsheet to a dataframe.
##    il = df['Invoiced Lines'].loc[:, ['Customer', 'Invoice Date', 'Inside Sales','Prcpart','Qty','Cost','Ext Cost','Resale','Ext Resale', 'GM', 'Mfg']]
##    il['Profit Margin'] = il['Ext Resale'] - il['Ext Cost']
##    
##    #Sum Profit Margin and create a new dataframe
##    dataframe = il.groupby('Invoice Date').agg({'Profit Margin':'sum'}).reset_index()
##    new_dataframe = dataframe.sort_values(by='Invoice Date',ascending =True)
##
##    #Plotting line graph of Profit Margin characterized by Invoice Date.
##    return px.line(new_dataframe, x='Invoice Date' , y='Profit Margin', title='Daily Total Profit Margin')


if __name__ == '__main__':
    app.run_server(debug=True)
