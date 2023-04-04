from main import data
import dash_bootstrap_components as dbc
from dash import html, dcc, register_page


register_page(__name__, path='/')

layout = html.Div([
    html.H1("League Start Auditor", className='py-3'),
    html.Div([
        dcc.Input(id='pob_input', placeholder="Pastebin/pobb.in Link", type='text', className='form-control'),
    ], className='input-group input-group-lg'),
    html.Div([
        html.H3(id='character_level_ascendancy', className='mt-4'),
        html.Div([
            html.Table(id='offensive_misc_stats_table', className='col-4'),
            html.Table(id='defensive_stats_table', className='col-4'),
            html.Div(id='dps_stats', className='col-4')
        ], className='row align-items-start p-3', style={'margin': 'auto'})
    ]),
    html.Div([
        html.H4(['Uniques']),
        html.Div([
            html.Table(id='unique_price_breakdown', children=[''], className='col-9'),
            html.Div(id='unique_total_cost', className='col-3')
        ], className='row', style={'margin': 'auto'})
    ], className='p-3', style={'display': 'none'}, id='uniques_panel'),
    html.Div([
        dbc.Container([
            dbc.Row([
                dbc.Col(dcc.Dropdown(id='unique_dropdown', style={'display': 'none'})),
                dbc.Col(dcc.Dropdown(id='link_dropdown', style={'display': 'none'}))
            ])
        ])
    ]),
    dcc.Graph(id='unique_price_graph', style={'display': 'none'}),
    html.Div([
        html.H4(['Cluster Jewels']),
        html.Div([
            html.Table(id='cluster_price_breakdown', children=[''], className='col-9'),
            html.Div(id='cluster_total_cost', className='col-3')
        ], className='row', style={'margin': 'auto'})
    ], className='p-3', style={'display': 'none'}, id='clusters_panel'),
    html.Div([
        dbc.Container([
            dbc.Row([
                dbc.Col(dcc.Dropdown(id='cluster_type_dropdown', style={'display': 'none'})),
                dbc.Col(dcc.Dropdown(id='num_passives_dropdown', style={'display': 'none'})),
                dbc.Col(dcc.Dropdown(id='item_level_dropdown', style={'display': 'none'}))
            ])
        ])
    ]),
    dcc.Graph(id='cluster_price_graph', style={'display': 'none'})
], className='m-5 px-5')
