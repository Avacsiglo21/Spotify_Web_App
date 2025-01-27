import pandas as pd
import numpy as np
import re
import plotly.express as px
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
from wordcloud import WordCloud


# Filter data
df = pd.read_csv("spotify_data_clean.csv", parse_dates=['date']).drop("Unnamed: 0", axis=1)

spotify_df = df.query("year >= 2020 and year <= 2024")

external_stylesheets = [dbc.themes.SLATE, 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.1/css/all.min.css']

date_picker_style = {
    'padding': '5px',
    'borderRadius': '10px',
    'margin': '5px',
    'boxShadow': '1px 1px 2px rgba(10, 10, 10, 0.1)',  
    'width': '300px',
    'font-family': 'Arial, sans-serif',
    'font-size': '24px'  
}

column_style = {
    'box-shadow': '0 4px 8px 0 rgba(0,0,0,0.2)', 
    'padding': '20px', 
    'border-radius': '10px', 
    'background-color': '#ffffff'
}

# Inicializar la aplicación Dash con los estilos de Bootstrap
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.title = "My Spotify Streaming Data"

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.I(className="fab fa-spotify", style={"color": "#1DB954", "fontSize": "4rem"}), width=1),
        dbc.Col(html.H1("My Spotify Streaming Data Journey", className="display-4"), width=10),
        dbc.Col(html.I(className="fas fa-music fa-2x", style={"color": "#1DB954", "fontSize": "4rem"}), width=1)
    ]),

    html.Hr(className="my-2"),

    dbc.Row([
        dbc.Col(
            [html.H5("Select a Date", style={'text-align': 'left'}), 
             dcc.DatePickerRange(
                id='date-picker-range',
                start_date_placeholder_text='2020-03-20',
                end_date_placeholder_text='2024-12-30',
                # calendar_orientation='vertical',
                clearable=True,
                min_date_allowed='2020-03-20',
                max_date_allowed='2024-12-30',
                style=date_picker_style
            ),
             dbc.Tooltip("Start Date = 2020-03-20, End Date=2024-12-30", target="date-picker-range")
            ], 
            width=3
        ),
        dbc.Col([
            html.H4("Total Minutes", style={'text-align': 'center'}), 
            html.H5(id='total-minutes-played', style={'text-align': 'center'})
        ], style=column_style, width=2), 
        dbc.Col([
            html.H4("Average Minutes", style={'text-align': 'center'}),
            html.H5(id='average-minutes-played', style={'text-align': 'center'})
        ], style=column_style, width=2),
        dbc.Col([
            html.H4("Total Tracks", style={'text-align': 'center'}),
            html.H5(id='total_tracks_played', style={'text-align': 'center'})
        ], style=column_style, width=2),
        dbc.Col([
            html.H4("Total Artist", style={'text-align': 'center'}),
            html.H5(id='total_artist_played', style={'text-align': 'center'})
        ], style=column_style, width=2)
        
    
        
    ]),

    html.Hr(className="my-2"),

    dbc.Tabs([
        dbc.Tab(label="My Intro", tab_id="tab-1"),
        dbc.Tab(label="My Most-Played Hits: Artists, Albums, and Tracks", tab_id="tab-2"),
        dbc.Tab(label="My Music Listening Timeline", tab_id="tab-3"),
        dbc.Tab(label="My Music Habits: Weekday and Hours", tab_id="tab-4"),
        dbc.Tab(label="Words that Define My Listening Habits", tab_id="tab-5"),
        
    ], id="tabs", active_tab="tab-1"),
    
    html.Div(id="tab-content")
], fluid=True)

def create_figure(data, x, y):
    fig = px.bar(data, y=y, x=x, template='plotly_white', text_auto=True, text=y, labels={y: ''},
                color_discrete_sequence=px.colors.qualitative.Dark2)
    fig.update_xaxes(visible=False)
    return fig

def create_sunburst(data):
    fig = px.sunburst(data,
                      path=['album_name', 'Minutes Played', 'Counts Albums Played'],
                      values='Minutes Played',
                      template='presentation',
                      color_discrete_sequence=px.colors.qualitative.Dark2,
                      branchvalues='total'
                     )
    return fig

def get_graphs(data_filtered):
    artists_most_played = (data_filtered
                           .groupby('artist_name', as_index=False)
                           .agg({'mins_played': 'sum'})
                           .sort_values('mins_played')
                           .round(2)
                           .tail(3))
    
    albums_most_played = (data_filtered
                          .groupby('album_name')
                          .agg({'mins_played': 'sum', 'album_name': 'count'})
                          .sort_values('mins_played', ascending=False)
                          .round(2)
                          .rename(columns={'album_name': 'Counts Albums Played',
                                           'mins_played':'Minutes Played'})
                          .reset_index()
                          .head(3))
    
    tracks_most_played = (data_filtered
                          .groupby('track_name', as_index=False)
                          .agg({'mins_played': 'sum'})
                          .sort_values('mins_played').round(2).tail(3))

    fig1 = create_figure(artists_most_played, 'mins_played', 'artist_name')
    fig2 = create_sunburst(albums_most_played)
    fig3 = create_figure(tracks_most_played, 'mins_played', 'track_name')
    
    return fig1, fig2, fig3

def create_area_chart(data):
    fig = px.area(data, x='date', y='mins_played', 
                  labels={'mins_played': 'Total Minutes Played', 'date':''}, template='presentation',
                  color_discrete_sequence=px.colors.qualitative.Dark2
                  
                 )
    return fig


def create_scatter_plot(data):

    grouped_data = data.groupby(['day_of_week', 'hour_played'], as_index=False)['mins_played'].sum()
    
    category_orders={'day_of_week':['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'],
                     'hour_played':['12 am', '1 am', '2 am', '3 am', '4 am', '5 am', '6 am', '7 am', '8 am', '9 am', '10 am',
                                    '11 am', '12 pm', '1 pm', '2 pm', '3 pm', '4 pm', '5 pm', '6 pm', '7 pm', '8 pm', 
                                    '9 pm', '10 pm', '11 pm']}
    fig = px.scatter(grouped_data, 
                     x='hour_played', 
                     y='day_of_week', 
                     color='mins_played', 
                     size='mins_played', 
                     size_max=30,
                     labels={'mins_played': 'Total Minutes Played', 'day_of_week': '', 'hour_played': ''}, 
                     category_orders=category_orders,
                     color_continuous_scale=px.colors.sequential.YlGn, 
                     template='plotly_white')

    fig.update_layout(
        xaxis=dict(showline=True, showgrid=True, showticklabels=True,
                   linecolor='rgb(10, 10, 10)', linewidth=1.5,
                   ticks='inside', tickfont=dict(family='Arial', size=14, color='rgb(82, 82, 82)')
        ),
        yaxis=dict(showline=True, showgrid=True, showticklabels=True,
                   linecolor='rgb(10, 10, 10)', linewidth=1.5,
                   ticks='inside', tickfont=dict(family='Arial', size=18, color='rgb(82, 82, 82)')
        )
    )
    
    return fig


def generate_word_cloud_image(text):
    if len(text.split()) < 1:
        raise ValueError("We need at least 1 word to plot a word cloud, got 0.")
    
    wordcloud = WordCloud(max_words=50, background_color='white', colormap='YlGn').generate(text) 
    img_array = wordcloud.to_array() 
    fig = px.imshow(img_array) 
    fig.update_layout(
        xaxis=dict(showticklabels=False), 
        yaxis=dict(showticklabels=False), 
        margin=dict(l=0, r=0, t=0, b=0)
    ) 
    
    return fig

def clean_text(text):
    # Eliminar puntos suspensivos, guiones y cualquier cosa que no sea una palabra
    text = re.sub(r'[^\w\s]', '', text)
    
    return text


@app.callback(
    
    [Output("total_artist_played", "children"),
     Output("total_tracks_played", "children"),
     Output("total-minutes-played", "children"), 
     Output("average-minutes-played", "children"),
     Output("tab-content", "children")], 
    [Input("tabs", "active_tab"), 
     Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date')]
)

def render_tab_content(active_tab, start_date, end_date):
    
    if start_date and end_date:
        
        data_filtered = spotify_df[(spotify_df['date'] >= start_date) & (spotify_df['date'] <= end_date)]
    
    else:
        data_filtered = spotify_df.copy()
    
    total_minutes_played = data_filtered['mins_played'].sum().round()
    average_minutes_played = data_filtered['mins_played'].mean()
    total_tracks_played = data_filtered['track_name'].nunique()
    total_artist_played = data_filtered['artist_name'].nunique()
    
    if active_tab == "tab-1": 
        
        tab_content = dbc.Row([
            html.Hr(className="my-2"),
            html.H4("Welcome to My Spotify Journey", style={'text-align': 'center'}),
            html.Hr(className="my-2"),
            html.B(),
            dbc.Col(dbc.Card([
                html.Hr(className="my-2"),
                html.Spacer(),
                html.P("Uncover the trends and insights within my Spotify listening data. To begin, choose a date range using the calendar. This will filter my Spotify dataset and update the metrics and visualizations in the tabs. View the most played artists and albums in user-friendly charts. Track the trend of total minutes played over time. Analyze the frequency of my Spotify playback by day and hour in a scatter plot. Discover the most common words in my album and song titles through interactive word clouds.", style={'text-align': 'center'}),
                html.Hr(className="my-2")
          
        ]),width=4),
            dbc.Col(html.Img(src=app.get_asset_url('image_spotify_covers.jpg'), style={'max-width': '100%','border': '1px solid #ffffff'}),
                    class_name="card border-light mb-3",style=column_style, width=4),  
            dbc.Col(html.Img(src=app.get_asset_url('image_spotify_covers_2.jpg'), style={'max-width': '100%','border': '1px solid #ffffff'}),
                    class_name="card border-light mb-3", style=column_style, width=4)  
            
        ])

    elif active_tab == "tab-2":
        
        fig1, fig2, fig3 = get_graphs(data_filtered)
        
        tab_content = dbc.Row([
            html.Hr(),
            dbc.Col(dbc.Card([        
                html.H4("Artist Most Played", style={'text-align': 'center'}),
                dcc.Graph(figure=fig1)
            ], 
                    class_name="card border-light mb-3"),style=column_style, width=4),
            dbc.Col(dbc.Card([
                html.H4("Album Most Played", style={'text-align': 'center'}),
                dcc.Graph(figure=fig2)
            ], 
                     
                   class_name="card border-light mb-3" ),style=column_style, width=4),
            dbc.Col(dbc.Card([
                html.H4("Track Most Played", style={'text-align': 'center'}),
                dcc.Graph(figure=fig3)
            ], 
                     
                  class_name="card border-light mb-3"),style=column_style, width=4)
        ])
    
    elif active_tab == "tab-3":
        fig = create_area_chart(data_filtered)
        tab_content = dbc.Row([
            html.Hr(),
            dbc.Col(dbc.Card([
                html.H5("Trend of Total Minutes Played", style={'text-align': 'center'}),
                dcc.Graph(figure=fig)
            ],class_name="card border-light mb-3"), style=column_style, width=12)
        ])
    
    elif active_tab == "tab-4":
        fig = create_scatter_plot(data_filtered)
        tab_content = dbc.Row([
            html.Hr(),
            dbc.Col(dbc.Card([
                html.H5("Frequency of Music Played by Weekday and Hour", style={'text-align': 'center'}),
                dcc.Graph(figure=fig)
            ],class_name="card border-light mb-3"), style=column_style, width=12)
        ])
    
    elif active_tab == "tab-5":
        
        album_text_list = [str(item) for item in data_filtered['album_name'].tolist() if item is not None]
        track_text_list = [str(item) for item in data_filtered['track_name'].tolist() if item is not None]
        
        album_text_list = [clean_text(item) for item in album_text_list]
        track_text_list = [clean_text(item) for item in track_text_list]


        album_text = ' '.join(album_text_list)
        track_text = ' '.join(track_text_list)


        word_cloud_album_fig = generate_word_cloud_image(album_text)
        word_cloud_track_fig = generate_word_cloud_image(track_text)
    
        tab_content = dbc.Row([
            html.Hr(),
            dbc.Col(dbc.Card([html.H5("Album title Words", style={'text-align': 'center'}),
                     dcc.Graph(figure=word_cloud_album_fig)],class_name="card border-light mb-3"),style=column_style, width=6),
            dbc.Col(dbc.Card([html.H5("Track title Words", style={'text-align': 'center'}),
                     dcc.Graph(figure=word_cloud_track_fig)],class_name="card border-light mb-3"),style=column_style, width=6)
    ])


    return f"{total_artist_played:,}", f"{total_tracks_played:,}", f"{total_minutes_played:,}", f"{average_minutes_played:.2f}", tab_content

