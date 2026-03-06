import uuid

import streamlit as st
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_groq import ChatGroq

import config
import database as db

# region PASSWORD
# -----------------------------------
# SENHA PARA PROTEGER A COTA DO GROQ
# -----------------------------------
if "password" not in st.session_state:
    st.session_state.password = False

if not st.session_state.password:
    pwd = st.text_input("Digite a senha:")
    if pwd == st.secrets["PASSWORD"]:
        st.session_state.password = True
        st.rerun()
    elif pwd:
        st.error("Senha incorreta.")
    st.stop()
# endregion

# region PAGE
# -----------------------
# CONFIGURAÇÃO DA PÁGINA
# -----------------------
st.set_page_config(
    page_title=f"Recinto do {config.ANIMAL_NOME}",
    page_icon=config.ANIMAL_EMOJI,
    layout="centered",
)

# --- BOTÃO PARA NOVA SESSÃO ---
with st.sidebar:
    st.header("⚙️ Controle do Totem")
    if st.button("🔄 Novo Visitante / Limpar Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.sessao_id = str(uuid.uuid4())
        st.session_state.ultimo_id_db = None
        st.rerun()

# --- TÍTULO E BOAS VINDAS ---
st.title(f"{config.ANIMAL_EMOJI} Recinto do {config.ANIMAL_NOME}")
st.caption(f"*{config.ANIMAL_NOME_CIENTIFICO}*")
st.markdown("Olá! Sou seu guia virtual. Pergunte qualquer coisa sobre os **leões**!")
st.divider()

# --- INICIALIZAÇÃO DE ESTADO (SESSION STATE) ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "sessao_id" not in st.session_state:
    # Gera o UUID da visita uma única vez
    st.session_state.sessao_id = str(uuid.uuid4())

if "ultimo_id_db" not in st.session_state:
    st.session_state.ultimo_id_db = None

# --- EXIBE O HISTÓRICO DE MENSAGENS ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
# endregion

# region CORE
# ----------------------------
# LANGCHAIN + GROQ + SUPABASE
# ----------------------------
# Campo de input do chat. Se há input, entra no if.
if prompt := st.chat_input(f"Pergunte sobre o {config.ANIMAL_NOME}..."):
    # Salva e exibe a mensagem do usuário
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Monta a lista de mensagens para o LangChain
    langchain_messages: list[BaseMessage] = [
        SystemMessage(content=config.SYSTEM_PROMPT)
    ]
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            langchain_messages.append(HumanMessage(content=msg["content"]))
        else:
            langchain_messages.append(AIMessage(content=msg["content"]))

    # Instancia o modelo via Groq
    llm = ChatGroq(
        api_key=st.secrets["GROQ_API_KEY"],
        model=config.MODEL_NAME,
        temperature=config.TEMPERATURE,
    )

    # --- EXIBIÇÃO DA RESPOSTA E ARMAZENAGEM DA CONVERSA NO SUPABASE ---
    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            # Aquisição da resposta
            response = llm.invoke(langchain_messages)
            # Exibição da resposta
            st.markdown(response.content)
            # Salvamento da pergunta e resposta no banco de dados
            st.session_state.ultimo_id_db = db.salvar_pergunta(
                sessao=st.session_state.sessao_id,
                modelo=config.MODEL_NAME,
                animal=config.ANIMAL_NOME,
                pergunta=prompt,
                resposta=response.content,
            )
            # Botões de feedback que inserem avaliação no banco de dados
            st.feedback(
                "thumbs",
                key="feedback",
                on_change=lambda: db.atualizar_feedback(
                    id_log=st.session_state.ultimo_id_db,
                    feedback=st.session_state.feedback,
                ),
            )

    # Salva a resposta no histórico
    st.session_state.messages.append({"role": "assistant", "content": response.content})
# endregion
