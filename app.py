import streamlit as st

# region PASSWORD
# -------------------------------------------------------
# SENHA PARA PROTEGER AS COTAS DE API DO GROQ E DA OPENAI
# -------------------------------------------------------
if "password" not in st.session_state:
    st.session_state.password = False

# Se a senha não foi inserida corretamente, exibe o campo de input para a senha e bloqueia o acesso ao restante da aplicação
if not st.session_state.password:
    pwd = st.text_input("Digite a senha:")
    if pwd == st.secrets["PASSWORD"]:
        # Se a senha estiver correta, libera acesso
        st.session_state.password = True
        st.rerun()
    elif pwd:
        st.error("Senha incorreta.")
    # Enquanto a senha não for inserida ou estiver incorreta, para a execução do código aqui
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
# Inicializa o totem com um animal e o prompt de sistema, armazenando-os no session state
if "config" not in st.session_state:
    st.session_state.config = config.setup()

# Variável auxiliar para acessar as configurações do animal e do prompt de sistema
CONFIG = st.session_state.config

# Inicializa o histórico de mensagens
if "messages" not in st.session_state:
    st.session_state.messages = []

# Identifica a sessão atual
if "sessao_id" not in st.session_state:
    # Gera o UUID da visita
    st.session_state.sessao_id = str(uuid.uuid4())
# endregion

# region PAGE
# -----------------------
# CONFIGURAÇÃO DA PÁGINA
# -----------------------

# Configuração básica inicial da página, incluindo título e icone
st.set_page_config(
    page_title=f"Recinto do {CONFIG['NOME']}",
    page_icon=CONFIG["EMOJI"],
)

# --- BOTÃO PARA NOVA SESSÃO ---
with st.sidebar:  # Dentro da sidebar para não ocupar espaço do totem
    # Botão que limpa a sessão atual
    if st.button("🔄 Novo Visitante", use_container_width=True):
        # Variáveis que precisam se manter ativas para usabilidade
        whitelist = ["password"]
        # Loop que limpa o session state, exceto as chaves da whitelist
        for key in st.session_state.keys():
            if key not in whitelist:
                del st.session_state[key]
        st.rerun()  # Recarrega a página para refletir as mudanças no session state

# --- TÍTULO E BOAS VINDAS ---
# Descrição do animal no recinto
st.title(f"{CONFIG['EMOJI']} Animal do recinto: {CONFIG['NOME']}")
# Exibe o nome científico do animal em itálico como legenda
st.caption(f"*{CONFIG['NOME_CIENTIFICO']}*")
# Mensagem de boas-vindas e instrução para o visitante
st.markdown(
    "Olá! Sou seu guia virtual. Pergunte qualquer coisa sobre a espécie neste recinto!"
)
st.divider()

# --- EXIBE O HISTÓRICO DE MENSAGENS ---
# Loop que enumera as mensagens no histórico da sessão, para índice
for i, msg in enumerate(st.session_state.messages):
    # Estiliza a mensagem de acordo com o autor (usuário ou assistente)
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])  # Exibe a mensagem
        if msg["role"] == "assistant":  # Caso o autor seja o assistente:
            # Exibe o widget de feedback vinculado à mensagem, usando o índice gerado pelo enumerate
            st.feedback(
                "thumbs",
                key=f"feedback_{i}",
                on_change=db.feedback_callback,
                args=[i],
            )
# endregion

# region CORE
# ---------------------------------------------------
# LANGCHAIN + GROQ + SUPABASE + OPENAI TTS + GROQ TTS
# ---------------------------------------------------

# --- ENTRADA DO USUÁRIO ---
# Caixa de input para o usuário digitar ou gravar áudio
entrada_usuario = st.chat_input(
    f"Pergunte sobre o {CONFIG['NOME']}...", accept_audio=True
)

# Declaração da variável que armazenará o prompt final a ser enviado para o modelo
prompt = None

if entrada_usuario:
    # 1. Verifica se o usuário gravou um áudio
    # A propriedade .audio retorna um objeto UploadedFile
    if entrada_usuario.audio:
        # O .read() extrai os bytes crus do arquivo WAV
        audio_bytes = entrada_usuario.audio.read()

        with st.spinner("Interpretando a sua voz..."):
            # Manda o áudio para a transcrição
            texto_transcrito = config.transcrever_audio_groq(audio_bytes)
            # Se a transcrição for bem sucedida, define o prompt como o texto transcrito
            if texto_transcrito:
                prompt = texto_transcrito

    # 2. Se não tem áudio, verifica se o usuário digitou texto
    elif entrada_usuario.text:
        # Se o usuário digitou texto, define o prompt como o texto digitado
        prompt = entrada_usuario.text

# Se há prompt, inicia o processo de resposta do assistente
if prompt:
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

            # Widget de feedback da resposta do assistente, vinculado à última mensagem de resposta
            st.feedback(
                "thumbs",
                key=f"feedback_{len(st.session_state.messages) - 1}",
                on_change=db.feedback_callback,
                args=[len(st.session_state.messages) - 1],
            )
# endregion
