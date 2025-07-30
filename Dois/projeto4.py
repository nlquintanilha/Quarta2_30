import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import re
from datetime import datetime
import io

class DNAStreamlitApp:
    def __init__(self):
        """
        Inicializa a aplicação Streamlit para análise de DNA
        """
        # Configuração da página
        st.set_page_config(
            page_title="Analisador de DNA - Bioinformática",
            page_icon="🧬",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Inicializa o banco de dados
        self.init_database()
    
    def init_database(self):
        """
        Inicializa o banco de dados SQLite com session state do Streamlit
        """
        # Usa session_state para manter conexão persistente
        if 'db_conn' not in st.session_state:
            st.session_state.db_conn = sqlite3.connect('dna_sequences_streamlit.db', check_same_thread=False)
            
        self.conn = st.session_state.db_conn
        self.cursor = self.conn.cursor()
        
        # Cria tabela se não existir
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS dna_sequences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                sequence TEXT NOT NULL,
                length INTEGER,
                gc_content REAL,
                a_count INTEGER,
                t_count INTEGER,
                g_count INTEGER,
                c_count INTEGER,
                at_content REAL,
                melting_temp REAL,
                date_added TEXT,
                description TEXT
            )
        ''')
        self.conn.commit()
    
    def validate_dna_sequence(self, sequence):
        """
        Valida e limpa sequência de DNA
        Aceita também códigos IUPAC ambíguos (N, R, Y, etc.)
        """
        # Remove espaços, quebras de linha e números (comum em arquivos FASTA)
        clean_sequence = re.sub(r'[\s\d]', '', sequence.upper())
        
        # Códigos IUPAC para nucleotídeos (incluindo ambíguos)
        iupac_codes = set('ATGCRYSWKMBDHVN')
        
        # Verifica se contém apenas códigos válidos
        if all(nucleotide in iupac_codes for nucleotide in clean_sequence):
            return clean_sequence
        else:
            # Identifica caracteres inválidos para feedback
            invalid_chars = set(clean_sequence) - iupac_codes
            return None, invalid_chars
    
    def analyze_dna_sequence(self, sequence):
        """
        Análise completa de sequência de DNA com métricas avançadas
        """
        length = len(sequence)
        
        # Contagem de nucleotídeos básicos
        a_count = sequence.count('A')
        t_count = sequence.count('T')
        g_count = sequence.count('G')
        c_count = sequence.count('C')
        
        # Conteúdos GC e AT
        gc_content = ((g_count + c_count) / length) * 100 if length > 0 else 0
        at_content = ((a_count + t_count) / length) * 100 if length > 0 else 0
        
        # Temperatura de melting aproximada (fórmula simples)
        # Tm = 4°C × (G + C) + 2°C × (A + T) para sequências curtas
        melting_temp = 4 * (g_count + c_count) + 2 * (a_count + t_count)
        
        # Contagem de códigos ambíguos IUPAC
        ambiguous_count = sum(1 for base in sequence if base not in 'ATGC')
        
        return {
            'length': length,
            'a_count': a_count,
            't_count': t_count,
            'g_count': g_count,
            'c_count': c_count,
            'gc_content': gc_content,
            'at_content': at_content,
            'melting_temp': melting_temp,
            'ambiguous_count': ambiguous_count,
            'purine_count': sequence.count('A') + sequence.count('G'),  # Purinas
            'pyrimidine_count': sequence.count('T') + sequence.count('C')  # Pirimidinas
        }
    
    def get_reverse_complement(self, sequence):
        """
        Calcula a sequência complementar reversa
        """
        complement = {
            'A': 'T', 'T': 'A', 'G': 'C', 'C': 'G',
            'R': 'Y', 'Y': 'R', 'S': 'S', 'W': 'W',
            'K': 'M', 'M': 'K', 'B': 'V', 'D': 'H',
            'H': 'D', 'V': 'B', 'N': 'N'
        }
        
        # Gera complemento e reverte
        reverse_complement = ''.join(complement.get(base, base) for base in reversed(sequence))
        return reverse_complement
    
    def find_orfs(self, sequence):
        """
        Encontra Open Reading Frames (ORFs) na sequência
        """
        start_codons = ['ATG']
        stop_codons = ['TAA', 'TAG', 'TGA']
        orfs = []
        
        # Analisa as 3 fases de leitura
        for frame in range(3):
            i = frame
            while i < len(sequence) - 2:
                codon = sequence[i:i+3]
                if codon in start_codons:
                    # Procura por códon de parada
                    for j in range(i + 3, len(sequence) - 2, 3):
                        next_codon = sequence[j:j+3]
                        if next_codon in stop_codons:
                            orf_length = j + 3 - i
                            if orf_length >= 150:  # ORFs mínimas de 50 aminoácidos
                                orfs.append({
                                    'frame': frame + 1,
                                    'start': i + 1,
                                    'end': j + 3,
                                    'length': orf_length,
                                    'sequence': sequence[i:j+3]
                                })
                            break
                i += 3
        
        return orfs
    
    def create_visualization(self, df):
        """
        Cria visualizações interativas com Plotly
        """
        if df.empty:
            st.warning("Nenhuma sequência encontrada para visualização.")
            return
        
        # Layout com 2 colunas para gráficos
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de distribuição do conteúdo GC
            fig_gc = px.histogram(
                df, 
                x='gc_content', 
                nbins=20,
                title='Distribuição do Conteúdo GC (%)',
                labels={'gc_content': 'Conteúdo GC (%)', 'count': 'Número de Sequências'},
                color_discrete_sequence=['#1f77b4']
            )
            fig_gc.update_layout(height=400)
            st.plotly_chart(fig_gc, use_container_width=True)
        
        with col2:
            # Gráfico de dispersão: Comprimento vs GC
            fig_scatter = px.scatter(
                df, 
                x='length', 
                y='gc_content',
                hover_data=['name'],
                title='Comprimento vs Conteúdo GC',
                labels={'length': 'Comprimento (bp)', 'gc_content': 'Conteúdo GC (%)'},
                color='gc_content',
                color_continuous_scale='viridis'
            )
            fig_scatter.update_layout(height=400)
            st.plotly_chart(fig_scatter, use_container_width=True)
        
        # Gráfico de composição nucleotídica
        st.subheader("Composição Nucleotídica das Sequências")
        
        # Prepara dados para gráfico de barras empilhadas
        composition_data = []
        for _, row in df.iterrows():
            total = row['a_count'] + row['t_count'] + row['g_count'] + row['c_count']
            composition_data.append({
                'Sequência': row['name'],
                'A': (row['a_count'] / total) * 100,
                'T': (row['t_count'] / total) * 100,
                'G': (row['g_count'] / total) * 100,
                'C': (row['c_count'] / total) * 100
            })
        
        comp_df = pd.DataFrame(composition_data)
        
        fig_comp = go.Figure()
        colors = {'A': '#FF6B6B', 'T': '#4ECDC4', 'G': '#45B7D1', 'C': '#96CEB4'}
        
        for nucleotide in ['A', 'T', 'G', 'C']:
            fig_comp.add_trace(go.Bar(
                name=nucleotide,
                x=comp_df['Sequência'],
                y=comp_df[nucleotide],
                marker_color=colors[nucleotide]
            ))
        
        fig_comp.update_layout(
            title='Composição Percentual de Nucleotídeos',
            xaxis_title='Sequências',
            yaxis_title='Porcentagem (%)',
            barmode='stack',
            height=500
        )
        
        st.plotly_chart(fig_comp, use_container_width=True)
    
    def main(self):
        """
        Função principal da aplicação Streamlit
        """
        # Header da aplicação
        st.title("🧬 Analisador de Sequências de DNA")
        st.markdown("### Plataforma de Bioinformática para Análise de DNA")
        
        # Sidebar para navegação
        st.sidebar.title("Menu de Navegação")
        page = st.sidebar.selectbox(
            "Escolha uma página:",
            ["📝 Entrada de Dados", "📊 Visualizações", "🔍 Busca e Análise", "📋 Banco de Dados"]
        )
        
        # Página de entrada de dados
        if page == "📝 Entrada de Dados":
            self.data_entry_page()
        
        # Página de visualizações
        elif page == "📊 Visualizações":
            self.visualization_page()
        
        # Página de busca e análise
        elif page == "🔍 Busca e Análise":
            self.analysis_page()
        
        # Página do banco de dados
        elif page == "📋 Banco de Dados":
            self.database_page()
    
    def data_entry_page(self):
        """
        Página para entrada de novas sequências
        """
        st.header("Entrada de Novas Sequências")
        
        # Formulário de entrada
        with st.form("sequence_form"):
            col1, col2 = st.columns([1, 2])
            
            with col1:
                name = st.text_input("Nome da Sequência*", placeholder="Ex: Gene_BRCA1")
                description = st.text_area("Descrição (opcional)", placeholder="Descrição da sequência...")
            
            with col2:
                sequence = st.text_area(
                    "Sequência de DNA*", 
                    height=150,
                    placeholder="Cole sua sequência aqui (aceita códigos IUPAC)...",
                    help="Aceita sequências com espaços, números e códigos IUPAC ambíguos"
                )
            
            # Opções avançadas
            with st.expander("Opções Avançadas"):
                col3, col4 = st.columns(2)
                with col3:
                    find_orfs_option = st.checkbox("Encontrar ORFs", help="Busca por Open Reading Frames")
                with col4:
                    show_complement = st.checkbox("Mostrar complemento reverso")
            
            submitted = st.form_submit_button("Analisar e Salvar", type="primary")
            
            if submitted:
                if not name or not sequence:
                    st.error("❌ Por favor, preencha o nome e a sequência!")
                else:
                    # Valida sequência
                    validation_result = self.validate_dna_sequence(sequence)
                    
                    if isinstance(validation_result, tuple):  # Erro de validação
                        clean_sequence, invalid_chars = validation_result
                        st.error(f"❌ Sequência contém caracteres inválidos: {', '.join(invalid_chars)}")
                    else:
                        clean_sequence = validation_result
                        
                        # Analisa sequência
                        analysis = self.analyze_dna_sequence(clean_sequence)
                        
                        # Salva no banco
                        try:
                            self.cursor.execute('''
                                INSERT INTO dna_sequences 
                                (name, sequence, length, gc_content, a_count, t_count, g_count, c_count, 
                                 at_content, melting_temp, date_added, description)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                name, clean_sequence, analysis['length'], analysis['gc_content'],
                                analysis['a_count'], analysis['t_count'], analysis['g_count'], 
                                analysis['c_count'], analysis['at_content'], analysis['melting_temp'],
                                datetime.now().strftime("%Y-%m-%d %H:%M:%S"), description
                            ))
                            self.conn.commit()
                            
                            st.success("✅ Sequência salva com sucesso!")
                            
                            # Exibe resultados da análise
                            self.display_analysis_results(name, clean_sequence, analysis, 
                                                         find_orfs_option, show_complement)
                            
                        except sqlite3.Error as e:
                            st.error(f"❌ Erro ao salvar no banco: {e}")
    
    def display_analysis_results(self, name, sequence, analysis, find_orfs=False, show_complement=False):
        """
        Exibe resultados da análise de forma organizada
        """
        st.subheader(f"📊 Resultados da Análise: {name}")
        
        # Métricas principais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Comprimento", f"{analysis['length']} bp")
        with col2:
            st.metric("Conteúdo GC", f"{analysis['gc_content']:.1f}%")
        with col3:
            st.metric("Temp. Melting", f"{analysis['melting_temp']:.1f}°C")
        with col4:
            st.metric("Bases Ambíguas", analysis['ambiguous_count'])
        
        # Composição detalhada
        st.subheader("Composição Nucleotídica")
        comp_col1, comp_col2 = st.columns(2)
        
        with comp_col1:
            st.write("**Contagem Absoluta:**")
            st.write(f"- Adenina (A): {analysis['a_count']}")
            st.write(f"- Timina (T): {analysis['t_count']}")
            st.write(f"- Guanina (G): {analysis['g_count']}")
            st.write(f"- Citosina (C): {analysis['c_count']}")
        
        with comp_col2:
            st.write("**Porcentagens:**")
            st.write(f"- Conteúdo AT: {analysis['at_content']:.1f}%")
            st.write(f"- Conteúdo GC: {analysis['gc_content']:.1f}%")
            st.write(f"- Purinas (A+G): {((analysis['purine_count'])/analysis['length']*100):.1f}%")
            st.write(f"- Pirimidinas (T+C): {((analysis['pyrimidine_count'])/analysis['length']*100):.1f}%")
        
        # Complemento reverso
        if show_complement:
            st.subheader("Sequência Complementar Reversa")
            reverse_comp = self.get_reverse_complement(sequence)
            st.code(reverse_comp, language="text")
        
        # Busca por ORFs
        if find_orfs:
            st.subheader("Open Reading Frames (ORFs)")
            orfs = self.find_orfs(sequence)
            
            if orfs:
                orf_df = pd.DataFrame(orfs)
                st.dataframe(orf_df[['frame', 'start', 'end', 'length']], use_container_width=True)
                
                # Mostra sequência da maior ORF
                if orfs:
                    longest_orf = max(orfs, key=lambda x: x['length'])
                    st.write(f"**Maior ORF (Frame {longest_orf['frame']}):**")
                    st.code(longest_orf['sequence'], language="text")
            else:
                st.info("Nenhuma ORF significativa encontrada (mínimo 150 bp)")
    
    def visualization_page(self):
        """
        Página de visualizações e gráficos
        """
        st.header("📊 Visualizações e Estatísticas")
        
        # Carrega dados do banco
        try:
            df = pd.read_sql_query("SELECT * FROM dna_sequences ORDER BY date_added DESC", self.conn)
            
            if df.empty:
                st.info("Nenhuma sequência encontrada. Adicione sequências na página 'Entrada de Dados'.")
                return
            
            # Estatísticas gerais
            st.subheader("Estatísticas Gerais do Banco")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total de Sequências", len(df))
            with col2:
                st.metric("Comprimento Médio", f"{df['length'].mean():.0f} bp")
            with col3:
                st.metric("GC Médio", f"{df['gc_content'].mean():.1f}%")
            with col4:
                st.metric("Maior Sequência", f"{df['length'].max()} bp")
            
            # Visualizações interativas
            self.create_visualization(df)
            
            # Tabela de estatísticas descritivas
            st.subheader("Estatísticas Descritivas")
            stats_columns = ['length', 'gc_content', 'at_content', 'melting_temp']
            st.dataframe(df[stats_columns].describe(), use_container_width=True)
            
        except Exception as e:
            st.error(f"Erro ao carregar dados: {e}")
    
    def analysis_page(self):
        """
        Página para análises avançadas e busca
        """
        st.header("🔍 Busca e Análise Avançada")
        
        # Tabs para diferentes análises
        tab1, tab2, tab3 = st.tabs(["Busca por Sequência", "Filtros Avançados", "Comparação"])
        
        with tab1:
            st.subheader("Busca por Padrão de Sequência")
            
            pattern = st.text_input("Digite o padrão a buscar:", placeholder="Ex: ATGCGATCG")
            
            if pattern:
                try:
                    # Busca no banco
                    df = pd.read_sql_query(
                        "SELECT * FROM dna_sequences WHERE sequence LIKE ?", 
                        self.conn, 
                        params=[f"%{pattern.upper()}%"]
                    )
                    
                    if not df.empty:
                        st.success(f"Encontradas {len(df)} sequências contendo o padrão.")
                        st.dataframe(df[['name', 'length', 'gc_content', 'description']], use_container_width=True)
                    else:
                        st.info("Nenhuma sequência encontrada com esse padrão.")
                        
                except Exception as e:
                    st.error(f"Erro na busca: {e}")
        
        with tab2:
            st.subheader("Filtros por Propriedades")
            
            col1, col2 = st.columns(2)
            
            with col1:
                min_length = st.number_input("Comprimento mínimo (bp):", min_value=0, value=0)
                max_length = st.number_input("Comprimento máximo (bp):", min_value=0, value=10000)
            
            with col2:
                min_gc = st.slider("GC mínimo (%):", 0, 100, 0)
                max_gc = st.slider("GC máximo (%):", 0, 100, 100)
            
            if st.button("Aplicar Filtros"):
                try:
                    query = """
                    SELECT * FROM dna_sequences 
                    WHERE length BETWEEN ? AND ? 
                    AND gc_content BETWEEN ? AND ?
                    ORDER BY date_added DESC
                    """
                    
                    df = pd.read_sql_query(query, self.conn, params=[min_length, max_length, min_gc, max_gc])
                    
                    if not df.empty:
                        st.success(f"Encontradas {len(df)} sequências que atendem aos critérios.")
                        st.dataframe(df[['name', 'length', 'gc_content', 'melting_temp']], use_container_width=True)
                    else:
                        st.info("Nenhuma sequência atende aos critérios especificados.")
                        
                except Exception as e:
                    st.error(f"Erro ao aplicar filtros: {e}")
        
        with tab3:
            st.subheader("Comparação de Sequências")
            
            try:
                # Lista sequências disponíveis
                df_names = pd.read_sql_query("SELECT id, name FROM dna_sequences", self.conn)
                
                if len(df_names) >= 2:
                    seq_options = [f"{row['id']} - {row['name']}" for _, row in df_names.iterrows()]
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        seq1 = st.selectbox("Primeira sequência:", seq_options)
                    with col2:
                        seq2 = st.selectbox("Segunda sequência:", seq_options, index=1)
                    
                    if st.button("Comparar Sequências"):
                        if seq1 != seq2:
                            # Carrega sequências
                            id1 = int(seq1.split(" - ")[0])
                            id2 = int(seq2.split(" - ")[0])
                            
                            result1 = pd.read_sql_query("SELECT * FROM dna_sequences WHERE id = ?", self.conn, params=[id1])
                            result2 = pd.read_sql_query("SELECT * FROM dna_sequences WHERE id = ?", self.conn, params=[id2])
                            
                            # Exibe comparação
                            comp_data = {
                                'Propriedade': ['Comprimento (bp)', 'Conteúdo GC (%)', 'Conteúdo AT (%)', 'Temp. Melting (°C)'],
                                result1.iloc[0]['name']: [
                                    result1.iloc[0]['length'],
                                    f"{result1.iloc[0]['gc_content']:.1f}",
                                    f"{result1.iloc[0]['at_content']:.1f}",
                                    f"{result1.iloc[0]['melting_temp']:.1f}"
                                ],
                                result2.iloc[0]['name']: [
                                    result2.iloc[0]['length'],
                                    f"{result2.iloc[0]['gc_content']:.1f}",
                                    f"{result2.iloc[0]['at_content']:.1f}",
                                    f"{result2.iloc[0]['melting_temp']:.1f}"
                                ]
                            }
                            
                            comp_df = pd.DataFrame(comp_data)
                            st.dataframe(comp_df, use_container_width=True)
                        else:
                            st.warning("Selecione duas sequências diferentes para comparar.")
                else:
                    st.info("É necessário ter pelo menos 2 sequências no banco para fazer comparações.")
                    
            except Exception as e:
                st.error(f"Erro na comparação: {e}")
    
    def database_page(self):
        """
        Página para gerenciamento do banco de dados
        """
        st.header("📋 Gerenciamento do Banco de Dados")
        
        try:
            # Carrega todos os dados
            df = pd.read_sql_query("SELECT * FROM dna_sequences ORDER BY date_added DESC", self.conn)
            
            if df.empty:
                st.info("Banco de dados vazio.")
                return
            
            # Opções de visualização
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📥 Exportar para CSV"):
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f"dna_sequences_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
            
            with col2:
                if st.button("🗑️ Limpar Banco", type="secondary"):
                    if st.session_state.get('confirm_delete', False):
                        self.cursor.execute("DELETE FROM dna_sequences")
                        self.conn.commit()
                        st.success("Banco de dados limpo!")
                        st.experimental_rerun()
                    else:
                        st.session_state.confirm_delete = True
                        st.warning("Clique novamente para confirmar a exclusão de todos os dados.")
            
            with col3:
                total_size = sum(len(seq) for seq in df['sequence'])
                st.metric("Tamanho Total", f"{total_size:,} bp")
            
            # Tabela completa
            st.subheader("Todas as Sequências")
            
            # Seleção de colunas para exibir
            display_columns = st.multiselect(
                "Colunas para exibir:",
                df.columns.tolist(),
                default=['name', 'length', 'gc_content', 'date_added']
            )
            
            if display_columns:
                st.dataframe(df[display_columns], use_container_width=True)
            
            # Opção para deletar sequências individuais
            st.subheader("Deletar Sequência Individual")
            seq_to_delete = st.selectbox(
                "Selecionar sequência para deletar:",
                options=[f"{row['id']} - {row['name']}" for _, row in df.iterrows()],
                index=None,
                placeholder="Escolha uma sequência..."
            )
            
            if seq_to_delete and st.button("Deletar Sequência Selecionada", type="secondary"):
                seq_id = int(seq_to_delete.split(" - ")[0])
                self.cursor.execute("DELETE FROM dna_sequences WHERE id = ?", (seq_id,))
                self.conn.commit()
                st.success("Sequência deletada com sucesso!")
                st.experimental_rerun()
                
        except Exception as e:
            st.error(f"Erro ao gerenciar banco: {e}")

# Ponto de entrada da aplicação
if __name__ == "__main__":
    app = DNAStreamlitApp()
    app.main()
