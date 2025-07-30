import streamlit as st
import sqlite3
import pandas as pd # Usaremos pandas para exibir os dados de forma mais bonita

# --- 1. Funções de Configuração do Banco de Dados e Lógica Bioinformática ---

DB_NAME = 'sequencias_dna_gc_streamlit.db' # Nome diferente para este banco de dados

def conectar_db():
    """Conecta ao banco de dados SQLite e retorna o objeto de conexão."""
    conn = sqlite3.connect(DB_NAME)
    return conn

def criar_tabela():
    """Cria a tabela 'sequencias' se ela não existir, com coluna para GC."""
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sequencias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sequencia TEXT NOT NULL,
            conteudo_gc REAL
        )
    ''')
    conn.commit()
    conn.close()

def adicionar_sequencia_db(sequencia, conteudo_gc):
    """Adiciona uma nova sequência de DNA e seu conteúdo GC ao banco de dados."""
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO sequencias (sequencia, conteudo_gc) VALUES (?, ?)', (sequencia, conteudo_gc))
    conn.commit()
    conn.close()

def obter_todas_sequencias_db():
    """Retorna todas as sequências de DNA e seus conteúdos GC do banco de dados."""
    conn = conectar_db()
    # Usamos pd.read_sql_query para ler diretamente para um DataFrame, o que é ótimo para o Streamlit
    df = pd.read_sql_query("SELECT id, sequencia, conteudo_gc FROM sequencias", conn)
    conn.close()
    return df # Retorna um DataFrame do pandas

def calcular_conteudo_gc(sequencia):
    """Calcula o percentual de Guanina (G) e Citosina (C) em uma sequência de DNA."""
    sequencia = sequencia.upper()
    gc_count = sequencia.count('G') + sequencia.count('C')
    total_bases = len(sequencia)

    if total_bases == 0:
        return 0.0
    
    return round((gc_count / total_bases) * 100, 2)

# --- 2. Interface Web (Streamlit) ---

st.set_page_config(page_title="Analisador de Conteúdo GC", layout="centered") # Configurações da página

st.title("🧬 Analisador Web de Conteúdo GC de Sequências de DNA") # Título principal

st.markdown("""
Bem-vindo ao analisador de sequências de DNA!
Insira uma sequência de DNA abaixo para armazená-la e calcular seu conteúdo de Guanina e Citosina (GC).
""")

# Input para a sequência
st.subheader("Inserir Nova Sequência")
sequencia_input = st.text_input("Cole sua sequência de DNA aqui (A, T, C, G)", key="dna_sequence_input")

# Botão para adicionar e analisar
if st.button("Adicionar e Analisar Sequência"):
    nova_sequencia = sequencia_input.strip().upper()

    # Validação da sequência
    if not nova_sequencia:
        st.error("A sequência não pode estar vazia. Por favor, insira bases de DNA.")
    elif not all(base in 'ATCG' for base in nova_sequencia):
        st.error("A sequência deve conter apenas os caracteres A, T, C ou G.")
    else:
        conteudo_gc = calcular_conteudo_gc(nova_sequencia)
        adicionar_sequencia_db(nova_sequencia, conteudo_gc)
        st.success(f"Sequência adicionada com sucesso! Conteúdo GC: **{conteudo_gc}%**")
        # Limpa o input após a adição bem-sucedida
        st.session_state.dna_sequence_input = "" 

st.markdown("---") # Linha divisória

# Exibição das sequências armazenadas
st.subheader("Sequências Armazenadas")

# Garante que a tabela exista antes de tentar buscar dados
criar_tabela() 

df_sequencias = obter_todas_sequencias_db()

if not df_sequencias.empty:
    # Exibe o DataFrame de forma interativa com Streamlit
    st.dataframe(df_sequencias, use_container_width=True, hide_index=True)
else:
    st.info("Nenhuma sequência armazenada ainda. Adicione uma acima!")

st.markdown("---") # Linha divisória

st.caption("Desenvolvido por seu professor de Bioinformática para o estudo de Python, SQLite e Streamlit.")
