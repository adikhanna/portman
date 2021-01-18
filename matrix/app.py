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
    'admin': 'teakandorange'
}


app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server
app.title = "AB Capital"
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
current_tickers = ticks[1:]

matrix_alert = dbc.Alert("Matrix", color="light", id="mat")
stats_alert = dbc.Alert("Stats", color="light", id="statsmat")
# fin_alert = dbc.Alert("Financial Data", color="light", id="finmat")

lookback_alert = dbc.Alert("Lookback Period", color="light", id="lookback")
stats_lookback_alert = dbc.Alert("Lookback Period", color="light", id="stats-lookback")


opts = ["1d", "5d", "7d", "60d", "1mo", "3mo", "6mo", "1y", "2y", "ytd"]

select = dbc.Select(
    id="select",
    options=[{"label": val, "id": i} for i, val in enumerate(opts)],
    style={"margin-left": "10px", "margin-bottom": "12px", "width": "99%"},
)

stats_select = dbc.Select(
    id="stats-select",
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

stats_form = dbc.Form(
    [
        dbc.FormGroup(
            [
                dbc.Label("Add Ticker", className="mr-2"),
                dbc.Input(type="text", placeholder="TSLA", id="statsaddin"),
            ],
            className="mr-3",
        ),
        dbc.FormGroup(
            [
                dbc.Label("Remove Ticker", className="mr-2"),
                dbc.Input(type="text", placeholder="ACB", id="statsremovein"),
            ],
            className="mr-3",
        ),
        dbc.Button("Update Tickers", color="light", id="stats-ticker-button"),
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

@app.callback(
    Output("stats-tickbody", "children"),
    [Input("stats-ticker-button", "n_clicks"),
    Input("statsaddin", "value"),
    Input("statsremovein", "value")],
)
def update_stats_tickers(n, addin, removein):
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

stats_popover = html.Div(
    [
        dbc.Button(
            "Last Refreshed", id="stats-popover-target", color="danger"
        ),
        dbc.Popover(
            [
                dbc.PopoverHeader("Stats were last refreshed at:"),
                dbc.PopoverBody("", id="statsbody"),
            ],
            id="stats-popover",
            is_open=False,
            target="stats-popover-target",
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

@app.callback(
    Output("stats_tick_popover", "is_open"),
    [Input("stats-popover-tar", "n_clicks")],
    [State("stats_tick_popover", "is_open")],
)
def toggle_stats_tick_popover(n, is_open):
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

stats_tick_popover = html.Div(
    [
        dbc.Button(
            "Current Tickers", id="stats-popover-tar", color="danger"
        ),
        dbc.Popover(
            [
                dbc.PopoverHeader("Current tickers: "),
                dbc.PopoverBody(", ".join(current_tickers), id="stats-tickbody"),
            ],
            id="stats_tick_popover",
            is_open=False,
            target="stats-popover-tar",
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

@app.callback(
    Output("stats-popover", "is_open"),
    [Input("stats-popover-target", "n_clicks")],
    [State("stats-popover", "is_open")],
)
def toggle_stats_popover(n, is_open):
    if n:
        return not is_open
    return is_open


tab1 = html.Div([dbc.Jumbotron([
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
                         data=[{"Tickers": ticks[i+1]} for i in range(len(ticks)-1)]),
    html.Div(json.dumps({"n_clicks":0,
                      "n_previous_clicks":0}),
                       id="local_data",
                       style= {"display": "none"}),
    html.Div(id="table-hidden-target", style={"display": "none"}),
])

tab2 = html.Div([dbc.Jumbotron([
                        html.H1("Datacenter", className="display-3"),
                        html.P(
                            "Statistics & other data.  ",
                            className="lead",
                        ),dbc.Spinner(html.Div(id="loading-output_2")),]),
                stats_popover,
                dcc.Interval(id='stats-update',
                             interval=1*300000,
                             n_intervals=0),
    stats_tick_popover,
    stats_form,
    stats_lookback_alert,
    stats_select,
    dbc.Button("Update Stats", color="light", block=True, id="substats", style={"margin-left": "10px", "width": "99%"}),
    stats_alert,
    dash_table.DataTable(id='stats-table',
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
                         columns=[{"name": i, "id": i} for i in ["Stats"] + current_tickers],
                         data=[]),
    # fin_alert,
    html.Div(json.dumps({"n_clicks":0,
                      "n_previous_clicks":0}),
                       id="stats_local_data",
                       style= {"display": "none"}),
    html.Div(id="stats-table-hidden-target", style={"display": "none"}),
])

tab3 = html.Div([dbc.Jumbotron([
                        html.H1("Fundamentals", className="display-3"),
                        html.P(
                            "Trade events, invest in trends.  ",
                            className="lead",
                        ),dbc.Spinner(html.Div(id="loading-output_3")),]),
                # popover,
                # dcc.Interval(id='graph-update',
                #              interval=1*300000,
                #              n_intervals=0),
    # tick_popover,
    # form,
    # lookback_alert,
    # select,
    # dbc.Button("Update Matrix", color="light", block=True, id="sub", style={"margin-left": "10px", "width": "99%"}),
    # matrix_alert,
    # dash_table.DataTable(id='my-table',
    #                     fixed_rows={"headers": True},
    #                     style_header={
    #                     "overflow": "hidden",
    #                     "textOverflow": "ellipsis",
    #                     "maxWidth": MAX_COL_WIDTH,
    #                     },
    #                     style_cell={
    #                     "minWidth": "100px",
    #                     "maxWidth": "300px",
    #                     "whiteSpace": "normal",
    #                     "font_family": "Gill Sans",
    #                     "font_size": "20px",
    #                     "text_align": "center"
    #                     },
    #                      columns=[{"name": i, "id": i} for i in ["Tickers"] + current_tickers],
    #                      data=[{"Tickers": ticks[i+1]} for i in range(len(ticks)-1)]),
    # html.Div(json.dumps({"n_clicks":0,
    #                   "n_previous_clicks":0}),
    #                    id="local_data",
    #                    style= {"display": "none"}),
    # html.Div(id="table-hidden-target", style={"display": "none"}),
])

app.layout = html.Div([dcc.Tabs(id="tabs",
                                children=[dcc.Tab(label="Matrix", children=[tab1]),
                                dcc.Tab(label="Datacenter", children=[tab2]),
                                dcc.Tab(label="Fundamentals", children=[tab3])])])


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

@app.callback(
    output=Output(component_id="stats_local_data",
                  component_property="children"),
    inputs=[Input("substats", "n_clicks")],
    state=[State("stats_local_data", "children")]
)
def track_stat_submit_clicks(n_clicks,
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

@app.callback([Output('stats-table', 'data'),
              Output("statsbody", "children"),
              Output("loading-output_2", "children"),
               Output('stats-table', 'columns')],
              [Input('stats-update', 'n_intervals'),
               Input("stats_local_data", "children"),
               Input("stats-select", "value")])
def update_stats_table(n, local_data_json, period):
    callback = dash.callback_context.triggered[0]["prop_id"]
    local_data = json.loads(local_data_json)
    n_clicks = local_data["n_clicks"]
    n_previous_clicks = local_data["n_previous_clicks"]
    if (n > 0 or (n_clicks > n_previous_clicks)) and "date_input" not in callback and "stats-select" not in callback and period:
        tickers = []
        for symbol in current_tickers:
            ticker = Ticker(symbol.lower())
            row = ticker.history(interval='1d', period=period)
            row["Symbol"] = symbol
            tickers.append(row)
        df = pd.concat(tickers)
        df = df.reset_index()
        df = df[["date", "close", "Symbol"]]
        df["close"] = df["close"].pct_change()
        df.set_index('Symbol', inplace=True)
        new_df = df.groupby(["Symbol"]).agg({'close': ['mean', 'std', 'min', 'max', 'median']})
        stats = new_df.to_dict('dict')
        new_stats = []
        for k, v in stats.items():
            if k[1] == 'mean':
                v["Stats"] = "Mean"
                new_stats.insert(0, v)
            elif k[1] == 'std':
                v["Stats"] = "Std"
                new_stats.insert(1, v)
            elif k[1] == 'min':
                v["Stats"] = "Min"
                new_stats.insert(2, v)
            elif k[1] == 'max':
                v["Stats"] = "Max"
                new_stats.insert(3, v)
            elif k[1] == 'median':
                v["Stats"] = "Median"
                new_stats.insert(4, v)
        for element in new_stats:
            element = sorted(element.items())
        last_update_time = time.strftime("%Y-%m-%d %H:%M:%S")
        return new_stats, [html.P(last_update_time)], "", [{"name": i, "id": i} for i in ["Stats"] + current_tickers]
    else:
        raise dash.exceptions.PreventUpdate

financial_data = ['beta', 'bookValue', 'priceToBook', '52WeekChange', 'SandP52WeekChange',
             'targetHighPrice', 'targetLowPrice', 'targetMeanPrice', 'targetMedianPrice']

# @app.callback([Output('stats-table', 'data'),
#               Output("statsbody", "children"),
#               Output("loading-output_2", "children"),
#                Output('stats-table', 'columns')],
#               [Input('stats-update', 'n_intervals'),
#                Input("stats_local_data", "children"),
#                Input("stats-select", "value")])
# def update_fin_data_table(n, local_data_json, period):
#     callback = dash.callback_context.triggered[0]["prop_id"]
#     local_data = json.loads(local_data_json)
#     n_clicks = local_data["n_clicks"]
#     n_previous_clicks = local_data["n_previous_clicks"]
#     if (n > 0 or (n_clicks > n_previous_clicks)) and "date_input" not in callback and "stats-select" not in callback and period:
#         all_data = []
#         for symbol in current_tickers:
#             ticker = Ticker(symbol.lower())
#
#
#
#             data = {your_key: d[your_key] for your_key in financial_data}
#
#         for element in new_stats:
#             element = sorted(element.items())
#         last_update_time = time.strftime("%Y-%m-%d %H:%M:%S")
#         return new_stats, [html.P(last_update_time)], "", [{"name": i, "id": i} for i in ["Stats"] + current_tickers]
#     else:
#         raise dash.exceptions.PreventUpdate


if __name__ == "__main__":
    from waitress import serve
    serve(server, host="0.0.0.0", port=5000)
