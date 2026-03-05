import pandas as pd
import streamlit as st

from database import sensor_de_presenca

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
st.set_page_config(page_title="Sensor de Presença", page_icon="📊", layout="wide")
# Título
st.title("📊 Leituras do Sensor de Presença")

# Se o botão de recarregar for clicado, limpamos o cache para pegar dados novos
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
dados = sensor_de_presenca()
# Se não houver dados, avisa
if not dados:
    st.info("Nenhuma interação registrada no banco de dados ainda.")
# Se houver dados, prossegue
else:
    # Transforma o JSON do Supabase em um DataFrame do Pandas
    df = pd.DataFrame(dados)

    st.dataframe(df, hide_index=True)
# endregion
