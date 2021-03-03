# -*- coding: utf-8 -*-
import os
import numpy as np
from zipfile import ZipFile
from flask import send_from_directory
from serial import SerialException

import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Output, Input, State
from dash_extensions.snippets import send_file


from app import app, colors
# from app.utils import get_devices, get_files, matrix_sheet, current_state, change_state
from app.devices import ToneGenerator, PowerSupply, scan, exposure
import app.components as comp
import app.utils as utils


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
        html.Div(dcc.Markdown(utils.current_state(), id='current_state') ),
        html.Br(),

        html.Div(style={'width': '100%'},
                 children=[
                     comp.com_inputs(),
                     comp.temp_options(),

                     comp.graph(),
                 ]),
        comp.tabs(),
        comp.refresh(),
        comp.quick_refresh()
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
def test_connection(n_clicks, tone_port, power_port):
    c = {True: colors['on'], False: colors['off']}
    if n_clicks == 0:
        return '', c[False], c[False]
    else:
        s = ''
        conn = [False, False]
        try:
            T = ToneGenerator(tone_port)
            conn[0] = True
        except SerialException as error:
            s += str(error)

        try:
            P = PowerSupply(power_port)
            conn[1] = True
        except SerialException as error:
            s += str(error)

        if s:
            return s, c[conn[0]], c[conn[1]]

        return T.ID+P.ID, c[conn[0]], c[conn[1]]


@app.callback(
    [Output('tone_com', 'options'), Output('power_com', 'options')],
    Input('refresh', 'n_intervals')
)
def refresh_options(n_intervals):
    options_list = utils.get_devices()
    options = [{'label': a, 'value': a} for a in options_list]
    return options, options


@app.callback(
    [Output('current_state', 'children'),
     Output('exp_button', 'children'),
     Output('exp_button', 'style')],
    Input('quick_refresh', 'n_intervals')
)
def refresh(n_intervals):
    exposure_on = utils.exposing()
    if exposure_on:
        return utils.current_state(), "Stop", {'textColor': colors['off'], 'width': '200px'}
    else:
        return utils.current_state(), "Start", {'textColor': colors['on'], 'width': '200px'}

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


@app.callback(
    Output('tune_div', 'children'),
    Input('confirm_tuning', 'submit_n_clicks'),
    [State('freq_low', 'value'),
     State('freq_high', 'value'),
     State('coil_type', 'value'),
     State('cap_type', 'value'),
     State('tone_com', 'value'),
     State('power_com', 'value')]
)
def tune(clicks, flow, fhigh, coil, cap, tone, power):
    if clicks == None:
        return "Click tune to tune system"

    else:
        try:
            T = ToneGenerator(tone)
        except SerialException:
            utils.change_state("Tuning failed!", 'current')
            ports = utils.get_devices()
            if tone not in ports:
                return "Tone Generator is not present on port %s" %tone
            else:
                return "Cannot connect to the tone generator"

        try:
            P = PowerSupply(power)
        except SerialException:
            utils.change_state("Tuning failed!", 'current')
            ports = utils.get_devices()
            if power not in ports:
                return "Power Supply is not present on port %s" %tone
            else:
                return "Cannot connect to the power supply"

        V = utils.matrix_sheet.loc[(utils.matrix_sheet['Coil Turns'] == coil) &
                         (utils.matrix_sheet['Capacitance [nF]'] == cap)].iloc[0]['Voltage [V]']
        I = utils.matrix_sheet.loc[(utils.matrix_sheet['Coil Turns'] == coil) &
                         (utils.matrix_sheet['Capacitance [nF]'] == cap)].iloc[0]['Current [A]']

        state = utils.current_state().split('\n\n')
        if state[0] == "**Current State**: Tuning the system":
            P.set_output('OFF')
            P.set(0,0)
            utils.change_state("Tuning was interrupted", 'current')
            utils.change_state("N/A", 'freq')
            # import dash
            # raise dash.exceptions.PreventUpdate
            return "Tuning interrupted!"

    utils.change_state("Tuning the system", 'current')
    # import time
    # time.sleep(5)
    freqs = np.linspace(flow*1e3, fhigh*1e3, 11)
    current = scan(T, P, freqs, V / 3, I)

    mx = np.argmax(current)
    freqs2 = np.linspace(freqs[mx] - 1e3, freqs[mx] + 1e3, 11, endpoint=True)
    current2 = scan(T, P, freqs2, V=40.9 / 3, I=20)

    resonance = freqs2[np.argmax(current2)]
    T.frequency(resonance)
    utils.change_state('Tuning successful', 'current')
    utils.change_state('%.3f kHz'%(resonance*1e-3), 'freq')
    # change_state('Frequency set to %.3f kHz' %(resonance*1e-3))
    return "Resonance frequency at %.3f kHz" %(resonance*1e-3)
    # return 'Tuning test done'


#Exposure
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

@app.callback(
    Output('exp_current', 'value'),
    Input('exp_field', 'value')
)
def field_to_current(field):
    field = float(field)
    f = utils.get_frequency()
    try:
        power_current = utils.field_to_current(field, f)
    except TypeError as e:
        return str(e)

    return "%.3f"%power_current


@app.callback(
    [Output('confirm_exposure', 'displayed'),
     Output('confirm_exposure', 'message')],
    Input('exp_button', 'n_clicks'),
    [State('exp_time', 'value'),
     State('exp_field', 'value')]
)
def confirm_exposure(clicks, time, field):
    if clicks == 0:
        return False, ""
    else:
        return True, "Expose %s mT for %s seconds?"%(str(field), str(time))

@app.callback(
    Output('expose_div', 'children'),
    Input('confirm_exposure', 'submit_n_clicks'),
    [State('exp_time', 'value'),
     State('exp_current', 'value'),
     State('tone_com', 'value'),
     State('power_com', 'value')]
)
def expose(clicks, time, current, tone, power):
    if clicks == None:
        return "Click to start exposure"

    elif not time or not current:
        return "Please enter valid values"

    else:
        exposure_on = utils.exposing()
        if exposure_on:
            utils.set_exposure(False)
            return 'Exposure Interrupted'

        utils.set_exposure(1)
        # import time as t
        # t.sleep(time)

        try:
            T = ToneGenerator(tone)
        except SerialException:
            utils.change_state("Tuning failed!", 'current')
            ports = utils.get_devices()
            if tone not in ports:
                return "Tone Generator is not present on port %s" %tone
            else:
                return "Cannot connect to the tone generator"

        try:
            P = PowerSupply(power)
        except SerialException:
            utils.change_state("Tuning failed!", 'current')
            ports = utils.get_devices()
            if power not in ports:
                return "Power Supply is not present on port %s" %tone
            else:
                return "Cannot connect to the power supply"

        # Checks if system is tuned
        f = utils.get_frequency()
        try:
            f = float(f)
        except TypeError:
            return "TUNE THE SYSTEM!"

        # Checks if current is numeric
        try:
            current = float(current)
        except:
            return "Input valid number at current"

        exposure(T, P, time, V=45, I=current)

        utils.set_exposure(0)
        return "Exposure done"



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
        app.run_server(debug=True, host='0.0.0.0')
