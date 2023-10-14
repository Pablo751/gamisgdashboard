
from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import pandas as pd
import dash_table

# Initialize the Dash app
app = Dash(__name__, suppress_callback_exceptions=True)


# Read and preprocess the data
df_countries = pd.read_csv('/countries_table.csv')
df = pd.read_csv('./game_info.csv')
df['released'] = pd.to_datetime(df['released'], errors='coerce')  # Convert to datetime
df['year'] = df['released'].dt.year  # Extract year
df['genres'] = df['genres'].apply(lambda x: x.split('||') if pd.notna(x) and isinstance(x, str) else [])

df_metacritic = df[df['metacritic'].notna() & (df['metacritic'] > 0)].copy()
df_metacritic = df_metacritic.explode('genres')
df_countries['Prize Money'] = df_countries['Prize Money'].str.replace(',', '').str.replace('$', '').astype(float)
# Get the most recent year
most_recent_year = df_countries['Year'].max()

# Filter the DataFrame to only include data for the most recent year
df_recent_year = df_countries[df_countries['Year'] == most_recent_year]

# Sort the DataFrame by 'Prize Money' in descending order
df_recent_year = df_recent_year.sort_values(by='Prize Money', ascending=False)


# Create list of unique genres
unique_genres = df_metacritic['genres'].dropna().unique().tolist()




# Update this function
def create_chart_section(title, chart_id, include_dropdown=False, include_hidden_div=False):
    if chart_id == 'prize-money-bar-chart':
        fig = px.bar(df_recent_year.head(10), x='Name', y='Prize Money', title='Top 10 Countries by Prize Money')
        chart_component = dcc.Graph(id=chart_id, figure=fig)  # directly set the figure here
    else:
        chart_component = dcc.Graph(id=chart_id)
        
    layout = [
        html.H2(title),
        chart_component,  # Use the chart_component here
        html.Hr()  # Horizontal line for separation
    ]
    if include_dropdown:
        dropdown = dcc.Dropdown(
            id=f'{chart_id}-dropdown',
            options=[{'label': 'All Games', 'value': 'All Games'}] + [{'label': genre, 'value': genre} for genre in unique_genres],
            value='All Games'
        )
        layout.insert(1, dropdown)  # insert dropdown just before the chart
        
    if include_hidden_div:
        hidden_div = html.Div(id='hidden-div', style={'display':'none'}, children='initial_value')
        layout.append(hidden_div)
        
    return html.Div(layout)



# Update this function
def create_table_section(title, table_id, columns, data, include_dropdown=False):
    layout = [
        html.H2(title),
    ]
    if include_dropdown:
        layout.append(
            dcc.Dropdown(
                id=f'{table_id}-dropdown',
                options=[{'label': 'All Games', 'value': 'All Games'}] + [{'label': genre, 'value': genre} for genre in unique_genres],
                value='All Games'
            )
        )
    layout.extend([
        dash_table.DataTable(
            id=table_id,
            columns=columns,
            data=data,
        ),
        html.Hr()  # Horizontal line for separation
    ])
    return layout

# Layout of the app
core_layout = html.Div([
    dcc.Dropdown(
        id='genre-dropdown',
        options=[{'label': 'All Games', 'value': 'All Games'}] + [{'label': genre, 'value': genre} for genre in unique_genres],
        value='All Games'
    ),
    html.H2('Games by score and Genre'),
    dcc.Graph(id='scatter-plot'),
    html.Hr(),
    html.H2('Distribution of Metacritic Scores by Genre'),
    dcc.Graph(id='box-plot'),
    html.Hr(),
    html.H2('Game Releases Over Time'),
    dcc.Graph(id='time-series-plot'),
], id='core-layout') 

# New app.layout for routing
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),  # for routing
    html.Div(id='page-content')  # content will be rendered here
])

# Use the helper functions to append sections
sections_to_add = [
    create_chart_section('Releases by Platform', 'platform-bar-chart', include_dropdown=True),
    create_chart_section('Distribution of Games by Genre', 'pie-chart', include_dropdown=False),
    create_chart_section('Distribution of Games by ESRB Ratings', 'esrb-bar-chart', include_dropdown=True),
    create_chart_section('Distribution of Metacritic Scores', 'metacritic-histogram', include_dropdown=True),
    create_chart_section('Correlation between Metacritic Scores and User Ratings', 'correlation-scatter', include_dropdown=True),
    create_chart_section('Trend Analysis: Genre Popularity Over Time (Games with Metascore)', 'trend-line-plot', include_dropdown=True),
    create_chart_section('Ownership Analysis: Most Owned Games', 'ownership-bar-chart', include_dropdown=True),
    create_chart_section('Completion Analysis: Most Beaten Games', 'completion-bar-chart', include_dropdown=True),
    create_chart_section('Game Releases Over Time', 'time-series-plot', include_dropdown=True),
    create_table_section('Prize Money by Country (Table)', 'prize-money-table', [{"name": i, "id": i} for i in df_recent_year.columns], df_recent_year.head(10).to_dict('records')),
    create_chart_section('Prize Money by Country (Bar Chart)', 'prize-money-bar-chart', include_dropdown=False, include_hidden_div=True),
    create_chart_section('Games by Score and Genre', 'scatter-plot', include_dropdown=True),
    create_chart_section('Distribution of Metacritic Scores by Genre', 'box-plot', include_dropdown=True)


    ]



# Callback for scatter plot
@app.callback(
    Output('scatter-plot', 'figure'),
    [Input('scatter-plot-dropdown', 'value')]
)
def update_scatter(selected_genre):
    if selected_genre == 'All Games':
        filtered_df = df_metacritic
    else:
        filtered_df = df_metacritic[df_metacritic['genres'] == selected_genre]

    # Limit to top 20 games based on Metacritic score
    filtered_df = filtered_df.nlargest(20, 'metacritic')

    # Check if 'name' column contains any NaN values
    filtered_df = filtered_df.dropna(subset=['name'])  # Drop rows with NaN in 'name' column

    fig = px.scatter(filtered_df, x='metacritic', y='name', title=f'Games in Genre: {selected_genre}',
                     labels={'metacritic': 'Metacritic Score', 'name': 'Game Name'}, height=800)

    return fig


# Callback for box plot
@app.callback(
    Output('box-plot', 'figure'),
    [Input('box-plot-dropdown', 'value')]
)
def update_boxplot(selected_genre):
    if selected_genre == 'All Games':
        filtered_df = df_metacritic
    else:
        filtered_df = df_metacritic[df_metacritic['genres'] == selected_genre]
    
    # Group by genres and calculate the median
    sorted_genres = filtered_df.groupby('genres')['metacritic'].median().sort_values(ascending=False).index.tolist()

    # Use Categorical data type to impose an order on the 'genres' column based on sorted_genres
    filtered_df['genres'] = pd.Categorical(filtered_df['genres'], categories=sorted_genres, ordered=True)
    
    # Sort the DataFrame by 'genres'
    filtered_df.sort_values('genres', inplace=True)
    
    fig = px.box(filtered_df, x='genres', y='metacritic', title=f'Distribution of Metacritic Scores in Genre: {selected_genre}',
                 labels={'metacritic': 'Metacritic Score', 'genres': 'Genre'})
    
    return fig

# Modified callback
@app.callback(
    Output('time-series-plot', 'figure'),
    [Input('time-series-plot-dropdown', 'value')]  # Changed ID
)
def update_time_series(selected_genre):
    if selected_genre == 'All Games':
        filtered_df = df
    else:
        filtered_df = df[df['genres'].apply(lambda x: selected_genre in x)]
    
    # Filter to only include data up to the year 2020
    filtered_df = filtered_df[filtered_df['year'] <= 2020]
    
    time_series_df = filtered_df.groupby('year').size().reset_index(name='count').dropna()
    
    fig = px.line(time_series_df, x='year', y='count', title=f'Number of Game Releases Over Time in Genre: {selected_genre}')
    return fig

# Callback for pie chart
@app.callback(
    Output('pie-chart', 'figure'),
    [Input('pie-chart-dropdown', 'value')]
)
def update_pie_chart(selected_genre):
    if selected_genre == 'All Games':
        filtered_df = df_metacritic
    else:
        filtered_df = df_metacritic[df_metacritic['genres'] == selected_genre]
    
    genre_count = filtered_df['genres'].value_counts().reset_index()
    genre_count.columns = ['Genre', 'Count']
    
    fig = px.pie(genre_count, names='Genre', values='Count', title=f'Distribution of Games by Genre: {selected_genre}')
    return fig

# Callback for ESRB bar chart
@app.callback(
    Output('esrb-bar-chart', 'figure'),
    [Input('esrb-bar-chart-dropdown', 'value')]  # Change the Input to be specific to ESRB chart
)
def update_esrb_chart(selected_genre):
    if selected_genre == 'All Games':
        filtered_df = df
    else:
        filtered_df = df[df['genres'].apply(lambda x: selected_genre in x if isinstance(x, list) else False) if 'genres' in df.columns else False]

    esrb_count = filtered_df['esrb_rating'].value_counts().reset_index()
    esrb_count.columns = ['ESRB Rating', 'Count']
    
    fig = px.bar(esrb_count, x='ESRB Rating', y='Count', title=f'Distribution of Games by ESRB Ratings: {selected_genre}')
    return fig


# Callback for Metacritic Histogram
@app.callback(
    Output('metacritic-histogram', 'figure'),
    [Input('metacritic-histogram-dropdown', 'value')]  # Change this line
)
def update_metacritic_histogram(selected_genre):
    if selected_genre == 'All Games':
        filtered_df = df_metacritic
    else:
        filtered_df = df_metacritic[df_metacritic['genres'] == selected_genre]

    fig = px.histogram(filtered_df, x='metacritic', nbins=20, title=f'Distribution of Metacritic Scores: {selected_genre}')
    return fig

# Callback for Platform Bar Chart
@app.callback(
    Output('platform-bar-chart', 'figure'),
    [Input('platform-bar-chart-dropdown', 'value')]
)
def update_platform_chart(selected_genre):
    if selected_genre == 'All Games':
        filtered_df = df
    elif 'genres' in df.columns:
        filtered_df = df[df['genres'].apply(lambda x: selected_genre in x if isinstance(x, list) else False)]
    else:
        filtered_df = pd.DataFrame()


    def split_platforms(x):
        if pd.notna(x) and isinstance(x, str):
            return x.split('||')
        else:
            return []
    
    filtered_df = filtered_df.copy()
    filtered_df['platforms'] = filtered_df['platforms'].apply(split_platforms)
    
    platform_df = filtered_df.explode('platforms')
    
    platform_count = platform_df['platforms'].value_counts().reset_index()
    platform_count.columns = ['Platform', 'Count']

    fig = px.bar(platform_count, x='Platform', y='Count', title=f'Popularity by Platform: {selected_genre}',
            text='Count')
    
    fig.update_traces(texttemplate='%{text}', textposition='outside')

    return fig

 #New Callback to update the correlation scatter plot
@app.callback(
    Output('correlation-scatter', 'figure'),
    [Input('correlation-scatter-dropdown', 'value')]
)
def update_correlation_scatter(selected_genre):
    if selected_genre == 'All Games':
        filtered_df = df_metacritic
    else:
        filtered_df = df_metacritic[df_metacritic['genres'] == selected_genre]

    fig = px.scatter(filtered_df, x='metacritic', y='rating', title=f'Correlation between Metacritic Scores and User Ratings: {selected_genre}',
                     labels={'metacritic': 'Metacritic Score', 'rating': 'User Rating'})

    return fig

@app.callback(
    Output('trend-line-plot', 'figure'),
    [Input('trend-line-plot-dropdown', 'value')]
)
def update_trend_line(selected_genre):
    if selected_genre == 'All Games':
        filtered_df = df_metacritic  # Use the exploded DataFrame here
    else:
        filtered_df = df_metacritic[df_metacritic['genres'] == selected_genre]
    
    # Group by year and genre, then count the number of games
    trend_df = filtered_df.groupby(['year', 'genres']).size().reset_index(name='count')

    fig = px.line(trend_df, x='year', y='count', color='genres', title=f'Trend Analysis: Genre Popularity Over Time in {selected_genre}')
    
    return fig

# New Callback to update the ownership bar chart
@app.callback(
    Output('ownership-bar-chart', 'figure'),
    [Input('ownership-bar-chart-dropdown', 'value')]
)
def update_ownership_bar(selected_genre):
    if selected_genre == 'All Games':
        filtered_df = df
    else:
        filtered_df = df[df['genres'].apply(lambda x: selected_genre in x if isinstance(x, list) else False)]
    
    # Sort games by 'added_status_owned' and take the top 20
    top_owned_games = filtered_df.nlargest(20, 'added_status_owned')

    fig = px.bar(top_owned_games, x='name', y='added_status_owned', title=f'Most Owned Games in Genre: {selected_genre}',
                 labels={'added_status_owned': 'Number of Owners', 'name': 'Game Name'})
    
    return fig

# New Callback to update the completion bar chart
@app.callback(
    Output('completion-bar-chart', 'figure'),
    [Input('completion-bar-chart-dropdown', 'value')]
)
def update_completion_bar(selected_genre):
    if selected_genre == 'All Games':
        filtered_df = df
    else:
        filtered_df = df[df['genres'].apply(lambda x: selected_genre in x if isinstance(x, list) else False)]
    
    # Sort games by 'added_status_beaten' and take the top 20
    top_beaten_games = filtered_df.nlargest(20, 'added_status_beaten')

    fig = px.bar(top_beaten_games, x='name', y='added_status_beaten', title=f'Most Beaten Games in Genre: {selected_genre}',
                 labels={'added_status_beaten': 'Number of Users Who Beat the Game', 'name': 'Game Name'})
    
    return fig




@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def display_page(pathname):
    if pathname == '/':
        return core_layout  # the main dashboard layout
    elif pathname == '/platform-bar-chart':
        return create_chart_section('Releases by Platform', 'platform-bar-chart', include_dropdown=True)
    elif pathname == '/pie-chart':
        return create_chart_section('Distribution of Games by Genre', 'pie-chart', include_dropdown=True)
    elif pathname == '/esrb-bar-chart':
        return create_chart_section('Distribution of Games by ESRB Ratings', 'esrb-bar-chart', include_dropdown=True)
    elif pathname == '/metacritic-histogram':
        return create_chart_section('Distribution of Metacritic Scores', 'metacritic-histogram', include_dropdown=True)
    elif pathname == '/correlation-scatter':
        return create_chart_section('Correlation between Metacritic Scores and User Ratings', 'correlation-scatter', include_dropdown=True)
    elif pathname == '/trend-line-plot':
        return create_chart_section('Trend Analysis: Genre Popularity Over Time (Games with Metascore)', 'trend-line-plot', include_dropdown=True)
    elif pathname == '/ownership-bar-chart':
        return create_chart_section('Ownership Analysis: Most Owned Games', 'ownership-bar-chart', include_dropdown=True)
    elif pathname == '/completion-bar-chart':
        return create_chart_section('Completion Analysis: Most Beaten Games', 'completion-bar-chart', include_dropdown=True)
    elif pathname == '/prize-money-table':
        return create_table_section('Prize Money by Country (Table)', 'prize-money-table', [{"name": i, "id": i} for i in df_recent_year.columns], df_recent_year.head(10).to_dict('records'))
    elif pathname == '/prize-money-bar-chart':
        return create_chart_section('Prize Money by Country (Bar Chart)', 'prize-money-bar-chart')
    elif pathname == '/time-series-only':
        return create_chart_section('Game Releases Over Time', 'time-series-plot', include_dropdown=True),
    elif pathname == '/scatter-plot':  
        return create_chart_section('Games by Score and Genre', 'scatter-plot', include_dropdown=True),
    elif pathname == '/box-plot':  
        return create_chart_section('Distribution of Metacritic Scores by Genre', 'box-plot', include_dropdown=True)


    else:
        return '404'  # If the user tries a route that's not defined, return a 404 message



# Run the app

if __name__ == '__main__':
    app.run_server(debug=True, port=8054)  # Here, the port is changed to 8051
