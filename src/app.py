import dash
from dash import html
import dash_bootstrap_components as dbc

from components import navbar

dbc_css = ("https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates@V1.0.2/dbc.min.css")

app = dash.Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[
        dbc_css,
        dbc.themes.FLATLY,
        'https://use.fontawesome.com/releases/v6.7.2/css/all.css',
    ],
    meta_tags=[
        {
            'name': 'viewport',
            'content': 'width=device-width, initial-scale=1'
        }
    ],
    suppress_callback_exceptions=True,
    title='TH - Tagger',
)


def serve_layout():
    return html.Div(
        [
            navbar.navbar,
            dbc.Container(
               html.Div(dash.page_container, className='my-1'),
               class_name='page-container'
            )
        ],
        className='dbc app'
    )


app.layout = serve_layout
server = app.server

if __name__ == "__main__":
    app.run_server(debug=True)
