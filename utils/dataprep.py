from statsbombpy import sb
import json
from copy import copy
from utils.cache_manager import cache_manager
import requests_cache


class PlayerStatsError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

# Classe com funções para recuperar os dados de uma partida específica a partir de um match_id e retornar uma string JSON


class GetMatchStats:
    def __init__(self, match_id):
        self.match_id = int(match_id)
        self.session = requests_cache.CachedSession(
            'statsbomb_cache',
            backend='sqlite',
            expire_after=3600
        )

    def get_events(self) -> str:
        '''Função que retorna os eventos de uma partida em formato JSON
        Args:
            match_id (int): ID da partida
        Returns:
            str: JSON com os eventos da partida
        '''
        try:
            events = sb.events(match_id=self.match_id)
            events = events[['timestamp', 'team', 'type',
                             'minute', 'location', 'pass_end_location', 'player']]
            events = events.sort_values(['minute', 'timestamp'])
            return json.dumps(events.to_dict('records'), indent=4)
        except Exception as e:
            return json.dumps({"error": f"Error getting events: {str(e)}"}, indent=4)

    def get_lineups(self) -> str:
        '''
        Função que retorna as escalações de uma partida em formato JSON
        Args:
            match_id (int): ID da partida
        Returns:
            str: JSON com as escalações da partida
        '''
        try:
            lineups = sb.lineups(match_id=self.match_id)
            return json.dumps(lineups, indent=4)
        except Exception as e:
            return json.dumps({"error": f"Error getting lineups: {str(e)}"}, indent=4)

    def get_player_stats(self) -> str:
        '''
        Função que retorna as estatísticas dos jogadores de uma partida em formato JSON
        Args:
            match_id (int): ID da partida
        Returns:
            str: JSON com as estatísticas dos jogadores da partida
        '''
        try:
            events = sb.events(match_id=self.match_id)
            all_players = self.get_all_players(events)

            all_stats = []
            for player_name in all_players:
                player_events = events[events['player'] == player_name]
                stats = {
                    "player": player_name,
                    "team": player_events['team'].iloc[0] if not player_events.empty else None,
                    "statistics": {
                        "passes_completed": int(player_events[(player_events['type'] == 'Pass') & (player_events['pass_outcome'].isna())].shape[0]),
                        "passes_attempted": int(player_events[player_events['type'] == 'Pass'].shape[0]),
                        "shots": int(player_events[player_events['type'] == 'Shot'].shape[0]),
                        "shots_on_target": int(player_events[(player_events['type'] == 'Shot') & (player_events['shot_outcome'] == 'On Target')].shape[0]),
                        "goals": int(player_events[(player_events['type'] == 'Shot') & (player_events['shot_outcome'] == 'Goal')].shape[0]),
                        "assists": int(player_events[player_events['pass_goal_assist'] == True].shape[0]),
                        "fouls_committed": int(player_events[player_events['type'] == 'Foul Committed'].shape[0]),
                        "fouls_won": int(player_events[player_events['type'] == 'Foul Won'].shape[0]),
                        "tackles": int(player_events[player_events['type'] == 'Tackle'].shape[0]),
                        "interceptions": int(player_events[player_events['type'] == 'Interception'].shape[0]),
                        "minutes_played": int(player_events['minute'].max() if not player_events.empty else 0)
                    }
                }
                all_stats.append(stats)

            return json.dumps(all_stats, indent=4)
        except Exception as e:
            return json.dumps({"error": f"Error getting player stats: {str(e)}"}, indent=4)

    @staticmethod
    def get_all_players(events_df):
        '''
        Função que retorna uma lista com todos os jogadores que participaram de uma partida
        Args:
            events_df (pd.DataFrame): DataFrame com os eventos da partida
        Returns:
            list: Lista com os nomes de todos os jogadores que participaram da partida
        '''
        try:
            home_team = events_df[events_df['type']
                                  == 'Starting XI'].iloc[0]['team']
            away_team = [team for team in events_df['team'].unique()
                         if team != home_team][0]

            home_team_events = events_df[events_df['team'] == home_team]
            away_team_events = events_df[events_df['team'] == away_team]

            home_team_players = home_team_events['player'].dropna().unique()
            away_team_players = away_team_events['player'].dropna().unique()

            return list(set(home_team_players).union(set(away_team_players)))
        except Exception as e:
            raise PlayerStatsError(f"Error getting players: {str(e)}")
