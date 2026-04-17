# ==========================================
# CONFIGURAÇÕES DA IA E DO ANIMAL DO RECINTO
# ==========================================
import base64

import streamlit as st
from groq import Groq
from langchain_groq import ChatGroq
from openai import OpenAI

from animals import ANIMALS

# --- CONFIGURAÇÕES DA LLM ---
# Nome do modelo no Groq
MODEL_NAME = "openai/gpt-oss-120b"
# Temperatura para comportamento mais factual, restringindo halucinações
TEMPERATURE = 0.4


# Função que retorna a lista de nomes dos animais, usando cache para otimização
@st.cache_data
def nomes_animais() -> list[str]:
    """Função para extrair e retornar a lista de nomes dos animais, usando cache_data para otimização."""
    return [animal["nome"] for animal in ANIMALS]


# Função que configura a sessão para o animal em questão
def setup(nome_animal: str) -> dict[str, str]:
    """Função que retorna um dicionário com informações do animal passado como argumento."""
    # Procura no arquivo de animais o animal recebido como argumento
    for animal in ANIMALS:
        # Se o nome do animal for encontrado
        if animal["nome"] == nome_animal:
            # Para a busca e segue para montar o system prompt
            break
    else:
        # Se o animal não for encontrado, levanta um erro
        raise ValueError(f"Animal '{nome_animal}' não encontrado.")

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


# Função que instancia a LLM no Groq usando cache_resource para evitar re-instanciações desnecessárias
@st.cache_resource
def get_llm() -> ChatGroq:
    """Função para instanciar a LLM usando cache_resource."""
    return ChatGroq(
        api_key=st.secrets["GROQ_API_KEY"],
        model=MODEL_NAME,
        temperature=TEMPERATURE,
    )


# Função que instancia o cliente da OpenAI usando cache_resource para evitar re-instanciações desnecessárias
@st.cache_resource
def get_openai_client() -> OpenAI:
    """Função para instanciar o cliente da OpenAI usando cache_resource."""
    return OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


# Instancia o cliente da OpenAI utilizando o cache_resource para otimizar o desempenho e evitar re-instanciações desnecessárias
client_openai = get_openai_client()


# Função que gera o áudio em formato HTML usando a API de TTS da OpenAI
def gerar_audio_openai(texto) -> str:
    """
    Gera um componente de áudio HTML em formato base64 usando a API de TTS da OpenAI.
    O retorno é uma tag de áudio configurada para reprodução automática.
    """

    try:
        # Envia a requisição síncrona para a API de geração de fala
        response = client_openai.audio.speech.create(
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


# Função que instancia o cliente da Groq usando cache_resource para evitar re-instanciações desnecessárias
@st.cache_resource
def get_groq_client() -> Groq:
    """Função para instanciar o cliente da Groq usando cache_resource."""
    return Groq(api_key=st.secrets["GROQ_API_KEY"])


# Instancia o cliente da Groq utilizando o cache_resource para otimizar o desempenho e evitar re-instanciações desnecessárias
client_groq = get_groq_client()


# Função que recebe os bytes de áudio do microfone e usa o modelo Whisper da Groq para transcrever para texto em tempo real
def transcrever_audio_groq(audio_bytes: bytes) -> str:
    """
    Recebe os bytes de áudio do microfone e usa o modelo Whisper da Groq
    para transcrever para texto em tempo real.
    """

    try:
        # A API da Groq espera um formato de arquivo, passamos os bytes em memória
        transcription = client_groq.audio.transcriptions.create(
            file=("audio.wav", audio_bytes),  # Bytes do áudio
            model="whisper-large-v3-turbo",  # Modelo com menos latência
            prompt="O áudio está em português brasileiro.",  # Dica de contexto para o modelo
            language="pt",  # Especifica o idioma para melhorar a precisão
        )
        return transcription.text
    except Exception as e:
        st.error(f"⚠️ Erro ao ouvir: {e}")
        return ""


OBS = """\
### Observações:

- **Interface Híbrida:**
    - **É necessário clicar novamente no ícone de microfone ao terminar de falar**. No totem físico, usaremos widget de áudio que detecta quando o visitante para de falar.
    - O input de texto foi mantido estritamente para facilitar a avaliação, caso o avaliador não possa usar o microfone por algum motivo. No totem físico, a interface será só por captura de voz.
- **Delay no TTS:**
    - Há um delay de cerca de 5 segundos entre a chegada da resposta e a reprodução do áudio. Isso se deve ao uso de uma API da OpenAI de baixa prioridade (custo).
- **Simulação de Hardware:**
    - O botão "Novo Visitante" simula a saída do visitante (afastamento detectado pelo sensor de presença), reiniciando a sessão.\
"""
