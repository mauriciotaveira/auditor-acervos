import streamlit as st
from google import genai
from pypdf import PdfReader 
from pymarc import MARCReader # A NOSSA NOVA ARMA SECRETA!
import io

# 1. Configuração de Página
st.set_page_config(page_title="Auditor de Acervos PRO", page_icon="🏛️", layout="centered")

# Inicialização da Memória
if "historico" not in st.session_state:
    st.session_state.historico = []
if "texto_acumulado" not in st.session_state:
    st.session_state.texto_acumulado = ""

# 2. CSS Customizado - Máxima Legibilidade
st.markdown("""
    <style>
    [data-testid="stHeader"], header, footer, .stAppDeployButton, #MainMenu {visibility: hidden; display: none;}
    .block-container {padding-top: 1rem !important; background-color: #ffffff;}
    .main-title { color: #000000; font-size: 48px !important; font-weight: 850; text-align: center; margin-bottom: 5px; }
    .subtitle { color: #000000; text-align: center; font-size: 16px; font-weight: 500; margin-bottom: 2rem; }
    .parecer-texto { color: #000000 !important; font-size: 16px !important; line-height: 1.6 !important; background-color: #ffffff; padding: 20px; border: 1px solid #e0e0e0; border-radius: 4px; margin-bottom: 20px; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    h3 { color: #000000 !important; font-size: 22px !important; font-weight: 700 !important; border-bottom: 2px solid #000000; padding-bottom: 5px; margin-top: 30px !important;}
    .stButton>button { background-color: #000000 !important; color: white !important; font-weight: bold !important; border-radius: 2px !important; padding: 10px 40px !important; border: none !important; }
    </style>
    """, unsafe_allow_html=True)

# 3. Configuração do Motor e Instrução de Sistema
try:
    MINHA_CHAVE = st.secrets["GOOGLE_API_KEY"]
    client_gemini = genai.Client(api_key=MINHA_CHAVE)
    MODELO_IA = "gemini-2.5-flash"
    
    INSTRUCAO_SISTEMA = (
        "Você é o Auditor de Acervos PRO, um especialista de elite em Ciência da Informação e Biblioteconomia. "
        "Sua missão é auditar documentos de acervos e registros MARC21 originais. "
        "DIRETRIZES: 1) Identifique inconsistências em metadados, tags MARC ausentes (ex: falta de tag 650 para assunto), e erros de digitação. "
        "2) Use tom acadêmico e técnico focado em arquivologia/biblioteconomia. "
        "3) Estruture em: RESUMO DA CURADORIA, INCONSISTÊNCIAS ENCONTRADAS e SUGESTÃO DE PADRONIZAÇÃO. "
        "Use negrito para destacar campos, tags MARC e valores divergentes."
    )
except:
    st.error("Erro de Autenticação nos Secrets. Verifique a chave da API.")
    st.stop()

# 4. O NOVO EXTRATOR BILINGUE (Lê PDF e Lê MARC21)
def extrair_texto(arquivos):
    texto_total = ""
    for arq in arquivos:
        nome_arquivo = arq.name.lower()
        try:
            # Se for PDF, faz o que já fazia antes
            if nome_arquivo.endswith('.pdf'):
                reader = PdfReader(arq)
                for page in reader.pages:
                    content = page.extract_text()
                    if content: texto_total += f"\n--- DOC (PDF): {arq.name} ---\n{content}\n"
            
            # A MÁGICA NOVA: Se for arquivo de biblioteca (.mrc ou .marc)
            elif nome_arquivo.endswith('.mrc') or nome_arquivo.endswith('.marc'):
                dados_binarios = arq.read()
                reader_marc = MARCReader(dados_binarios)
                texto_total += f"\n--- REGISTROS MARC21: {arq.name} ---\n"
                for record in reader_marc:
                    if record:
                        texto_total += str(record) + "\n\n"
        except Exception as e:
            texto_total += f"\n[Erro ao ler arquivo {arq.name}: {e}]\n"
            continue
    return texto_total

# 5. Interface
st.markdown('<p class="main-title">Auditor de Acervos PRO</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">INTELIGÊNCIA EM CURADORIA E AUDITORIA DE METADADOS (PDF & MARC21)</p>', unsafe_allow_html=True)

st.write("---")

st.subheader("📂 Central de Documentos (Acervo)")
# AGORA ELE ACEITA AS EXTENSÕES DE BIBLIOTECA!
arquivos_pdf = st.file_uploader("Selecione os PDFs ou arquivos brutos MARC (.mrc, .marc)", type=["pdf", "mrc", "marc"], accept_multiple_files=True, label_visibility="collapsed")

if arquivos_pdf:
    st.session_state.texto_acumulado = extrair_texto(arquivos_pdf)

if st.session_state.historico:
    st.subheader("📜 Relatório de Curadoria")
    for msg in st.session_state.historico:
        if msg["role"] == "assistant":
            st.markdown(f'<div class="parecer-texto">{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f"**👤 Sua Instrução:** {msg['content']}")

st.subheader("🏛️ Nova Instrução")
user_prompt = st.text_area("O que deseja auditar no acervo?", placeholder="Ex: Analise este arquivo .mrc e me aponte quais livros estão sem a tag 650 de assunto...", height=100, label_visibility="collapsed")

col1, col2 = st.columns([1, 1])
with col1:
    if st.button("EXECUTAR AUDITORIA"):
        if not st.session_state.texto_acumulado or not user_prompt:
            st.warning("Suba os documentos do acervo e digite a instrução.")
        else:
            with st.spinner("⏳ Analisando metadados..."):
                try:
                    contexto_conversa = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.historico])
                    prompt_final = f"{INSTRUCAO_SISTEMA}\n\nDOCS:\n{st.session_state.texto_acumulado}\n\nHISTÓRICO:\n{contexto_conversa}\n\nPERGUNTA: {user_prompt}"
                    response = client_gemini.models.generate_content(model=MODELO_IA, contents=prompt_final)
                    
                    st.session_state.historico.append({"role": "user", "content": user_prompt})
                    st.session_state.historico.append({"role": "assistant", "content": response.text})
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")

with col2:
    if st.button("LIMPAR"):
        st.session_state.historico = []
        st.session_state.texto_acumulado = ""
        st.rerun()

if st.session_state.historico:
    st.download_button(
        label="📄 BAIXAR RELATÓRIO",
        data=st.session_state.historico[-1]["content"],
        file_name="relatorio_acervo.txt",
        mime="text/plain",
        use_container_width=True
    )

st.markdown("<br><br><center><small>Auditor de Acervos PRO | © 2026</small></center>", unsafe_allow_html=True)