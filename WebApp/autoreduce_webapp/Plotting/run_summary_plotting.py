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
import plotly.express as px
import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go


# External styling document - will likely want to change at some point to keep in house
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

"""Generate random numbers and place inside dataframe for plotting."""
N = 100
x = np.random.randn(N)
y = np.random.randn(N)
z = np.random.randn(N)
w = np.random.randn(N)

df = pd.DataFrame(list(zip(w, x, y, z)), columns=['w', 'x', 'y', 'z'])


# Plot Styling
app.layout = html.Div([
    dcc.Graph(
        id='random-integers-between-1-2001',
        figure={

            'data': [
                go.Scatter(
                    x=df['x'],
                    y=df['y'],
                    mode='markers',
                    opacity=0.7,
                    marker={
                        'size': 15,
                        'line': {'width': 0.5, 'color': 'white'}
                    },
                )
            ],
            'layout': go.Layout(
                xaxis={'type': 'log', 'title': 'random x values'},
                yaxis={'title': 'random y values'},
                margin={'l': 100, 'b': 100, 't': 20, 'r': 20},
                legend={'x': 0, 'y': 1},
                hovermode='closest'
            )
        }
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)



