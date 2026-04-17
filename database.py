import streamlit as st
from st_supabase_connection import SupabaseConnection


# --- CONFIGURAÇÕES DE BANCO DE DADOS ---
@st.cache_resource(ttl=3000)
def init_connection() -> SupabaseConnection:
    """
    Inicia conexão com o Supabase usando as credenciais do secrets.toml, faz login para autorizar SELECT, INSERT, UPDATE, e retorna o objeto de conexão.
    Usa `@st.cache_resource` para impedir re-instanciações desnecessárias.
    """
    # Inicializa a conexão com o Supabase usando as credenciais do secrets.toml
    conn = st.connection("supabase", type=SupabaseConnection)
    # Login para autorizar SELECT, INSERT, UPDATE
    conn.client.auth.sign_in_with_password(
        {
            "email": st.secrets["credentials"]["EMAIL"],
            "password": st.secrets["credentials"]["PASSWORD"],
        }
    )
    return conn


conn = init_connection()

# ------------------------------------------------------------------------------------
# O banco de dados tem 2 tabelas:
# 1. conversas: cada linha é um par pergunta-resposta
# 2. aproximacoes: cada linha é ou uma aproximação / afastamento do sensor de presença
# ------------------------------------------------------------------------------------

# --- FUNÇÕES DE INTERAÇÃO COM O BANCO DE DADOS ---


# Função para salvar a pergunta no banco de dados
def insert_pergunta(sessao, modelo, animal, pergunta):
    """Insere a pergunta na tabela 'conversas' e retorna o ID do registro criado"""
    try:
        log_data = {
            "sessao": sessao,
            "modelo": modelo,
            "animal": animal,
            "pergunta": pergunta,
        }
        res = conn.table("conversas").insert(log_data).execute()
        if res.data:
            return res.data[0]["id"]  # type: ignore
    except Exception as e:
        st.error(f"Erro no banco: {e}")
    return None


# Função para salvar a resposta no banco de dados
def insert_resposta(conversas_id, resposta):
    """Insere a resposta do modelo usando UPDATE no registro correspondente"""
    try:
        conn.table("conversas").update({"resposta": resposta}).eq(
            "id", conversas_id
        ).execute()
    except Exception as e:
        st.error(f"Erro ao salvar resposta: {e}")


# Função para salvar o feedback no banco de dados
def insert_feedback(conversas_id, feedback):
    """Insere o feedback usando UPDATE no registro correspondente"""
    if conversas_id and feedback is not None:
        voto = True if feedback == 1 else False  # Lógica booleana solicitada
        try:
            conn.table("conversas").update({"feedback": voto}).eq(
                "id", conversas_id
            ).execute()
        except Exception as e:
            st.error(f"Erro no feedback: {e}")


# Função auxiliar para callback do `st.feedback`
def feedback_callback(index):
    """Callback para o st.feedback, que salva o feedback no banco de dados"""
    conversas_id = st.session_state.messages[index].get("conversas_id")
    feedback = st.session_state.get(f"feedback_{index}")
    insert_feedback(conversas_id=conversas_id, feedback=feedback)


# Usamos o cache de 60 segundos para não queimar API do Supabase.
@st.cache_data(ttl=60)
def carregar_dados_do_banco():
    # Puxa todas as linhas da tabela "conversas"
    res = conn.table("conversas").select("*").execute()
    return res.data
