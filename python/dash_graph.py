"""
Simple example of building a dashboard using Dash

Packages that need to be installed to use this script:
  - dash
  - pandas
"""

from math import cos, sin, pi

import numpy as np
import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output


def empty_figure():
    # {
    #     'data': [{'x': [], 'y': [], 'type': 'line'}],
    #     'layout': {'title': ''}
    # }
    return px.line()


def figure_1():
    countries = ['Australia', 'Bangladesh', 'New Zealand', 'USA', 'Canada', 'United Kingdom']
    population = [25_972_900, 164_700_000, 5_084_000, 331_893_745, 30_010_000, 67_220_000]
    df = pd.DataFrame(list(zip(countries, population)), columns=['Country', 'Population'])
    fig = px.bar(df, x='Country', y='Population', title='Country populations (April 2022)')
    return fig


def figure_2():
    data = np.random.normal(0, 3, size=5000)
    fig = px.histogram(data, title='Normal Distribution', range_x=[-10, 10])
    return fig


def figure_3():
    x_vals = list(range(0, 720))
    data = {
        'sin(x)': [sin(x*pi/180) for x in x_vals],
        'cos(x)': [cos(x*pi/180) for x in x_vals]
    }
    df = pd.DataFrame(data)
    fig = px.line(df, title='Trig functions', labels={'index': 'Degrees', 'value': 'f(x)'})
    fig.update_layout(xaxis={'tickmode': 'linear', 'tick0': 0, 'dtick': 90})
    return fig


FIGURES = dict([
    ('Country populations', figure_1),
    ('Normal distribution', figure_2),
    ('Trig functions', figure_3),
])

app = Dash()

app.layout = html.Div(children=[
    html.H1(children='Building graphs with Dash'),
    html.Div([
        dcc.Dropdown(list(FIGURES.keys()), id='figure-ids')
        ],
        style={'width': '25%'}
    ),
    dcc.Graph(
        id='dash-graph',
        figure=empty_figure()
    )
])


@app.callback(Output(component_id='dash-graph', component_property='figure'),
              Input(component_id='figure-ids', component_property='value'))
def update_output_div(input_value):
    figure_func = FIGURES.get(input_value, empty_figure)
    return figure_func()


if __name__ == '__main__':
    app.run_server(debug=True)
