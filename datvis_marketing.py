from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import dash_table
import numpy as np
from datetime import datetime

# Initialize the Dash app
app = Dash(__name__, suppress_callback_exceptions=True)

# For deployment
server = app.server

# Read and preprocess the data
df_countries = pd.read_csv('countries_table.csv')
df = pd.read_csv('game_info.csv')
df['released'] = pd.to_datetime(df['released'], errors='coerce')
df['year'] = df['released'].dt.year
df['genres'] = df['genres'].apply(lambda x: x.split('||') if pd.notna(x) and isinstance(x, str) else [])

# Marketing Data Preprocessing
df_metacritic = df[df['metacritic'].notna() & (df['metacritic'] > 0)].copy()
df_metacritic = df_metacritic.explode('genres')

# Create Marketing KPIs
def calculate_marketing_metrics(df):
    """Calculate key marketing metrics for each game"""
    marketing_df = df.copy()
    
    # Customer Lifecycle Metrics
    marketing_df['total_users'] = (marketing_df['added_status_yet'].fillna(0) + 
                                  marketing_df['added_status_owned'].fillna(0) + 
                                  marketing_df['added_status_beaten'].fillna(0) + 
                                  marketing_df['added_status_toplay'].fillna(0) + 
                                  marketing_df['added_status_dropped'].fillna(0) + 
                                  marketing_df['added_status_playing'].fillna(0))
    
    # Conversion Funnel Metrics
    marketing_df['awareness_rate'] = marketing_df['total_users'] / marketing_df['total_users'].max()
    marketing_df['ownership_rate'] = marketing_df['added_status_owned'].fillna(0) / marketing_df['total_users'].replace(0, 1)
    marketing_df['engagement_rate'] = marketing_df['added_status_playing'].fillna(0) / marketing_df['added_status_owned'].fillna(1).replace(0, 1)
    marketing_df['completion_rate'] = marketing_df['added_status_beaten'].fillna(0) / marketing_df['added_status_owned'].fillna(1).replace(0, 1)
    marketing_df['churn_rate'] = marketing_df['added_status_dropped'].fillna(0) / marketing_df['added_status_owned'].fillna(1).replace(0, 1)
    
    # Engagement Score (0-100)
    marketing_df['engagement_score'] = (
        (marketing_df['ownership_rate'] * 0.3) + 
        (marketing_df['engagement_rate'] * 0.4) + 
        (marketing_df['completion_rate'] * 0.3)
    ) * 100
    
    # Customer Lifetime Value Proxy
    marketing_df['clv_proxy'] = (marketing_df['playtime'].fillna(0) * 
                                marketing_df['rating'].fillna(0) * 
                                marketing_df['completion_rate'])
    
    return marketing_df

# Apply marketing metrics
df_marketing = calculate_marketing_metrics(df)
df_marketing_exploded = df_marketing.explode('genres')

# Cohort Analysis by Release Year
def create_cohort_data(df):
    """Create cohort analysis data"""
    cohort_data = []
    years = sorted(df['year'].dropna().unique())
    
    for year in years:
        if year >= 2000 and year <= 2020:  # Focus on relevant years
            year_games = df[df['year'] == year]
            avg_ownership = year_games['ownership_rate'].mean()
            avg_engagement = year_games['engagement_rate'].mean() 
            avg_completion = year_games['completion_rate'].mean()
            avg_churn = year_games['churn_rate'].mean()
            
            cohort_data.append({
                'year': year,
                'avg_ownership_rate': avg_ownership,
                'avg_engagement_rate': avg_engagement,
                'avg_completion_rate': avg_completion,
                'avg_churn_rate': avg_churn,
                'games_released': len(year_games)
            })
    
    return pd.DataFrame(cohort_data)

cohort_df = create_cohort_data(df_marketing)

# Genre Performance Analysis
def analyze_genre_performance():
    """Analyze marketing performance by genre"""
    genre_perf = df_marketing_exploded.groupby('genres').agg({
        'engagement_score': 'mean',
        'ownership_rate': 'mean',
        'completion_rate': 'mean',
        'churn_rate': 'mean',
        'clv_proxy': 'mean',
        'total_users': 'sum',
        'metacritic': 'mean'
    }).round(3)
    
    genre_perf = genre_perf.sort_values('engagement_score', ascending=False)
    return genre_perf.reset_index()

genre_performance = analyze_genre_performance()

# Create unique genres list
unique_genres = df_marketing_exploded['genres'].dropna().unique().tolist()

# Marketing Dashboard Layout Components
def create_marketing_kpi_cards():
    """Create KPI cards for key marketing metrics"""
    total_games = len(df_marketing)
    avg_engagement = df_marketing['engagement_score'].mean()
    avg_completion_rate = df_marketing['completion_rate'].mean() * 100
    top_genre = genre_performance.iloc[0]['genres']
    
    return html.Div([
        html.Div([
            html.H3(f"{total_games:,}", className="kpi-number"),
            html.P("Total Games Analyzed", className="kpi-label")
        ], className="kpi-card"),
        
        html.Div([
            html.H3(f"{avg_engagement:.1f}", className="kpi-number"),
            html.P("Avg Engagement Score", className="kpi-label")
        ], className="kpi-card"),
        
        html.Div([
            html.H3(f"{avg_completion_rate:.1f}%", className="kpi-number"),
            html.P("Avg Completion Rate", className="kpi-label")
        ], className="kpi-card"),
        
        html.Div([
            html.H3(f"{top_genre}", className="kpi-number"),
            html.P("Top Performing Genre", className="kpi-label")
        ], className="kpi-card"),
    ], className="kpi-container")

def create_enhanced_chart_section(title, chart_id, include_dropdown=False, description=None):
    """Enhanced chart section with business context"""
    layout = [
        html.H2(title, className="chart-title"),
    ]
    
    if description:
        layout.append(html.P(description, className="chart-description"))
    
    if include_dropdown:
        dropdown = dcc.Dropdown(
            id=f'{chart_id}-dropdown',
            options=[{'label': 'All Games', 'value': 'All Games'}] + 
                   [{'label': genre, 'value': genre} for genre in unique_genres],
            value='All Games',
            className="genre-dropdown"
        )
        layout.append(dropdown)
    
    layout.extend([
        dcc.Graph(id=chart_id, className="chart-graph"),
        html.Hr(className="section-divider")
    ])
    
    return html.Div(layout, className="chart-section")

# Marketing-focused layout
marketing_layout = html.Div([
    html.H1("Gaming Marketing Analytics Dashboard", className="main-title"),
    html.P("Data-driven insights for marketing strategy and customer engagement optimization", 
           className="main-subtitle"),
    
    create_marketing_kpi_cards(),
    
    # Customer Lifecycle Analysis
    create_enhanced_chart_section(
        "Customer Lifecycle Funnel", 
        "lifecycle-funnel",
        include_dropdown=True,
        description="Track user journey from awareness to completion - critical for optimizing conversion rates"
    ),
    
    # Cohort Analysis
    create_enhanced_chart_section(
        "Cohort Performance Analysis", 
        "cohort-analysis",
        description="Year-over-year performance trends to identify market shifts and opportunities"
    ),
    
    # Genre Performance Matrix
    create_enhanced_chart_section(
        "Genre Performance Matrix", 
        "genre-matrix",
        description="ROI and engagement analysis by genre - key for content strategy decisions"
    ),
    
    # Engagement Scoring
    create_enhanced_chart_section(
        "Engagement Score Distribution", 
        "engagement-distribution",
        include_dropdown=True,
        description="Proprietary engagement scoring model combining ownership, activity, and completion metrics"
    ),
    
    # Churn Analysis
    create_enhanced_chart_section(
        "Churn vs Retention Analysis", 
        "churn-analysis",
        include_dropdown=True,
        description="Identify patterns in user drop-off to inform retention strategies"
    ),
    
    # Market Penetration
    create_enhanced_chart_section(
        "Market Penetration by Platform", 
        "market-penetration",
        include_dropdown=True,
        description="Platform adoption rates and market share analysis for channel strategy"
    ),
    
    # Business Recommendations
    html.Div([
        html.H2("Strategic Recommendations", className="recommendations-title"),
        html.Div(id="business-recommendations", className="recommendations-content")
    ], className="recommendations-section")
    
], className="marketing-dashboard")

# App layout for routing
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

# Marketing-focused callbacks
@app.callback(
    Output('lifecycle-funnel', 'figure'),
    [Input('lifecycle-funnel-dropdown', 'value')]
)
def update_lifecycle_funnel(selected_genre):
    if selected_genre == 'All Games':
        filtered_df = df_marketing
    else:
        filtered_df = df_marketing[df_marketing['genres'].apply(lambda x: selected_genre in x if isinstance(x, list) else False)]
    
    # Calculate funnel metrics
    total_awareness = filtered_df['total_users'].sum()
    total_owned = filtered_df['added_status_owned'].sum()
    total_playing = filtered_df['added_status_playing'].sum()
    total_completed = filtered_df['added_status_beaten'].sum()
    
    stages = ['Awareness', 'Ownership', 'Active Use', 'Completion']
    values = [total_awareness, total_owned, total_playing, total_completed]
    
    # Calculate conversion rates
    conversion_rates = [100]  # Start at 100% for awareness
    for i in range(1, len(values)):
        if values[0] > 0:
            conversion_rates.append((values[i] / values[0]) * 100)
        else:
            conversion_rates.append(0)
    
    fig = go.Figure()
    
    # Funnel chart
    fig.add_trace(go.Funnel(
        y=stages,
        x=values,
        textinfo="value+percent initial",
        marker=dict(color=["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4"])
    ))
    
    fig.update_layout(
        title=f"Customer Lifecycle Funnel - {selected_genre}",
        font=dict(size=12),
        height=500
    )
    
    return fig

@app.callback(
    Output('cohort-analysis', 'figure')
)
def update_cohort_analysis(_=None):
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Ownership Rate by Year', 'Engagement Rate by Year', 
                       'Completion Rate by Year', 'Churn Rate by Year'),
        specs=[[{"secondary_y": True}, {"secondary_y": True}],
               [{"secondary_y": True}, {"secondary_y": True}]]
    )
    
    # Ownership Rate
    fig.add_trace(
        go.Scatter(x=cohort_df['year'], y=cohort_df['avg_ownership_rate'], 
                  name='Ownership Rate', line=dict(color='#FF6B6B')),
        row=1, col=1
    )
    
    # Engagement Rate  
    fig.add_trace(
        go.Scatter(x=cohort_df['year'], y=cohort_df['avg_engagement_rate'],
                  name='Engagement Rate', line=dict(color='#4ECDC4')),
        row=1, col=2
    )
    
    # Completion Rate
    fig.add_trace(
        go.Scatter(x=cohort_df['year'], y=cohort_df['avg_completion_rate'],
                  name='Completion Rate', line=dict(color='#45B7D1')),
        row=2, col=1
    )
    
    # Churn Rate
    fig.add_trace(
        go.Scatter(x=cohort_df['year'], y=cohort_df['avg_churn_rate'],
                  name='Churn Rate', line=dict(color='#E74C3C')),
        row=2, col=2
    )
    
    fig.update_layout(
        title="Cohort Analysis: Gaming Industry Performance Trends",
        height=600,
        showlegend=False
    )
    
    return fig

@app.callback(
    Output('genre-matrix', 'figure')
)
def update_genre_matrix(_=None):
    # Create bubble chart showing genre performance
    fig = px.scatter(
        genre_performance.head(15), 
        x='completion_rate', 
        y='engagement_score',
        size='total_users',
        color='churn_rate',
        hover_name='genres',
        labels={
            'completion_rate': 'Completion Rate',
            'engagement_score': 'Engagement Score',
            'total_users': 'Total Users',
            'churn_rate': 'Churn Rate'
        },
        title="Genre Performance Matrix: Engagement vs Completion",
        color_continuous_scale='RdYlGn_r'
    )
    
    fig.update_layout(height=600)
    return fig

@app.callback(
    Output('engagement-distribution', 'figure'),
    [Input('engagement-distribution-dropdown', 'value')]
)
def update_engagement_distribution(selected_genre):
    if selected_genre == 'All Games':
        filtered_df = df_marketing
    else:
        filtered_df = df_marketing[df_marketing['genres'].apply(lambda x: selected_genre in x if isinstance(x, list) else False)]
    
    fig = px.histogram(
        filtered_df, 
        x='engagement_score',
        nbins=20,
        title=f'Engagement Score Distribution - {selected_genre}',
        labels={'engagement_score': 'Engagement Score (0-100)', 'count': 'Number of Games'},
        color_discrete_sequence=['#45B7D1']
    )
    
    # Add average line
    avg_score = filtered_df['engagement_score'].mean()
    fig.add_vline(x=avg_score, line_dash="dash", line_color="red", 
                  annotation_text=f"Average: {avg_score:.1f}")
    
    return fig

@app.callback(
    Output('churn-analysis', 'figure'),
    [Input('churn-analysis-dropdown', 'value')]
)
def update_churn_analysis(selected_genre):
    if selected_genre == 'All Games':
        filtered_df = df_marketing_exploded
    else:
        filtered_df = df_marketing_exploded[df_marketing_exploded['genres'] == selected_genre]
    
    # Create churn vs completion scatter plot
    fig = px.scatter(
        filtered_df,
        x='churn_rate',
        y='completion_rate', 
        color='engagement_score',
        size='total_users',
        hover_data=['name', 'metacritic'],
        title=f'Churn vs Completion Analysis - {selected_genre}',
        labels={
            'churn_rate': 'Churn Rate',
            'completion_rate': 'Completion Rate',
            'engagement_score': 'Engagement Score'
        },
        color_continuous_scale='Viridis'
    )
    
    return fig

@app.callback(
    Output('market-penetration', 'figure'),
    [Input('market-penetration-dropdown', 'value')]
)
def update_market_penetration(selected_genre):
    if selected_genre == 'All Games':
        filtered_df = df_marketing
    else:
        filtered_df = df_marketing[df_marketing['genres'].apply(lambda x: selected_genre in x if isinstance(x, list) else False)]
    
    # Process platform data
    platform_data = []
    for _, row in filtered_df.iterrows():
        if pd.notna(row['platforms']):
            platforms = row['platforms'].split('||')
            for platform in platforms:
                platform_data.append({
                    'platform': platform.strip(),
                    'total_users': row['total_users'],
                    'ownership_rate': row['ownership_rate'],
                    'engagement_score': row['engagement_score']
                })
    
    platform_df = pd.DataFrame(platform_data)
    if not platform_df.empty:
        platform_summary = platform_df.groupby('platform').agg({
            'total_users': 'sum',
            'ownership_rate': 'mean',
            'engagement_score': 'mean'
        }).reset_index()
        
        platform_summary = platform_summary.sort_values('total_users', ascending=False).head(10)
        
        fig = px.bar(
            platform_summary,
            x='platform',
            y='total_users',
            color='engagement_score',
            title=f'Market Penetration by Platform - {selected_genre}',
            labels={'total_users': 'Total Users', 'platform': 'Platform'},
            color_continuous_scale='Blues'
        )
        
        fig.update_xaxes(tickangle=45)
        return fig
    
    # Return empty figure if no data
    return px.bar()

@app.callback(
    Output('business-recommendations', 'children')
)
def update_recommendations(_=None):
    # Generate dynamic recommendations based on data
    top_genre = genre_performance.iloc[0]
    worst_churn_genre = genre_performance.loc[genre_performance['churn_rate'].idxmin()]
    best_engagement_genre = genre_performance.loc[genre_performance['engagement_score'].idxmax()]
    
    recommendations = [
        html.Div([
            html.H4("🎯 Content Strategy", className="rec-title"),
            html.P(f"Focus on {top_genre['genres']} genre - highest overall performance with {top_genre['engagement_score']:.1f} engagement score.", className="rec-text")
        ], className="recommendation-card"),
        
        html.Div([
            html.H4("📈 User Retention", className="rec-title"),
            html.P(f"Model retention strategies after {worst_churn_genre['genres']} games - lowest churn rate at {worst_churn_genre['churn_rate']*100:.1f}%.", className="rec-text")
        ], className="recommendation-card"),
        
        html.Div([
            html.H4("🚀 Marketing Investment", className="rec-title"),
            html.P(f"Increase marketing spend on {best_engagement_genre['genres']} - shows highest engagement potential.", className="rec-text")
        ], className="recommendation-card"),
        
        html.Div([
            html.H4("📊 KPI Focus", className="rec-title"), 
            html.P(f"Industry average completion rate is {df_marketing['completion_rate'].mean()*100:.1f}% - focus on improving post-purchase engagement.", className="rec-text")
        ], className="recommendation-card")
    ]
    
    return recommendations

# Routing callback
@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def display_page(pathname):
    if pathname == '/marketing' or pathname == '/' or pathname is None:
        return marketing_layout
    else:
        return html.Div([
            html.H1("404 - Page Not Found"),
            html.P("The page you're looking for doesn't exist."),
            html.A("Go to Marketing Dashboard", href="/marketing")
        ])

# Add custom CSS
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f8f9fa;
                margin: 0;
                padding: 20px;
            }
            .marketing-dashboard {
                max-width: 1200px;
                margin: 0 auto;
            }
            .main-title {
                color: #2c3e50;
                text-align: center;
                font-size: 2.5rem;
                margin-bottom: 10px;
            }
            .main-subtitle {
                text-align: center;
                color: #7f8c8d;
                font-size: 1.2rem;
                margin-bottom: 40px;
            }
            .kpi-container {
                display: flex;
                justify-content: space-around;
                margin-bottom: 40px;
                flex-wrap: wrap;
            }
            .kpi-card {
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                text-align: center;
                min-width: 200px;
                margin: 10px;
            }
            .kpi-number {
                font-size: 2rem;
                font-weight: bold;
                color: #3498db;
                margin: 0;
            }
            .kpi-label {
                color: #7f8c8d;
                margin: 5px 0 0 0;
            }
            .chart-section {
                background: white;
                margin-bottom: 30px;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .chart-title {
                color: #2c3e50;
                margin-bottom: 10px;
            }
            .chart-description {
                color: #7f8c8d;
                font-style: italic;
                margin-bottom: 20px;
            }
            .genre-dropdown {
                margin-bottom: 20px;
            }
            .recommendations-section {
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .recommendations-title {
                color: #2c3e50;
                margin-bottom: 20px;
            }
            .recommendation-card {
                background: #f8f9fa;
                padding: 20px;
                margin-bottom: 15px;
                border-radius: 8px;
                border-left: 4px solid #3498db;
            }
            .rec-title {
                color: #2c3e50;
                margin: 0 0 10px 0;
            }
            .rec-text {
                color: #34495e;
                margin: 0;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

if __name__ == '__main__':
    app.run_server(debug=True, port=8055, host='0.0.0.0') 