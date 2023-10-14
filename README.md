# Gaming Dashboard with Dash and Plotly

## Table of Contents
- [Introduction](#introduction)
- [Technologies Used](#technologies-used)
- [Dashboard Logic](#dashboard-logic)
- [Bootstrap Template](#bootstrap-template)
- [Database Extraction](#database-extraction)
  - [Source](#source)
  - [Columns in the Dataset](#columns-in-the-dataset)
  - [Methodology](#methodology)
- [Tables Explained](#tables-explained)
- [Dash Application for Game Analysis](#dash-application-for-game-analysis)
  - [Core Layout](#core-layout)
  - [Sections](#sections)
    - [Releases by Platform (Bar Chart)](#1-releases-by-platform-bar-chart)
    - [Distribution of Games by Genre (Pie Chart)](#2-distribution-of-games-by-genre-pie-chart)
    - [Distribution of Games by ESRB Ratings (Bar Chart)](#3-distribution-of-games-by-esrb-ratings-bar-chart)
    - [Distribution of Metacritic Scores (Histogram)](#4-distribution-of-metacritic-scores-histogram)
    - [Correlation between Metacritic Scores and User Ratings (Scatter Plot)](#5-correlation-between-metacritic-scores-and-user-ratings-scatter-plot)
    - [Trend Analysis: Genre Popularity Over Time (Line Chart)](#6-trend-analysis-genre-popularity-over-time-line-chart)
    - [Ownership Analysis: Most Owned Games (Bar Chart)](#7-ownership-analysis-most-owned-games-bar-chart)
    - [Completion Analysis: Most Beaten Games (Bar Chart)](#8-completion-analysis-most-beaten-games-bar-chart)
    - [Game Releases Over Time (Line Chart)](#9-game-releases-over-time-line-chart)
    - [Prize Money by Country (Table)](#10-prize-money-by-country-table)
    - [Prize Money by Country (Bar Chart)](#11-prize-money-by-country-bar-chart)
  - [Callbacks](#callbacks)
  - [Conclusion](#conclusion)

## Introduction
This project aims to provide a comprehensive dashboard for gaming analytics. It utilizes Dash and Plotly for the backend and a Bootstrap template for the frontend. The data is sourced from the RAWG API.

## Technologies Used
- Python
- Dash
- Plotly
- Pandas
- Bootstrap

## Dashboard Logic
The dashboard is built using Dash, a Python framework for building analytical web applications. The logic is encapsulated in Python functions that generate different sections of the dashboard. These functions are then used in Dash callbacks to update the dashboard dynamically based on user input.

## Bootstrap Template
The frontend of the dashboard uses a Bootstrap template to ensure a responsive and visually appealing design. The template is integrated into the Dash application, allowing for seamless interaction between the frontend and backend.

## Database Extraction

### Source
The data used in this project was sourced from [Kaggle's RAWG Game Dataset](https://www.kaggle.com/datasets/jummyegg/rawg-game-dataset?rvi=1). ### Source
At the same time, this database used [RAWG API](https://rawg.io/apidocs) to get all the videogame information. This API provides a comprehensive collection of video game data, including genres, platforms, ratings, and more.
Although the RAWG API provides a comprehensive collection of video game data, it is limited to 1,000 API calls per month. Given that the Kaggle dataset contains hundreds of thousands of games, it was more practical to use this dataset directly.

### Columns in the Dataset
- **id**: An unique ID identifying this Game in RAWG Database
- **slug**: An unique slug identifying this Game in RAWG Database
- **name**: Name of the game
- **metacritic**: Rating of the game on Metacritic
- **released**: The date the game was released
- **tba**: To be announced state
- **updated**: The date the game was last updated
- **website**: Game Website
- **rating**: Rating rated by RAWG user
- **rating_top**: Maximum rating
- **playtime**: Hours needed to complete the game
- **achievements_count**: Number of achievements in game
- **ratings_count**: Number of RAWG users who rated the game
- **suggestions_count**: Number of RAWG users who suggested the game
- **game_series_count**: Number of games in the series
- **reviews_count**: Number of RAWG users who reviewed the game
- **platforms**: Platforms game was released on. Separated by ||
- **developers**: Game developers. Separated by ||
- **genres**: Game genres. Separated by ||
- **publishers**: Game publishers. Separated by ||
- **esrb_rating**: ESRB ratings
- **added_status_yet**: Number of RAWG users had the game as "Not played"
- **added_status_owned**: Number of RAWG users had the game as "Owned"
- **added_status_beaten**: Number of RAWG users had the game as "Completed"
- **added_status_toplay**: Number of RAWG users had the game as "To play"
- **added_status_dropped**: Number of RAWG users had the game as "Played but not beaten"
- **added_status_playing**: Number of RAWG users had the game as "Playing"

### Methodology
1. **Downloading the Dataset**: The first step was to download the dataset from Kaggle. The dataset is available in CSV format, which makes it easier to manipulate and analyze.
2. **Data Preprocessing**: After downloading, the data was preprocessed using Python's Pandas library. This involved cleaning the data, handling missing values, and converting data types where necessary.
3. **Data Transformation**: Some columns in the dataset contained multiple values separated by delimiters. These were split into lists for easier analysis. For example, the 'genres' column had values separated by '||', which were split into individual genres.
4. **Data Filtering**: The dataset was filtered to only include relevant columns and rows. For instance, games without a Metacritic score were excluded from certain analyses.
5. **Data Aggregation**: The data was grouped by various categories like genre, platform, and year for different types of analyses. This was crucial for generating insights into trends, popularity, and quality of games.

## Tables Explained
- **Game Releases Over Time**: This table shows the number of game releases each year, providing insights into the industry's growth and trends.
- **Releases by Platform**: This table categorizes games based on the platforms they are available on.
- **Distribution of Games by Genre**: This table provides a breakdown of games by their genres.
- **Distribution of Games by ESRB Ratings**: This table categorizes games based on their ESRB ratings.
- **Distribution of Metacritic Scores**: This table shows the distribution of Metacritic scores for games, offering insights into their quality.
- **Correlation between Metacritic Scores and User Ratings**: This table explores the relationship between Metacritic scores and user ratings.
- **Games by Score and Genre**: This table categorizes games based on their scores and genres.
- **Trend Analysis**: This table provides a year-by-year breakdown of the popularity of different genres.
- **Ownership Analysis**: This table lists the most owned games.
- **Completion Analysis**: This table lists the games that have been completed by the most players.
- **Prize Money by Country**: This table shows the countries that have earned the most prize money in gaming competitions.

# Dash Application for Game Analysis

## Core Layout

The core layout is the main dashboard layout that includes dropdowns for genre selection and several key charts:

- **Games by Score and Genre (Scatter Plot)**
- **Distribution of Metacritic Scores by Genre (Box Plot)**
- **Game Releases Over Time (Line Chart)**

## Sections

### 1. Releases by Platform (Bar Chart)

- **What it shows**: This chart displays the number of game releases for each platform.
- **Dropdown**: Allows the user to filter the data by genre.
- **Data Columns**: `platforms`

### 2. Distribution of Games by Genre (Pie Chart)

- **What it shows**: The pie chart shows the distribution of games across different genres.
- **Data Columns**: `genres`

### 3. Distribution of Games by ESRB Ratings (Bar Chart)

- **What it shows**: This bar chart shows how many games fall under each ESRB rating.
- **Dropdown**: Allows the user to filter the data by genre.
- **Data Columns**: `esrb_rating`

### 4. Distribution of Metacritic Scores (Histogram)

- **What it shows**: This histogram shows the distribution of Metacritic scores.
- **Dropdown**: Allows the user to filter the data by genre.
- **Data Columns**: `metacritic`

### 5. Correlation between Metacritic Scores and User Ratings (Scatter Plot)

- **What it shows**: This scatter plot shows the relationship between Metacritic scores and user ratings.
- **Dropdown**: Allows the user to filter the data by genre.
- **Data Columns**: `metacritic`, `rating`

### 6. Trend Analysis: Genre Popularity Over Time (Line Chart)

- **What it shows**: This line chart shows the trend of genre popularity over time based on Metacritic scores.
- **Dropdown**: Allows the user to filter the data by genre.
- **Data Columns**: `year`, `genres`

### 7. Ownership Analysis: Most Owned Games (Bar Chart)

- **What it shows**: This bar chart shows the games that are most owned by users.
- **Dropdown**: Allows the user to filter the data by genre.
- **Data Columns**: `name`, `added_status_owned`

### 8. Completion Analysis: Most Beaten Games (Bar Chart)

- **What it shows**: This bar chart shows the games that have been completed by the most users.
- **Dropdown**: Allows the user to filter the data by genre.
- **Data Columns**: `name`, `added_status_beaten`

### 9. Game Releases Over Time (Line Chart)

- **What it shows**: This line chart shows the number of game releases over time.
- **Dropdown**: Allows the user to filter the data by genre.
- **Data Columns**: `year`

### 10. Prize Money by Country (Table)

- **What it shows**: This table shows the prize money won by different countries.
- **Data Columns**: `Name`, `Prize Money`

### 11. Prize Money by Country (Bar Chart)

- **What it shows**: This bar chart shows the top 10 countries by prize money.
- **Data Columns**: `Name`, `Prize Money`

## Callbacks

The Dash app uses callbacks to update each chart based on user input from dropdowns. Each callback function takes the selected genre from the dropdown as an input and updates the corresponding chart.

For example, in the `update_scatter` function, the scatter plot updates based on the selected genre. The data is filtered, and a new Plotly figure is returned.

## Conclusion

This project aims to provide a well ordered and user-friendly platform for gaming analytics. Utilizing Python for setting the backend side of things and Dash and Plotly for data visualization, the project offers a centralized web to understanding various aspects of the gaming industry.

The dashboard is designed to be interactive, allowing users to filter data based on different criteria such as genre and platform. This functionality enhances the utility of the dashboard for a range of users, including researchers, game developers, and people interested in gaming metrics.

Data sourcing and preprocessing are key components of this project. The data is obtained from Kaggle's RAWG Game Dataset, which provides a comprehensive set of gaming metrics. This dataset is then processed and transformed to fit the analytical needs of the project, ensuring that the visualizations are both accurate and meaningful.

The project also includes various types of analyses, from basic distribution charts to more complex correlations and trends. These analyses offer a more nuanced understanding of the gaming landscape, providing insights into areas like genre popularity, user ratings, and game ownership.

In terms of future development, there are several avenues for expansion. Real-time data integration and the inclusion of more advanced analytical methods, such as predictive analytics, could be considered to enhance the project's capabilities.

