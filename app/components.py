import plotly.express as px
from dash import dcc, html
import dash_daq as daq
# import dash_bootstrap_components as dbc

from dash_dual_listbox import DualList
from dash.dash_table import DataTable

from app import colors
from app.utils import get_files, get_devices

from datetime import datetime

# def refresh():
#     return dcc.Interval(id='refresh', interval=5e3)
#
# def quick_refresh():
#     return dcc.Interval(id='quick_refresh', interval=1e3)

# def tune_interval():
#     return dcc.Interval(id='tune_interval', interval=1e3)

# def exp_interval():
#     return dcc.Interval(id='exp_interval', interval=1e3, disabled=True)

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
    sensors = [{'label': 'Thermocouple', 'value': 'TC'},
               {'label': 'Optical Fiber', 'value': 'OFT'}]
    return html.Div(
        style={
            'width': '20%',
            'height': 290,
            # 'float': 'left',
            'display': 'inline-block',
            'backgroundColor': colors['background'],
            # 'padding': '20px',
            # 'marginLeft': 5,
            # 'marginRight': 5,
            # 'borderStyle': 'solid',
            # 'borderColor': '#616161'
               },
        children=[
            html.Div(
                style={
                    'borderStyle': 'solid',
                    'borderColor': '#616161',
                    'padding': '20px',
                    'marginLeft': 5,
                    'marginRight': 5,
                    'height': 180,
                },
                children=[
                    html.Label("Temperature Sensor"),
                    dcc.Dropdown(
                        id='t_sensor',
                        options=sensors
                    ),
                    html.Div(
                        children=[],
                        id = 'temp_div'
                    )
                ]
            ),
            html.Div(
                style={
                    'borderStyle': 'solid',
                    'borderColor': '#616161',
                    'padding': '20px',
                    'marginLeft': 5,
                    'marginRight': 5,
                    'height': 45
                },
                children=[
                    html.Label("Filename (.txt)"),
                    dcc.Input(id='filename-input', value=datetime.now().strftime('%Y-%m-%d'),
                              debounce=True, style={'width': '90%'})
                ]
            )
        ]
    )


def thermo_div():
    types = [{'label': 'Type K', 'value': 'K'},
             {'label': 'Type J', 'value': 'J'},
             {'label': 'Type N', 'value': 'N'},
             {'label': 'Type R', 'value': 'R'}]
    res = [{'label': '300 ms', 'value': 18},
           {'label': '80 ms',  'value': 16},
           {'label': '20 ms',  'value': 14},
           {'label': '5 ms',   'value' : 12}]
    return [html.Label("Thermocouple type"),
            dcc.Dropdown(
                id='tc_type',
                options=types,
                value='N'
            )]


def fiber_div():
    options_list = get_devices()
    options = [{'label': a, 'value': a} for a in options_list]
    return [html.Br(),
            html.Label("Choose USB port"),
            dcc.Dropdown(
                id='fiber_com',
                options=options,
                value='N'
            ),
            html.Button('Connect', id='fiber_connect'),
            html.Div(children='', id='fiber_connect_div')]

def graph():
    return html.Div(
        id='graph_div',
        style={
            'width': '50%',
            'height': 740,
            'padding': '20px',
            'float': 'right',
            'textAlign': 'center',
        },
        children=[
            dcc.Interval(id='tune_interval', interval=1000, n_intervals=0, max_intervals=0),
            dcc.Interval(id='exp_interval', interval=1000, n_intervals=0, max_intervals=0),
            dcc.Graph(id='tune_graph', animate=False, style={'height': 315}),
            html.Br(),
            dcc.Graph(id='exp_graph',  animate=False, style={'height': 315})
        ]
    )

def stop():
    return html.Button('STOP', id='stop_button',
                       style={'background-color': 'red',
                              'height': '50px',
                              'width': '100px',
                              'font-weight': 'bold',
                              })

def tabs():
    return html.Div(
        style={
            'width': '40%',
            'height': 400,
            'float': 'left',
            # 'padding': '20px',
            'marginTop': '20px',
            'paddingLeft': '0px',
            'borderStyle': 'solid',
            'borderColor': '#616161'
        },
        children=[
            dcc.Store(id='configuration', storage_type='session'),
            dcc.Tabs(id='main_tabs', value='tab_1',
                     children=[
                         dcc.Tab(label="Tuning", value='tab_1', children=tuning()),
                         dcc.Tab(label="Exposure", value='tab_2', children=exposure()),
                         dcc.Tab(label="Temperature", value='tab_3', children=temperature_exp())
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
        {'label': '6.2 nF', 'value': '6.2 nF'},
        {'label': '15 nF', 'value': '15 nF'},
        {'label': '26 nF', 'value': '26 nF'},
        {'label': '88 nF', 'value': '88 nF'},
        {'label': '200 nF', 'value': '200 nF'},
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
                                 value=18, persistence=True, clearable=False),
                    html.Br(),
                    html.Label("Choose Capacitor"),
                    dcc.Dropdown(id='cap_type', options=cap,
                                 value='6.2 nF', persistence=True, clearable=False),
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
                                n_clicks=0, disabled=False),
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
            'width': '100%',
        },
        children=[
            dcc.ConfirmDialog(
                id='confirm_exposure_exp',
                message='Sure you want to expose?',
            ),
            html.Div(
                style={
                    'width': '25%',
                    # 'float': 'left',
                    'display': 'inline-block',
                    'padding': '20px',
                },
                children=[
                    html.Label("Power Supply Current [A]"),
                    dcc.Input(
                        id="exp_current", type='number', placeholder='',
                        style={'width': '100%'}, persistence=True, value=0, debounce=True
                    ),
                    html.Br(), html.Br(),
                    html.Label("Exposure Field [mT]"),
                    dcc.Input(
                        id="exp_field", type='number',
                        style={'width': '100%'}, persistence=True, value=0, debounce=True
                    ),
                    html.Br(), html.Br(),
                    html.Label("dt [s]"),
                    dcc.Input(
                        id="sample_rate", type='number',
                        style={'width': '100%'}, persistence=True, value=0, debounce=True
                    ),
                    html.Br(), html.Br(),
                ]
            ),
            html.Div(
                style={'width': '25%',
                       'display': 'inline-block',
                       'padding': '20px',
                       },
                children=[
                    html.Label("Record Before [s]"),
                    dcc.Input(
                        id="rec_before", type='number',
                        style={'width': '100%'}, persistence=True, value=30
                    ),
                    html.Br(), html.Br(),
                    html.Label("Record After [s]"),
                    dcc.Input(
                        id="rec_after", type='number', placeholder='',
                        style={'width': '100%'}, persistence=True, value=60
                    ),
                    html.Br(), html.Br(),
                    html.Label('Number of Steps'),
                    dcc.Input(
                        id="no_steps", type='number',
                        style={'width': '100%'}, persistence=True, value=180
                    ),
                    html.Br(), html.Br()
                ]
            ),
            html.Div(
                style={'width': '25%',
                       'display': 'inline-block',
                       'padding': '20px',
                       },
                children=[
                    html.Label('On Time [s]'),
                    dcc.Input(
                        id="on_time", type='number',
                        style={'width': '100%'}, persistence=True, value=180
                    ),
                    html.Br(), html.Br(),
                    html.Label('Off time [s]'),
                    dcc.Input(
                        id="off_time", type='number',
                        style={'width': '100%'}, persistence=True, value=180
                    ),
                    html.Br(), html.Br(), html.Br(),
                    html.Button("Start", id="exp_button", style={'width': '100%'},
                                n_clicks=0, disabled=False),
                    # dbc.Progress(id="progress_expose", value=0, striped=True, animated=True),
                    html.Br(),
                    dcc.Loading(
                        id="exposing",
                        children=[html.Div(id='expose_div')],
                        type="circle"),
                ]
            ),
        ],
    )

def temperature_exp():
    return html.Div(
        style={
            'width': '100%',
        },
        children=[
            dcc.ConfirmDialog(
                id='confirm_exposure_temp',
                message='Sure you want to expose?',
            ),
            html.Div(
                style={
                    'width': '25%',
                    # 'float': 'left',
                    'display': 'inline-block',
                    'padding': '20px',
                },
                children=[
                    html.Label("Power Supply Current [A]"),
                    dcc.Input(
                        id="temp_current", type='number', placeholder='',
                        style={'width': '100%'}, persistence=True, value=0, debounce=True
                    ),
                    html.Br(), html.Br(),
                    html.Label("Exposure Field [mT]"),
                    dcc.Input(
                        id="temp_field", type='number',
                        style={'width': '100%'}, persistence=True, value=0, debounce=True
                    ),
                    html.Br(), html.Br(),
                    html.Label("dt [s]"),
                    dcc.Input(
                        id="temp_sample_rate", type='number',
                        style={'width': '100%'}, persistence=True, value=0, debounce=True
                    ),
                    html.Br(), html.Br(),
                ]
            ),
            html.Div(
                style={'width': '25%',
                       'display': 'inline-block',
                       'padding': '20px',
                       },
                children=[
                    html.Label("Record Before [s]"),
                    dcc.Input(
                        id="temp_rec_before", type='number',
                        style={'width': '100%'}, persistence=True, value=30
                    ),
                    html.Br(), html.Br(),
                    html.Label("Record After [s]"),
                    dcc.Input(
                        id="temp_rec_after", type='number', placeholder='',
                        style={'width': '100%'}, persistence=True, value=60
                    ),
                    html.Br(), html.Br(),
                    html.Label('Number of Steps'),
                    dcc.Input(
                        id="temp_no_steps", type='number',
                        style={'width': '100%'}, persistence=True, value=180
                    ),
                    html.Br(), html.Br()
                ]
            ),
            html.Div(
                style={'width': '25%',
                       'display': 'inline-block',
                       'padding': '20px',
                       },
                children=[
                    html.Label('Set Temperature [℃]'),
                    dcc.Input(
                        id="set_temperature", type='number',
                        style={'width': '100%'}, persistence=True, value=35
                    ),
                    html.Br(), html.Br(),
                    html.Label('Temperature Range [℃]'),
                    dcc.Input(
                        id="temperature_range", type='number',
                        style={'width': '100%'}, persistence=True, value=4
                    ),
                    html.Br(), html.Br(), html.Br(),
                    html.Button("Start", id="temp_button", style={'width': '100%'},
                                n_clicks=0, disabled=False),
                    # dbc.Progress(id="progress_expose", value=0, striped=True, animated=True),
                    html.Br(),
                    dcc.Loading(
                        id="temp_exposing",
                        children=[html.Div(id='temperature_exp_div')],
                        type="circle"),
                ]
            ),
        ]
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
            dcc.Download(id="download"),
            dcc.Loading(id="dl_loading", children=html.Div(id="dl_loading_output"))
        ]
    )
