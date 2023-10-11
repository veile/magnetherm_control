# -*- coding: utf-8 -*-
import os
import time
import numpy as np
import pandas as pd
from zipfile import ZipFile
from flask import send_from_directory
from serial import SerialException

import dash
from dash import html, dcc, ctx

from dash.dependencies import Output, Input, State

import plotly.graph_objects as go
import plotly.express as px

from app import app, colors
# from app.utils import get_devices, get_files, matrix_sheet, current_state, change_state
from app.devices import ToneGenerator, PowerSupply, fiber, TC, dummy_ToneGenerator, dummy_PowerSupply, dummy_TC, dummy_fiber

import app.components as comp
import app.utils as utils
import app.functions as func

# Debugging mode
# PowerSupply = dummy_PowerSupply
# ToneGenerator = dummy_ToneGenerator
# TC = dummy_TC
# fiber = dummy_fiber
# --------------

global tone
global power
global fres
global temp

# Storing these global variables in a .txt file instead
# exposing = False
# tuned = False
with open('state.txt', 'w') as f:
    f.write('exposing: False\ntuned: False')


temp = None


app.config['suppress_callback_exceptions'] = True
app.scripts.config.serve_locally = True


@app.server.route('/data/<path:path>')
def serve_static(path):
    root_dir = os.getcwd()
    return send_from_directory(
        os.path.join(root_dir, 'data'), path, as_attachment=True)


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
        dcc.Markdown('# Magnetherm Dashboard', id='header',
                     style={'textAlign': 'center'}),
        html.Div(style={'textAlign': 'center'}, children=[comp.stop()]),
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
    ]
)

# Data page layout
data_layout = html.Div(
    style={
        'backgroundColor': colors['background']
    },
    children=[
        dcc.Markdown('# Magnetherm Dashboard', id='header',
                     style={'textAlign': 'center'}),
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
            tone = ToneGenerator(tone_port)
            # tone = dummy_ToneGenerator(tone_port)
            conn[0] = True
        except SerialException as error:
            s += str(error)

        try:
            power = PowerSupply(power_port)
            # power = dummy_PowerSupply(power_port)
            conn[1] = True
        except SerialException as error:
            s += str(error)

        if s:
            return s, c[conn[0]], c[conn[1]]

        return html.P([tone.get_id(), html.Br(), power.get_id()]), c[conn[0]], c[conn[1]]


@app.callback(
    Output('temp_div', 'children'),
    Input('t_sensor', 'value')
)
def choose_temp_sensor(sensor):
    global temp
    if sensor is None:
        raise dash.exceptions.PreventUpdate

    if sensor == 'TC':
        # temp = TC([0x60])
        temp = TC(CS_PINS=['D5'])
        return comp.thermo_div()
    if sensor == 'OFT':
        temp = None
        return comp.fiber_div()


@app.callback(
    Output('fiber_connect_div', 'children'),
    Input('fiber_connect', 'n_clicks'),
    State('fiber_com', 'value')
)
def fiber_connect(n, port):
    global temp
    if n is None:
        raise dash.exceptions.PreventUpdate

    temp = fiber(port)
    return 'Connected'



@app.callback(
    [Output('tone_com', 'options'), Output('power_com', 'options')],
    Input('header', 'children')
)
def refresh_options(n_intervals):
    options_list = utils.get_devices()
    options = [{'label': a, 'value': a} for a in options_list]
    return options, options

@app.callback(
    [Output('freq_low', 'value'),
     Output('freq_high', 'value'),
     Output('configuration', 'data')],
    [Input('coil_type', 'value'),
     Input('cap_type', 'value')],
    State('configuration', 'data')
)
def set_frequency_range(coil_type, cap_type, data):
    f = utils.matrix_sheet.loc[(utils.matrix_sheet['CoilTurns'] == coil_type) &
                               (utils.matrix_sheet['CapacitorName'] == cap_type)].iloc[0]['FreqWork']
    data = {'CoilTurns': coil_type, 'CapacitorName': cap_type}

    return f - 5, f + 5, data


@app.callback(
    Output('test_div', 'children'),
    (Input('tc_type', 'value'))
)
def tc_configure(thermo_type, res):
    temp.set_type(thermo_type)
    print(f'Set to type {thermo_type}')
    return f'Thermcouple type set to {thermo_type}'


@app.callback(
    Output('stop_button', 'value'),
    Input('stop_button', 'n_clicks')
)
def stop_exposure(n):
    if n is None:
        raise dash.exceptions.PreventUpdate


    global power
    #Maybe I need to do this in the experiments such that it does not have 2 serial connections and fail.
    power.set_default()
    utils.write_state('exposing', False)
    return 'STOP'


@app.callback(
    Output('filename-input', 'style'),
    Input('filename-input', 'value')
)
def display_overwrite(filename):
    if filename is None:
        raise dash.exceptions.PreventUpdate

    if os.path.exists('data/'+filename+'.txt'):
        return {'color': 'red'}
    else:
        return {'color': 'green'}


# -------------------------------------------------------------------------------------------------------------------
@app.callback(
    [Output('confirm_tuning', 'displayed'),
     Output('confirm_tuning', 'message')],
    Input('tune_button', 'n_clicks'),
    [State('coil_type', 'value'),
     State('cap_type', 'value'),
     State('filename-input', 'value')]
)
def confirm_tuning(clicks, coil, cap, filename):
    if clicks == 0:
        raise dash.exceptions.PreventUpdate

    overwrite_msg = ''
    filename = 'data/' + filename + '.txt'
    if os.path.exists(filename):
        overwrite_msg = 'FILE ALREADY EXISTS!\n'

    return True, overwrite_msg+"Make sure that the coil has %s turns and the capacitor is at %s" % (str(coil), str(cap))


@app.callback(
    Output('tune_interval', 'max_intervals'),
    Input('confirm_tuning', 'submit_n_clicks'),
    State('tune_interval', 'n_intervals')
)
def start_tune_graphing(n, n_ints):
    if n is None:
        return 0
    return n_ints + 20


@app.callback(
    Output('tune_graph', 'figure'),
    Input('tune_interval', 'n_intervals'),
    State('filename-input', 'value')
)
def update_tune_graph(n, filename):
    if n is None:
        raise dash.exceptions.PreventUpdate
    if filename is None:
        raise dash.exceptions.PreventUpdate

    filename = 'data/' + filename + ".txt"

    try:
        df = pd.read_csv(filename, sep='\t')

    except:
        raise dash.exceptions.PreventUpdate

    x = 'Frequency [Hz]'
    y = 'Current [A]'

    # Splitting DataFrame rough/fine sweep
    idx = df[x] < df[x].shift()
    if idx.sum() != 0:
        split = np.where(idx == True)[0][0]
    else:
        split = df[x].size

    df1 = df[:split]
    df2 = df[split:]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df1[x], y=df1[y], name='Rough Sweep'))
    fig.add_trace(go.Scatter(x=df2[x], y=df2[y], name='Fine Sweep'))

    fig.update_traces(mode='lines+markers')
    fig.update_xaxes()
    fig.update_yaxes()

    return fig


@app.callback(
    Output('tune_div', 'children'),
    Input('tune_interval', 'max_intervals'),
    [State('freq_low', 'value'),
     State('freq_high', 'value'),
     State('coil_type', 'value'),
     State('cap_type', 'value'),
     State('filename-input', 'value')]
)
def tune(max_ints, flow, fhigh, coil, cap, filename):
    global tone, power, fres
    if max_ints == 0:
        return "Click tune to tune system"
    # if n is None:
    #    return "Click to tune system"

    if 'tone' not in globals() or 'power' not in globals():
        return "Please connect to devices."

    exposing = utils.read_states()[0]
    if exposing:
        return "Experiment is running!"

    if filename is None:
        return "Please input a filename"

    if temp is None:
        return "Please choose temperature sensor"

    utils.write_state('exposing', True)

    filename = 'data/' + filename + '.txt'

    t_header = "\t".join(['T%i [degC]' % i for i in range(len(temp))])
    header = 'Frequency [Hz]\tCurrent [A]\tVoltage [V]\t' + t_header
    with open(filename, 'w') as file:
        file.write(header + "\n")

    V = utils.matrix_sheet.loc[(utils.matrix_sheet['CoilTurns'] == coil) &
                               (utils.matrix_sheet['CapacitorName'] == cap)].iloc[0]['VoltsPSU']
    I = utils.matrix_sheet.loc[(utils.matrix_sheet['CoilTurns'] == coil) &
                               (utils.matrix_sheet['CapacitorName'] == cap)].iloc[0]['AmpsPSU']

    currents = []

    # Rough estimate
    freqs = np.linspace(flow * 1e3, fhigh * 1e3, 11)
    tone.set_frequency(freqs[0])
    tone.set_output('ON')

    power.set(V / 3, I)
    power.set_output('ON')
    for f in freqs:
        exposing = utils.read_states()[0]
        if not exposing:
            return 'Tuning stopped'

        tone.set_frequency(f)
        temp.initiate()
        time.sleep(.5)

        readingI = power.get_I().strip('A')
        readingV = power.get_V().strip('V')
        temperatures = '\t'.join(list(map(str, temp.get_T())))
        with open(filename, 'a') as file:
            output = '%.1f\t%s\t%s\t' % (f, readingI, readingV) + temperatures
            file.write(output + "\n")

        currents.append(readingI)

    fmax = freqs[np.argmax(currents)]

    # with open(filename, 'a') as file:
    #     nan_space = ['#N/A' for i in range(len(header.split('\t')))]
    #     file.write('\t'.join(nan_space) + '\n')

    # Finer estimate
    currents = []
    freqs = np.linspace(fmax - 1e3, fmax + 1e3, 5)
    for f in freqs:
        exposing = utils.read_states()[0]
        if not exposing:
            return 'Tuning stopped'

        tone.set_frequency(f)
        temp.initiate()
        time.sleep(.5)

        readingI = power.get_I().strip('A')
        readingV = power.get_V().strip('V')
        temperatures = '\t'.join(list(map(str, temp.get_T())))
        with open(filename, 'a') as file:
            output = '%.1f\t%s\t%s\t' % (f, readingI, readingV) + temperatures
            file.write(output + "\n")

        currents.append(readingI)

    fres = freqs[np.argmax(currents)]

    power.set_default()
    utils.write_state('exposing', False)

    tone.set_frequency(fres)
    utils.write_state('tuned', True)

    return "Resonance frequency is %.1f kHz" % (fres * 1e-3)


# -------------------------------------------------------------------------------------------------------------------

# #Exposure tabs
@app.callback(
    [Output('exp_field', 'value'),
     Output('temp_field', 'value')],
    [Input('exp_current', 'value'),
     Input('temp_current', 'value')],
    State('configuration', 'data')
)
def current_to_field(exp_current, temp_current, config):

    exp_current, temp_current = float(exp_current), float(temp_current)

    try:
        exp_field = utils.current_to_field(exp_current, **config)
        temp_field = utils.current_to_field(temp_current, **config)
    except TypeError as e:
        return str(e), str(e)

    return "%.2f" % exp_field, "%.2f" % temp_field


@app.callback(
    [Output('exp_current', 'value'),
     Output('temp_current', 'value')],
    [Input('exp_field', 'value'),
     Input('temp_field', 'value')],
    State('configuration', 'data')
)
def field_to_current(exp_field, temp_field, config):
    exp_field, temp_field = float(exp_field), float(temp_field)

    try:
        exp_current = utils.field_to_current(exp_field, **config)
        field_current = utils.field_to_current(temp_field, **config)
    except TypeError as e:
        return str(e), str(e)

    return "%.2f" % exp_current, "%.2f" % field_current

@app.callback(
    [Output('confirm_exposure_exp', 'displayed'),
     Output('confirm_exposure_exp', 'message')],
    Input('exp_button', 'n_clicks'),
    [State('exp_current', 'value'),
     State('exp_field', 'value'),
     State('filename-input', 'value')]
)
def confirm_exposure_exp(clicks, current, field, filename):
    if clicks == 0:
        raise dash.exceptions.PreventUpdate

    overwrite_msg = ''
    filename = 'data/' + filename + '.txt'
    if os.path.exists(filename):
        overwrite_msg = 'FILE ALREADY EXISTS!\n'

    return True, overwrite_msg+"Expose the sample with %s A (%s mT)?" % (str(current), str(field))


@app.callback(
    [Output('confirm_exposure_temp', 'displayed'),
     Output('confirm_exposure_temp', 'message')],
    Input('temp_button', 'n_clicks'),
    [State('temp_current', 'value'),
     State('temp_field', 'value'),
     State('filename-input', 'value')]
)
def confirm_exposure_temp(clicks, current, field, filename):
    if clicks == 0:
        raise dash.exceptions.PreventUpdate

    overwrite_msg = ''
    filename = 'data/' + filename + '.txt'
    if os.path.exists(filename):
        overwrite_msg = 'FILE ALREADY EXISTS!\n'

    return True, overwrite_msg+"Expose the sample with %s A (%s mT)?" % (str(current), str(field))


@app.callback(
    Output('exp_interval', 'max_intervals'),
    [Input('confirm_exposure_temp', 'submit_n_clicks'),
     Input('confirm_exposure_exp', 'submit_n_clicks')],
    [State('exp_interval', 'n_intervals'),
     State('rec_before', 'value'),
     State('rec_after', 'value'),
     State('no_steps', 'value'),
     State('on_time', 'value'),
     State('off_time', 'value'),
     State('temp_rec_before', 'value'),
     State('temp_rec_after', 'value'),
     State('temp_no_steps', 'value')]
)
def start_exp_graphing(click_temp, click_exp, n_ints, rec_before, rec_after, N, on_time, off_time, temp_before,
                       temp_after, temp_N):
    if ctx.triggered_id is None:
        dash.exceptions.PreventUpdate

    id = ctx.triggered_id

    if id == 'confirm_exposure_exp':
        if not all(isinstance(x, int) for x in [N, rec_before, rec_after, on_time, off_time]):
            return 0
        else:
            return n_ints + rec_before + N * (on_time+off_time) + rec_after + 5  # 5 sec buffer

    elif id == 'confirm_exposure_temp':
        if not all(isinstance(x, int) for x in [N, temp_before, temp_after, temp_N]):
            return 0
        else:
            return n_ints + temp_before + temp_N* 900 + temp_after + 5  # 5 sec buffer

    else:
        return 0

@app.callback(
    Output('exp_graph', 'figure'),
    Input('exp_interval', 'n_intervals'),
    State('filename-input', 'value')
)
def update_exp_graph(n, filename):
    if n is None:
        raise dash.exceptions.PreventUpdate
    if filename is None:
        raise dash.exceptions.PreventUpdate
    if temp is None:
        raise dash.exceptions.PreventUpdate

    filename = 'data/' + filename + ".txt"

    try:
        df = pd.read_csv(filename, sep='\t', comment='#')

    except:
        raise dash.exceptions.PreventUpdate

    x = 'Time [s]'
    ys = [y for y in df.columns if y.startswith('T')]
    # ys = "\t".join(['T%i [degC]' % i for i in range(len(temp))])
    fig = px.scatter(df, x, y=ys)

    fig.update_traces(mode='lines+markers')
    fig.update_xaxes(autorange=True)
    fig.update_yaxes(title_text='Temperature [degC]')

    return fig


@app.callback(
    [Output('expose_div', 'children'),
     Output('temperature_exp_div', 'children')],
    [Input('confirm_exposure_exp', 'submit_n_clicks'),
     Input('confirm_exposure_temp', 'submit_n_clicks')],
    [State('on_time', 'value'),
     State('off_time', 'value'),
     State('rec_before', 'value'),
     State('rec_after', 'value'),
     State('exp_current', 'value'),
     State('filename-input', 'value'),
     State('sample_rate', 'value'),
     State('no_steps', 'value'),
     State('temp_current', 'value'),
     State('temp_sample_rate', 'value'),
     State('set_temperature', 'value'),
     State('temperature_range', 'value'),
     State('temp_rec_before', 'value'),
     State('temp_rec_after', 'value'),
     State('temp_no_steps', 'value')],
)
def expose(exp_click, temp_click, on_time, off_time, rec_before, rec_after, current, filename, dt, N,
           temp_current, temp_dt, Tset, Trange, temp_before, temp_after, temp_N):

    global power, tone

    id = ctx.triggered_id if not None else 'No clicks'
    if id is None:
        return "Click to start exposure", "Click to start exposure"

    def return_select(msg, id):
        if id == 'confirm_exposure_exp':
            return msg, "Click to start exposure"
        elif id == 'confirm_exposure_temp':
            return "Click to start exposure", msg

    if 'tone' not in globals() or 'power' not in globals():
        return return_select("Please connect to devices.", id)

    tuned = utils.read_states()[1]
    if not tuned:
        return return_select("Please tune the system first!", id)

    # if not all(isinstance(x, int) for x in [on_time, off_time, rec_before, rec_after, N]):
    #     return return_select("Please enter valid values", id)

    exposing = utils.read_states()[0]
    if exposing:
        return return_select("Experiment is running!", id)

    if temp is None:
        return_select("Please select temperature sensor.", id)
    temp.initiate()
    
    # Checks if current is numeric
    try:
        current = float(current)
        temp_current = float(temp_current)
    except:
        return "Input valid number at current"

    filename = 'data/' + filename + '.txt'

    props = """#Resonance Frequency: %.3f kHz\n#Set Current: %.2f A\n""" % (fres, current)

    t_header = "\t".join(['T%i [degC]' % i for i in range(len(temp))])
    header = 'Time [s]\tCurrent [A]\tVoltage [V]\t' + t_header + "\tState"
    with open(filename, 'w') as file:
        file.write(props + header + "\n")

    tone.set_output('ON')
    utils.write_state('exposing', True)

    if id == 'confirm_exposure_exp':
        exitmsg = func.time_exp(power, temp, current, filename, rec_before, N, on_time, off_time, rec_after, dt)

    elif id == 'confirm_exposure_temp':
        exitmsg = func.temp_exp(power, temp, temp_current, filename, temp_before, temp_N,
                                Tset, Trange, temp_after, temp_dt)

    utils.write_state('exposing', False)
    return return_select(exitmsg, id)


# Callbacks for data page
@app.callback(
    [Output('download', 'data'), Output('dl_loading_output', 'children')],
    Input('download_button', 'n_clicks'),
    [State('files_list', 'data'),
     State('files_list', 'selected_rows')]
)
def download_file(n_clicks, data, rows):
    if n_clicks == 0:
        raise dash.exceptions.PreventUpdate


    directory = os.getcwd() + "/data/"
    files = [data[r]['Filename'] for r in rows]

    if len(files) == 1:
        return dcc.send_file(directory + files[0]), ''
    else:
        # create a ZipFile object
        zip_obj = ZipFile(directory + 'measurements.zip', 'w')
        # Add multiple files to the zip
        for f in files:
            zip_obj.write(directory + f, arcname=f)
        # close the Zip File
        zip_obj.close()
        return dcc.send_file(directory + "measurements.zip"), ''



@app.callback(
    Output('files_list', 'data'),
    Input('refresh_files', 'n_clicks')
)
def refresh_files_list(n_clicks):
    return utils.get_files()


if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0')
