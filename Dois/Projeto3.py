import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import sqlite3
import re
from datetime import datetime

class DNASequenceManager:
    def __init__(self):
        # Inicializa a classe e configura a interface
        self.root = tk.Tk()
        self.root.title("Gerenciador de Sequências de DNA")
        self.root.geometry("800x600")
        
        # Inicializa o banco de dados
        self.init_database()
        
        # Cria a interface gráfica
        self.create_widgets()
    
    def init_database(self):
        """
        Inicializa o banco de dados SQLite e cria a tabela se não existir
        """
        # Conecta ao banco de dados (cria o arquivo se não existir)
        self.conn = sqlite3.connect('dna_sequences.db')
        self.cursor = self.conn.cursor()
        
        # Cria a tabela para armazenar sequências de DNA
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sequences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                sequence TEXT NOT NULL,
                length INTEGER,
                gc_content REAL,
                a_count INTEGER,
                t_count INTEGER,
                g_count INTEGER,
                c_count INTEGER,
                date_added TEXT
            )
        ''')
        self.conn.commit()
    
    def create_widgets(self):
        """
        Cria todos os widgets da interface gráfica
        """
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configuração do grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Label e entrada para nome da sequência
        ttk.Label(main_frame, text="Nome da Sequência:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_entry = ttk.Entry(main_frame, width=50)
        self.name_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Label e área de texto para sequência de DNA
        ttk.Label(main_frame, text="Sequência de DNA:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.sequence_text = scrolledtext.ScrolledText(main_frame, height=6, width=60)
        self.sequence_text.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Frame para botões
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        # Botões de ação
        ttk.Button(button_frame, text="Adicionar Sequência", 
                  command=self.add_sequence).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Listar Sequências", 
                  command=self.list_sequences).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Limpar", 
                  command=self.clear_fields).pack(side=tk.LEFT, padx=5)
        
        # Área de resultados
        ttk.Label(main_frame, text="Resultados:").grid(row=3, column=0, sticky=tk.W, pady=(20,5))
        self.results_text = scrolledtext.ScrolledText(main_frame, height=15, width=80)
        self.results_text.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Configurar expansão da área de resultados
        main_frame.rowconfigure(4, weight=1)
    
    def validate_dna_sequence(self, sequence):
        """
        Valida se a sequência contém apenas nucleotídeos válidos (A, T, G, C)
        Ignora espaços e quebras de linha
        """
        # Remove espaços e quebras de linha, converte para maiúscula
        clean_sequence = re.sub(r'\s', '', sequence.upper())
        
        # Verifica se contém apenas A, T, G, C
        if re.match(r'^[ATGC]+$', clean_sequence):
            return clean_sequence
        else:
            return None
    
    def analyze_sequence(self, sequence):
        """
        Realiza análises básicas da sequência de DNA:
        - Contagem de cada nucleotídeo
        - Cálculo do conteúdo GC
        - Comprimento da sequência
        """
        # Conta cada nucleotídeo
        a_count = sequence.count('A')
        t_count = sequence.count('T')
        g_count = sequence.count('G')
        c_count = sequence.count('C')
        
        # Calcula o comprimento total
        length = len(sequence)
        
        # Calcula o conteúdo GC (porcentagem de G e C)
        gc_content = ((g_count + c_count) / length) * 100 if length > 0 else 0
        
        return {
            'length': length,
            'a_count': a_count,
            't_count': t_count,
            'g_count': g_count,
            'c_count': c_count,
            'gc_content': gc_content
        }
    
    def add_sequence(self):
        """
        Adiciona uma nova sequência ao banco de dados
        """
        # Obtém os dados dos campos de entrada
        name = self.name_entry.get().strip()
        sequence = self.sequence_text.get("1.0", tk.END).strip()
        
        # Validação básica
        if not name:
            messagebox.showerror("Erro", "Por favor, insira um nome para a sequência.")
            return
        
        if not sequence:
            messagebox.showerror("Erro", "Por favor, insira uma sequência de DNA.")
            return
        
        # Valida a sequência de DNA
        clean_sequence = self.validate_dna_sequence(sequence)
        if not clean_sequence:
            messagebox.showerror("Erro", "Sequência inválida! Use apenas nucleotídeos A, T, G, C.")
            return
        
        # Analisa a sequência
        analysis = self.analyze_sequence(clean_sequence)
        
        # Insere no banco de dados
        try:
            self.cursor.execute('''
                INSERT INTO sequences 
                (name, sequence, length, gc_content, a_count, t_count, g_count, c_count, date_added)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                name,
                clean_sequence,
                analysis['length'],
                analysis['gc_content'],
                analysis['a_count'],
                analysis['t_count'],
                analysis['g_count'],
                analysis['c_count'],
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            self.conn.commit()
            
            # Mostra resultado da análise
            result = f"Sequência '{name}' adicionada com sucesso!\n"
            result += f"Comprimento: {analysis['length']} nucleotídeos\n"
            result += f"Conteúdo GC: {analysis['gc_content']:.2f}%\n"
            result += f"Contagem - A: {analysis['a_count']}, T: {analysis['t_count']}, "
            result += f"G: {analysis['g_count']}, C: {analysis['c_count']}\n"
            result += "-" * 50 + "\n"
            
            self.results_text.insert(tk.END, result)
            self.clear_fields()
            
        except sqlite3.Error as e:
            messagebox.showerror("Erro no Banco", f"Erro ao adicionar sequência: {e}")
    
    def list_sequences(self):
        """
        Lista todas as sequências armazenadas no banco de dados
        """
        try:
            self.cursor.execute('SELECT * FROM sequences ORDER BY date_added DESC')
            sequences = self.cursor.fetchall()
            
            if not sequences:
                self.results_text.insert(tk.END, "Nenhuma sequência encontrada.\n")
                return
            
            result = "=== SEQUÊNCIAS ARMAZENADAS ===\n\n"
            
            for seq in sequences:
                # seq contém: id, name, sequence, length, gc_content, a_count, t_count, g_count, c_count, date_added
                result += f"ID: {seq[0]}\n"
                result += f"Nome: {seq[1]}\n"
                result += f"Sequência: {seq[2][:100]}{'...' if len(seq[2]) > 100 else ''}\n"
                result += f"Comprimento: {seq[3]} nucleotídeos\n"
                result += f"Conteúdo GC: {seq[4]:.2f}%\n"
                result += f"Contagem - A: {seq[5]}, T: {seq[6]}, G: {seq[7]}, C: {seq[8]}\n"
                result += f"Data: {seq[9]}\n"
                result += "-" * 60 + "\n"
            
            self.results_text.delete("1.0", tk.END)
            self.results_text.insert("1.0", result)
            
        except sqlite3.Error as e:
            messagebox.showerror("Erro no Banco", f"Erro ao listar sequências: {e}")
    
    def clear_fields(self):
        """
        Limpa os campos de entrada
        """
        self.name_entry.delete(0, tk.END)
        self.sequence_text.delete("1.0", tk.END)
    
    def run(self):
        """
        Inicia a aplicação
        """
        # Configura o fechamento da aplicação
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
    
    def on_closing(self):
        """
        Fecha a conexão com o banco e encerra a aplicação
        """
        self.conn.close()
        self.root.destroy()

# Executa a aplicação
if __name__ == "__main__":
    app = DNASequenceManager()
    app.run()