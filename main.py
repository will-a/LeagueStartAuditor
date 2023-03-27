import pandas as pd
from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
import logging

from pobutils import get_pob_code_from_url, get_uniques_from_pob_code

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
        dcc.Input(id='pob_url', placeholder="Pastebin/pobb.in Link", type='text', className='form-control'),
    ], className='input-group input-group-lg'),
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
    Input('pob_url', 'value')
)
def update_page_with_new_build(pob_url: str):
    pob_code = get_pob_code_from_url(pob_url)
    if not pob_code:
        return [], None, [], []
    build_uniques = get_uniques_from_pob_code(pob_code)

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

    return build_uniques, build_uniques[0], price_breakdown, [f"Total cost: {total_cost:0.0f} chaos"]


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
