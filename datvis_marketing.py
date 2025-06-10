from dash import Dash, dcc, html, Input, Output, dash_table
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime

# Initialize the Dash app
app = Dash(__name__, suppress_callback_exceptions=True)

# For deployment
server = app.server

# Read and preprocess the data
df_countries = pd.read_csv('countries_table.csv')
df = pd.read_csv('game_info.csv')

# Clean data to prevent JSON serialization issues
def clean_text(text):
    if pd.isna(text) or not isinstance(text, str):
        return text
    # Remove control characters that cause JSON issues
    import re
    return re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)

# Clean text columns that might have control characters
text_columns = ['name', 'slug', 'website', 'platforms', 'developers', 'genres', 'publishers', 'esrb_rating']
for col in text_columns:
    if col in df.columns:
        df[col] = df[col].apply(clean_text)

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

# Pre-calculate heavy operations to improve performance
print("Pre-calculating analytics data...")

# Cache frequently used data
df_marketing_clean = df_marketing[df_marketing['total_users'] > 0].copy()
df_marketing_exploded_clean = df_marketing_exploded[df_marketing_exploded['total_users'] > 0].copy()

# Fix the funnel logic - Keep realistic interpretation  
def recalculate_funnel_metrics(df):
    """Recalculate funnel with realistic business logic"""
    df = df.copy()
    
    # Total users (awareness/reach)
    df['total_users'] = (df['added_status_yet'].fillna(0) + 
                        df['added_status_owned'].fillna(0) + 
                        df['added_status_beaten'].fillna(0) + 
                        df['added_status_toplay'].fillna(0) + 
                        df['added_status_dropped'].fillna(0) + 
                        df['added_status_playing'].fillna(0))
    
    # Ownership (purchased/acquired)
    df['owned_users'] = df['added_status_owned'].fillna(0)
    
    # Active Use = Currently playing (snapshot)
    df['active_users'] = df['added_status_playing'].fillna(0)
    
    # Completion = Total ever completed (cumulative)
    df['completed_users'] = df['added_status_beaten'].fillna(0)
    
    return df

# Recalculate with better logic
df_marketing_clean = recalculate_funnel_metrics(df_marketing_clean)
df_marketing_exploded_clean = recalculate_funnel_metrics(df_marketing_exploded_clean)

print("Data pre-processing complete!")

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
            html.P("Avg Community Engagement", className="kpi-label")
        ], className="kpi-card"),
        
        html.Div([
            html.H3(f"{avg_completion_rate:.1f}%", className="kpi-number"),
            html.P("Community Completion Rate", className="kpi-label")
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
        dcc.Loading(
            id=f"loading-{chart_id}",
            type="default",
            children=[dcc.Graph(id=chart_id, className="chart-graph")],
            style={"margin": "20px 0"}
        ),
        html.Hr(className="section-divider")
    ])
    
    return html.Div(layout, className="chart-section")

# Marketing-focused layout
marketing_layout = html.Div([
    html.H1("Gaming Marketing Analytics Dashboard", className="main-title"),
    html.P("Data-driven insights for marketing strategy and customer engagement optimization", 
           className="main-subtitle"),
    
    # Data Disclaimer
    html.Div([
        html.H4("📊 Data Source & Methodology", style={"color": "#2c3e50", "margin-bottom": "10px"}),
        html.P([
            "This dashboard analyzes ", html.Strong("850K+ games"), " from the RAWG gaming database. ",
            "The metrics represent ", html.Strong("user-generated engagement data"), " where community members mark games as 'owned', 'playing', 'completed', etc. ",
            html.Br(),
            "⚠️ ", html.Strong("Important:"), " These are ", html.Em("not actual sales figures"), " but rather community engagement patterns that provide insights into user behavior and game popularity trends."
        ], style={"margin": "10px 0", "line-height": "1.6"}),
        html.P([
            "🎯 ", html.Strong("Business Value:"), " This type of engagement data is valuable for marketing teams to understand genre preferences, completion rates, and user lifecycle patterns."
        ], style={"margin": "10px 0", "color": "#27ae60", "font-weight": "500"})
    ], style={
        "background-color": "#f8f9fa", 
        "padding": "20px", 
        "border-radius": "8px", 
        "border-left": "4px solid #3498db",
        "margin": "20px 0"
    }),
    
    dcc.Loading(
        id="loading-kpis",
        type="default", 
        children=[create_marketing_kpi_cards()],
        style={"margin": "20px 0"}
    ),
    
    # User Engagement Analysis
    create_enhanced_chart_section(
        "User Engagement Funnel", 
        "lifecycle-funnel",
        include_dropdown=True,
        description="Community engagement patterns from game discovery to completion - insights for user acquisition and retention strategies"
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
    ], className="recommendations-section"),
    
    # Top Performing Games Analysis
    create_enhanced_chart_section(
        "Top Reviewed Games Analysis", 
        "top-games-analysis",
        include_dropdown=True,
        description="Identify market leaders and success patterns for competitive intelligence and content strategy"
    ),
    
    # Review Quality vs Volume Matrix  
    create_enhanced_chart_section(
        "Review Quality vs Volume Matrix", 
        "review-matrix",
        include_dropdown=True,
        description="Discover games with both high quality and high buzz - perfect targets for marketing partnerships"
    ),
    
    # Marketing Performance Table
    html.Div([
        html.H2("Top Marketing Targets", className="chart-title"),
        html.P("Games with highest marketing potential based on engagement, reviews, and user metrics", className="chart-description"),
        dcc.Dropdown(
            id='marketing-table-dropdown',
            options=[{'label': 'All Games', 'value': 'All Games'}] + 
                   [{'label': genre, 'value': genre} for genre in unique_genres],
            value='All Games',
            className="genre-dropdown"
        ),
        dcc.Loading(
            id="loading-marketing-table",
            type="default",
            children=[dash_table.DataTable(
                id='marketing-targets-table',
                columns=[
                    {"name": "Game", "id": "name"},
                    {"name": "Genre", "id": "genres"},  
                    {"name": "Metacritic", "id": "metacritic"},
                    {"name": "User Rating", "id": "rating"},
                    {"name": "Engagement Score", "id": "engagement_score"},
                    {"name": "Total Users", "id": "total_users"},
                    {"name": "Completion Rate", "id": "completion_rate"},
                    {"name": "Year", "id": "year"}
                ],
                style_cell={'textAlign': 'left', 'padding': '10px'},
                style_header={'backgroundColor': '#3498db', 'color': 'white', 'fontWeight': 'bold'},
                style_data_conditional=[
                    {
                        'if': {'column_id': 'engagement_score'},
                        'backgroundColor': '#e8f5e8',
                        'color': 'black',
                    }
                ],
                page_size=15,
                sort_action="native"
            )],
            style={"margin": "20px 0"}
        ),
        html.Hr(className="section-divider")
    ], className="chart-section"),
    
    # Critical Success Factors
    create_enhanced_chart_section(
        "Critical Success Factors", 
        "success-factors",
        description="Key metrics correlation analysis - what drives game success for strategic planning"
    )
    
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
    try:
        if selected_genre == 'All Games':
            filtered_df = df_marketing_clean
        else:
            # Use exploded data for genre filtering
            genre_mask = df_marketing_exploded_clean['genres'] == selected_genre
            filtered_df = df_marketing_exploded_clean[genre_mask]
            
            # If no games found for this genre, return empty funnel
            if filtered_df.empty:
                return go.Figure().add_trace(go.Funnel(
                    y=["No Data"],
                    x=[0],
                    text=["No games found for this genre"]
                ))
        
        # Filter to commercial games (100+ total users) for realistic metrics
        commercial_games = filtered_df[filtered_df['total_users'] >= 100]
        
        # Calculate funnel metrics using commercial games only
        total_awareness = commercial_games['total_users'].sum()
        total_owned = commercial_games['owned_users'].sum()
        total_playing = commercial_games['active_users'].sum() 
        total_completed = commercial_games['completed_users'].sum()
        
        # If no commercial games, fall back to top games
        if len(commercial_games) == 0:
            top_games = filtered_df.nlargest(50, 'total_users')
            total_awareness = top_games['total_users'].sum()
            total_owned = top_games['owned_users'].sum()
            total_playing = top_games['active_users'].sum() 
            total_completed = top_games['completed_users'].sum()
        
        stages = ['Awareness', 'Ownership', 'Completion', 'Active Use']
        values = [total_awareness, total_owned, total_completed, total_playing]
        
        # Calculate conversion rates
        conversion_rates = [100]
        for i in range(1, len(values)):
            if values[0] > 0:
                conversion_rates.append((values[i] / values[0]) * 100)
            else:
                conversion_rates.append(0)
        
        fig = go.Figure()
        
        # Funnel chart with better colors
        fig.add_trace(go.Funnel(
            y=stages,
            x=values,
            textinfo="value+percent initial",
            marker=dict(color=["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4"])
        ))
        
        # Use appropriate game count for title
        games_count = len(commercial_games) if len(commercial_games) > 0 else len(filtered_df.nlargest(50, 'total_users'))
        
        fig.update_layout(
            title=f"User Engagement Funnel - {selected_genre} Popular Games ({games_count} games)<br><sub>Community-reported data: Current players vs Total completions - Games with 100+ community members</sub>",
            font=dict(size=12),
            height=500
        )
        
        return fig
        
    except Exception as e:
        # Return error funnel if something goes wrong
        return go.Figure().add_trace(go.Funnel(
            y=["Data Loading Error"],
            x=[1],
            text=[f"Error: {str(e)[:50]}..."]
        ))

@app.callback(
    Output('cohort-analysis', 'figure'),
    [Input('url', 'pathname')]
)
def update_cohort_analysis(pathname):
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
    Output('genre-matrix', 'figure'),
    [Input('url', 'pathname')]
)
def update_genre_matrix(pathname):
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
        filtered_df = df_marketing_clean
    else:
        filtered_df = df_marketing_exploded_clean[df_marketing_exploded_clean['genres'] == selected_genre]
    
    fig = px.histogram(
        filtered_df, 
        x='engagement_score',
        nbins=20,
        title=f'Engagement Score Distribution - {selected_genre} ({len(filtered_df)} games)',
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
        filtered_df = df_marketing_exploded_clean
    else:
        filtered_df = df_marketing_exploded_clean[df_marketing_exploded_clean['genres'] == selected_genre]
    
    # Create churn vs completion scatter plot
    fig = px.scatter(
        filtered_df.head(500),  # Limit for performance
        x='churn_rate',
        y='completion_rate', 
        color='engagement_score',
        size='total_users',
        hover_data=['name', 'metacritic'],
        title=f'Churn vs Completion Analysis - {selected_genre} ({len(filtered_df)} games)',
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
        filtered_df = df_marketing_clean
    else:
        filtered_df = df_marketing_clean[df_marketing_clean['genres'].apply(lambda x: selected_genre in x if isinstance(x, list) else False)]
    
    # Process platform data (optimized)
    platform_data = []
    for _, row in filtered_df.head(1000).iterrows():  # Limit for performance
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
    return px.bar(title="No platform data available")

@app.callback(
    Output('business-recommendations', 'children'),
    [Input('url', 'pathname')]
)
def update_recommendations(pathname):
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

@app.callback(
    Output('top-games-analysis', 'figure'),
    [Input('top-games-analysis-dropdown', 'value')]
)
def update_top_games_analysis(selected_genre):
    if selected_genre == 'All Games':
        filtered_df = df_marketing_exploded[df_marketing_exploded['metacritic'].notna()]
    else:
        filtered_df = df_marketing_exploded[
            (df_marketing_exploded['genres'] == selected_genre) & 
            (df_marketing_exploded['metacritic'].notna())
        ]
    
    # Get top 20 games by combined score (metacritic + user rating + engagement)
    filtered_df['combined_score'] = (
        (filtered_df['metacritic'] / 100 * 0.4) + 
        (filtered_df['rating'] / 5 * 0.3) + 
        (filtered_df['engagement_score'] / 100 * 0.3)
    ) * 100
    
    top_games = filtered_df.nlargest(20, 'combined_score')
    
    fig = px.bar(
        top_games,
        x='combined_score',
        y='name', 
        color='metacritic',
        title=f'Top Reviewed Games - {selected_genre}',
        labels={
            'combined_score': 'Marketing Appeal Score (0-100)',
            'name': 'Game Title',
            'metacritic': 'Metacritic Score'
        },
        color_continuous_scale='Viridis',
        height=800
    )
    
    fig.update_layout(yaxis={'categoryorder': 'total ascending'})
    return fig

@app.callback(
    Output('review-matrix', 'figure'),
    [Input('review-matrix-dropdown', 'value')]
)
def update_review_matrix(selected_genre):
    if selected_genre == 'All Games':
        filtered_df = df_marketing_exploded[
            (df_marketing_exploded['metacritic'].notna()) & 
            (df_marketing_exploded['reviews_count'].notna())
        ]
    else:
        filtered_df = df_marketing_exploded[
            (df_marketing_exploded['genres'] == selected_genre) & 
            (df_marketing_exploded['metacritic'].notna()) & 
            (df_marketing_exploded['reviews_count'].notna())
        ]
    
    # Focus on games with significant review activity
    filtered_df = filtered_df[filtered_df['reviews_count'] > 10]
    
    fig = px.scatter(
        filtered_df.head(200),  # Top 200 for performance
        x='reviews_count',
        y='metacritic',
        size='total_users',
        color='engagement_score',
        hover_data=['name', 'rating', 'year'],
        title=f'Review Quality vs Volume Matrix - {selected_genre}',
        labels={
            'reviews_count': 'Number of Reviews (Buzz Factor)',
            'metacritic': 'Metacritic Score (Quality)',
            'total_users': 'Total Users',
            'engagement_score': 'Engagement Score'
        },
        color_continuous_scale='RdYlBu'
    )
    
    # Add quadrant lines
    median_reviews = filtered_df['reviews_count'].median()
    median_metacritic = filtered_df['metacritic'].median()
    
    fig.add_hline(y=median_metacritic, line_dash="dash", line_color="gray", 
                  annotation_text="Quality Threshold")
    fig.add_vline(x=median_reviews, line_dash="dash", line_color="gray",
                  annotation_text="Buzz Threshold")
    
    return fig

@app.callback(
    Output('marketing-targets-table', 'data'),
    [Input('marketing-table-dropdown', 'value')]
)
def update_marketing_table(selected_genre):
    if selected_genre == 'All Games':
        filtered_df = df_marketing_exploded
    else:
        filtered_df = df_marketing_exploded[df_marketing_exploded['genres'] == selected_genre]
    
    # Calculate marketing priority score
    filtered_df['marketing_score'] = (
        (filtered_df['engagement_score'] / 100 * 0.3) +
        (filtered_df['metacritic'].fillna(0) / 100 * 0.25) +
        (filtered_df['rating'].fillna(0) / 5 * 0.25) +
        (filtered_df['completion_rate'].fillna(0) * 0.2)
    ) * 100
    
    # Get top marketing targets
    top_targets = filtered_df.nlargest(25, 'marketing_score')
    
    # Format data for table
    table_data = []
    for _, row in top_targets.iterrows():
        table_data.append({
            'name': row['name'][:30] + ('...' if len(str(row['name'])) > 30 else ''),
            'genres': row['genres'],
            'metacritic': f"{row['metacritic']:.0f}" if pd.notna(row['metacritic']) else 'N/A',
            'rating': f"{row['rating']:.1f}" if pd.notna(row['rating']) else 'N/A',
            'engagement_score': f"{row['engagement_score']:.1f}",
            'total_users': f"{row['total_users']:,.0f}",
            'completion_rate': f"{row['completion_rate']*100:.1f}%" if pd.notna(row['completion_rate']) else 'N/A',
            'year': f"{row['year']:.0f}" if pd.notna(row['year']) else 'N/A'
        })
    
    return table_data

@app.callback(
    Output('success-factors', 'figure'),
    [Input('url', 'pathname')]
)
def update_success_factors(pathname):
    # Create correlation matrix of key success metrics
    success_metrics = df_marketing_exploded[
        ['metacritic', 'rating', 'total_users', 'engagement_score', 
         'completion_rate', 'ownership_rate', 'playtime']
    ].dropna()
    
    # Calculate correlation matrix
    corr_matrix = success_metrics.corr()
    
    # Create heatmap
    fig = px.imshow(
        corr_matrix,
        labels=dict(x="Metrics", y="Metrics", color="Correlation"),
        x=['Metacritic', 'User Rating', 'Total Users', 'Engagement Score', 
           'Completion Rate', 'Ownership Rate', 'Playtime'],
        y=['Metacritic', 'User Rating', 'Total Users', 'Engagement Score', 
           'Completion Rate', 'Ownership Rate', 'Playtime'],
        color_continuous_scale='RdBu',
        title="Success Factors Correlation Matrix"
    )
    
    # Add correlation values as text
    fig.update_traces(text=corr_matrix.round(2), texttemplate="%{text}")
    fig.update_layout(height=600)
    
    return fig

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