from dash.dependencies import Output, Input, State
import app

@app.callback(
    Output('connect_container', 'children'),
    [Input('connect')],
    [State('tone_com', 'value1'), State('power_com', 'value2')])
def update_output(value1, value2):
    return 'The input value was "{}" and "{}"'.format(
        value1, value2
    )