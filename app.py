import streamlit as st
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_groq import ChatGroq

# ---------------------------------------------------------------
# CONFIGURAÇÕES DO ANIMAL DO RECINTO E MODELO
# Troque estas variáveis para adaptar o totem a outro animal
# ---------------------------------------------------------------
# Animal do recinto
ANIMAL_NOME = "Leão"
ANIMAL_EMOJI = "🦁"
ANIMAL_NOME_CIENTIFICO = "Panthera leo"

# Prompt de sistema, que define o comportamento do guia virtual
SYSTEM_PROMPT = f"""Você é um guia especialista do Zoológico, responsável pelo recinto do {ANIMAL_NOME} ({ANIMAL_NOME_CIENTIFICO}).

Seu papel é responder perguntas dos visitantes sobre este animal de forma:
- Amigável e entusiasmada
- Educativa, com fatos científicos corretos
- Acessível para crianças e adultos
- Sempre em português brasileiro

Se a pergunta for sobre outro animal ou tema não relacionado ao {ANIMAL_NOME},
diga gentilmente que você só pode falar sobre os {ANIMAL_NOME}s deste recinto
e convide a pessoa a perguntar algo sobre eles.

Mantenha as respostas com tamanho adequado para leitura em um tablet de totem:
nem muito curtas, nem muito longas. Use parágrafos curtos.
"""
# Modelo
MODEL_NAME = "llama-3.3-70b-versatile"

# ---------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# ---------------------------------------------------------------
st.set_page_config(
    page_title=f"Recinto do {ANIMAL_NOME}",
    page_icon=ANIMAL_EMOJI,
    layout="centered",
)
# Senha
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

# Título e boas-vindas
st.title(f"{ANIMAL_EMOJI} Recinto do {ANIMAL_NOME}")
st.caption(f"*{ANIMAL_NOME_CIENTIFICO}*")
st.write("Olá! Sou seu guia virtual. Pergunte qualquer coisa sobre os leões!")
st.divider()

# Inicializa o histórico de mensagens na sessão
if "messages" not in st.session_state:
    st.session_state.messages = []

# Exibe o histórico de mensagens
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# ---------------------------------------------------------------
# LANGCHAIN + GROQ
# ---------------------------------------------------------------
# Campo de input do chat. Se há input, entra no if.
if prompt := st.chat_input(f"Pergunte sobre o {ANIMAL_NOME}..."):
    # Exibe e salva a mensagem do usuário
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Monta a lista de mensagens para o LangChain
    langchain_messages: list[BaseMessage] = [SystemMessage(content=SYSTEM_PROMPT)]
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            langchain_messages.append(HumanMessage(content=msg["content"]))
        else:
            langchain_messages.append(AIMessage(content=msg["content"]))

    # Chama o modelo via Groq
    llm = ChatGroq(
        api_key=st.secrets["GROQ_API_KEY"],
        model=MODEL_NAME,
        temperature=0.5,
    )

    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            response = llm.invoke(langchain_messages)
            st.write(response.content)

    # Salva a resposta no histórico
    st.session_state.messages.append({"role": "assistant", "content": response.content})
