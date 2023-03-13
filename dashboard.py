
import sys
import os
import base64
import traceback
import pandas as pd
import urllib

import flask
from flask import send_from_directory

from dash import html
from dash import dcc
import dash
import dash_auth
import dash_table_experiments as dte

from dash.dependencies import Input, Output, State

from plotly.offline import plot as plotly
import plotly.graph_objs as go

# %% Setup

debug = False

# %% App

# See: https://github.com/plotly/dash-recipes
def app(users = None, title = 'Dash'):
    
    app = dash.Dash()
    app.title = title
    
    # Enable basic auth
    if not users == None:
        auth = dash_auth.BasicAuth(app, users)
        
    # Add local static path (in dashboard.py's folder, we expect a folder containing dashboard.css and bootstrap.min.css ...)
    def send_static(filename):
        base   = os.path.dirname(__file__)
        folder = os.path.join(base, 'dashboard')
        if debug:
            print('send_static(): base "{}" and folder "{}" and filename "{}"'.format(base, folder, filename))
        return flask.send_from_directory(folder, filename)
    app.server.route('/dashboard/<path:filename>')(send_static)
    
    # Make sure we don't download anything from the web
    app.css.config.serve_locally     = True
    app.scripts.config.serve_locally = True
    
    # Add download() function to app
    def download(folder = './output'):
        nonlocal app
        send_static = lambda filename: flask.send_from_directory(folder, filename)
        app.server.route('/download/<path:filename>')(send_static)
    app.download = download
    
    # Add do() function to app
    def app_do(on, set, to, using = [], init = True):
        nonlocal app
        return do(app, on, set, to, using, init)
    app.do = app_do
    
    return app

# %% Page layout

def page(title, menu, body):
    page = html.Div(className = '', children = [
        html.Link(rel='stylesheet', href='/dashboard/bootstrap.min.css'),
        html.Link(rel='stylesheet', href='/dashboard/dashboard.css'),
        head(title),
        html.Div(className = 'container-fluid mt-3', children = html.Div(className = 'row', children = [
            '' if menu == None else html.Div(className = 'col-sm-2', children = menu),
            html.Div(className = 'col-sm-12' if menu == None else 'col-sm-10', children = body)
        ])),
        dcc.Location(id = '_url', refresh = True)
    ])
    return page


def head(title):
    return html.Nav(className = 'navbar', children = html.H3(className = 'font-weight-normal', children = title))

def menu(title, content):
    card_header = html.Div(className = 'card-header',    children = html.Strong(title)) if not title == None else ''
    card_body   = html.Div(className = 'card-body',      children = content)
    card        = html.Div(className = 'card menu-card', children = [ card_header, card_body ])
    col         = html.Div(className = 'd-inline-block mt-3 col-sm-12', children = card)
    row         = html.Div(className = 'row',            children = col)
    return row

def menuitem(title, content):
    item = html.Div(className = 'form-group mb-0', children = [
        html.Label(className = 'font-weight-bold', children = title) if not title == None else '',
        html.Div(className = 'd-block', children = content)
    ])
    return item

def menuhead(title):
    return html.Label(className = 'font-weight-bold', children = title)

def body(content):
    col = html.Div(className = 'col-sm-12', children = content)
    row = html.Div(className = 'row',       children = col)
    return row

def row(content):
    return html.Div(className = 'row', children = content)

def box(title = None, width = 4, content = None):
    box = html.Div(className = 'd-inline-block mt-3 col-sm-' + str(width), children =
        html.Div(className = 'card', children = [
            html.Div(className = 'card-header', children = html.Strong(title)) if title != None else '',
            html.Div(className = 'card-body',  children = content)
        ])
    )
    return box

def block(width = 4, content = None, center = False):
    css_center = 'mx-auto' if center else ''
    css_width  = 'col-sm-{}'.format(width)
    css_block  = 'd-inline-block'
    css = ' '.join([css_center, css_width, css_block])
    box = html.Div(className = css, children = content)
    return box

# %% Simple components

def form(id, content = None):
    form = html.Form(html.Div(id = id, className = 'form-row', children = content))
    return form

def formitem(label, item, note = None, width = 12):
    formitem = html.Div(className = 'form-group col-md-' + str(width), children = [
        html.Label(className = 'form-label', children = label) if not label is None else '',
        html.Div(className = '', children = item),
        html.Small(className = 'form-text text-muted', children = note) if not note is None else ''
    ])
    return formitem

# %% Elements

def hidden(id):
    return html.Div(id = id, className = 'd-none')

def btn(id, name = None, color = 'primary', link = False, new = True):
    """
    name:  string shown on button (default = id)
    color: primary, secondary, success, danger, warning, info, light, dark, link
    link:  True: return html <a>, False: return html <button> (True if you want to set href property)
    new:   True (default): open link in new window/tab
    """
    if name is None:
        name = id
    if link:
        btn = html.A(id = id, children = name, className = 'btn btn-' + color + ' mr-2', href = '', target = '_blank' if new else '')
    else:
        btn = html.Button(id = id, type = 'button', children = name, className = 'btn btn-' + color + ' mr-2')
    return btn

# Alias for compatib.
btn2 = btn

def rag_green(title):
    return html.H1(html.Span(className = 'badge badge-pill badge-success', children = title))

def rag_amber(title):
    return html.H1(html.Span(className = 'badge badge-pill badge-warning', children = title))

def rag_red(title):
    return html.H1(html.Span(className = 'badge badge-pill badge-danger',  children = title))

def numinput(id, placeholder):
    return dcc.Input(id = id, type = 'numeric', placeholder = placeholder, className = 'form-control')

def dropdown(id, placeholder, options):
    return dcc.Dropdown(id = id, placeholder = placeholder, className = 'form-control', options = options)

def div(id, children = None):
    return html.Div(id = id, children = children)

# %% Complex components

# layout can be None, 'fixed' or 'scroll'
def table(id, layout = None):
    if layout != None:
        layout = 'table-' + layout
    return html.Div(id = id, className = layout)

def make_table(df = None, format = True):
    if format:
        def colfmt(c):
            if c.dtype.kind == 'M':
                return c.apply(lambda t: t.strftime('%Y-%m-%d %H:%M'))
            if c.dtype.kind == 'f':
                return c.apply("{:.2f}".format)
            return c
        df = pd.concat([colfmt(df[c]) for c in df.columns], axis = 1)

    header = html.Thead(html.Tr([ html.Th(col) for col in df.columns ]))
    body   = html.Tbody([ html.Tr([ html.Td(col) for col in row ]) for row in df.itertuples(index = False, name = None) ])
    table  = html.Table(className = 'table', children = [header, body])
    return table


# %% Interactions

# do(app = app, on = on | ondate | oncontent | onclick | ontick, set = setvalue | setcontent | setdate | setoptions, to = fun, using = valueof | dateof | contentof )

# On-functions (detect changes)
def on(id):
    return [Input(id, 'value')]

def ons(id):
    return [Input(id, 'values')]

def ondate(id):
    return [Input(id, 'date')]

def oncontent(id):
    return [Input(id, 'children')]

def onclick(id):
    return [Input(id, 'n_clicks')]

def ontick(id):
    return [Input(id, 'n_intervals')]

def onzoom(id):
    return [Input(id, 'relayoutData')] # only plots

def onhover(id):
    return [Input(id, 'hoverData')]  # only plots

def onplotclick(id):
    return [Input(id, 'clickData')] # only plots

# On change of the app url
def onurl():
    return [Input('_url', 'pathname')]

# Set-functions (update dashboard)
def setvalue(id):
    return Output(id, 'value')

def setcontent(id):
    return Output(id, 'children')

def setdate(id):
    return Output(id, 'date')

def setoptions(id):
    return Output(id, 'options')

def setplot(id):
    return Output(id, 'figure')

def settable(id):
    return setcontent(id)

def setclass(id):
    return Output(id, 'className')

def seturl():
    return Output('_url', 'pathname')

def setlink(id):
    return Output(id, 'href')


# Using-functions (inputs)
def valueof(id):
    return [State(id, 'value')]

def valuesof(id):
    return [State(id, 'values')]

def dateof(id):
    return [State(id, 'date')]

def contentof(id):
    return [State(id, 'children')]

def urlof():
    return [State('_url', 'pathname')]

# Interaction logic
def toval(val):
    return lambda *args, **kwargs: val

def fun(funorval):
    if callable(funorval):
        return funorval
    else:
        return lambda *args, **kwargs: funorval

# Detect competing change triggers in ui.do() callbacks!
def changed():
    memory = {}
    def detector(newdata):
        nonlocal memory
        
        # Initial call is ignored ... nothing change
        if memory == {}:
            memory = newdata
            return []
        
        # Check if anything changed and return list of changed keys
        keys = set(newdata.keys()).intersection(newdata.keys())
        changes = [key for key in keys if newdata[key] != memory[key]]
        memory = newdata
        return changes
    
    return detector

# Get changes
def getchanges(inputs):
    return inputs['_changes']

#change_detector = changed()    # Create
#change_detector({'button': 0}) # No change (emtpy list)
#change_detector({'button': 1}) # Change in 'button' ... returns list ['button']
#change_detector({'button': 1}) # No change (empty list again)

def do(app, on, set, to, using = [], init = True):
    """
    on:  on(), ons(), ontick(), onclick(), ondate(), onzoom(), onhover()
    set: setvalue(), setcontent(), setplot(), settable(), setdatatable()
    to:  <function>
    using: valueof(), dateof(), contentof()
    changes: True: enable change tracking in inputs['_changes'] otherwise False
    """
    names = [e.component_id       for e in on] + [e.component_id       for e in using]
    comps = [e.component_property for e in on] + [e.component_property for e in using]
    combs = ['.'.join(comb) for comb in zip(names, comps)]
    detector = changed()
    initialized = False
    def to2(*args):
        nonlocal initialized
        inputs1 = dict(zip(names, args))
        inputs2 = dict(zip(combs, args))
        inputs = {**inputs1, **inputs2}
        inputs['_changes'] = detector(inputs)
        if init == False and initialized == False:
            initialized = True
            if debug:
                print()
                print()
                print('{function}() INIT:'.format(function = to.__name__))
                print()
                print(inputs)
                print()
            return None
        else:
            try:
                output = to(inputs)
                if debug:
                    print()
                    print()
                    print('{function}() inputs:'.format(function = to.__name__))
                    print()
                    print(inputs)
                    print()
                    print('{function}() outputs:'.format(function = to.__name__))
                    print()
                    print(output)
                    print()
            except Exception as e:
                ex_type, ex_value, ex_traceback = sys.exc_info()
                output = traceback.format_exc()
                print()
                print()
                print('{function}() inputs:'.format(function = to.__name__))
                print()
                print(inputs)
                print()
                print('{function}() EXCEPTION:'.format(function = to.__name__))
                print()
                print(traceback.format_exc())
                print()
        return output
    return app.callback(set, on, using)(to2)

# Plotting

def make_plot(df, height = 350):
    # tz_localize(None) -> https://github.com/plotly/plotly.py/issues/209
    lines  = [go.Scatter(x = df.index.tz_localize(None), y = df[col], name = col) for col in df.columns]
    margin = go.Margin(l = 30, r = 10, t = 10, b = 30, autoexpand = False)
    layout = go.Layout(margin = margin, height = height, showlegend = False)
    figure = {'data': lines, 'layout': layout}
    # plotly(figure)
    return figure

def make_barplot(df, stacked = False):
    idx = df.index
    if df.index.dtype == pd.DatetimeIndex: idx = idx.tz_localize(None)
    bars = [go.Bar(x = idx, y = df[col], name = col) for col in df.columns]
    margin = go.Margin(l = 30, r = 10, t = 10, b = 30, autoexpand = False)
    layout = go.Layout(margin = margin, barmode = 'stack' if stacked else '')
    figure = go.Figure(data = bars, layout = layout)
    # plotly(figure)
    return figure



# %% Helper functions

def make_options(labels, values = None):
    if values == None:
        values = labels
    return [{'label': pair[0], 'value': pair[1]} for pair in zip(labels, values)]

# Aliases
clock    = dcc.Interval
dropdown = dcc.Dropdown
plot     = dcc.Graph

# Add to dashboard.py lib
textinput = lambda **kwargs: dcc.Input(type = 'text', className = 'form-control', **kwargs)

# Datatable stuff (somehow, we need a row() around the datatable to make it behave layout-wise!)
datatable = lambda id, row_selectable = True, filterable = True, sortable = True, rows = [{}], **kwargs: row([dte.DataTable(id = id, rows = rows, row_selectable = row_selectable, filterable = filterable, sortable = sortable, **kwargs)])
onrows = lambda id: [Input(id, 'selected_row_indices'), Input(id, 'rows')]
rowsof = lambda id: [State(id, 'selected_row_indices'), State(id, 'rows')]
make_datatable = lambda data: data.to_dict('records')
setdatatable = lambda id: Output(id, 'rows')
setrows = setdatatable

def getrows(inputs, id, selected = False):
    
    rows  = '{id}.rows'.format(id = id)
    index = '{id}.selected_row_indices'.format(id = id)
        
    if not rows in inputs or not index in inputs:
        return pd.DataFrame()
    
    data  = inputs[rows]
    index = inputs[index]
    
    if not type(data) is list:
        return pd.DataFrame()
    
    data  = pd.DataFrame(data)
    
    if not selected:
        return data
    
    if selected and not index is None:
        data  = data.iloc[index]
        return data
    
    if selected and index is None:
        return pd.DataFrame()
    
    return pd.DataFrame()

textarea = lambda id, **kwargs: dcc.Textarea(id = id, className = 'form-control', **kwargs)

# Upload button
def upload(id, name, multiple = True):
    return dcc.Upload(id = id, multiple = multiple, children = btn(None, name))

# Get the 
def getupload(inputs, id):
    names = inputs[id + '.filename']
    conts = inputs[id + '.contents']
    dates = inputs[id + '.last_modified']
    if names is None or conts is None or dates is None:
        names = []
        conts = []
        dates = []
    upload = zip(names, conts, dates)
    return upload

def savefile(folder, name, content, date):
    content_type, content_string = content.split(',')
    decoded = base64.b64decode(content_string)
    filepath = folder + '/' + name
    with open(filepath, 'w+b') as file:
        file.write(decoded)
    return os.path.isfile(filepath)

onupload = lambda id: [Input(id, 'contents'), Input(id, 'filename'), Input(id, 'last_modified')]

# Get currently logged in user
def getuser():
    # Credit: dash_auth package source code
    header = flask.request.headers.get('Authorization', None)
    usrpwd = base64.b64decode(header.split('Basic ')[1])
    usrpwd = usrpwd.decode('utf-8')
    usr    = usrpwd.split(':')[0]
    return usr

# Get current URL of loaded page
def geturl(inputs):
    if not '_url' in inputs:        
        return '/'
    url = inputs['_url']
    if url is None:
        return '/'
    else:
        return urllib.parse.unquote(url)

# Classes for hidding
class_hidden  = 'd-none'
class_default = ''





def on2(id):
    elem = app.layout[id]
    if type(elem) in [dcc.Dropdown, dcc.Input, dcc.Slider, dcc.Textarea, dcc.RadioItems]:
        return [Input(id, 'value')]
    if type(elem) in [dcc.Checklist, dcc.RangeSlider]:
        return [Input(id, 'values')]
    if type(elem) in [dcc.Location]:
        return [Input(id, 'pathname')]
    if type(elem) in [dcc.Button]:
        return [Input(id, 'n_clicks')]
    if type(elem) in [dcc.Interval]:
        return [Input(id, 'n_intervals')]
    if type(elem) in [dcc.DatePickerRange, dcc.DatePickerSingle]:
        return [Input(id, 'date')]
    if type(elem) in [dcc.Graph]:
        return [Input(id, 'relayoutData'), Input(id, 'hoverData'), Input(id, 'clickData')]
    return [Input(id, 'children')] # all other

# enable later?
#on = on2