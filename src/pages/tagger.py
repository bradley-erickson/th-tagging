import collections
import dash
from dash import html, dcc, Input, Output, State, callback, ctx, Patch
import dash_bootstrap_components as dbc
import datetime
import flask
import inspect
import json
import random
import string
import uuid

import utils.cards

dash.register_page(
    __name__,
    path='/tagger',
    title='Tagger'
)

_prefix = 'tagger'
_card = f'{_prefix}-card'
_card_image = f'{_card}-image'
_alert = f'{_prefix}-alert'
_submit = f'{_prefix}-submit'
_add = f'{_prefix}-add'
_tags = f'{_prefix}-tags'
_row = f'{_tags}-row'
_verb_select = f'{_tags}-verb-select'
_remove = f'{_tags}-remove'
_dynamic_fields = f'{_tags}-dynamic-fields'
_dynamic_input = f'{_tags}-dynamic-input'
_new_card = f'{_prefix}-new'


VERBS = {
    'search': '{actor} searches {location} for {multiple} {card_types} and adds them to {location}',
    'discard': '{actor} discards {card_types} {multiple} from {location}'
}

NOUNS = {
    'actor': {'component': dbc.Select, 'options': ['you', 'opponent']},
    'location': {'component': dbc.Select, 'options': ['deck', 'discard-pile', 'hand', 'prizes', 'lost-zone', 'in-play']},
    'multiple': {'component': dbc.RadioItems, 'options': ['single', 'multiple']},
    'card_types': {'component': dbc.Select, 'options': ['card', 'pokemon']}
}


def _create_noun_component(id, noun):
    options = {o: o.replace('-', ' ').title() for o in NOUNS[noun]['options']}
    kwargs = {
        'id': id,
        'options': options,
        'class_name': 'w-auto'
    }
    if 'placeholder' in inspect.getfullargspec(NOUNS[noun]['component']).args:
        kwargs['placeholder'] = noun
    component = NOUNS[noun]['component'](**kwargs)
    return component


NOUN_COMPONENTS = {
    noun: lambda id, noun=noun: _create_noun_component(id, noun) for noun in NOUNS
}


def _get_card():
    chosen_card = random.choice(utils.cards.cards)
    return {
        'image_url': chosen_card.images.large,
        'id': chosen_card.id
    }


def _create_input(verb, uid):
    # def extract_variables(fmt_str):
        # return [fn for _, fn, _, _ in Formatter().parse(fmt_str) if fn]

    format_str = VERBS[verb]
    # variables = extract_variables(format_str)
    components = []
    counts = collections.defaultdict(int)

    for part in string.Formatter().parse(format_str):
        literal_text, field_name, _, _ = part

        if literal_text:
            components.append(html.Span(literal_text, className='w-auto mx-1'))

        if field_name:
            counts[field_name] += 1
            unique_id = f'{uid}:{verb}:{field_name}-{counts[field_name]}'
            id = {'type': _dynamic_input, 'index': unique_id}
            component = NOUN_COMPONENTS[field_name](id)
            components.append(component)

    return dbc.Row(components, align='center', class_name='ms')


def _create_verb_dropdown(uid):
    return dbc.Select(
        id={'type': _verb_select, 'index': uid},
        options={o: o.replace('-', ' ').title() for o in VERBS},
        placeholder='Select Action',
    )


def _create_row(uid):
    return dbc.Row([
            dbc.Col([
                _create_verb_dropdown(uid),
                html.Div(id={'type': _dynamic_fields, 'index': uid}, className='ms-5 mt-2'),
            ], lg=11, class_name='mb-3'),
            dbc.Col(
                dbc.Button(
                    html.I(className='fas fa-trash'),
                    id={'type': _remove, 'index': uid},
                    color='danger'),
                lg=1
            ),
            html.Hr()
        ],
        id={'type': _row, 'index': uid}
    )


def layout():
    card = _get_card()
    return html.Div([
        dbc.Alert(id=_alert, is_open=False, duration=3000, fade=True, dismissable=True),
        dbc.Card([
            dbc.CardHeader('Tagger'),
            dbc.CardBody([
                # TODO make the card object json serializable
                dcc.Store(id=_card, data=card),
                html.Img(id=_card_image, src=card['image_url'], style={'width': '20%'}),
                html.Div([
                    _create_row(str(uuid.uuid4()))
                ], id=_tags),
                dbc.Button('Add', id=_add)
            ]),
            dbc.CardFooter([
                dbc.Button('New Card', color='danger', id=_new_card, n_clicks=0),
                dbc.Button('Submit', color='primary', id=_submit, n_clicks=0, class_name='float-end')
            ])
        ])
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
    return _create_input(verb, uid)


@callback(
    Output(_submit, 'disabled'),
    Input({'type': _verb_select, 'index': dash.ALL}, 'value'),
    Input({'type': _dynamic_input, 'index': dash.ALL}, 'value')
)
def _validate_submit(verbs, inputs):
    return not (all(verbs) and all(inputs))


def log_card(data):
    """Append JSON data to log file with timestamp and user"""
    timestamp = datetime.datetime.now().isoformat(timespec='milliseconds')
    username = flask.request.authorization.username if flask.request.authorization else 'anonymous'

    full_record = {
        'timestamp': timestamp,
        'user': username,
        'data': data
    }
    with open('tags.jsonl', 'a') as f:
        f.write(json.dumps(full_record) + '\n')


@callback(
    Output(_alert, 'is_open'),
    Output(_alert, 'color'),
    Output(_alert, 'children'),
    Output(_new_card, 'n_clicks'),
    Input(_submit, 'n_clicks'),
    State({'type': _verb_select, 'index': dash.ALL}, 'value'),
    State({'type': _verb_select, 'index': dash.ALL}, 'id'),
    State({'type': _dynamic_input, 'index': dash.ALL}, 'value'),
    State({'type': _dynamic_input, 'index': dash.ALL}, 'id'),
    State(_card, 'data'),
)
def _submit_tags(n_clicks, verbs, verb_ids, values, value_ids, currentCard):
    if not n_clicks:
        raise dash.exceptions.PreventUpdate

    tags = []
    for verb, id_obj in zip(verbs, verb_ids):
        uid = id_obj['index']
        verb_inputs = {id['index'][id['index'].rfind(':'):]: i for i, id in zip(values, value_ids) if id['index'].startswith(uid)}
        tag = {
            'verb': verb,
            'options': verb_inputs
        }
        tags.append(tag)

    data = {
        'id': currentCard['id'],
        'tags': tags
    }

    log_card(data)

    new_card_patch = Patch()
    new_card_patch += 1
    return True, 'success', 'Successfully saved data', new_card_patch


@callback(
    Output(_card, 'data'),
    Output(_card_image, 'src'),
    Output(_tags, 'children', allow_duplicate=True),
    Input(_new_card, 'n_clicks'),
    prevent_initial_call=True
)
def _reset_data(clicks):
    new_row = [_create_row(str(uuid))]
    new_card = _get_card()
    new_src = new_card['image_url']
    return _get_card(), new_src, new_row
