import plotly.express as px
import dash_core_components as dcc
import dash_daq as daq
import dash_html_components as html
# import dash_bootstrap_components as dbc

from dash_dual_listbox import DualList
from dash_table import DataTable
from dash_extensions import Download


from app import colors
from app.utils import get_files, matrix_sheet


def refresh():
    return dcc.Interval(id='refresh', interval=5e3)

def quick_refresh():
    return dcc.Interval(id='quick_refresh', interval=1e3)

def markdown(text, plc='center'):
    return dcc.Markdown(children=text,
                        style={
                            'textAlign' : plc
                        }
    )


def com_inputs():
    # options_list = get_devices()
    # options = [{'label': a, 'value': a} for a in options_list]
    options = []
    return html.Div(
        style={'width' : '20%',
               'height': 270,
               'padding': '20px',
               'marginRight': 5,
               'float': 'left',
               'backgroundColor': colors['background'],
               'borderStyle': 'solid',
               'borderColor': '#616161'},
        children=[
            html.Label("Tone Generator"),
            dcc.Dropdown(
                id='tone_com',
                options=options,
                persistence=True
            ),
            html.Br(),
            html.Label("Power Supply"),
            dcc.Dropdown(
                id='power_com',
                options=options,
                persistence=True
            ),
            html.Br(),
            html.Div(style={'display': 'flex'}, children=[
                html.Button('Connect', id='connect', n_clicks=0),
                daq.Indicator(id='connection_statusT', color=colors['off'], value=True,
                              style={'marginLeft': 10, 'marginTop': 10}),
                daq.Indicator(id='connection_statusP', color=colors['off'], value=True,
                              style={'marginLeft': 10, 'marginTop': 10})
                ]
            ),
            html.Div(id='connect_container',
                     children=''),
            html.Div(id='com_inputs')
        ]
    )


def temp_options():
    types = [{'label' : 'Type K', 'value' : 'K'},
             {'label' : 'Type J', 'value' : 'J'},
             {'label' : 'Type N', 'value' : 'N'}]
    res = [{'label': '300 ms', 'value': 18},
           {'label': '80 ms',  'value': 16},
           {'label': '20 ms',  'value': 14},
           {'label': '5 ms',   'value' : 12}]
    return html.Div(
        style={
                'width': '20%',
                'height': 270,
                # 'float': 'left',
                'display': 'inline-block',
                'backgroundColor': colors['background'],
                'padding': '20px',
                'marginLeft': 5,
                'marginRight': 5,
                'borderStyle': 'solid',
                'borderColor': '#616161'
               },
        children=[
            html.Label("Thermocouple type"),
            dcc.Dropdown(
                id='tc_type',
                options=types,
                value='K'
            ),
            html.Br(),
            html.Label("Sampling rate"),
            dcc.Dropdown(
                id='tc_rate',
                options=res,
                value=14
            )
        ]
    )


def graph():
    return html.Div(
        style={
            'width': '50%',
            'height': 270,
            'padding': '20px',
            'float': 'right',
            'textAlign': 'center',
            'borderStyle': 'solid'
        },
        children=[
            html.H1("PLACEHOLDER FOR GRAPH")
        ]
    )


def tabs():
    return html.Div(
        style={
            'width': '40%',
            'height': 290,
            'float': 'left',
            # 'padding': '20px',
            'marginTop': '20px',
            'paddingLeft': '0px',
            'borderStyle': 'solid',
            'borderColor': '#616161'
        },
        children=[
            dcc.Tabs(id='main_tabs', value='tab_1',
                     children=[
                         dcc.Tab(label="Tuning", value='tab_1'),
                         dcc.Tab(label="Exposure", value='tab_2')
                ]
            ),
            html.Div(id='tab_content')
        ]
    )


def tuning():
    coils=[
        {'label': '9 Turns', 'value': 9},
        {'label': '17 Turns', 'value': 17},
        {'label': '18 Turns', 'value': 18}
    ]
    cap=[
        {'label': '6.2 nF', 'value': 6.2},
        {'label': '15 nF', 'value': 15},
        {'label': '26 nF', 'value': 26},
        {'label': '88 nF', 'value': 88},
        {'label': '200 nF', 'value': 200},
    ]
    return html.Div(
        style={
            'width': '100%'
        },
        children=[
            dcc.ConfirmDialog(
                id='confirm_tuning',
                message='Make sure that the correct capacitor and coil is chosen!',
            ),
            html.Div(
                style={
                    'width': '20%',
                    'padding': '20px',
                    'float': 'left',
                    # 'display': 'inline-block'
                },
                children=[
                    html.Label("Choose Coil Type"),
                    dcc.Dropdown(id='coil_type', options=coils,
                                 value=18, persistence=True),
                    html.Br(),
                    html.Label("Choose Capacitor"),
                    dcc.Dropdown(id='cap_type', options=cap,
                                 value=6.2, persistence=True),
                ]
            ),
            html.Div(
                style={
                    'width': '30%',
                    'display': 'inline-block',
                    'padding': '20px',
                },
                children=[
                    html.Label("Frequency Range [kHz]"),
                    dcc.Input(
                        id="freq_low", type='number', placeholder='',
                        style={'width': '100px'}, persistence=True
                    ),
                    dcc.Input(
                        id="freq_high", type='number', placeholder='',
                        style={'width': '100px'}, persistence=True
                    ),
                    html.Br(), html.Br(), html.Br(),
                    html.Button("Tune", id="tune_button", style={'width': '200px'},
                                n_clicks=0),
                    dcc.Loading(
                        id="tuning",
                        children=[html.Div(id='tune_div')],
                        type="circle",
                    )
                ]
            ),
            # dcc.Markdown("""#### Tuning the Magnetherm\nSelect the correct coil and capacitor values.
            # The frequency range is automatically chosen based on the expected resonance frequency.
            # If the sample alters the resonance frequency out of the range, it is necessary to manually set the range.""",
            #              style={'width': '40%', 'display': 'inline-block', 'marginLeft': '20px'})
        ],
    )


def exposure():
    return html.Div(
        style={
            'width': '100%'
        },
        children=[
            dcc.ConfirmDialog(
                id='confirm_exposure',
                message='Sure you want to expose?',
            ),
            html.Div(
                style={
                    'width': '30%',
                    'float': 'left',
                    'padding': '20px',
                },
                children=[
                    html.Label("Power Supply Current [A]"),
                    dcc.Input(
                        id="exp_current", type='number', placeholder='',
                        style={'width': '200px'}, persistence=True
                    ),
                    html.Br(), html.Br(),
                    html.Label("Exposure Time [s]"),
                    dcc.Input(
                        id="exp_time", type='number', placeholder='',
                        style={'width': '200px'}, persistence=True
                    ),
                    html.Br(), html.Br(),
                ]
            ),
            html.Div(
                style={'width': '30%',
                        'display': 'inline-block',
                        'padding': '20px',
                        },
                children=[
                    html.Label("Exposure Field [mT]"),
                    dcc.Input(
                        id="exp_field", type='number', placeholder='',
                        style={'width': '200px'}, persistence=True
                    ),
                    html.Br(), html.Br(), html.Br(),
                    html.Button("Start", id="exp_button", style={'width': '200px'},
                                n_clicks=0),
                    # dbc.Progress(id="progress_expose", value=0, striped=True, animated=True),
                    dcc.Loading(
                        id="exposing",
                        children=[html.Div(id='expose_div')],
                        type="circle",
                    )
                ]
            )
        ],
    )


def files_list():
    data = get_files()
    return html.Div(
        style={
            'width': '95%',
            'height': '95%',
            'float': 'right',
            'marginRight': 20
        },
        children=[
            DataTable(
                id='files_list', columns=[{'name': 'Filename', 'id': 'Filename'},
                                          {'name': 'Filesize', 'id': 'Filesize'},
                                          {'name': 'Last Modified', 'id': 'Last Modified'},
                                          {'name': 'File Created', 'id': 'File Created'}],
                data=data,
                style_cell={'textAlign': 'center'},
                style_header={
                    'textAlign': 'center',
                    'fontWeight': 'bold',
                    'fontSize': 12
                },
                page_size=20,
                style_cell_conditional=[
                    {'if': {'column_id': 'Filename'},
                     'width': '45%'},
                    {'if': {'column_id': 'Last Modified'},
                     'width': '20%'},
                    {'if': {'column_id': 'File Created'},
                     'width': '20%'},
                    {'if': {'column_id': 'Filesize'},
                     'width': '10%'},
                ],
                filter_action="native",
                sort_action="native",
                sort_mode="multi",
                row_selectable="multi"
            ),
            html.Br(),
            html.Button("Download", id="download_button", n_clicks=0),
            Download(id="download"),
            dcc.Loading(id="dl_loading", children=html.Div(id="dl_loading_output"))
        ]
    )
