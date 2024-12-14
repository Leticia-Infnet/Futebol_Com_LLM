import streamlit as st
import json
import tabs
from statsbombpy import sb
from utils.cache_manager import cache_manager


@st.cache_data
def load_data() -> dict:
    '''
    Função que carrega os dados das competições da API StatsBomb
    e os armazena em cache para evitar múltiplas requisições.
    Args:
        None
    Returns:
        dict: Dicionário com as informações das competições.
    '''
    competitions = sb.competitions(fmt='dict')

    return competitions


data = load_data()

# Sidebar para seleção da competição
st.sidebar.title('Selecione uma competição')
unique_competitions = list({entry['competition_name']
                           for entry in data.values()})
selected_competition = st.sidebar.selectbox(
    'Selecione competição', unique_competitions, key='competition_name'
)

selected_competition_id = None
for entry in data.values():
    if entry['competition_name'] == selected_competition:
        selected_competition_id = entry['competition_id']
        break

# Sidebar para seleção da temporada e filtro das partidas
filtered_seasons = [
    (entry['season_name'], entry['season_id'])
    for entry in data.values()
    if entry['competition_name'] == selected_competition
]

season_names = [season[0] for season in filtered_seasons]
season_ids = {season[0]: season[1] for season in filtered_seasons}

selected_season_name = st.sidebar.selectbox(
    'Selecione temporada', season_names, key='season_name'
)


selected_season_id = season_ids[selected_season_name]

matches = sb.matches(
    competition_id=selected_competition_id,
    season_id=selected_season_id,
    fmt='dict'
)

filtered_matches = [
    {
        "match_id": match['match_id'],
        "match_display": f"{match['home_team']['home_team_name']} vs {match['away_team']['away_team_name']}"
    }
    for match in matches.values()
    if match['competition']['competition_id'] == selected_competition_id and match['season']['season_id'] == selected_season_id
]


match_names = [match['match_display'] for match in filtered_matches]
match_ids = {match['match_display']: match['match_id']
             for match in filtered_matches}

# Sidebar para seleção da partida
selected_match_display = st.sidebar.selectbox(
    'Selecione partida', match_names, key='match_name', index=None
)

# Radio button para seleção do tom da narração
st.sidebar.title('Escolha seu narrador!')

selected_broadcaster_style = st.sidebar.radio(
    "Selecione o estilo do narrador", ('Formal', 'Humorístico', 'Técnico'))

# Ao selecionar uma partida, exibir as abas de visão geral, perfil do jogador, mapa de passe e perguntas e respostas
if selected_match_display is not None:

    selected_match_id = match_ids[selected_match_display]

    selected_match = matches[selected_match_id]

    selected_match_info = {
        'match_date': selected_match.get('match_date') if selected_match.get('match_date') is not None else 'N/A',
        'competition_country': selected_match.get('competition', {}).get('country_name') if selected_match.get('competition', {}).get('country_name') is not None else 'N/A',
        'competition_name': selected_match.get('competition', {}).get('competition_name') if selected_match.get('competition', {}).get('competition_name') is not None else 'N/A',
        'home_team_country': selected_match.get('home_team', {}).get('country', {}).get('name') if selected_match.get('home_team', {}).get('country', {}).get('name') is not None else 'N/A',
        'away_team_country': selected_match.get('away_team', {}).get('country', {}).get('name') if selected_match.get('away_team', {}).get('country', {}).get('name') is not None else 'N/A',
        'stadium_name': selected_match.get('stadium', {}).get('name') if selected_match.get('stadium', {}).get('name') is not None else 'N/A',
        'season_name': selected_match.get('season', {}).get('season_name') if selected_match.get('season', {}).get('season_name') is not None else 'N/A',
        'home_team_name': selected_match.get('home_team', {}).get('home_team_name') if selected_match.get('home_team', {}).get('home_team_name') is not None else 'N/A',
        'away_team_name': selected_match.get('away_team', {}).get('away_team_name') if selected_match.get('away_team', {}).get('away_team_name') is not None else 'N/A',
        'home_team_manager': selected_match.get('home_team', {}).get('managers', [{}])[0].get('name') if selected_match.get('home_team', {}).get('managers') else 'N/A',
        'away_team_manager': selected_match.get('away_team', {}).get('managers', [{}])[0].get('name') if selected_match.get('away_team', {}).get('managers') else 'N/A',
        'home_score': selected_match.get('home_score') if selected_match.get('home_score') is not None else 'N/A',
        'away_score': selected_match.get('away_score') if selected_match.get('away_score') is not None else 'N/A',
        'competition_stage': selected_match.get('competition_stage', {}).get('name') if selected_match.get('competition_stage', {}).get('name') is not None else 'N/A'
    }

    json_selected_match_info = json.dumps(selected_match_info, indent=4)

    st.session_state['json_selected_match_info'] = selected_match_info

    st.session_state['selected_match_id'] = selected_match_id

    st.session_state['selected_broadcast_style'] = selected_broadcaster_style

    (overview_tab, player_stats_tab, pass_map_tab, match_qa_tab) = st.tabs(
        ("Visão Geral da Partida", "Perfil do Jogador", "Mapa de Passe", "Perguntas e Respostas"))

    tabs.tab_overview(overview_tab)

    tabs.player_stats_tab(player_stats_tab)

    tabs.pass_map_tab(pass_map_tab)

    tabs.match_qa_tab(match_qa_tab)
