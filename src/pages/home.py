import dash
from dash import html, dcc

dash.register_page(
    __name__,
    path='/',
    title='Tagging Home',
)

def layout():
    return html.Div([
        html.H1('Home'),
        dcc.Link('Tag card', href='/tagger')
    ])
