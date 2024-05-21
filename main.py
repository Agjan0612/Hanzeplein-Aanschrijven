import dash.exceptions
import pandas as pd
import openpyxl as pxl
from dash import Dash, html, dcc, callback, Output, Input, State
import plotly.express as px
import numpy as np
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import dash_bootstrap_templates
from dash_bootstrap_templates import load_figure_template
from dash.exceptions import PreventUpdate
import gunicorn

pd.options.display.width= None
pd.options.display.max_columns= None
pd.set_option('display.max_rows', 3000)
pd.set_option('display.max_columns', 3000)



recept_hzp = pd.read_csv('receptverwerking_hanzeplein.txt')


columns_recept = ['UZOVI-rec', 'PATIENTNR-rec','GEBOORTE DATUM-rec', 'MW-rec', 'DATUM AANSCHRIJVEN-rec',
                  'TIJDSTIP AANSCHRIJVEN-rec', 'RECEPTHERKOMST-rec', 'WTG-CODE-rec',
                  'ZI-rec', 'ETIKETNAAM-rec', 'EH-rec', 'AANTAL-rec', 'RECEPTLOCATIE-rec',
                  'VOORSCHRIJVER-rec', 'WTG-TOESLAG-rec', 'BETALER-rec', 'CF? JA/NEE-rec']

recept_hzp.columns = columns_recept

# tijd (dag, week, maand, kwartaal, jaar, dag-maand-jaar, maand-jaar) toevoegen
recept_hzp['DATUM AANSCHRIJVEN-rec'] = pd.to_datetime(recept_hzp['DATUM AANSCHRIJVEN-rec'])
recept_hzp['DAG-rec'] = recept_hzp['DATUM AANSCHRIJVEN-rec'].dt.day
recept_hzp['WEEKDAG-rec'] = recept_hzp['DATUM AANSCHRIJVEN-rec'].dt.day_name()
recept_hzp['WEEKDAGNR-rec'] = recept_hzp['DATUM AANSCHRIJVEN-rec'].dt.dayofweek
recept_hzp['WEEKNR-rec'] = recept_hzp['DATUM AANSCHRIJVEN-rec'].dt.isocalendar().week
recept_hzp['MAAND-rec'] = recept_hzp['DATUM AANSCHRIJVEN-rec'].dt.month
recept_hzp['MAAND-naam-rec'] = recept_hzp['DATUM AANSCHRIJVEN-rec'].dt.month_name()
recept_hzp['KWARTAAL-rec'] = recept_hzp['DATUM AANSCHRIJVEN-rec'].dt.quarter
recept_hzp['JAAR-rec'] = recept_hzp['DATUM AANSCHRIJVEN-rec'].dt.year
recept_hzp['DAG-MAAND-JAAR-rec'] = recept_hzp['DATUM AANSCHRIJVEN-rec'].dt.strftime('%d-%m-%Y')
recept_hzp['WTG-CODE-rec'] = recept_hzp['WTG-CODE-rec'].replace(np.nan, 999)
recept_hzp['WTG-CODE-rec'] = recept_hzp['WTG-CODE-rec'].astype(int)
recept_hzp['CF? JA/NEE-rec'] = recept_hzp['CF? JA/NEE-rec'].str.replace('J', 'CF')
recept_hzp['CF? JA/NEE-rec'] = recept_hzp['CF? JA/NEE-rec'].str.replace('N', 'LOKAAL')



# # Receptherkomst = H, D filteren
# print(recept_hzp['RECEPTHERKOMST-rec'].unique())
# # MW = LSP filteren
# print(recept_hzp['MW-rec'].unique())
# # WTG-CODE-rec: 150, 154, 149, 152, 156 filteren
# print(recept_hzp['WTG-CODE-rec'].unique())

recept_hzp_dashboard = recept_hzp.loc[(recept_hzp['RECEPTHERKOMST-rec']!='H')
                            &(recept_hzp['RECEPTHERKOMST-rec']!='D')
                            &(recept_hzp['MW-rec']!='LSP')
                            &(recept_hzp['RECEPTHERKOMST-rec']!='Z')
                            &(recept_hzp['WTG-CODE-rec']!=150)
                            &(recept_hzp['WTG-CODE-rec']!=149)
                            &(recept_hzp['WTG-CODE-rec']!=154)
                            &(recept_hzp['WTG-CODE-rec']!=152)
                            &(recept_hzp['WTG-CODE-rec']!=156)]



mw = recept_hzp_dashboard.groupby(by=['WEEKNR-rec', 'WEEKDAGNR-rec', 'DAG-MAAND-JAAR-rec', 'DATUM AANSCHRIJVEN-rec' , 'MW-rec'])['MW-rec'].count().to_frame('RECEPTEN PER MEDEWERKER PER DAG').reset_index()
mw_filter = mw.loc[mw['WEEKNR-rec']==16]

#mw_filter1 = mw_filter.sort_values(by=['DATUM'], ascending=True)

bar = px.bar(mw_filter,
             x='DATUM AANSCHRIJVEN-rec',
             y='RECEPTEN PER MEDEWERKER PER DAG',
             color='MW-rec')
#bar.show()
# ===========================================================================================================================================================

mw_week = recept_hzp_dashboard.groupby(by=['WEEKNR-rec', 'MW-rec'])['MW-rec'].count().to_frame('RECEPTEN PER MEDEWERKER PER WEEK').reset_index()

mw_week1 = mw_week.loc[mw_week['WEEKNR-rec']==16]

mw_week1 = mw_week1.sort_values(by='RECEPTEN PER MEDEWERKER PER WEEK', ascending=False)




week = px.bar(mw_week1,
              x='MW-rec',
              y='RECEPTEN PER MEDEWERKER PER WEEK')
#week.show()
# ===========================================================================================================================================================
mw_maand = recept_hzp_dashboard.groupby(by=['MAAND-rec', 'MW-rec'])['MW-rec'].count().to_frame('RECEPTEN PER MEDEWERKER PER MAAND').reset_index()

mw_maand1 = mw_maand.loc[mw_maand['MAAND-rec']==4]

mw_maand1 = mw_maand1.sort_values(by='RECEPTEN PER MEDEWERKER PER MAAND', ascending=False)




maand = px.bar(mw_maand1,
              x='MW-rec',
              y='RECEPTEN PER MEDEWERKER PER MAAND')
#maand.show()



recept_hzp_dashboard1 = recept_hzp_dashboard.sort_values(by=['DATUM AANSCHRIJVEN-rec'], ascending=True)
print(recept_hzp_dashboard1.head(50))



#============================================================================================================================================================

app = Dash(__name__, external_stylesheets=[dbc.themes.COSMO])

server = app.server

app.layout = dbc.Container([
    dcc.Tabs([
        # ========================================================================================================  TAB 1 ==================
        dcc.Tab(label='Dag overzicht',
                children=[
                    html.Br(),
                    html.H1('Apotheek Hanzeplein: Aanschrijven Dagoverzicht', style={'textAlign':'center'}),
                    dbc.Row([
                        dbc.Col([], width=5),
                        dbc.Col([
                            dcc.Dropdown(id='dag-selecteer datum',
                                         options=recept_hzp_dashboard1['DAG-MAAND-JAAR-rec'].unique(),
                                         value=recept_hzp_dashboard1['DAG-MAAND-JAAR-rec'].max())
                                        ], width=2),
                        dbc.Col([], width=5)
                    ]),
                    dbc.Row([
                        dbc.Col([
                            dcc.Graph(id='dag-Aanschrijven')
                        ], width=8),
                        dbc.Col([
                            dcc.Graph(id='dag-CF%')
                        ], width=4)
                    ]),
                    dcc.Graph(id='dag-top medewerkers'),


                ]),
# ========================================================================================================  TAB 2 ==================

        dcc.Tab(label = 'Week overzicht',
                children=[
                    html.Br(),
                    html.H1('Apotheek Hanzeplein: Aanschrijven Weekoverzicht', style={'textAlign':'center'}),
                    dbc.Row([
                        dbc.Col([], width=5),
                        dbc.Col([
                            dcc.Dropdown(id='week-weekselectie',
                                         options=recept_hzp_dashboard1['WEEKNR-rec'].unique(),
                                         value=recept_hzp_dashboard1['WEEKNR-rec'].max())
                        ], width=2),
                        dbc.Col([], width=5)
                    ]),
                    dbc.Row([
                        dbc.Col([
                            dcc.Graph(id='week-Aanschrijven')
                        ], width=8),
                        dbc.Col([
                            dcc.Graph(id='week-CF%')
                        ], width=4)
                    ]),
                    dcc.Graph(id='week-top medewerkers')

                ]),
# ========================================================================================================  TAB 3 ==================

        dcc.Tab(label='Maand overzicht',
                children=[
                    html.Br(),
                    html.H1('Apotheek Hanzeplein: Aanschrijven Maandoverzicht', style={'textAlign':'center'}),
                    dbc.Row([
                        dbc.Col([], width=5),
                        dbc.Col([
                            dcc.RadioItems(id='maand-maandselectie',
                                           options=recept_hzp_dashboard1['MAAND-naam-rec'].unique(),
                                           value=recept_hzp_dashboard1['MAAND-naam-rec'].max(),
                                           inline=True)
                        ], width=2),
                        dbc.Col([], width=5),
                    ]),
                    dbc.Row([
                        dbc.Col([
                            dcc.Graph(id='maand-Aanschrijven')
                        ], width=8),
                        dbc.Col([
                            dcc.Graph(id='maand-CF%')
                        ], width=4)
                    ]),
                    dcc.Graph(id='maand-top mw')
                ]),
# ========================================================================================================  TAB 4 ==================

        dcc.Tab(label='Kwartaal overzicht',
                children=[
                    html.Br(),
                    html.H1('Apotheek Hanzeplein: Aanschrijven Kwartaaloverzicht', style={'textAlign':'center'}),
                    dbc.Row([
                        dbc.Col([], width=5),
                        dbc.Col([
                            dcc.RadioItems(id='kwartaal-kwartaalselectie',
                                           options=recept_hzp_dashboard1['KWARTAAL-rec'].unique(),
                                           value=recept_hzp_dashboard1['KWARTAAL-rec'].max(),
                                           inline=True)
                        ], width=2),
                        dbc.Col([], width=5),
                    ]),
                    dbc.Row([
                        dbc.Col([
                            dcc.Graph(id='kwartaal-aanschrijven')
                        ], width=8),
                        dbc.Col([
                            dcc.Graph(id='kwartaal-CF%')
                        ], width=4)
                    ]),
                    dcc.Graph(id='kwartaal-top mw')

                ]),
# ========================================================================================================  TAB 5 ==================
        dcc.Tab(label='Jaar overzicht',
                children=[
                    html.Br(),
                    html.H1('Apotheek Hanzeplein: Aanschrijven Jaaroverzicht', style={'textAlign':'center'}),
                    dbc.Row([
                        dbc.Col([], width=5),
                        dbc.Col([
                            dcc.RadioItems(id='jaar-jaarselectie',
                                           options=recept_hzp_dashboard1['JAAR-rec'].unique(),
                                           value=recept_hzp_dashboard1['JAAR-rec'].max(),
                                           inline=True)
                        ], width=2),
                        dbc.Col([], width=5)
                    ]),
                    dbc.Row([
                        dbc.Col([
                            dcc.Graph(id='jaar-aanschrijven')
                        ], width=8),
                        dbc.Col([
                            dcc.Graph(id='jaar-CF%')
                        ], width=4)
                    ]),
                    dcc.Graph(id='jaar-top mw')
                ])

    ])
])
# ============================== CALLBACK TAB 1 ====================================================================================
@callback(
    Output('dag-Aanschrijven', 'figure'),
    Input('dag-selecteer datum', 'value')
)

def dag_aanschrijven(dag_selectie):
    dag_regels_mw = recept_hzp_dashboard1.groupby(by=['DAG-MAAND-JAAR-rec', 'MW-rec'])['MW-rec'].count().to_frame('Regels per medewerker').reset_index()
    regels_dag = dag_regels_mw.loc[dag_regels_mw['DAG-MAAND-JAAR-rec']== dag_selectie]
    regels_per_dag = px.bar(regels_dag,
                            x='MW-rec',
                            y='Regels per medewerker',
                            hover_data='Regels per medewerker',
                            text='Regels per medewerker')
    return regels_per_dag

@callback(
    Output('dag-CF%', 'figure'),
    Input('dag-selecteer datum', 'value')
)

def dag_aanschrijven_CF(dag_r):
    dag = recept_hzp_dashboard1.groupby(by=['DAG-MAAND-JAAR-rec', 'CF? JA/NEE-rec'])['CF? JA/NEE-rec'].count().to_frame('CF%').reset_index()
    cf_dag = dag.loc[dag['DAG-MAAND-JAAR-rec']==dag_r]

    CF_perc_dag = px.pie(cf_dag,
                         values='CF%',
                         names='CF? JA/NEE-rec')

    return CF_perc_dag

@callback(
    Output('dag-top medewerkers', 'figure'),
    Input('dag-selecteer datum', 'value')
)

def top_mw_dag(dag_mw_top):
    top_mw = recept_hzp_dashboard1.groupby(by=['DAG-MAAND-JAAR-rec', 'MW-rec'])['MW-rec'].count().to_frame('REGELS PER MEDEWERKER').reset_index()
    top_mw_filter = top_mw.loc[top_mw['DAG-MAAND-JAAR-rec']==dag_mw_top]
    top_mw_filter1 = top_mw_filter.sort_values(by=['REGELS PER MEDEWERKER'], ascending=False)

    top_mw_graph = px.bar(top_mw_filter1,
                          x='MW-rec',
                          y='REGELS PER MEDEWERKER',
                          text='REGELS PER MEDEWERKER')
    return top_mw_graph

# ============================== CALLBACK TAB 2 ====================================================================================

@callback(
    Output('week-Aanschrijven', 'figure'),
    Input('week-weekselectie', 'value')
)
def week_aanschrijven(week):
    weekregels = recept_hzp_dashboard1.groupby(by=['WEEKNR-rec', 'DATUM AANSCHRIJVEN-rec'])['DATUM AANSCHRIJVEN-rec'].count().to_frame('Regels per dag').reset_index()
    weekregels_f = weekregels.loc[weekregels['WEEKNR-rec']==week]

    week_totaal_grafiek = px.bar(weekregels_f,
                                 x='DATUM AANSCHRIJVEN-rec',
                                 y='Regels per dag',
                                 text='Regels per dag')
    return week_totaal_grafiek

@callback(
    Output('week-CF%', 'figure'),
    Input('week-weekselectie', 'value')
)
def week_CF(week):
    CF_week = recept_hzp_dashboard1.groupby(by=['WEEKNR-rec', 'CF? JA/NEE-rec'])['CF? JA/NEE-rec'].count().to_frame('CF%').reset_index()
    CF_week_f = CF_week.loc[CF_week['WEEKNR-rec']==week]
    week_CF_grafiek = px.pie(CF_week_f,
                             values='CF%',
                             names='CF? JA/NEE-rec')
    return week_CF_grafiek

@callback(
    Output('week-top medewerkers', 'figure'),
    Input('week-weekselectie', 'value')
)
def week_top_mw(week):
    mw_week = recept_hzp_dashboard1.groupby(by=['WEEKNR-rec', 'MW-rec'])['MW-rec'].count().to_frame('Regels per medewerker').reset_index()
    mw_week_f = mw_week.loc[mw_week['WEEKNR-rec']==week]
    mw_week_f1 = mw_week_f.sort_values(by=['Regels per medewerker'], ascending=False)
    mw_week_grafiek = px.bar(mw_week_f1,
                             x='MW-rec',
                             y='Regels per medewerker',
                             text='Regels per medewerker')
    return mw_week_grafiek

# ============================== CALLBACK TAB 3 ====================================================================================

@callback(
    Output('maand-Aanschrijven', 'figure'),
    Input('maand-maandselectie', 'value')
)
def maand_aanschrijven(maand):
    maand_rec = recept_hzp_dashboard1.groupby(by=['MAAND-naam-rec', 'WEEKNR-rec'])['WEEKNR-rec'].count().to_frame('Regels per week').reset_index()
    maand_rec_f = maand_rec.loc[maand_rec['MAAND-naam-rec']==maand]
    maand_aanschrijven_grafiek = px.bar(maand_rec_f,
                                        x='WEEKNR-rec',
                                        y='Regels per week',
                                        text='Regels per week')
    return maand_aanschrijven_grafiek

@callback(
    Output('maand-CF%', 'figure'),
    Input('maand-maandselectie', 'value')
)
def maand_cf(maand):
    maand_cf = recept_hzp_dashboard1.groupby(by=['MAAND-naam-rec', 'CF? JA/NEE-rec'])['CF? JA/NEE-rec'].count().to_frame('CF%').reset_index()
    maand_cf_f = maand_cf.loc[maand_cf['MAAND-naam-rec']==maand]
    maand_cf_grafiek = px.pie(maand_cf_f,
                              values='CF%',
                              names='CF? JA/NEE-rec')
    return maand_cf_grafiek

@callback(
    Output('maand-top mw', 'figure'),
    Input('maand-maandselectie', 'value')
)

def maand_top_mw(maand):
    maand_mw = recept_hzp_dashboard1.groupby(by=['MAAND-naam-rec', 'MW-rec'])['MW-rec'].count().to_frame('Regels per medewerker').reset_index()
    maand_mw_f = maand_mw.loc[maand_mw['MAAND-naam-rec']==maand]
    maand_mw_f_sort = maand_mw_f.sort_values(by=['Regels per medewerker'], ascending=False)
    maand_mw_grafiek = px.bar(maand_mw_f_sort,
                              x='MW-rec',
                              y='Regels per medewerker',
                              text='Regels per medewerker')
    return maand_mw_grafiek

# ============================== CALLBACK TAB 4 ====================================================================================

@callback(
    Output('kwartaal-aanschrijven', 'figure'),
    Input('kwartaal-kwartaalselectie', 'value')
)
def kwartaal_aanschrijven(kwartaal):
    kwartaal_rec = recept_hzp_dashboard1.groupby(by=['KWARTAAL-rec','MAAND-rec', 'MAAND-naam-rec'])['MAAND-naam-rec'].count().to_frame('Regels per maand').reset_index()
    kwartaal_rec_f = kwartaal_rec.loc[kwartaal_rec['KWARTAAL-rec']==kwartaal]
    kwartaal_rec_f_sort = kwartaal_rec_f.sort_values(by=['MAAND-rec'], ascending=True)
    kwartaal_grafiek = px.bar(kwartaal_rec_f_sort,
                              x='MAAND-naam-rec',
                              y='Regels per maand',
                              text='Regels per maand')
    return kwartaal_grafiek

@callback(
    Output('kwartaal-CF%', 'figure'),
    Input('kwartaal-kwartaalselectie', 'value')
)
def kwartaal_CF(kwartaal):
    kwartaal_CF = recept_hzp_dashboard1.groupby(by=['KWARTAAL-rec', 'CF? JA/NEE-rec'])['CF? JA/NEE-rec'].count().to_frame('CF%').reset_index()
    kwartaal_CF_f = kwartaal_CF.loc[kwartaal_CF['KWARTAAL-rec']==kwartaal]
    kwartaal_CF_grafiek = px.pie(kwartaal_CF_f,
                                 values='CF%',
                                 names='CF? JA/NEE-rec')
    return kwartaal_CF_grafiek


@callback(
    Output('kwartaal-top mw', 'figure'),
    Input('kwartaal-kwartaalselectie', 'value')
)

def kwartaal_mw(kwartaal):
    kwartaal_mw_top = recept_hzp_dashboard1.groupby(by=['KWARTAAL-rec', 'MW-rec'])['MW-rec'].count().to_frame('Regels per medewerker').reset_index()
    kwartaal_mw_top_f = kwartaal_mw_top.loc[kwartaal_mw_top['KWARTAAL-rec']==kwartaal]
    kwartaal_mw_top_f_sort = kwartaal_mw_top_f.sort_values(by=['Regels per medewerker'], ascending=False)
    kwartaal_mw_top_grafiek = px.bar(kwartaal_mw_top_f_sort,
                                     x='MW-rec',
                                     y='Regels per medewerker',
                                     text='Regels per medewerker')
    return kwartaal_mw_top_grafiek

# ============================== CALLBACK TAB 5 ====================================================================================

@callback(
    Output('jaar-aanschrijven', 'figure'),
    Input('jaar-jaarselectie', 'value')
)

def jaar_aanschrijven(jaar):
    jaar_recept = recept_hzp_dashboard1.groupby(by=['JAAR-rec', 'MAAND-rec', 'MAAND-naam-rec'])['MAAND-rec'].count().to_frame('Regels per maand').reset_index()
    jaar_recept_f = jaar_recept.loc[jaar_recept['JAAR-rec']==jaar]
    jaar_recept_f_sort = jaar_recept_f.sort_values(by=['MAAND-rec'], ascending=True)
    jaar_recept_grafiek = px.bar(jaar_recept_f_sort,
                                 x='MAAND-naam-rec',
                                 y='Regels per maand',
                                 text='Regels per maand')
    return jaar_recept_grafiek

@callback(
    Output('jaar-CF%', 'figure'),
    Input('jaar-jaarselectie', 'value')
)

def jaar_CF(jaar):
    jaar_cf = recept_hzp_dashboard1.groupby(by=['JAAR-rec', 'CF? JA/NEE-rec'])['CF? JA/NEE-rec'].count().to_frame('CF%').reset_index()
    jaar_cf_f = jaar_cf.loc[jaar_cf['JAAR-rec']==jaar]
    jaar_cf_grafiek = px.pie(jaar_cf_f,
                             values='CF%',
                             names='CF? JA/NEE-rec')
    return jaar_cf_grafiek

@callback(
    Output('jaar-top mw', 'figure'),
    Input('jaar-jaarselectie', 'value')
)

def jaar_mw_top(jaar):
    jaar_mw = recept_hzp_dashboard1.groupby(by=['JAAR-rec', 'MW-rec'])['MW-rec'].count().to_frame('Regels per medewerker').reset_index()
    jaar_mw_f = jaar_mw.loc[jaar_mw['JAAR-rec']==jaar]
    jaar_mw_f_sort = jaar_mw_f.sort_values(by=['Regels per medewerker'], ascending=False)
    jaar_mw_grafiek = px.bar(jaar_mw_f_sort,
                             x='MW-rec',
                             y='Regels per medewerker',
                             text='Regels per medewerker')
    return jaar_mw_grafiek

if __name__ == '__main__':
    app.run(debug=True)