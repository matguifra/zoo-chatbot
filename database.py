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
            "resposta": resposta
        }
        res = conn.table("conversas").insert(log_data).execute()
        if res.data:
            return res.data[0]["id"] # type: ignore
    except Exception as e:
        st.error(f"Erro no banco: {e}")
    return None

# Função para atualizar o feedback no banco de dados
def atualizar_feedback(id_log, feedback):
    """Atualiza a coluna de feedback"""
    if id_log and feedback is not None:
        voto = True if feedback == 1 else False # Lógica booleana solicitada
        try:
            conn.table("conversas").update({"feedback": voto}).eq("id", id_log).execute()
        except Exception as e:
            st.error(f"Erro no feedback: {e}")
