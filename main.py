# -*- coding: utf-8 -*-
import os
import time
import numpy as np
from zipfile import ZipFile
from flask import send_from_directory
from serial import SerialException

import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Output, Input, State
from dash_extensions.snippets import send_file


from app import app, colors
# from app.utils import get_devices, get_files, matrix_sheet, current_state, change_state
from app.devices import ToneGenerator, PowerSupply, dummy_ToneGenerator, dummy_PowerSupply
import app.components as comp
import app.utils as utils

import waitress

# tone = dummy_ToneGenerator()
# power = dummy_PowerSupply()

global tone
global power
exposing = False
tuned = False

@app.server.route('/data/<path:path>')
def serve_static(path):
    root_dir = os.getcwd()
    return send_from_directory(
        os.path.join(root_dir, 'data'), path, as_attachment=True)


markdown_text = r'''
# Magnetherm Dashboard
'''

content_div = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page_content')
])

# Main Page layout
index_page = html.Div(
    style={
        'backgroundColor': colors['background']
    },
    children=[
        comp.markdown(markdown_text, plc='center'),
        # html.Br(),
        dcc.Link('Go to data', href='/data'),
        # html.Div(dcc.Markdown(utils.current_state(), id='current_state') ),
        html.Br(),

        html.Div(style={'width': '100%'},
                 children=[
                     comp.com_inputs(),
                     comp.temp_options(),

                     comp.graph(),
                 ]),
        comp.tabs(),
        comp.tune_interval(),
        html.Br(),
        comp.stop(),
        html.Div(id='test_div')
    ]
)

# Data page layout
data_layout = html.Div(
    style={
        'backgroundColor': colors['background']
    },
    children=[
        comp.markdown(markdown_text, plc='center'),
        # html.Br(),
        dcc.Link('Go back', href='/'),
        html.Div(style={'float': 'right', 'marginRight': 20}, children=[
            html.Button('Refresh List', id='refresh_files')
        ]),
        html.Br(),

        comp.files_list()
    ]
)

app.layout = content_div

app.validation_layout = html.Div([
    content_div,
    index_page,
    data_layout
])


# Callbacks
# Update the index
@app.callback(Output('page_content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/data':
        return data_layout
    else:
        return index_page


@app.callback(
    [Output('connect_container', 'children'),
     Output('connection_statusT', 'color'), Output('connection_statusP', 'color')],
    [Input('connect', 'n_clicks')],
    [State('tone_com', 'value'), State('power_com', 'value')]
)
def connect(n_clicks, tone_port, power_port):
    global tone, power

    c = {True: colors['on'], False: colors['off']}
    if n_clicks == 0:
        return 'Please connect to the devices', c[False], c[False]
    else:
        s = ''
        conn = [False, False]
        try:
            tone = dummy_ToneGenerator(tone_port)
            conn[0] = True
        except SerialException as error:
            s += str(error)

        try:
            power = dummy_PowerSupply(power_port)
            conn[1] = True
        except SerialException as error:
            s += str(error)

        if s:
            return s, c[conn[0]], c[conn[1]]

        return html.P([tone.get_id(), html.Br(), power.get_id()]), c[conn[0]], c[conn[1]]

@app.callback(
    [Output('tone_com', 'options'), Output('power_com', 'options')],
    Input('refresh', 'n_intervals')
)
def refresh_options(n_intervals):
    options_list = utils.get_devices()
    options = [{'label': a, 'value': a} for a in options_list]
    return options, options


# @app.callback(
#     [Output('current_state', 'children'),
#      Output('exp_button', 'children'),
#      Output('exp_button', 'style')],
#     Input('quick_refresh', 'n_intervals')
# )
# def refresh(n_intervals):
#     exposure_on = utils.exposing()
#     if exposure_on:
#         return utils.current_state(), "Stop", {'textColor': colors['off'], 'width': '200px'}
#     else:
#         return utils.current_state(), "Start", {'textColor': colors['on'], 'width': '200px'}
#
@app.callback(
    Output('tab_content', 'children'),
    Input('main_tabs', 'value'))
def render_content(tab):
    if tab == 'tab_1':
        return comp.tuning()
    elif tab == 'tab_2':
        return comp.exposure()

@app.callback(
    [Output('freq_low', 'value'),
     Output('freq_high', 'value')],
    [Input('coil_type', 'value'),
     Input('cap_type',  'value')]
)
def set_frequency_range(coil_type, cap_type):
    f = utils.matrix_sheet.loc[(utils.matrix_sheet['Coil Turns'] == coil_type) &
                        (utils.matrix_sheet['Capacitance [nF]'] == cap_type)].iloc[0]['Frequency [kHz]']
    return f-5, f+5


@app.callback(
    Output('stop_button', 'value'),
    Input('stop_button', 'n_clicks')
)
def stop_exposure(n):
    if n == 0:
        return 'STOP'

    global exposing, power
    power.set_default()
    exposing = False
    return 'STOP'

# -------------------------------------------------------------------------------------------------------------------
@app.callback(
    [Output('confirm_tuning', 'displayed'),
     Output('confirm_tuning', 'message')],
    Input('tune_button', 'n_clicks'),
    [State('coil_type', 'value'),
     State('cap_type', 'value')]
)
def confirm_tuning(clicks, coil, cap):
    if clicks == 0:
        return False, ""
    else:
        return True, "Make sure that the coil has %s turns and the capacitor is at %s nF"%(str(coil), str(cap))

# @app.callback(
#     [Output('tune_interval', 'disabled'),
#      Output('tune_button', 'disabled'),
#      Output('test_div', 'children')],
#     [Input('confirm_tuning', 'submit_n_clicks'),
#      Input('tune_div', 'children')]
# )
# def start_graphing(n, div):
#     print(div)
#     if n is not None:
#         ctx = dash.callback_context
#
#
#         return False, True, str(ctx.triggered)
#
#         # context = dash.callback_context.triggered[0]['prop_id'].split('.')[0]
#         # if context == 'submit_n_clicks':
#         #     return False, True
#         # else:
#         #     return True, False
#
#     else:
#         return True, False, 'n was None'

@app.callback(
    Output('tune_interval', 'disabled'),
    [Input('confirm_tuning', 'submit_n_clicks'),
     Input('tune_div', 'children')]
)
def start_graphing(n, div):
    print(dash.callback_context.triggered)
    if n is not None:
        return False

    else:
        return True

@app.callback(
    Output('graph_div', 'children'),
    Input('tune_interval', 'n_intervals')
)
def update(n):
    if n is None:
        return 'PLACEHOLDER'
    return "Interval has been triggered %i times" % n


@app.callback(
    Output('tune_div', 'children'),
    Input('confirm_tuning', 'submit_n_clicks'),
    [State('freq_low', 'value'),
     State('freq_high', 'value'),
     State('coil_type', 'value'),
     State('cap_type', 'value')]
)
# @app.callback(
#     Output('tune_div', 'children'),
#     Input('tune_interval', 'disabled'),
#     [State('freq_low', 'value'),
#      State('freq_high', 'value'),
#      State('coil_type', 'value'),
#      State('cap_type', 'value')]
# )
def tune(n, flow, fhigh, coil, cap):
    global tone, power, exposing, tuned
    # if disabled:
    #     return "Click tune to tune system"
    if n is None:
        return "Click to tune system"

    if 'tone' not in globals() or 'power' not in globals():
        return "Please connect to devices."

    if exposing:
        return "Experiment is running!"

    exposing = True

    V = utils.matrix_sheet.loc[(utils.matrix_sheet['Coil Turns'] == coil) &
                     (utils.matrix_sheet['Capacitance [nF]'] == cap)].iloc[0]['Voltage [V]']
    I = utils.matrix_sheet.loc[(utils.matrix_sheet['Coil Turns'] == coil) &
                     (utils.matrix_sheet['Capacitance [nF]'] == cap)].iloc[0]['Current [A]']

    currents = []

    freqs = np.linspace(flow*1e3, fhigh*1e3, 11)
    tone.set_frequency(freqs[0])
    tone.set_output('ON')

    power.set(0, 0)
    power.set_output('ON')

    print('*TUNING STARTED')
    for f in freqs:
        if not exposing:
            return 'Tuning stopped'
        # print(f)
        tone.set_frequency(f)
        time.sleep(1)
        reading = power.get_I()

        currents.append(reading)

    power.set_default()
    exposing = False

    tuned = True
    return currents.__repr__()
# -------------------------------------------------------------------------------------------------------------------

# #Exposure
# Gives circular dependence - in theory fine but gives clunky response
# @app.callback(
#     Output('exp_field', 'value'),
#     Input('exp_current', 'value')
# )
# def current_to_field(current):
#     f = utils.get_frequency()
#     current = float(current)
#     try:
#         field = utils.current_to_field(f, current)
#     except TypeError as e:
#         return str(e)
#         # return str(f)
#
#     return "%.3f"%field

# @app.callback(
#     Output('exp_current', 'value'),
#     Input('exp_field', 'value')
# )
# def field_to_current(field):
#     field = float(field)
#     f = utils.get_frequency()
#     try:
#         power_current = utils.field_to_current(field, f)
#     except TypeError as e:
#         return str(e)
#
#     return "%.3f"%power_current

@app.callback(
    [Output('confirm_exposure', 'displayed'),
     Output('confirm_exposure', 'message')],
    Input('exp_button', 'n_clicks'),
    [State('exp_time', 'value'),
     State('exp_field', 'value')]
)
def confirm_exposure(clicks, exp_time, field):
    if clicks == 0:
        return False, ""
    else:
        return True, "Expose %s mT for %s seconds?"%(str(field), str(exp_time))

@app.callback(
    Output('expose_div', 'children'),
    Input('confirm_exposure', 'submit_n_clicks'),
    [State('exp_time', 'value'),
     State('exp_current', 'value')]
)
def expose(clicks, exp_time, current):
    global power, tone, exposing, tuned
    if clicks is None:
        return "Click to start exposure"

    if 'tone' not in globals() or 'power' not in globals():
        return "Please connect to devices."

    if not tuned:
        return "Please tune the system first!"

    if not exp_time or not current:
        return "Please enter valid values"

    if exposing:
        return "Experiment is running!"
    exposing = True


    # Checks if current is numeric
    try:
        current = float(current)
    except:
        return "Input valid number at current"


    tone.set_output('ON')
    V  = []
    I  = []
    t  = []

    start = time.time()
    power.set(V=45, I=current)
    power.set_output('ON')

    while (time.time() - start) < exp_time:
        if not exposing:
            return "Experiment stopped"


        t = time.time()

        V.append(power.get_V())
        I.append(power.get_I())

        print(V, I)
        time.sleep(1)

    power.set_default()
    exposing = False
    return "Exposure done"





# @app.callback(
#     [Output('exp_button', 'disabled'),
#      Output('tune_button', 'disabled')],
#     [Input('expose_div', 'children'),
#      Input('confirm_exposure', 'submit_n_clicks')]
# )
# def lock_buttons():
#     context = dash.callback_context.triggered[0]['prop_id'].split('.')[0]
#
#     if context == 'confirm_exposing':
#         return True
#     else:
#         return False

# Callbacks for data page
@app.callback(
    [Output('download', 'data'), Output('dl_loading_output', 'children')],
    Input('download_button', 'n_clicks'),
    [State('files_list', 'data'),
     State('files_list', 'selected_rows')]
)
def download_file(n_clicks, data, rows):
    if n_clicks != 0:
        directory = os.getcwd() + "/data/"
        files = [data[r]['Filename'] for r in rows]

        if len(files) == 1:
            return send_file(directory+files[0]), ''
        else:
            # create a ZipFile object
            zip_obj = ZipFile(directory+'measurements.zip', 'w')
            # Add multiple files to the zip
            for f in files:
                zip_obj.write(directory+f, arcname=f)
            # close the Zip File
            zip_obj.close()
            return send_file(directory+"measurements.zip", mime_type='application/zip'), ''

    else:
        return None, None

@app.callback(
    Output('files_list', 'data'),
    Input('refresh_files', 'n_clicks')
)
def refresh_files_list(n_clicks):
    return utils.get_files()


if __name__ == '__main__':

    app.run_server(debug=True, host='0.0.0.0', threaded=False, processes=4)
    # waitress.serve(app.server, threads=4)
