import dash
from dash import dash_table
from dash import html
from dash import dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px

# Importazione CSV
fanta = pd.read_csv('./csv/fantasanremo.csv', sep=',')
# Operazioni preliminari per sistemare il dataframe
fanta.fillna(0, inplace=True)

capitani = ['Tananai', 'Elodie', 'Ultimo', 'Giorgia', 'Modà', 'Colla Zio', 'Marco Mengoni']
punti = ['Punti Serata 1', 'Punti Serata 2', 'Punti Serata 3', 'Punti Serata 4', 'Punti Finale', 'Totale Punti']
selezionate = ['Cantante', 'Squadra', 'Punti Serata 1', 'Punti Serata 2', 'Punti Serata 3', 'Punti Serata 4', 'Punti Finale', 'Somma Punti Classifica', 'Totale Punti']

# Raddoppia i punti dei capitani nell'ultima serata
fanta.loc[fanta['Cantante'].isin(capitani), 'Totale Punti'] += fanta['Punti Finale'] + fanta['Punti Classifica Finale']

fanta = fanta.assign(Somma = fanta['Punti Classifica Serata 2'] + fanta['Punti Classifica Serata 3'] + fanta['Punti Classifica Serata 4'] + fanta['Punti Classifica Finale'])
fanta.rename(columns={'Somma':'Somma Punti Classifica'}, inplace=True)
sorted_fanta = fanta.sort_values(by='Totale Punti', ascending=False)

dropdown = dcc.Dropdown(
    id='punti-dropdown',
    options=[{'label': i, 'value': i} for i in punti],
    value='Totale Punti'
)

table = dash_table.DataTable(
    id='table',
    style_cell={'textAlign': 'center'},
    style_header={
        'backgroundColor': '#636EFA',
        'fontWeight': 'bold',
        'fontSize': '25px'
    }
)

table_csv = dash_table.DataTable(
    id='table_csv',
    columns=[{"name": i, "id": i} for i in selezionate],
    data=sorted_fanta.to_dict("records"),
    style_cell={'textAlign': 'center'},
    style_header={
        'backgroundColor': '#636EFA',
        'fontWeight': 'bold',
        'fontSize': '25px'
    }
)

app = dash.Dash(
    __name__,
    external_stylesheets=['./assets/style.css', dbc.themes.SANDSTONE],
    suppress_callback_exceptions=True
)

server = app.server

app.layout = html.Div(children=[
    html.H1(children='Statistiche Fanta Sanremo'),
    dbc.Row([
        dropdown,
    ], className='mb-4'),
    dbc.Row([
        dbc.Col(
            dcc.Graph(id='box-plot-distribuzione-punti'),
            md=6
        ),
        dbc.Col(
            html.Div(children=[html.H3(children='Classifica'), table],
                     style={'marginBottom': 25, 'marginTop': 25}
            ),
            md=6
        )
    ], className='mb-4'),
    dbc.Row([
        dcc.Graph(id='bar-plot-prestazione')
    ], className='mb-4'),
    dbc.Row([
        table_csv
    ], className='mb-4'),
    dbc.Row([
        dcc.Graph(id='bar-plot-quotazioni')
    ], className='mb-4'),
], style={'background-color': '#C7BEC7',
          'width': 'auto',
          'padding': '25px'})

# Quotazione dei cantanti
@app.callback(
    Output(component_id='bar-plot-quotazioni', component_property='figure'),
    Input(component_id='punti-dropdown', component_property='value')
)
def update_bar_quotazioni(dummy):
    fanta.sort_values(by='Quotazione', ascending=False, inplace=True)
    fig = px.bar(fanta, x='Cantante', y='Quotazione', title=f'Quotazione dei cantanti')
    return fig

# Box plot distribuzione punti
@app.callback(
    Output(component_id='box-plot-distribuzione-punti', component_property='figure'),
    Input(component_id='punti-dropdown', component_property='value')
)
def update_box_distribuzione_punti(punti_scelti):
    fig = px.box(fanta, y=punti_scelti, title=f'Distribuzione dei punti ({punti_scelti})', points='all')
    return fig

# Classifica squadre
@app.callback(
    [Output('table', 'columns'), Output('table', 'data')],
    [Input(component_id='punti-dropdown', component_property='value')]
)
def update_classifica(punti_scelti):
    result = fanta.groupby('Squadra')[punti_scelti].sum().reset_index(name=punti_scelti).sort_values(punti_scelti, ascending=False)
    return [{"name": i, "id": i} for i in ['Squadra', punti_scelti]], result.to_dict("records")

@app.callback(
    Output(component_id='bar-plot-prestazione', component_property='figure'),
    Input(component_id='punti-dropdown', component_property='value')
)
def update_bar_prestazione(punti_scelti):
    # CALCOLO RAPPORTO PRESTAZIONE/QUOTA
    max_punti = (fanta[punti_scelti]).max()
    min_punti = (fanta[punti_scelti]).min()
    max_quota = (fanta['Quotazione']).max()
    min_quota = (fanta['Quotazione']).min()
    # Valore massimo e minimo del rapporto prestazione/quota
    old_max = max_punti / min_quota
    old_min = min_punti / max_quota
    new_max = 100
    new_min = 0
    old_range = (old_max - old_min)
    new_range = (new_max - new_min)
    fanta['Prestazione'] = ((((fanta[punti_scelti] / fanta['Quotazione']) - old_min) * new_range) / old_range) + new_min
    sorted_fanta = fanta.sort_values('Prestazione', ascending=False)
    fig = px.bar(sorted_fanta, x='Cantante', y='Prestazione', title=f'Rapporto {punti_scelti}/Quotazione (Range 0-100)')
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
    
