""" Passing Networks """

from mplsoccer import Sbopen
from mplsoccer import Pitch
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import to_rgba
import streamlit as st


parser = Sbopen()
matches = parser.match(55, 282)
matches['match'] = matches['home_team_name'] + ' vs ' + matches['away_team_name']
matches = matches[['match_id', 'home_team_name', 'away_team_name', 'match']]


st.title("Passing Networks")

selected_match = st.selectbox('Select a match', matches['match'].to_list())

match_id = matches.loc[matches['match'] == selected_match, 'match_id'].iloc[0]
home_team = matches.loc[matches['match'] == selected_match, 'home_team_name'].iloc[0]
away_team = matches.loc[matches['match'] == selected_match, 'away_team_name'].iloc[0]

teams = [home_team, away_team]

team_colours = {
    "Netherlands": "#FF8C00",     # bright orange (DarkOrange)
    "Spain": "#FF4C4C",           # bright red
    "Portugal": "#B22222",        # firebrick (lighter than darkred)
    "Denmark": "#FF4C4C",         # bright red
    "England": "white",         
    "Ukraine": "#FFD300",         # bright yellow (high contrast)
    "Czech Republic": "#FF4C4C",  # bright red
    "Austria": "#FF4C4C",         # bright red
    "Romania": "#FFD300",         # bright yellow
    "France": "#4C6FFF",          # brighter navy
    "Albania": "#FF4C4C",         # bright red
    "Germany": "white",         # light gray/white
    "Switzerland": "#FF4C4C",     # bright red
    "Scotland": "#4C6FFF",        # bright navy/blue
    "Croatia": "#FF4C4C",         # bright red
    "Belgium": "#FF4C4C",         # bright red
    "Italy": "#4C9AFF",           # bright azzurri blue
    "Poland": "#FFFFFF",          # white
    "Slovakia": "#4C9AFF",        # bright blue
    "Georgia": "white",         # lighter dark red
    "Turkey": "#FF4C4C",          # bright red
    "Slovenia": "#7CFC00",        # bright green (LawnGreen)
    "Serbia": "#FF4C4C",          # bright red
    "Hungary": "#FF4C4C",         # bright red
}


col1, col2 = st.columns(2)

df, related, freeze, tactics = parser.event(match_id)

for i, team in enumerate(teams):

    # pick which column to draw into
    col = col1 if i == 0 else col2

    with col:

        pitch = Pitch(pitch_type='statsbomb', pitch_color="#0E1117", line_color="white")
        fig, ax = plt.subplots(figsize=(9, 6))

        team_df = df.loc[df['team_name'] == team]

        substitutions = team_df.loc[df['type_name'] == 'Substitution']
        first_sub = substitutions['index'].iloc[0]

        # cleanining the dataframe of passes
        passes = team_df.loc[team_df['type_name'] == 'Pass'].set_index('id')
        passes = passes[['index', 'player_name', 'pass_recipient_name', 'x', 'y', 'end_x', 'end_y', 'outcome_name']]
        passes = passes[passes['outcome_name'].isna()].drop(columns=['outcome_name'])
        passes = passes[passes['index'] < first_sub]

        # creating passing links
        passing_links = passes.groupby(['player_name', 'pass_recipient_name']).size().reset_index(name='pass_count')
        max_line_width = 8
        passing_links['line_width'] = (passing_links['pass_count'] / passing_links['pass_count'].max() * max_line_width) + 1

        # average positions
        avg_pass_pos = passes.groupby('player_name')[['x', 'y']].mean().reset_index()
        avg_rec_pos = passes.groupby('pass_recipient_name')[['end_x', 'end_y']].mean().reset_index()
        positions = pd.concat([avg_pass_pos, avg_rec_pos], axis=1)
        positions['x'] = (positions['x'] + positions['end_x']) / 2
        positions['y'] = (positions['y'] + positions['end_y']) / 2

        # marker sizes (involvement)
        max_marker_size = 500
        involvement = []
        for player in positions['player_name']:
            passes_made = len(passes.loc[passes['player_name'] == player])
            passes_received = len(passes.loc[passes['pass_recipient_name'] == player])
            involvement.append(passes_made + passes_received)
        positions['count'] = involvement
        positions['marker_size'] = (positions['count'] / positions['count'].max() * max_marker_size) + 100

        # jersey numbers
        lineup = parser.lineup(match_id)
        positions = positions.merge(lineup[['player_name', 'jersey_number']], on='player_name', how='left')
        positions = positions.set_index('player_name')

        # merge positions into passing links
        passing_links = passing_links.merge(positions[['x', 'y']], left_on='player_name', right_index=True).rename(columns={'x': 'x0', 'y': 'y0'})
        passing_links = passing_links.merge(positions[['x', 'y']], left_on='pass_recipient_name', right_index=True).rename(columns={'x': 'x1', 'y': 'y1'})

        if i == 1:
            positions['x'] = 120 - positions['x']
            positions['y'] = 80 - positions['y']
            passing_links['x0'] = 120 - passing_links['x0']
            passing_links['y0'] = 80 - passing_links['y0']
            passing_links['x1'] = 120 - passing_links['x1']
            passing_links['y1'] = 80 - passing_links['y1']

        # transparency gradient
        min_transparency = 0.05
        base_color = np.array(to_rgba(team_colours[team]))
        color = np.tile(base_color, (len(passing_links), 1))
        c_transparency = passing_links['pass_count'] / passing_links['pass_count'].max()
        c_transparency = (c_transparency * (1 - min_transparency)) + min_transparency
        color[:, 3] = c_transparency

        # draw links
        pitch.lines(
            passing_links['x0'], passing_links['y0'],
            passing_links['x1'], passing_links['y1'],
            ax=ax, color=color, zorder=1,
            linestyle='-', lw=passing_links['line_width']
        )

        # draw player positions
        pitch.scatter(
            positions['x'], positions['y'],
            s=positions['marker_size'], facecolor='white',
            edgecolors='black', zorder=2, linewidth=1, alpha=1, ax=ax
        )

        # jersey numbers
        for _, pos in positions.iterrows():
            pitch.annotate(
                int(pos['jersey_number']) if not np.isnan(pos['jersey_number']) else "",
                xy=(pos['x'], pos['y']), c='black',
                va='center', ha='center', size=9.5, weight='bold', ax=ax
            )


        if i == 0:
            fig.text(
                0.16, 0.91, team,
                ha="left", va="top", color = "white",
                fontsize=16, fontweight="bold"
            )
        
        # Second team → top right
        else:
            fig.text(
                0.86, 0.91, team,
                ha="right", va="top", color="white",
                fontsize=16, fontweight="bold"
            )
        pitch.draw(ax=ax)
        st.pyplot(fig, facecolor="#0E1117")

  
  
  
  
  
  
  
  
