import dash
from collections import defaultdict
from dash import html, Input, Output, State, callback, ctx, no_update, Patch, ALL
from string import Formatter
import dash_bootstrap_components as dbc
import uuid

dash.register_page(
    __name__,
    path='/tagger',
    title='Tagger'
)

_prefix = 'tagger'
_submit = f'{_prefix}-submit'
_add = f'{_prefix}-add'
_tags = f'{_prefix}-tags'
_row = f'{_tags}-row'
_verb_select = f'{_tags}-verb-select'
_remove = f'{_tags}-remove'
_dynamic_fields = f'{_tags}-dynamic-fields'
_dynamic_input = f'{_tags}-dynamic-input'


VERBS = {
    'Search': '{actor} searches {location} for {multiple} card_types and adds them to {location}.'
}

NOUNS = {
    'actor': {'component': dbc.Select, 'options': ['you', 'opponent']},
    'location': {'component': dbc.Select, 'options': ['deck', 'discard-pile', 'hand', 'prizes', 'lost-zone', 'in-play']},
    'multiple': {'component': dbc.RadioItems, 'options': ['single', 'multiple']}
}


def _create_noun_component(id, noun):
    options = {o: o.replace('-', ' ').title() for o in NOUNS[noun]['options']}
    return NOUNS[noun]['component'](id=id, options=options, class_name='')


NOUN_COMPONENTS = {
    noun: lambda id, noun=noun: _create_noun_component(id, noun) for noun in NOUNS
}


def _get_card():
    return {}


def _create_input(verb, uid):
    def extract_variables(fmt_str):
        return [fn for _, fn, _, _ in Formatter().parse(fmt_str) if fn]

    format_str = VERBS[verb]
    variables = extract_variables(format_str)
    components = []
    counts = defaultdict(int)
    
    for part in Formatter().parse(format_str):
        literal_text, field_name, _, _ = part
        
        if literal_text:
            components.append(html.Span(literal_text))
            
        if field_name:
            counts[field_name] += 1
            unique_id = f'{uid}-{field_name}-{counts[field_name]}'
            id = {'type': _dynamic_input, 'index': unique_id}
            component = NOUN_COMPONENTS[field_name](id)
            components.append(component)
    
    return html.Div(components, style={'margin': '10px 0'})


def _create_verb_dropdown(uid):
    return dbc.Col([
        dbc.Select(
            id={'type': _verb_select, 'index': uid},
            options=[{'label': v, 'value': v} for v in VERBS.keys()],
            placeholder='Select Verb',
        )
    ])


def _create_row(uid):
    return dbc.Row(
        children=[
            _create_verb_dropdown(uid),
            html.Div(id={'type': _dynamic_fields, 'index': uid}),
            dbc.Button(html.I(className='fas fa-close'), id={'type': _remove, 'index': uid})
        ],
        id={'type': _row, 'index': uid},
        className='mb-3'
    )


def layout():
    card = _get_card()
    return dbc.Card([
        dbc.CardHeader('Tagger'),
        dbc.CardBody([
            html.Img(),
            html.Div([
                _create_row(str(uuid.uuid4()))
            ], id=_tags),
            dbc.Button('Add', id=_add)
        ]),
        dbc.CardFooter(
            dbc.Button('Submit', color='primary', id=_submit, n_clicks=0, class_name='float-end')
        )
    ], id=_prefix)


@callback(
    Output(_tags, 'children'),
    Input(_add, 'n_clicks'),
)
def _add_row(clicks):
    if not clicks:
        raise dash.exceptions.PreventUpdate
    patch = Patch()
    patch.append(_create_row(str(uuid.uuid4())))
    return patch


@callback(
    Output(_tags, 'children', allow_duplicate=True),
    Input({'type': _remove, 'index': dash.ALL}, 'n_clicks'),
    State(_tags, 'children'),
    prevent_initial_call=True
)
def _remove_row(clicks, current_children):
    triggered_id = ctx.triggered_id['index']
    match_index = next((i for i, child in enumerate(current_children) if child['props']['id']['index'] == triggered_id), None)
    if match_index is None or not clicks[match_index]:
        raise dash.exceptions.PreventUpdate
    patch = Patch()
    del patch[match_index]
    return patch


@callback(
    Output({'type': _dynamic_fields, 'index': dash.MATCH}, 'children'),
    Input({'type': _verb_select, 'index': dash.MATCH}, 'value'),
    State({'type': _dynamic_fields, 'index': dash.MATCH}, 'id'),
    prevent_initial_call=True
)
def _update_inputs(verb, uid_dict):
    if not verb:
        return []
    uid = uid_dict['index']
    return [_create_input(verb, uid)]


@callback(
    Output(_submit, 'disabled'),
    Input({'type': _verb_select, 'index': dash.ALL}, 'value'),
    Input({'type': _dynamic_input, 'index': dash.ALL}, 'value')
)
def _validate_submit(verbs, inputs):
    return not (all(verbs) and all(inputs))
