import logging
from dash import Dash, html, page_registry, page_container

logging.basicConfig(level=logging.INFO)

if __name__ == '__main__':
    app = Dash(__name__, use_pages=True)
    app.config.suppress_callback_exceptions = True

    app.layout = html.Div([
        html.Nav([
            html.Div([
                html.Ul([
                    html.Li([
                        html.A([page['name']], className='nav-link', href=page['relative_path'])
                    ], className='nav-item')
                ], className='navbar-nav')
            for page in page_registry.values()
            ], className='collapse navbar-collapse')
        ], className='navbar navbar-expand-lg mx-3'),
        page_container
    ])

    app.run_server(debug=True)
