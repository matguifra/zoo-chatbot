import streamlit as st
from st_supabase_connection import SupabaseConnection

# Inicializa a conexão
conn = st.connection("supabase", type=SupabaseConnection)


# Função para salvar a pergunta e resposta no banco de dados
def salvar_pergunta(sessao, modelo, animal, pergunta, resposta):
    """Insere a pergunta e resposta no Supabase e retorna o ID do registro criado"""
    try:
        log_data = {
            "sessao": sessao,
            "modelo": modelo,
            "animal": animal,
            "pergunta": pergunta,
            "resposta": resposta,
        }
        res = conn.table("conversas").insert(log_data).execute()
        if res.data:
            return res.data[0]["id"]  # type: ignore
    except Exception as e:
        st.error(f"Erro no banco: {e}")
    return None


# Função para atualizar o feedback no banco de dados
def atualizar_feedback(id_log, feedback):
    """Atualiza a coluna de feedback"""
    if id_log and feedback is not None:
        voto = True if feedback == 1 else False  # Lógica booleana solicitada
        try:
            conn.table("conversas").update({"feedback": voto}).eq(
                "id", id_log
            ).execute()
        except Exception as e:
            st.error(f"Erro no feedback: {e}")


# Usamos o cache de 60 segundos para não queimar API do Supabase.
@st.cache_data(ttl=60)
def carregar_dados_do_banco():
    # Puxa todas as linhas da tabela "conversas"
    res = conn.table("conversas").select("*").execute()
    return res.data


@st.cache_data(ttl=60)
def sensor_de_presenca():
    # Puxa todas as linhas da tabela "aproximacoes"
    res = conn.table("aproximacoes").select("*").execute()
    return res.data
