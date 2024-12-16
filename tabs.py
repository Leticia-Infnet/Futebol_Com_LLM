import streamlit as st
import os
import json
import yaml
import pandas as pd
from google import genai
from google.genai import types
from utils.dataprep import GetMatchStats
from dotenv import load_dotenv
from statsbombpy import sb
from mplsoccer import Pitch
from agent import create_match_agent
from utils.cache_manager import cache_manager

# Tentar carregar as variáveis de ambiente do arquivo .env, se não existir, configurar manualmente
ENV_PATH = os.path.abspath(os.path.join('.env'))


if os.getenv('GEMINI_API_KEY') is None:
    try:
        load_dotenv(dotenv_path=ENV_PATH,
                    override=True)
    except FileNotFoundError:
        print('Arquivo .env não encontrado. As variáveis de ambiente devem ser configuradas manualmente.')

# Configuração do cliente com a chave da API
client = genai.Client(
    api_key=os.getenv('GEMINI_API_KEY')
)


def yaml_conversion(data: dict) -> str:
    return yaml.dump(data, allow_unicode=True)


def tab_overview(mytab):
    '''
    Função que cria a aba de visão geral da partida e narração.
    '''
    with mytab:
        st.title('Visão Geral da Partida :soccer:')
        json_selected_match_info = st.session_state['json_selected_match_info']

        col1, col2 = st.columns(2)
        col1.markdown("### Competição")
        col1.write(f"{json_selected_match_info['competition_name']}")
        col1.markdown("### Data da Partida")
        col1.write(f"{json_selected_match_info['match_date']}")
        col2.markdown("### Time da Casa")
        col2.write(f"{json_selected_match_info['home_team_name']}")
        col2.markdown("### Time Visitante")
        col2.write(f"{json_selected_match_info['away_team_name']}")
        col3, col4 = st.columns(2)
        home_team = json_selected_match_info['home_team_name']
        away_team = json_selected_match_info['away_team_name']
        home_score = json_selected_match_info['home_score']
        away_score = json_selected_match_info['away_score']
        col3.markdown("### Resultado")
        col3.write(f"{home_team} {home_score} x {away_score} {away_team}")
        col4.markdown("### Estádio")
        col4.write(json_selected_match_info['stadium_name'])

        st.markdown("## Narração da Partida:studio_microphone:")
        if st.button('Gerar Narração'):
            with st.spinner('Gerando narração sensacional...'):
                match_id = st.session_state['selected_match_id']
                lineups = GetMatchStats(match_id=match_id).get_lineups()
                match_info = st.session_state['json_selected_match_info']
                events = GetMatchStats(match_id=match_id).get_events()
                player_stats = GetMatchStats(
                    match_id=match_id).get_player_stats()
                broadcast_style = st.session_state['selected_broadcast_style']

                lineups_yaml = yaml_conversion(lineups)
                match_info_yaml = yaml_conversion(match_info)
                events_yaml = yaml_conversion(events)
                player_stats_yaml = yaml_conversion(player_stats)

                prompt = (f'''
                Elabore um resumo envolvente e informativo do jogo descrito abaixo, em português, através do conteúdo dos YAML fornecidos:
                - Lineups: {lineups_yaml} - contêm informações sobre as escalações dos times
                - Match Info: {match_info_yaml} - contêm informações gerais da partida como data, estádio, times, placar, nome da competição.
                - Events: {events_yaml} - contêm informações sobre os eventos da partida passes, faltas cometidas, faltas sofridas, interceptações, recuperação de bola, dribles e suas localizações.
                - Player Stats: {player_stats_yaml} - contêm informações sobre os jogadores individuais com os jogadores e, junto com os eventos, irão dar a visão geral da partida.
                - Broadcast Style: {broadcast_style} - contêm o estilo de narração escolhido pelo usuário. Podendo ser Formal(técnico e objetivo), Humorístico(descontraído e criativo) ou Técnico(análise detalhada dos eventos).
                Utilize apenas as informações fornecidas, sem fazer suposições ou preencher lacunas, como por exemplo adivinhar a ordem dos eventos da partida.
                O objetivo é criar um texto cativante e acessível, destacando os principais acontecimentos e aspectos interessantes da partida.
                O resumo deve ter no máximo 250 palavras e ser escrito como um comentarista esportivo, com o tom escolhido pelo usuário.
                Mencione a data da partida explicitamente, sem utilizar termos como 'hoje'.
                Não use termos como de acordo com os dados que me foram fornecidos, ou algo do tipo.
                Focalize os momentos-chave do jogo, não entre em detalhes excessivos sobre cada jogador.
                ''')

                response = client.models.generate_content(
                    model='gemini-1.5-flash',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.3,
                        max_output_tokens=500,
                        top_p=0.95,
                        top_k=40
                    ))

                response = response.text

                st.markdown(
                    f'<div style="text-align: justify;">{response}</div>', unsafe_allow_html=True)


def player_stats_tab(mytab):
    '''
    Criação da aba de perfil do jogador.
    '''
    with mytab:
        st.title('Perfil do Jogador:mag_right:')
        st.write('Selecione um jogador para ter o resumo dele na partida')

        match_id = st.session_state['selected_match_id']

        events = sb.events(match_id=int(match_id))

        home_team = events[events['type'] == 'Starting XI'].iloc[0]['team']
        away_team = [team for team in events['team'].unique()
                     if team != home_team][0]

        home_team_events = events[events['team'] == home_team]
        away_team_events = events[events['team'] == away_team]

        home_team_players = home_team_events['player'].dropna().unique()
        away_team_players = away_team_events['player'].dropna().unique()

        all_players = list(
            set(home_team_players).union(set(away_team_players)))

        selected_player = st.selectbox(
            'Selecione um jogador', all_players, index=None)

        if st.button('Gerar Perfil do Jogador'):
            if selected_player is not None:
                with st.spinner('Gerando um perfil impecável...'):
                    player_events = events[events['player'] == selected_player]
                    stats = {
                        "Jogador": selected_player,
                        "Passes Completos": player_events[
                            (player_events['type'] == 'Pass') & (
                                player_events['pass_outcome'].isna())
                        ].shape[0],
                        "Tentativas de Passes": player_events[player_events['type'] == 'Pass'].shape[0],
                        "Chutes": player_events[player_events['type'] == 'Shot'].shape[0],
                        "Chutes no Alvo": player_events[
                            (player_events['type'] == 'Shot') & (
                                player_events['shot_outcome'] == 'On Target')
                        ].shape[0],
                        "Faltas Cometidas": player_events[player_events['type'] == 'Foul Committed'].shape[0],
                        "Faltas Sofridas": player_events[player_events['type'] == 'Foul Won'].shape[0],
                        "Contestações de Bola": player_events[player_events['type'] == 'Tackle'].shape[0],
                        "Interceptações": player_events[player_events['type'] == 'Interception'].shape[0],
                        "Dribles Completados": player_events[
                            (player_events['type'] == 'Dribble') & (
                                player_events['dribble_outcome'] == 'Complete')
                        ].shape[0],
                        "Tentativas de Dribles": player_events[player_events['type'] == 'Dribble'].shape[0],
                        "Gols (exceto pênaltis)": player_events[
                            (player_events['type'] == 'Shot') &
                            (player_events['shot_outcome'] == 'Goal') &
                            (player_events['shot_type'] != 'Penalty')
                        ].shape[0],
                        "Gols de Pênalti": player_events[
                            (player_events['type'] == 'Shot') &
                            (player_events['shot_outcome'] == 'Goal') &
                            (player_events['shot_type'] == 'Penalty')
                        ].shape[0],
                        "Recuperações de Bola": player_events[player_events['type'] == 'Ball Recovery'].shape[0],
                        "Bloqueios": player_events[player_events['type'] == 'Block'].shape[0],
                        "Paralisações por Lesão": player_events[player_events['type'] == 'Injury Stoppage'].shape[0],
                        "Perda de Controle": player_events[player_events['type'] == 'Miscontrol'].shape[0],
                        # Safeguard against missing 'foul_committed_card' column
                        "Cartões Amarelos": player_events[
                            (player_events['type'] == 'Foul Committed') &
                            (player_events['foul_committed_card'].eq(
                                'Yellow Card') if 'foul_committed_card' in player_events else False)
                        ].shape[0],
                        "Cartões Vermelhos": player_events[
                            (player_events['type'] == 'Foul Committed') &
                            (player_events['foul_committed_card'].eq(
                                'Red Card') if 'foul_committed_card' in player_events else False)
                        ].shape[0]
                    }

                    json_player_stats_yaml = yaml_conversion(stats)

                    events = GetMatchStats(match_id=match_id).get_events()

                    events_yaml = yaml_conversion(events)

                    prompt = (f'''
                    Elabore um resumo envolvente e informativo do jogador selecionado, em português, através do conteúdo dos YAML fornecidos:
                            - Player_stats: {json_player_stats_yaml} - contêm informações sobre as estatísticas do jogador na partida. Como: passes completos,
                            tentativas de passes, chutes, chutes no alvo, faltas cometidas, faltas sofridas, contestações de bola, interceptações, dribles completados,
                            tentativas de dribles, gols (exceto pênaltis), gols de pênalti, recuperações de bola, bloqueios, cartões amarelos, cartões vermelhos,
                            paralisações por lesão, perda de controle.
                            - Events: {events_yaml} - contêm informações sobre os eventos gerais da partida, envolvendo todos os jogadores.
                            Com a combinação das estatísticas do jogador e dos eventos da partida, você irá traçar o perfil do jogador na partida.
                            Utilize apenas as informações fornecidas, sem fazer suposições ou preencher lacunas, como por exemplo adivinhar a ordem dos eventos da partida.
                            Não use termos como de acordo com os dados que me foram fornecidos, ou algo do tipo.
                            O objetivo é criar um texto cativante e acessível, destacando os principais acontecimentos e aspectos interessantes do jogador na partida.
                            O resumo deve ter no máximo 250 palavras e ser escrito como um comentarista esportivo.
                    ''')

                    response = client.models.generate_content(
                        model='gemini-1.5-flash',
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            temperature=0.3,
                            max_output_tokens=500,
                            top_p=0.95,
                            top_k=40
                        ))

                    response = response.text

                    st.markdown(
                        f'<div style="text-align: justify;">{response}</div>', unsafe_allow_html=True)


def pass_map_tab(mytab):
    '''
    Criação da aba de mapa de passe.
    '''
    with mytab:
        st.title('Mapa de Passe:man-running:')
        st.write(
            'Selecione um jogador para visualizar o mapa de passe dele na partida')

        match_id = st.session_state['selected_match_id']
        events = sb.events(match_id=match_id)

        home_team = events[events['type'] == 'Starting XI'].iloc[0]['team']
        away_team = [team for team in events['team'].unique()
                     if team != home_team][0]

        selected_team = st.selectbox(
            'Selecione time', [home_team, away_team], key='pass_team_selectbox', index=None)

        if selected_team is not None:

            events = sb.events(match_id=match_id)
            team_events = events[events['team'] == selected_team]
            players = team_events['player'].unique()
            players = players[~pd.isna(players)]
            selected_player = st.selectbox(
                'Selecione jogador', players, key='pass_player_selectbox', index=None)

            if selected_player is not None:
                with st.spinner('Carregando mapa de passes...'):
                    player_events = team_events[team_events['player']
                                                == selected_player]

                    pitch = Pitch(pitch_color='grass',
                                  line_color='white', line_zorder=2)
                    fig, ax = pitch.draw()

                    pass_events = player_events[player_events['type'] == 'Pass']

                    for _, event in pass_events.iterrows():
                        x = event['location'][0]
                        y = event['location'][1]
                        pass_end_location = event['pass_end_location']
                        x_end = pass_end_location[0]
                        y_end = pass_end_location[1]
                        pass_outcome = event['pass_outcome']

                        if pd.isna(pass_outcome):
                            color = 'blue'
                            alpha = 0.7
                            label = 'Passes Concluídos'
                        else:
                            color = 'red'
                            alpha = 0.5
                            label = 'Passes Incompletos'

                        pitch.arrows(x, y, x_end, y_end, color=color,
                                     alpha=alpha, ax=ax, width=2, label=label)

                    handles, labels = ax.get_legend_handles_labels()
                    by_label = dict(zip(labels, handles))
                    ax.legend(by_label.values(), by_label.keys(),
                              loc='upper left', fontsize='small')

                    st.pyplot(fig)


def match_qa_tab(mytab):
    '''
    Criação da aba de Q&A da partida.
    '''
    with mytab:
        st.title('Perguntas sobre a Partida:thinking_face:')
        st.write(
            'Faça perguntas sobre a partida em inglês e receba análises detalhadas')

        if 'selected_match_id' not in st.session_state:
            st.warning('Por favor, selecione uma partida primeiro.')
            return

        match_id = st.session_state['selected_match_id']
        match_info = st.session_state['json_selected_match_info']
        match_stats = GetMatchStats(match_id=match_id)

        # Limpar agente se a partida selecionada mudar
        if 'current_match_id' not in st.session_state or st.session_state['current_match_id'] != match_id:
            if 'match_agent' in st.session_state:
                del st.session_state['match_agent']
            st.session_state['current_match_id'] = match_id

        # Inicializa o agente se ainda não estiver no session state
        if 'match_agent' not in st.session_state:
            with st.spinner('Inicializando agente de análise...'):
                try:
                    # Pega as strings JSON dos dados da partida
                    events = match_stats.get_events()
                    player_stats = match_stats.get_player_stats()
                    lineups = match_stats.get_lineups()

                    # Debug: Mostra os dados carregados
                    with st.expander("Debug: Dados Carregados"):
                        st.write("Match Info:")
                        st.write(match_info)

                        st.write("\nEvents (raw):")
                        st.text(events[:1000] +
                                "..." if len(events) > 1000 else events)

                        st.write("\nPlayer Stats (raw):")
                        st.text(
                            player_stats[:1000] + "..." if len(player_stats) > 1000 else player_stats)

                        st.write("\nLineups (raw):")
                        st.text(
                            lineups[:1000] + "..." if len(lineups) > 1000 else lineups)

                        # Tenta parsear cada string JSON
                        st.write("\nValidating data formats:")
                        try:
                            events_dict = json.loads(events)
                            st.success("Events: Valid JSON")
                        except json.JSONDecodeError as e:
                            st.error(f"Events: Invalid JSON - {str(e)}")
                            events_dict = {"error": "Invalid JSON"}

                        try:
                            player_stats_dict = json.loads(player_stats)
                            st.success("Player Stats: Valid JSON")
                        except json.JSONDecodeError as e:
                            st.error(f"Player Stats: Invalid JSON - {str(e)}")
                            player_stats_dict = {"error": "Invalid JSON"}

                        try:
                            lineups_dict = json.loads(lineups)
                            st.success("Lineups: Valid JSON")
                        except json.JSONDecodeError as e:
                            st.error(f"Lineups: Invalid JSON - {str(e)}")
                            lineups_dict = {"error": "Invalid JSON"}

                    # Criação do contexto da partida
                    match_context = (
                        f"{match_info['home_team_name']} vs {match_info['away_team_name']} "
                        f"({match_info['match_date']})"
                    )

                    # Criação do agente com dados válidos
                    st.session_state['match_agent'] = create_match_agent(
                        match_info=match_info,
                        events=events_dict if isinstance(
                            events_dict, dict) else events,
                        player_stats=player_stats_dict if isinstance(
                            player_stats_dict, dict) else player_stats,
                        lineups=lineups_dict if isinstance(
                            lineups_dict, dict) else lineups
                    )

                    st.session_state['match_context'] = match_context

                except Exception as e:
                    st.error(f"Erro ao carregar dados da partida: {str(e)}")
                    st.exception(e)
                    return

        # Criando o input da questão do usuário
        user_question = st.text_input(
            "Digite sua pergunta sobre a partida:",
            key='question_input',
            placeholder="Ex: Where the match was played? What was the lineup of the home team?"
        )

        # Botão de submissão da pergunta
        submit_button = st.button("Analisar", key="submit_question")

        # Processa a pergunta quando submetida
        if submit_button and user_question:
            with st.spinner('Analisando a partida...'):
                try:
                    response = st.session_state['match_agent'].invoke(
                        {
                            "input": user_question,
                            "context": st.session_state['match_context']
                        }
                    )

                    # Mostra a resposta
                    st.markdown("### Resposta:")
                    if isinstance(response, dict) and "output" in response:
                        st.markdown(
                            f'<div style="background-color: #f0f2f6; padding: 20px; '
                            f'border-radius: 10px; border-left: 5px solid #1f77b4;">'
                            f'{response["output"]}</div>',
                            unsafe_allow_html=True
                        )
                    else:
                        st.error("Formato de resposta inesperado")
                        st.json(response)

                except Exception as e:
                    st.error(f"Erro ao processar pergunta: {str(e)}")
                    st.error("Por favor, tente reformular sua pergunta.")
