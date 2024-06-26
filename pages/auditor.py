import os
import logging
import validators
import numpy as np
import pandas as pd
import dash_bootstrap_components as dbc
from dash import html, dcc, register_page, callback, Output, Input
from pobutils import get_pob_code_from_url, read_pob_to_xml, get_uniques_from_xml, get_clusters_from_xml, get_stats_from_xml, load_data

from main import LEAGUE, ROOT_DIR

register_page(__name__, path='/')

if not os.path.isfile(os.path.join(ROOT_DIR, f'data/{LEAGUE}/{LEAGUE}.items.csv')):
    logging.error("Data file not found, exiting...")
    exit(1)

data = load_data(os.path.join(ROOT_DIR, f'data/{LEAGUE}/{LEAGUE}.items.csv'))
try:
    cluster_item_levels = pd.read_csv(os.path.join(ROOT_DIR, f'data/{LEAGUE}/{LEAGUE}.clusterjewels.ids.csv'))
    data = data.merge(cluster_item_levels, on='Id', how='left')
except FileNotFoundError as fnfe:
    logging.error("Could not read from item level CSV file")


def layout():
    return html.Div([
    html.H1("League Start Auditor", className='py-3'),
    html.Div([
        dcc.Input(id='pob_input', placeholder="Pastebin/pobb.in Link", type='text', className='form-control'),
    ], className='input-group input-group-lg'),
    dcc.Loading([
        html.Div([
            html.H4("Could not load build, please ensure the given link or build code is valid", id='error_reading_pob', style={'color': 'red', 'display': 'none'}, className='mt-4')
        ]),
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
    ], type='dot')
], className='m-5 px-5')


@callback([
    Output('unique_dropdown', 'options'),
    Output('unique_dropdown', 'value'),
    Output('cluster_type_dropdown', 'options'),
    Output('cluster_type_dropdown', 'value'),
    Output('unique_price_breakdown', 'children'),
    Output('cluster_price_breakdown', 'children'),
    Output('unique_total_cost', 'children'),
    Output('cluster_total_cost', 'children'),
    Output('character_level_ascendancy', 'children'),
    Output('offensive_misc_stats_table', 'children'),
    Output('defensive_stats_table', 'children'),
    Output('dps_stats', 'children'),
    Input('pob_input', 'value')
])
def update_page_with_new_build(pob_input: str):
    if validators.url(pob_input):
        pob_code = get_pob_code_from_url(pob_input)
        pob_xml = read_pob_to_xml(pob_code)
    else:
        pob_xml = read_pob_to_xml(pob_input)

    if not pob_xml:
        return [], None, [], None, [], [], [], [], [], [], [], []

    build_uniques = get_uniques_from_xml(pob_xml)
    build_clusters = get_clusters_from_xml(pob_xml)

    unique_total_cost_chaos = 0
    unique_dropdown_options = set()
    unique_price_breakdown = [html.Tr([html.Th(['Item']), html.Th(['First price']), html.Th(['First seen']), html.Th(['Week 1 Price'])])]
    for item in build_uniques:
        item_history = data.loc[(data['Name'] == item.name)]
        dates = data.loc[(data['Name'] == item.name), 'Date']
        if dates.size > 0:
            first_date = dates.iloc[0]
            first_price = round(item_history['Value'].iloc[0])
            week1_price = round(item_history.loc[item_history['Date'] == first_date + np.timedelta64(7, 'D'), 'Value'].iloc[0])
            week1_pct_change = (week1_price - first_price) / first_price * 100
            unique_price_breakdown.append(html.Tr([html.Td([item.name]), html.Td([first_price, ' chaos']), html.Td([first_date.strftime('%x')]), html.Td([week1_price, ' chaos (', '{:+0.0f}'.format(week1_pct_change), '%)'])]))
            unique_total_cost_chaos += first_price
            unique_dropdown_options.add(item.name)
        else:
            unique_price_breakdown.append(html.Tr([html.Td([item.name]), html.Td(['No data']), html.Td([]), html.Td([])]))

    unique_dropdown_options = list(unique_dropdown_options) if unique_dropdown_options else None
    unique_dropdown_default = unique_dropdown_options[0] if build_uniques else None
    if unique_total_cost_chaos > 0:
        unique_total_cost = [
            html.H4(['Total cost:']),
            html.H4(['{:0,.0f} chaos'.format(unique_total_cost_chaos)])
        ]
    else:
        unique_total_cost = []

    cluster_price_breakdown = [html.Tr([html.Th(['Item']), html.Th(['First price']), html.Th(['First seen']), html.Th(['Week 1 Price'])])]
    cluster_dropdown_options = set()
    cluster_total_cost_chaos = 0
    for item in build_clusters:
        item_history = data.loc[(data['BaseType'] == item.size) & (data['Variant'] == "{} passives".format(item.num_passives)) & (data['Name'] == item.small_passives)]
        cluster_levels = item_history['ItemLevel'].unique()
        min_ilvl = cluster_levels[cluster_levels < item.level].max()
        item_history = item_history.loc[item_history['ItemLevel'] == min_ilvl]

        item_name = '{}, {}, {} passives, Level {:0.0f}'.format(item.small_passives, item.size, item.num_passives, min_ilvl)
        cluster_dropdown_options.add(item.small_passives)
        if item_history.size > 0:
            first_date = item_history['Date'].iloc[0]
            first_price = round(item_history['Value'].iloc[0])
            week1_price = round(item_history.loc[item_history['Date'] == first_date + np.timedelta64(7, 'D'), 'Value'].iloc[0])
            week1_pct_change = (week1_price - first_price) / first_price * 100
            cluster_price_breakdown.append(html.Tr([html.Td([item_name]), html.Td([first_price, ' chaos']), html.Td([first_date.strftime('%x')]), html.Td([week1_price, ' chaos (', '{:+0.0f}'.format(week1_pct_change), '%)'])]))
            cluster_total_cost_chaos += first_price
        else:
            cluster_price_breakdown.append(html.Tr([html.Td([item_name]), html.Td(['No data']), html.Td([]), html.Td([])]))

    cluster_dropdown_options = list(cluster_dropdown_options)
    cluster_dropdown_options_default = cluster_dropdown_options[0] if cluster_dropdown_options else None
    if cluster_total_cost_chaos > 0:
        cluster_total_cost = [
            html.H4(['Total cost:']),
            html.H4(['{:0,.0f} chaos'.format(cluster_total_cost_chaos)])
        ]
    else:
        cluster_total_cost = []

    character, display_stats = get_stats_from_xml(pob_xml)
    character_level_ascendancy = [f"Level {character.get('level')} {character.get('class')}"]
    offensive_misc_stats_table = []
    defensive_stats_table = []
    
    offensive_misc_stats_table.append(html.Tr([html.Td(['Average Hit: {:0,.0f}'.format(display_stats.get('AverageDamage', display_stats.get('AverageHit', 0)))])]))
    offensive_misc_stats_table.append(html.Tr([html.Td(['Total DPS: {:0,.0f}'.format(display_stats.get('CombinedDPS', 0))])]))
    offensive_misc_stats_table.append(html.Tr([html.Td(['Speed: {:0,.2f}'.format(display_stats.get('Speed', 0))])]))
    offensive_misc_stats_table.append(html.Tr([html.Td(['Crit Chance: {:0.0f}%'.format(display_stats.get('CritChance', 0))])]))
    offensive_misc_stats_table.append(html.Tr([html.Td(['Crit Multiplier: {:0.0f}%'.format(display_stats.get('CritMultiplier', 0) * 100)])]))
    offensive_misc_stats_table.append(html.Tr([html.Td(['Attributes: ', 
                                                        html.Span('{:0.0f}'.format(display_stats.get('Dex', 0)), style={'color': 'green'}), '/', 
                                                        html.Span('{:0.0f}'.format(display_stats.get('Int', 0)), style={'color': 'blue'}), '/',
                                                        html.Span('{:0.0f}'.format(display_stats.get('Str', 0)), style={'color': 'red'})])]))
    offensive_misc_stats_table.append(html.Tr([html.Td(['Charges: ', 
                                                        html.Span('{:0.0f}'.format(display_stats.get('PowerChargesMax', 0)), style={'color': 'blue'}), '/', 
                                                        html.Span('{:0.0f}'.format(display_stats.get('FrenzyChargesMax', 0)), style={'color': 'green'}), '/',
                                                        html.Span('{:0.0f}'.format(display_stats.get('EnduranceChargesMax', 0)), style={'color': 'red'})])]))
    
    defensive_stats_table.append(html.Tr([html.Td(['Total EHP: {:0,.0f}'.format(display_stats.get('TotalEHP', 0))])]))
    defensive_stats_table.append(html.Tr([html.Td(['Life: {:0,.0f}'.format(display_stats.get('Life', 0))])]))
    defensive_stats_table.append(html.Tr([html.Td(['Energy Shield: {:0,.0f}'.format(display_stats.get('EnergyShield', 0))])]))
    defensive_stats_table.append(html.Tr([html.Td(['Armor: {:0,.0f}'.format(display_stats.get('Armour', 0))])]))
    defensive_stats_table.append(html.Tr([html.Td(['Evasion: {:0,.0f}'.format(display_stats.get('Evasion', 0))])]))
    defensive_stats_table.append(html.Tr([html.Td(['Resistances: ', 
                                                        html.Span('{:0.0f}%'.format(display_stats.get('FireResist', 0)), style={'color': 'orange'}), '/', 
                                                        html.Span('{:0.0f}%'.format(display_stats.get('ColdResist', 0)), style={'color': 'blue'}), '/',
                                                        html.Span('{:0.0f}%'.format(display_stats.get('LightningResist', 0)), style={'color': 'yellow'}), '/', 
                                                        html.Span('{:0.0f}%'.format(display_stats.get('ChaosResist', 0)), style={'color': 'purple'})])]))
    defensive_stats_table.append(html.Tr([html.Td(['Spell Suppression: {:0,.0f}%'.format(display_stats.get('SpellSuppressionChance', 0))])]))

    dps_stats = [html.P([ability[0], ': {:0,.0f}'.format(ability[1])], className='mb-2') for ability in character.get('FullDPSSkill', [])]

    return unique_dropdown_options, unique_dropdown_default, cluster_dropdown_options, cluster_dropdown_options_default, unique_price_breakdown, cluster_price_breakdown, unique_total_cost, cluster_total_cost, character_level_ascendancy, offensive_misc_stats_table, defensive_stats_table, dps_stats


@callback(
    Output('link_dropdown', 'options'),
    Output('link_dropdown', 'value'),
    Input('unique_dropdown', 'value')
)
def update_link_dropdown(item_name: str):
    options = data.loc[data['Name'] == item_name, 'Links'].unique()
    if not options.size > 0:
        return [], None
    return options, options[0]


@callback(
    Output('num_passives_dropdown', 'options'),
    Output('num_passives_dropdown', 'value'),
    Input('cluster_type_dropdown', 'value')
)
def update_num_passives_dropdown(cluster_type: str):
    if not cluster_type:
        return [], None
    options = data.loc[data['Name'] == cluster_type, 'Variant'].unique()
    if not options.size > 0:
        return [], None
    return options, options[0]


@callback(
    Output('item_level_dropdown', 'options'),
    Output('item_level_dropdown', 'value'),
    Input('cluster_type_dropdown', 'value')
)
def update_item_level_dropdown(cluster_type: str):
    if not cluster_type:
        return [], None
    options = data.loc[data['Name'] == cluster_type, 'ItemLevel'].unique()
    if not options.size > 0:
        return [], None
    return options, options[0]


@callback(
    Output('unique_price_graph', 'figure'),
    Input('unique_dropdown', 'value'),
    Input('link_dropdown', 'value')
)
def update_unique_price_graph(selected_item: str, selected_links: str):
    filtered_data = data.loc[(data['Name'] == selected_item) & (data['Links'] == selected_links)]
    unique_ids = filtered_data['Id'].unique()
    item_data = []

    for item_id in unique_ids:
        id_x_data = filtered_data.loc[filtered_data['Id'] == item_id]
        id_y_data = filtered_data.loc[filtered_data['Id'] == item_id]
        item_data.append({'x': id_x_data['Date'], 'y': id_y_data['Value']})

    figure = {
        'data': item_data
    }

    return figure


@callback(
    Output('cluster_price_graph', 'figure'),
    Input('cluster_type_dropdown', 'value'),
    Input('num_passives_dropdown', 'value'),
    Input('item_level_dropdown', 'value')
)
def update_cluster_price_graph(selected_type: str, selected_num_passives: str, selected_item_level: float):
    if not selected_type or not selected_num_passives or not selected_item_level:
        return {}
    filtered_data = data.loc[(data['Variant'] == selected_num_passives) & (data['Name'] == selected_type) & (data['ItemLevel'] == selected_item_level)]

    figure = {
        'data': [
            {
                'x': filtered_data['Date'],
                'y': filtered_data['Value']
            }
        ]
    }

    return figure


@callback(
    Output('unique_price_graph', 'style'),
    Output('cluster_price_graph', 'style'),
    Output('unique_dropdown', 'style'),
    Output('link_dropdown', 'style'),
    Output('uniques_panel', 'style'),
    Output('clusters_panel', 'style'),
    Output('cluster_type_dropdown', 'style'),
    Output('num_passives_dropdown', 'style'),
    Output('item_level_dropdown', 'style'),
    Output('error_reading_pob', 'style'),
    Input('unique_price_graph', 'figure'),
    Input('cluster_price_graph', 'figure'),
    Input('unique_dropdown', 'options'),
    Input('link_dropdown', 'options'),
    Input('cluster_type_dropdown', 'options'),
    Input('num_passives_dropdown', 'options'),
    Input('item_level_dropdown', 'options'),
    Input('unique_total_cost', 'children'),
    Input('cluster_total_cost', 'children'),
    Input('pob_input', 'value'),
    Input('character_level_ascendancy', 'children')
)
def update_visibility(unique_price_graph_figure: dict, cluster_price_graph_figure: dict, 
                      unique_dropdown_options: list, link_dropdown_options: list, cluster_type_dropdown_options: list,
                      num_passives_dropdown_options: list, item_level_dropdown_options: list,
                      unique_total_cost_children: list, cluster_total_cost_children: list, pob_input: str,
                      character_level_ascendancy_div: list):
    unique_price_graph_style = {'display': 'block'}
    cluster_price_graph_style = {'display': 'block'}
    unique_dropdown_style = {'display': 'block'}
    link_dropdown_style = {'display': 'block'}
    cluster_type_dropdown_style = {'display': 'block'}
    num_passives_dropdown_style = {'display': 'block'}
    item_level_dropdown_style = {'display': 'block'}
    uniques_panel_style = {'display': 'block'}
    clusters_panel_style = {'display': 'block'}
    error_reading_pob_style = {'color': 'red', 'display': 'block'}

    if not unique_price_graph_figure.get('data', []):
        unique_price_graph_style['display'] = 'none'
    if not cluster_price_graph_figure.get('data', []):
        cluster_price_graph_style['display'] = 'none'
    if not unique_dropdown_options:
        unique_dropdown_style['display'] = 'none'
    if not link_dropdown_options:
        link_dropdown_style['display'] = 'none'
    if not cluster_type_dropdown_options:
        cluster_type_dropdown_style['display'] = 'none'
    if not num_passives_dropdown_options:
        num_passives_dropdown_style['display'] = 'none'
    if not item_level_dropdown_options:
        item_level_dropdown_style['display'] = 'none'
    if not unique_total_cost_children:
        uniques_panel_style['display'] = 'none'
    if not cluster_total_cost_children:
        clusters_panel_style['display'] = 'none'
    if character_level_ascendancy_div or not pob_input:
        error_reading_pob_style['display'] = 'none'

    return unique_price_graph_style, cluster_price_graph_style, unique_dropdown_style, \
            link_dropdown_style, uniques_panel_style, clusters_panel_style, cluster_type_dropdown_style, \
            num_passives_dropdown_style, item_level_dropdown_style, error_reading_pob_style

