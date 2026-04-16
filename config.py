# ===============================================================================
# CONFIGURAÇÕES DA IA E DO ANIMAL DO RECINTO
# ==============================================================================
import base64
import random

import streamlit as st
from groq import Groq
from langchain_groq import ChatGroq
from openai import OpenAI

from animals import ANIMALS

# --- CONFIGURAÇÕES DA LLM ---
MODEL_NAME = "openai/gpt-oss-120b"  # "llama-3.3-70b-versatile"
TEMPERATURE = 0.4


def setup() -> dict[str, str]:
    """Escolhe um animal aleatório e monta a configuração para a sessão."""
    # Escolhe um animal aleatório da lista de animais disponíveis
    animal = random.choice(ANIMALS)

    # Montagem do system prompt usando as informações do animal escolhido
    system_prompt = f"""\
### PAPEL
Você é um Especialista em Zoologia e Educador Ambiental sênior. Sua função é responder perguntas de visitantes (adultos e crianças) de forma educativa, precisa e entusiasmada sobre o animal deste recinto: {animal["nome"]} ({animal["nome_cientifico"]}).

### DIRETRIZES DE CONTEÚDO
1. RIGOR CIENTÍFICO: Forneça apenas informações baseadas em fatos biológicos comprovados (dieta, habitat, comportamento, status de conservação).
2. VERACIDADE: **Nunca invente dados! Nem sobre o animal, nem sobre o zoológico!** Se não tiver certeza, admita e direcione o visitante ao Educador Ambiental ou Monitor mais próximo (caso a dúvida seja sobre o animal, como algo muito específico sobre um indivíduo que você não tenha dados sobre) ou ao balcão de informações (caso a pergunta seja sobre o zoológico em si, como horário de funcionamento, banheiro, etc.). **Priorize a segurança da informação sobre a cortesia de dar uma resposta qualquer.**
3. FOCO: Mantenha as respostas focadas no animal em questão. Se o visitante perguntar sobre algo não relacionado a animais ou ao zoológico, gentilmente traga o assunto de volta para a vida selvagem.

### TOM E ESTILO
- Educativo e Acessível: Use uma linguagem clara. Evite jargões excessivamente complexos.
- Conversacional e Falado: Suas respostas serão lidas em voz alta por um sistema de Text-to-Speech (TTS). Escreva de forma natural, como se estivesse conversando diretamente com o visitante.
- Ultra Conciso e Direto: Limite a resposta a, no máximo, 2 parágrafos bem curtos (idealmente de 2 a 3 frases cada). O visitante está em pé em um totem e precisa de respostas ágeis.
- Incentivador: Estimule a curiosidade e o respeito pela natureza com entusiasmo na voz.

### SEGURANÇA E ÉTICA
- Não responda a perguntas ofensivas ou inadequadas.
- Nunca incentive comportamentos perigosos (ex: tentar tocar no animal ou alimentá-lo).\
"""

    return {
        "NOME": animal["nome"],
        "EMOJI": animal["emoji"],
        "NOME_CIENTIFICO": animal["nome_cientifico"],
        "SYSTEM_PROMPT": system_prompt,
    }


@st.cache_resource
def get_llm() -> ChatGroq:
    """Função para instanciar a LLM usando cache_resource."""
    return ChatGroq(
        api_key=st.secrets["GROQ_API_KEY"],
        model=MODEL_NAME,
        temperature=TEMPERATURE,
    )


@st.cache_resource
def get_openai_client() -> OpenAI:
    """Função para instanciar o cliente da OpenAI usando cache_resource."""
    return OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


def gerar_audio_openai(texto) -> str:
    """
    Gera um componente de áudio HTML em formato base64 usando a API de TTS da OpenAI.
    O retorno é uma tag de áudio configurada para reprodução automática.
    """
    # Instancia o cliente da OpenAI utilizando o cache_resource para otimizar o desempenho e evitar re-instanciações desnecessárias
    client = get_openai_client()

    try:
        # Envia a requisição síncrona para a API de geração de fala
        response = client.audio.speech.create(
            input=texto,  # O texto gerado pela LLM
            model="gpt-4o-mini-tts",  # alternativas: "tts-1" (sem `instructions`, mais neutra), "gpt-4o-mini-tts" (com `instructions`, mais expressiva)
            voice="nova",  # Perfil de voz feminina, enérgica e clara
            instructions="Fale em português brasileiro, sotaque paulista, de maneira animada.",  # Instruções para o estilo de fala
            response_format="mp3",  # Formato mantido como mp3 para otimização da string Base64
            speed=1.25,  # Velocidade de reprodução (1.0 é a velocidade normal)
        )

        # Extrai os dados binários do áudio retornado pela API
        audio_binary = response.content

        # Codifica os dados binários em texto seguro (Base64) para embutimento no HTML
        audio_base64 = base64.b64encode(audio_binary).decode("utf-8")

        # Constrói o elemento HTML nativo com a diretiva 'autoplay'
        audio_html = f"""
            <audio autoplay>
                <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
            </audio>
        """
        return audio_html

    except Exception as e:
        # Em caso de falha na API ou rede, exibe o erro
        st.error(f"⚠️ Erro ao gerar a voz do guia: {e}")
        # Retorna um elemento HTML vazio para não causar erros visuais no components.html
        return "<div></div>"


@st.cache_resource
def get_groq_client() -> Groq:
    """Função para instanciar o cliente da Groq usando cache_resource."""
    return Groq(api_key=st.secrets["GROQ_API_KEY"])


def transcrever_audio_groq(audio_bytes: bytes) -> str:
    """
    Recebe os bytes de áudio do microfone e usa o modelo Whisper da Groq
    para transcrever para texto em tempo real.
    """
    # Instancia o cliente da Groq utilizando o cache_resource para otimizar o desempenho e evitar re-instanciações desnecessárias
    client = get_groq_client()

    try:
        # A API da Groq espera um formato de arquivo, passamos os bytes em memória
        transcription = client.audio.transcriptions.create(
            file=("audio.wav", audio_bytes),  # Nome fictício, o importante são os bytes
            model="whisper-large-v3-turbo",  # Modelo super rápido e no seu Free Tier
            prompt="O áudio está em português brasileiro.",  # Dica de contexto para o modelo
            language="pt",
        )
        return transcription.text
    except Exception as e:
        st.error(f"⚠️ Erro ao ouvir: {e}")
        return ""
