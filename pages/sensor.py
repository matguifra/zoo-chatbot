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
with st.sidebar:
    if st.button("🔄 Atualizar Dados Agora"):
        st.cache_data.clear()
        st.rerun()
    st.write(
        "Lista de eventos de aproximação e afastamento do Totem armazenados em tabela SQL no Supabase.\n",
        "\nDados simulados no Wokwi com ESP32 com sensor de proximidade enviando dados para o Supabase via API.\n",
        "\nRegistro de aproximação ocorre quando o visitante chega a 50cm do sensor de proximidade.",
    )
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

    df["aproximacao"] = df["aproximacao"].map(
        {True: "⬅️  Aproximação", False: " ➡️ Afastamento"}
    )

    st.dataframe(
        df,
        column_config={
            "timestamp": st.column_config.DatetimeColumn(
                label="Data/Hora",
                format="DD/MM/YYYY - HH:mm",
                timezone="America/Sao_Paulo",
            ),
            "aproximacao": "Aproximação",
        },
        column_order=["timestamp", "aproximacao"],
        hide_index=True,
    )
# endregion
