import pandas as pd
import streamlit as st
from st_supabase_connection import SupabaseConnection

# Configuração da página
st.set_page_config(page_title="Dashboard Admin", page_icon="📊", layout="wide")

st.title("📊 Painel de Desempenho do Totem")

# 1. SEGURANÇA: Exige a senha para ver o painel
if "password" not in st.session_state or not st.session_state.password:
    st.warning(
        "🔒 Acesso negado. Por favor, insira a senha na página principal (Totem) para desbloquear o painel."
    )
    st.stop()

# 2. CONEXÃO COM O BANCO
conn = st.connection("supabase", type=SupabaseConnection)


# Usamos o cache de 60 segundos para não queimar API do Supabase.
@st.cache_data(ttl=60)
def carregar_dados_do_banco():
    # Puxa todas as linhas da tabela "conversas"
    res = conn.table("conversas").select("*").execute()
    return res.data


dados = carregar_dados_do_banco()

# Se o botão de recarregar for clicado, limpamos o cache para pegar dados novos
if st.button("🔄 Atualizar Dados Agora"):
    st.cache_data.clear()
    st.rerun()

st.divider()

# 3. PROCESSAMENTO DOS DADOS E GRÁFICOS
if not dados:
    st.info("Nenhuma interação registrada no banco de dados ainda.")
else:
    # Transforma o JSON do Supabase em um DataFrame do Pandas
    df = pd.DataFrame(dados)

    # --- CÁLCULO DE MÉTRICAS ---
    total_interacoes = len(df)

    # Filtra apenas quem clicou no botão de feedback (ignora os nulos)
    avaliacoes = df.dropna(subset=["feedback"])
    total_avaliacoes = len(avaliacoes)

    likes = len(avaliacoes[avaliacoes["feedback"]])
    dislikes = len(avaliacoes[~avaliacoes["feedback"]])

    taxa_aprovacao = (likes / total_avaliacoes * 100) if total_avaliacoes > 0 else 0

    # --- EXIBIÇÃO: LINHA DE MÉTRICAS ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💬 Total de Perguntas", total_interacoes)
    col2.metric("👍 Likes", likes)
    col3.metric("👎 Dislikes", dislikes)
    col4.metric("⭐ Aprovação", f"{taxa_aprovacao:.1f}%")

    st.divider()

    # --- EXIBIÇÃO: GRÁFICOS E TABELA ---
    # A tabela fica 2x mais larga que o gráfico
    col_grafico, col_tabela = st.columns([1, 2])

    with col_grafico:
        st.subheader("Distribuição de Feedback")
        if total_avaliacoes > 0:
            # Cria um DataFrame simples só para o gráfico
            df_grafico = pd.DataFrame(
                {"Votos": [likes, dislikes], "Tipo": ["👍 Likes", "👎 Dislikes"]}
            ).set_index("Tipo")

            # Gráfico de barras
            st.bar_chart(df_grafico, color=["#2e8b57"])
        else:
            st.caption("Ainda não há avaliações suficientes para o gráfico.")

    with col_tabela:
        st.subheader("Últimas Interações")
        # Prepara a tabela para exibição: remove colunas técnicas e renomeia
        df_exibicao = df[
            ["timestamp", "sessao", "pergunta", "resposta", "feedback"]
        ].copy()
        df_exibicao = df_exibicao.sort_values(by="timestamp", ascending=False).head(
            10
        )  # Mostra as 10 mais recentes

        # Troca os valores True/False/None por emojis para legibilidade
        df_exibicao["feedback"] = (
            df_exibicao["feedback"].map({True: "👍", False: "👎"}).fillna("Sem voto")
        )

        st.dataframe(
            df_exibicao,
            column_config={
                "timestamp": st.column_config.DatetimeColumn(
                    "Data/Hora", format="DD/MM/YYYY - hh:mm a"
                ),
                "sessao": "ID Sessão",
                "pergunta": "Pergunta do Visitante",
                "resposta": "Resposta da IA",
                "feedback": "Avaliação",
            },
            hide_index=True,
            use_container_width=True,
        )
