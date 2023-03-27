import pandas as pd
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
data['Date'] = data['Date'].dt.date
data['Links'].fillna('None', inplace=True)
app = Dash(__name__)

app.layout = html.Div([
    html.H1("League Start Auditor", className='py-3'),
    html.Div([
        dcc.Input(id='pob_input', placeholder="Pastebin/pobb.in Link", type='text', className='form-control'),
    ], className='input-group input-group-lg'),
    html.Br(),
    html.Div([
        html.H3(id='character_level_ascendancy'),
        html.Div([
            html.Table(id='offensive_misc_stats_table', className='col-4'),
            html.Table(id='defensive_stats_table', className='col-4'),
        ], className='row p-3', style={'margin': 'auto'})
    ]),
    html.Br(),
    html.Div([
        html.Table(id='price_breakdown', children=[''], className='col-8'),
        html.H3(id='total_cost', className='col')
    ], className='row p-3', style={'margin': 'auto'}),
    html.Div([
        dbc.Container([
            dbc.Row([
                dbc.Col(dcc.Dropdown(id='item_dropdown')),
                dbc.Col(dcc.Dropdown(id='link_dropdown'))
            ])
        ])
    ]),
    dcc.Graph(id='price_graph')
], className='m-5 px-5')


@app.callback(
    Output('item_dropdown', 'options'),
    Output('item_dropdown', 'value'),
    Output('price_breakdown', 'children'),
    Output('total_cost', 'children'),
    Output('character_level_ascendancy', 'children'),
    Output('offensive_misc_stats_table', 'children'),
    Output('defensive_stats_table', 'children'),
    Input('pob_input', 'value')
)
def update_page_with_new_build(pob_input: str):
    pob_code = get_pob_code_from_url(pob_input)
    if not pob_code:
        pob_xml = read_pob_to_xml(pob_input)
        if not pob_xml:
            return [], None, [], [], [], [], []
    else:
        pob_xml = read_pob_to_xml(pob_code)

    build_uniques = get_uniques_from_xml(pob_xml)
    total_cost = 0
    price_breakdown = [html.Tr([html.Th(['Item']), html.Th(['First price (chaos)']), html.Th(['First seen'])])]
    for item in build_uniques:
        first_price = round(data.loc[(data['Name'] == item), 'Value'])
        first_date = data.loc[(data['Name'] == item), 'Date']
        if first_price.size > 0:
            price_breakdown.append(html.Tr([html.Td([item]), html.Td([first_price.iloc[0], ' chaos']), html.Td([first_date.iloc[0]])]))
            total_cost += first_price.iloc[0]
        else:
            price_breakdown.append(html.Tr([html.Td([item]), html.Td(['did not exist'])]))
    
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


    return build_uniques, build_uniques[0], price_breakdown, [f"Total cost: {total_cost:0.0f} chaos"], character_level_ascendancy, offensive_misc_stats_table, defensive_stats_table


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


if __name__ == '__main__':
    app.run_server(debug=True)
