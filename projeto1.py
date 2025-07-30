import tkinter as tk
from tkinter import messagebox
import sqlite3

# --- 1. Funções de Configuração do Banco de Dados ---

DB_NAME = 'sequencias_dna.db' # Nome do arquivo do banco de dados

def conectar_db():
    """Conecta ao banco de dados SQLite e retorna o objeto de conexão."""
    conn = sqlite3.connect(DB_NAME)
    return conn

def criar_tabela():
    """Cria a tabela 'sequencias' se ela não existir."""
    conn = conectar_db() # Conecta ao banco de dados
    cursor = conn.cursor() # Cria um objeto cursor para executar comandos SQL
    # Comando SQL para criar a tabela. 'id' é a chave primária auto-incrementável.
    # 'sequencia' armazena o texto da sequência de DNA.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sequencias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sequencia TEXT NOT NULL
        )
    ''')
    conn.commit() # Salva as alterações no banco de dados
    conn.close() # Fecha a conexão com o banco de dados

def adicionar_sequencia_db(sequencia):
    """Adiciona uma nova sequência de DNA ao banco de dados."""
    conn = conectar_db()
    cursor = conn.cursor()
    # Comando SQL para inserir uma sequência. O '?' é um placeholder para o valor.
    cursor.execute('INSERT INTO sequencias (sequencia) VALUES (?)', (sequencia,))
    conn.commit()
    conn.close()

def obter_todas_sequencias_db():
    """Retorna todas as sequências de DNA armazenadas no banco de dados."""
    conn = conectar_db()
    cursor = conn.cursor()
    # Comando SQL para selecionar todas as colunas de todas as linhas da tabela.
    cursor.execute('SELECT * FROM sequencias')
    sequencias = cursor.fetchall() # Obtém todos os resultados da consulta
    conn.close()
    return sequencias

# --- 2. Lógica da Aplicação (Interação com a Interface) ---

def adicionar_sequencia():
    """Função chamada quando o botão 'Adicionar' é clicado."""
    nova_sequencia = entrada_sequencia.get().strip().upper() # Pega o texto da caixa de entrada, remove espaços e converte para maiúsculas

    # Validação simples para sequências de DNA (A, T, C, G)
    if not nova_sequencia:
        messagebox.showwarning("Entrada Inválida", "A sequência não pode estar vazia.")
        return
    if not all(base in 'ATCG' for base in nova_sequencia):
        messagebox.showwarning("Entrada Inválida", "A sequência deve conter apenas A, T, C ou G.")
        return
    
    adicionar_sequencia_db(nova_sequencia) # Adiciona a sequência ao banco de dados
    messagebox.showinfo("Sucesso", "Sequência adicionada com sucesso!")
    entrada_sequencia.delete(0, tk.END) # Limpa a caixa de entrada após adicionar
    atualizar_lista_sequencias() # Atualiza a lista exibida na interface

def atualizar_lista_sequencias():
    """Atualiza a área de texto com todas as sequências do banco de dados."""
    lista_sequencias.delete('1.0', tk.END) # Limpa o conteúdo atual da área de texto
    sequencias = obter_todas_sequencias_db() # Obtém todas as sequências do banco

    if not sequencias:
        lista_sequencias.insert(tk.END, "Nenhuma sequência armazenada ainda.")
        return
    
    # Formata e insere cada sequência na área de texto
    for id_seq, seq_dna in sequencias:
        lista_sequencias.insert(tk.END, f"ID: {id_seq} - Sequência: {seq_dna}\n")

# --- 3. Interface Gráfica (Tkinter) ---

# Configura a janela principal do Tkinter
root = tk.Tk()
root.title("Gerenciador de Sequências de DNA")
root.geometry("600x500") # Define o tamanho da janela

# Rótulo e entrada para a sequência
label_sequencia = tk.Label(root, text="Digite a Sequência de DNA:")
label_sequencia.pack(pady=5) # Adiciona um espaçamento vertical

entrada_sequencia = tk.Entry(root, width=50) # Cria uma caixa de entrada de texto
entrada_sequencia.pack(pady=5)

# Botão para adicionar a sequência
botao_adicionar = tk.Button(root, text="Adicionar Sequência", command=adicionar_sequencia)
botao_adicionar.pack(pady=5)

# Rótulo para a lista de sequências
label_lista = tk.Label(root, text="Sequências Armazenadas:")
label_lista.pack(pady=5)

# Área de texto para exibir as sequências (com barra de rolagem)
frame_lista = tk.Frame(root) # Um frame para conter a área de texto e a barra de rolagem
frame_lista.pack(pady=5, fill=tk.BOTH, expand=True) # Preenche e expande o espaço disponível

barra_rolagem = tk.Scrollbar(frame_lista) # Cria a barra de rolagem
barra_rolagem.pack(side=tk.RIGHT, fill=tk.Y) # Posiciona à direita e preenche verticalmente

lista_sequencias = tk.Text(frame_lista, wrap=tk.WORD, yscrollcommand=barra_rolagem.set)
lista_sequencias.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

barra_rolagem.config(command=lista_sequencias.yview) # Conecta a barra de rolagem à área de texto

# --- Inicialização ---
criar_tabela() # Garante que a tabela do banco de dados exista ao iniciar
atualizar_lista_sequencias() # Carrega as sequências existentes ao iniciar

root.mainloop() # Inicia o loop principal da interface gráfica