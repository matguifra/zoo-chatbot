import streamlit as st

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

# region IMPORTS & CONFIG
# -----------------------------------
# IMPORTAÇÕES E CONFIGURAÇÕES GERAIS
# -----------------------------------
# Importa bibliotecas depois da senha para fins de performance
import uuid

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

import config
import database as db

# --- INICIALIZAÇÃO DE ESTADO (SESSION STATE) ---
if "config" not in st.session_state:
    st.session_state.config = config.setup()

# Variável auxiliar para acessar as configurações do animal e do prompt de sistema
CONFIG = st.session_state.config

if "messages" not in st.session_state:
    st.session_state.messages = []

if "sessao_id" not in st.session_state:
    # Gera o UUID da visita uma única vez
    st.session_state.sessao_id = str(uuid.uuid4())

if "ultimo_id_db" not in st.session_state:
    st.session_state.ultimo_id_db = None
# endregion

# region PAGE
# -----------------------
# CONFIGURAÇÃO DA PÁGINA
# -----------------------
st.set_page_config(
    page_title=f"Recinto do {CONFIG['NOME']}",
    page_icon=CONFIG["EMOJI"],
    layout="centered",
)

# --- BOTÃO PARA NOVA SESSÃO ---
with st.sidebar:
    st.header("⚙️ Controle do Totem")
    if st.button("🔄 Novo Visitante / Limpar Chat", use_container_width=True):
        # Variáveis que precisamos manter ativas para usabilidade
        whitelist = ["password"]
        # Limpamos o session state, exceto as chaves da whitelist
        for key in st.session_state.keys():
            if key not in whitelist:
                del st.session_state[key]
        st.rerun()

# --- TÍTULO E BOAS VINDAS ---
st.title(f"{CONFIG['EMOJI']} Animal do recinto: {CONFIG['NOME']}")
st.caption(f"*{CONFIG['NOME_CIENTIFICO']}*")
st.markdown(
    "Olá! Sou seu guia virtual. Pergunte qualquer coisa sobre a espécie neste recinto!"
)
st.divider()

# --- EXIBE O HISTÓRICO DE MENSAGENS ---
for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            st.feedback(
                "thumbs",
                key=f"feedback_{i}",
                on_change=db.feedback_callback,
                args=[i],
            )
# endregion

# region CORE
# ----------------------------
# LANGCHAIN + GROQ + SUPABASE + OPENAI TTS
# ----------------------------

# Aguarda o input do visitante no campo de texto
if prompt := st.chat_input(f"Pergunte sobre o {CONFIG['NOME']}..."):
    # Registra a pergunta no banco de dados e recupera a chave primária da operação
    conversas_id = db.insert_pergunta(
        sessao=st.session_state.sessao_id,
        modelo=config.MODEL_NAME,
        animal=CONFIG["NOME"],
        pergunta=prompt,
    )

    # Atualiza o estado da sessão com a nova mensagem para renderização e histórico
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Renderiza visualmente a mensagem do usuário na interface de chat
    with st.chat_message("user"):
        st.markdown(prompt)

    # Inicializa o array de contexto do LangChain com a instrução de comportamento do sistema
    langchain_messages: list[BaseMessage] = [
        SystemMessage(content=CONFIG["SYSTEM_PROMPT"])
    ]

    # Transcreve o histórico local da sessão para o formato exigido pelo LangChain
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            langchain_messages.append(HumanMessage(content=msg["content"]))
        else:
            langchain_messages.append(AIMessage(content=msg["content"]))

    # Recupera o objeto de inferência (ChatGroq) a partir do cache de recursos
    llm = config.get_llm()

    # Inicia a renderização da resposta do assistente
    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            # Submete o contexto ao modelo e exibe o texto resultante progressivamente (stream)
            response = st.write_stream(llm.stream(langchain_messages))

            # Executa o fechamento da transação no banco de dados, incluindo a resposta
            db.insert_resposta(conversas_id=conversas_id, resposta=response)

            # Anexa a resposta definitiva ao estado da sessão, vinculando-a ao ID do banco
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": response,
                    "conversas_id": conversas_id,
                }
            )

            # Aciona a função de conversão de texto em fala passando a resposta completa
            audio_html = config.gerar_audio_openai(response)

            # Injeta o código HTML invisível contendo a mídia; o autoplay inicia o som
            st.components.v1.html(audio_html, height=0)  # type: ignore

            # Instancia os controles de avaliação vinculando callbacks ao estado atual
            st.feedback(
                "thumbs",
                key=f"feedback_{len(st.session_state.messages) - 1}",
                on_change=db.feedback_callback,
                args=[len(st.session_state.messages) - 1],
            )
# endregion
