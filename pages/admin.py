import pandas as pd
import streamlit as st

from database import carregar_dados_do_banco

# region PWD & DEFs
# -----------------
# SENHA + SUPABASE
# -----------------
# SEGURANÇA: Exige a senha para ver o painel
if "password" not in st.session_state or not st.session_state.password:
    st.warning(
        "🔒 Acesso negado. Por favor, insira a senha na página principal (Totem) para desbloquear o painel."
    )
    st.stop()
# endregion

# region PAGE
# -----------------------
# CONFIGURAÇÃO DA PÁGINA
# -----------------------
st.set_page_config(page_title="Dashboard Admin", page_icon="📊", layout="wide")
# Título
st.title("📊 Painel de Desempenho do Totem")

# Se o botão de recarregar for clicado, limpamos o cache para pegar dados novos
with st.sidebar:
    if st.button("🔄 Atualizar Dados Agora"):
        st.cache_data.clear()
        st.rerun()

st.divider()
# endregion

# region CORE
# ----------------------------------
# PROCESSAMENTO DOS DADOS E GRÁFICOS
# ----------------------------------
# Carrega os dados do banco
dados = carregar_dados_do_banco()
# Se não houver dados, avisa
if not dados:
    st.info("Nenhuma interação registrada no banco de dados ainda.")
# Se houver dados, prossegue
else:
    # Transforma o JSON do Supabase em um DataFrame do Pandas
    df = pd.DataFrame(dados)

    # --- CÁLCULO DE MÉTRICAS ---
    total_interacoes = len(df)

    # Filtra apenas quem clicou no botão de feedback (ignora os nulos)
    avaliacoes = df.dropna(subset=["feedback"])
    total_avaliacoes = len(avaliacoes)

    likes = len(avaliacoes[avaliacoes["feedback"].eq(True)])
    dislikes = len(avaliacoes[avaliacoes["feedback"].eq(False)])

    taxa_aprovacao = (likes / total_avaliacoes * 100) if total_avaliacoes > 0 else 0

    # --- EXIBIÇÃO: LINHA DE MÉTRICAS E GRÁFICO ---
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("💬 Total de Mensagens", total_interacoes)
    col2.metric("👍 Likes", likes)
    col3.metric("👎 Dislikes", dislikes)
    col4.metric("⭐ Aprovação", f"{taxa_aprovacao:.1f}%")
    col5.bar_chart(
        pd.DataFrame({"Votos": [likes, dislikes], "Tipo": ["👍", "👎"]}).set_index(
            "Tipo"
        ),
        horizontal=True,
    )
    st.divider()

    # --- EXIBIÇÃO: TABELA ---
    st.subheader("Últimas Interações")

    # Ordena pelas interações mais recentes e limita a quantidade exibida
    df_exibicao = df.sort_values(by="timestamp", ascending=False).head(100)
    # Troca os valores True/False/None por emojis para legibilidade
    df_exibicao["feedback"] = (
        df_exibicao["feedback"].map({True: "👍", False: "👎"}).fillna("Sem voto")
    )

    st.dataframe(
        data=df_exibicao,
        column_config={
            # Formata o timestamp para o formato brasileiro
            "timestamp": st.column_config.DatetimeColumn(
                label="Data/Hora",
                format="DD/MM/YYYY - HH:mm",
                timezone="America/Sao_Paulo",
            ),
            "sessao": "ID Sessão",
            "pergunta": "Pergunta do Visitante",
            "resposta": "Resposta da IA",
            "feedback": "Avaliação",
        },
        column_order=["timestamp", "sessao", "pergunta", "resposta", "feedback"],
        hide_index=True,
    )
# endregion
