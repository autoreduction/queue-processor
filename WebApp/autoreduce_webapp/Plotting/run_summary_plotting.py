# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #

"""
Plotting run summary reduction job using Plotly
"""

# Dependencies
import numpy as np
import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go


# External styling document - will likely want to change at some point to keep in house
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

"""Generate random numbers and place inside dataframe for plotting."""
# N = 100
# x = np.random.randn(N)
# y = np.random.randn(N)
# z = np.random.randn(N)
# w = np.random.randn(N)

gem = pd.read_csv('GEM-Spectrum1.csv')
gem.columns = ['X', 'Y', 'E']
gem = gem.replace(np.nan, 0.0)
gem = gem.drop(gem.index[0])

#df = pd.DataFrame(list(zip(w, x, y, z)), columns=['w', 'x', 'y', 'z'])




# Plot Styling
app.layout = html.Div([
    dcc.Graph(
        id='random-integers-between-1-2001',

        figure={

            'data': [
                go.Scatter(
                    x=gem['X'],
                    y=gem['Y'],
                    # mode='markers',
                    opacity=0.7,
                    # marker={
                    #     'size': 15,
                    #     'line': {'width': 0.5, 'color': 'white'}
                    # },
                )
            ],
            'layout': go.Layout(
                xaxis={'type': 'log', 'title': 'Spectrum_1 X'},
                yaxis={'title': 'Spectrum_1 Y'},
                margin={'l': 50, 'b': 70, 't': 10, 'r': 10},
                legend={'x': 0, 'x': 1},
                hovermode='closest'
            )
        }
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)



