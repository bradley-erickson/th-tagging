import base64
from dash import html
import dash_bootstrap_components as dbc

logo_black_path = './assets/logo_black.png'
logo_black_tunel = base64.b64encode(open(logo_black_path, 'rb').read())

navbar = dbc.Navbar(dbc.Container(
    dbc.NavbarBrand(
        html.Img(
            height='40px',
            src='data:image/png;base64,{}'.format(logo_black_tunel.decode())
        ),
        href='/'
    )
), color='light')
