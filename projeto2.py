import tkinter as tk
from tkinter import messagebox
import sqlite3

# --- 1. Funções de Configuração do Banco de Dados (Reaproveitadas do Projeto 1) ---

DB_NAME = 'sequencias_dna_gc.db' # Nome diferente para este projeto

def conectar_db():
    conn = sqlite3.connect(DB_NAME)
    return conn

def criar_tabela():
    conn = conectar_db()
    cursor = conn.cursor()
    # Adicionamos uma coluna para armazenar o conteúdo GC
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sequencias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sequencia TEXT NOT NULL,
            conteudo_gc REAL -- Nova coluna para conteúdo GC, tipo REAL (número decimal)
        )
    ''')
    conn.commit()
    conn.close()

def adicionar_sequencia_db(sequencia, conteudo_gc):
    """Adiciona uma nova sequência de DNA e seu conteúdo GC ao banco de dados."""
    conn = conectar_db()
    cursor = conn.cursor()
    # Inserindo tanto a sequência quanto o conteúdo GC
    cursor.execute('INSERT INTO sequencias (sequencia, conteudo_gc) VALUES (?, ?)', (sequencia, conteudo_gc))
    conn.commit()
    conn.close()

def obter_todas_sequencias_db():
    """Retorna todas as sequências de DNA e seus conteúdos GC armazenados no banco de dados."""
    conn = conectar_db()
    cursor = conn.cursor()
    # Selecionando também a coluna conteudo_gc
    cursor.execute('SELECT id, sequencia, conteudo_gc FROM sequencias')
    sequencias = cursor.fetchall()
    conn.close()
    return sequencias

# --- 2. Lógica da Aplicação (Com Nova Função de Análise) ---

def calcular_conteudo_gc(sequencia):
    """Calcula o percentual de Guanina (G) e Citosina (C) em uma sequência de DNA."""
    sequencia = sequencia.upper() # Garante que a sequência esteja em maiúsculas
    gc_count = sequencia.count('G') + sequencia.count('C') # Conta G e C
    total_bases = len(sequencia) # Obtém o comprimento total da sequência

    if total_bases == 0:
        return 0.0 # Evita divisão por zero para sequências vazias
    
    # Calcula o percentual e arredonda para 2 casas decimais
    return round((gc_count / total_bases) * 100, 2)

def adicionar_e_analisar_sequencia():
    """Função chamada quando o botão 'Adicionar e Analisar' é clicado."""
    nova_sequencia = entrada_sequencia.get().strip().upper()

    # Validação (igual ao Projeto 1)
    if not nova_sequencia:
        messagebox.showwarning("Entrada Inválida", "A sequência não pode estar vazia.")
        return
    if not all(base in 'ATCG' for base in nova_sequencia):
        messagebox.showwarning("Entrada Inválida", "A sequência deve conter apenas A, T, C ou G.")
        return

    conteudo_gc = calcular_conteudo_gc(nova_sequencia) # Calcula o conteúdo GC
    
    adicionar_sequencia_db(nova_sequencia, conteudo_gc) # Adiciona ao banco, agora com GC
    
    messagebox.showinfo("Sucesso", f"Sequência adicionada e analisada! Conteúdo GC: {conteudo_gc}%")
    
    entrada_sequencia.delete(0, tk.END)
    atualizar_lista_sequencias() # Atualiza a lista com o novo dado

def atualizar_lista_sequencias():
    """Atualiza a área de texto com todas as sequências e seus conteúdos GC."""
    lista_sequencias.delete('1.0', tk.END)
    sequencias = obter_todas_sequencias_db()

    if not sequencias:
        lista_sequencias.insert(tk.END, "Nenhuma sequência armazenada ainda.")
        return

    # Iterando agora sobre (id, sequencia, conteudo_gc)
    for id_seq, seq_dna, gc_val in sequencias:
        lista_sequencias.insert(tk.END, f"ID: {id_seq} - Seq: {seq_dna} - GC: {gc_val}%\n")

# --- 3. Interface Gráfica (Tkinter - Similar ao Projeto 1, com pequenas adaptações) ---

root = tk.Tk()
root.title("Analisador de Conteúdo GC de Sequências de DNA")
root.geometry("700x550")

label_sequencia = tk.Label(root, text="Digite a Sequência de DNA:")
label_sequencia.pack(pady=5)

entrada_sequencia = tk.Entry(root, width=60)
entrada_sequencia.pack(pady=5)

# O botão agora chama a função que também faz a análise
botao_adicionar_analisar = tk.Button(root, text="Adicionar e Analisar Sequência", command=adicionar_e_analisar_sequencia)
botao_adicionar_analisar.pack(pady=5)

label_lista = tk.Label(root, text="Sequências Armazenadas e Conteúdo GC:")
label_lista.pack(pady=5)

frame_lista = tk.Frame(root)
frame_lista.pack(pady=5, fill=tk.BOTH, expand=True)

barra_rolagem = tk.Scrollbar(frame_lista)
barra_rolagem.pack(side=tk.RIGHT, fill=tk.Y)

lista_sequencias = tk.Text(frame_lista, wrap=tk.WORD, yscrollcommand=barra_rolagem.set)
lista_sequencias.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

barra_rolagem.config(command=lista_sequencias.yview)

# --- Inicialização ---
criar_tabela()
atualizar_lista_sequencias()

root.mainloop()