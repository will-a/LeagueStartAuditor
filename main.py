import pandas as pd
import numpy as np
from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
import logging

from pobutils import read_pob_to_xml, get_pob_code_from_url, get_stats_from_xml, get_uniques_from_xml

logging.basicConfig(level=logging.INFO)


def load_data(file_name: str) -> pd.DataFrame:
    try:
        return pd.read_csv(file_name, delimiter=';', parse_dates=['Date'])
    except FileNotFoundError:
        return pd.DataFrame()


data = load_data('data/Kalandra/Kalandra.items.csv')
data['Links'].fillna('None', inplace=True)
app = Dash(__name__)

app.layout = html.Div([
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
        html.Table(id='price_breakdown', children=[''], className='col-9'),
        html.Div(id='total_cost', className='col')
    ], className='row p-3', style={'margin': 'auto'}),
    html.Div([
        dbc.Container([
            dbc.Row([
                dbc.Col(dcc.Dropdown(id='item_dropdown', style={'display': 'none'})),
                dbc.Col(dcc.Dropdown(id='link_dropdown', style={'display': 'none'}))
            ])
        ])
    ]),
    dcc.Graph(id='price_graph', style={'display': 'none'})
], className='m-5 px-5')


@app.callback(
    Output('item_dropdown', 'options'),
    Output('item_dropdown', 'value'),
    Output('price_breakdown', 'children'),
    Output('total_cost', 'children'),
    Output('character_level_ascendancy', 'children'),
    Output('offensive_misc_stats_table', 'children'),
    Output('defensive_stats_table', 'children'),
    Output('dps_stats', 'children'),
    Input('pob_input', 'value')
)
def update_page_with_new_build(pob_input: str):
    pob_code = get_pob_code_from_url(pob_input)
    if not pob_code:
        pob_xml = read_pob_to_xml(pob_input)
        if not pob_xml:
            return [], None, [], [], [], [], [], []
    else:
        pob_xml = read_pob_to_xml(pob_code)

    build_uniques = get_uniques_from_xml(pob_xml)

    total_cost_chaos = 0
    price_breakdown = [html.Tr([html.Th(['Item']), html.Th(['First price']), html.Th(['First seen']), html.Th(['Week 1 Price'])])]
    for item in build_uniques:
        item_values = data.loc[(data['Name'] == item)]
        first_date_df = data.loc[(data['Name'] == item), 'Date']
        if first_date_df.size > 0:
            first_date = first_date_df.iloc[0]
            first_price = round(item_values['Value'].iloc[0])
            week1_price = round(item_values.loc[item_values['Date'] == first_date + np.timedelta64(7, 'D'), 'Value'].iloc[0])
            week1_pct_change = (week1_price - first_price) / first_price * 100
            price_breakdown.append(html.Tr([html.Td([item]), html.Td([first_price, ' chaos']), html.Td([first_date.strftime('%x')]), html.Td([week1_price, ' chaos (', '{:+0.0f}'.format(week1_pct_change), '%)'])]))
        else:
            first_price = 0
            price_breakdown.append(html.Tr([html.Td([item]), html.Td(['No data']), html.Td([]), html.Td([])]))

        total_cost_chaos += first_price
    
    total_cost = [
        html.H4(['Total cost:']),
        html.H4(['{:0,.0f} chaos'.format(total_cost_chaos)])
    ]

    character, display_stats = get_stats_from_xml(pob_xml)
    character_level_ascendancy = [f"Level {character.get('level')} {character.get('class')}"]
    offensive_misc_stats_table = []
    defensive_stats_table = []
    
    offensive_misc_stats_table.append(html.Tr([html.Td(['Average Hit: {:0,.0f}'.format(display_stats.get('AverageDamage', 0))])]))
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

    return build_uniques, build_uniques[0], price_breakdown, total_cost, character_level_ascendancy, offensive_misc_stats_table, defensive_stats_table, dps_stats


@app.callback(
    Output('link_dropdown', 'options'),
    Output('link_dropdown', 'value'),
    Input('item_dropdown', 'value')
)
def update_link_dropdown(item_name: str):
    options = data.loc[data['Name'] == item_name, 'Links'].unique()
    if not options.size > 0:
        return [], None
    return options, options[0]


@app.callback(
    Output('price_graph', 'figure'),
    Input('item_dropdown', 'value'),
    Input('link_dropdown', 'value')
)
def update_price_graph(selected_item: str, selected_links: str):
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


@app.callback(
    Output('price_graph', 'style'),
    Output('item_dropdown', 'style'),
    Output('link_dropdown', 'style'),
    Input('price_graph', 'figure'),
    Input('item_dropdown', 'options'),
    Input('link_dropdown', 'options')
)
def update_visibility(price_graph_figure: dict, item_dropdown_options: list, link_dropdown_options: list):
    price_graph_style = {'display': 'block'}
    item_dropdown_style = {'display': 'block'}
    link_dropdown_style = {'display': 'block'}

    if not price_graph_figure.get('data', []):
        price_graph_style = {'display': 'none'}
    if not item_dropdown_options:
        item_dropdown_style = {'display': 'none'}
    if not item_dropdown_options:
        link_dropdown_style = {'display': 'none'}
    
    return price_graph_style, item_dropdown_style, link_dropdown_style


if __name__ == '__main__':
    app.run_server(debug=True)
