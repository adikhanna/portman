import csv
import json
import time
import dash
import dash_auth
import waitress
import argparse
import dash_table

import pandas as pd
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html

from yahooquery import Ticker
from dash.dependencies import Input, Output, State

VALID_USERNAME_PASSWORD_PAIRS = {
    'admin': 'bebek'
}


app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server
app.title = "Correlation Matrix"
auth = dash_auth.BasicAuth(
    app,
    VALID_USERNAME_PASSWORD_PAIRS
)

MAX_COL_WIDTH = 300

def parse_args() -> str:
    parser = argparse.ArgumentParser(description="correlation matrix")
    parser.add_argument("-config", type=str, required=True,
                        help="Config file")
    args = parser.parse_args()
    return args.config

config = parse_args()

with open(config) as conf:
    params = json.load(conf)

ticks = sorted(params["tickers"])
ticks.insert(0, "Tickers")
cols = ticks
current_tickers = ticks[1:]

matrix_alert = dbc.Alert("Matrix", color="light", id="mat")
lookback_alert = dbc.Alert("Lookback Period", color="light", id="lookback")

opts = ["1d", "5d", "7d", "60d", "1mo", "3mo", "6mo", "1y", "2y", "ytd"]

select = dbc.Select(
    id="select",
    options=[{"label": val, "id": i} for i, val in enumerate(opts)],
    style={"margin-left": "10px", "margin-bottom": "12px", "width": "99%"},
)

form = dbc.Form(
    [
        dbc.FormGroup(
            [
                dbc.Label("Add Ticker", className="mr-2"),
                dbc.Input(type="text", placeholder="TSLA", id="addin"),
            ],
            className="mr-3",
        ),
        dbc.FormGroup(
            [
                dbc.Label("Remove Ticker", className="mr-2"),
                dbc.Input(type="text", placeholder="ACB", id="removein"),
            ],
            className="mr-3",
        ),
        dbc.Button("Update Tickers", color="light", id="ticker-button"),
    ],
    inline=True,
    style={"margin-left": "22px", "margin-bottom": "12px"},
)

@app.callback(
    Output("tickbody", "children"),
    [Input("ticker-button", "n_clicks"),
    Input("addin", "value"),
    Input("removein", "value")],
)
def update_tickers(n, addin, removein):
    callback = dash.callback_context.triggered[0]["prop_id"]
    if "addin" not in callback and "removein" not in callback:
        if n:
            if n > 0:
                if addin:
                    if len(addin) > 0 and addin not in current_tickers and len(addin) + 1 <= 9:
                        current_tickers.append(addin)
                        current_tickers.sort()
                if removein:
                    if len(removein) > 0 and removein in current_tickers:
                        current_tickers.remove(removein)
                        current_tickers.sort()
                return [html.P(", ".join(current_tickers))]
    else:
        raise dash.exceptions.PreventUpdate


popover = html.Div(
    [
        dbc.Button(
            "Last Refreshed", id="popover-target", color="danger"
        ),
        dbc.Popover(
            [
                dbc.PopoverHeader("Matrix was last refreshed at:"),
                dbc.PopoverBody("", id="body"),
            ],
            id="popover",
            is_open=False,
            target="popover-target",
        ),
    ],
    style={"margin-left": "10px", "margin-bottom": "12px"}
)

@app.callback(
    Output("tick_popover", "is_open"),
    [Input("popover-tar", "n_clicks")],
    [State("tick_popover", "is_open")],
)
def toggle_popover(n, is_open):
    if n:
        return not is_open
    return is_open

tick_popover = html.Div(
    [
        dbc.Button(
            "Current Tickers", id="popover-tar", color="danger"
        ),
        dbc.Popover(
            [
                dbc.PopoverHeader("Current tickers: "),
                dbc.PopoverBody(", ".join(current_tickers), id="tickbody"),
            ],
            id="tick_popover",
            is_open=False,
            target="popover-tar",
        ),
    ],
    style={"margin-left": "10px", "margin-bottom": "18px"}
)


@app.callback(
    Output("popover", "is_open"),
    [Input("popover-target", "n_clicks")],
    [State("popover", "is_open")],
)
def toggle_popover(n, is_open):
    if n:
        return not is_open
    return is_open


app.layout = html.Div([dbc.Jumbotron([
                        html.H1("Correlation Matrix", className="display-3"),
                        html.P(
                            "See how your favorite stocks correlate.  ",
                            className="lead",
                        ),dbc.Spinner(html.Div(id="loading-output")),]),
                popover,
                dcc.Interval(id='graph-update',
                             interval=1*300000,
                             n_intervals=0),
    tick_popover,
    form,
    lookback_alert,
    select,
    dbc.Button("Update Matrix", color="light", block=True, id="sub", style={"margin-left": "10px", "width": "99%"}),
    matrix_alert,
    dash_table.DataTable(id='my-table',
                        fixed_rows={"headers": True},
                        style_header={
                        "overflow": "hidden",
                        "textOverflow": "ellipsis",
                        "maxWidth": MAX_COL_WIDTH,
                        },
                        style_cell={
                        "minWidth": "100px",
                        "maxWidth": "300px",
                        "whiteSpace": "normal",
                        "font_family": "Gill Sans",
                        "font_size": "20px",
                        "text_align": "center"
                        },
                         columns=[{"name": i, "id": i} for i in ["Tickers"] + current_tickers],
                         data=[{"Tickers": cols[i+1]} for i in range(len(cols)-1)]),
    html.Div(json.dumps({"n_clicks":0,
                      "n_previous_clicks":0}),
                       id="local_data",
                       style= {"display": "none"}),
    html.Div(id="table-hidden-target", style={"display": "none"}),
])


@app.callback(
    output=Output(component_id="local_data",
                  component_property="children"),
    inputs=[Input("sub", "n_clicks")],
    state=[State("local_data", "children")]
)
def track_submit_clicks(n_clicks,
                        local_data_json):
    if n_clicks is None:
        n_clicks = 0
    local_data = json.loads(local_data_json)
    n_previous_clicks = local_data["n_clicks"]
    local_data.update(**{"n_clicks": n_clicks,
                         "n_previous_clicks": n_previous_clicks})
    return json.dumps(local_data)

@app.callback([Output('my-table', 'data'),
              Output("body", "children"),
              Output("loading-output", "children"),
               Output('my-table', 'columns')],
              [Input('graph-update', 'n_intervals'),
               Input("local_data", "children"),
               Input("select", "value")])
def update_table(n, local_data_json, period):
    callback = dash.callback_context.triggered[0]["prop_id"]
    local_data = json.loads(local_data_json)
    n_clicks = local_data["n_clicks"]
    n_previous_clicks = local_data["n_previous_clicks"]
    if (n > 0 or (n_clicks > n_previous_clicks)) and "date_input" not in callback and "select" not in callback and period:
        tickers = []
        for symbol in current_tickers:
            ticker = Ticker(symbol.lower())
            row = ticker.history(interval='1h', period=period)
            row["Symbol"] = symbol
            tickers.append(row)
        df = pd.concat(tickers)
        df = df.reset_index()
        df = df[["date", "close", "Symbol"]]
        df_pivot = df.pivot("date", "Symbol", "close").reset_index()
        corr_df = df_pivot.corr(method="pearson")
        corr_df.head().reset_index()
        matrix = corr_df.to_dict('records')
        for i, element in enumerate(matrix):
            element = dict(sorted(element.items()))
        for i in range(len(matrix)):
            matrix[i]["Tickers"] = list(current_tickers[i])
        last_update_time = time.strftime("%Y-%m-%d %H:%M:%S")
        return matrix, [html.P(last_update_time)], "", [{"name": i, "id": i} for i in ["Tickers"] + current_tickers]
    else:
        raise dash.exceptions.PreventUpdate

if __name__ == "__main__":
    from waitress import serve
    serve(server, host="0.0.0.0", port=5000)
