import streamlit as st
import pandas as pd
import math
from fpdf import FPDF
from datetime import datetime

# --- Configuração da Página ---
st.set_page_config(page_title="Pedido de Troca", page_icon="🚜", layout="centered")

# --- Função para Gerar PDF ---
def gerar_pdf(cliente, cidade, area, itens_pedido, total_sacas):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", style="B", size=16)
    
    # Cabeçalho
    pdf.cell(200, 10, txt="PEDIDO DE TROCA", ln=True, align="C")
    pdf.set_font("Helvetica", size=12)
    pdf.cell(200, 10, txt=f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True, align="C")
    pdf.ln(10)
    
    # Dados do Cliente
    pdf.set_font("Helvetica", style="B", size=12)
    pdf.cell(200, 8, txt="DADOS DO CLIENTE", ln=True)
    pdf.set_font("Helvetica", size=12)
    pdf.cell(200, 8, txt=f"Nome: {cliente}", ln=True)
    pdf.cell(200, 8, txt=f"Cidade: {cidade}", ln=True)
    pdf.cell(200, 8, txt=f"Área (ha): {area}", ln=True)
    pdf.ln(10)
    
    # Tabela de Itens
    pdf.set_font("Helvetica", style="B", size=10)
    # Cabeçalho da tabela
    pdf.cell(60, 8, txt="Produto", border=1)
    pdf.cell(30, 8, txt="Dose", border=1, align="C")
    pdf.cell(30, 8, txt="Emb.", border=1, align="C")
    pdf.cell(35, 8, txt="Qtde Ajst.", border=1, align="C")
    pdf.cell(35, 8, txt="Total (Sacas)", border=1, align="C")
    pdf.ln()
    
    pdf.set_font("Helvetica", size=10)
    for item in itens_pedido:
        pdf.cell(60, 8, txt=str(item['Produto'])[:30], border=1)
        pdf.cell(30, 8, txt=f"{item['Dose']:.2f}", border=1, align="C")
        pdf.cell(30, 8, txt=f"{item['Embalagem']}", border=1, align="C")
        pdf.cell(35, 8, txt=f"{item['Qtde Ajustada']}", border=1, align="C")
        pdf.cell(35, 8, txt=f"{item['Valor em Sacas']:.2f}", border=1, align="C")
        pdf.ln()
        
    pdf.ln(10)
    pdf.set_font("Helvetica", style="B", size=14)
    pdf.cell(200, 10, txt=f"TOTAL DO PEDIDO: {total_sacas:.2f} SACAS", ln=True, align="R")
    
    # Retorna o PDF em formato de bytes para o Streamlit
    return bytes(pdf.output())

# --- Estado do Aplicativo (Carrinho de compras) ---
if 'pedido' not in st.session_state:
    st.session_state.pedido = []

st.title("📱 Pedido de Troca Mobile")

# --- 1. Upload da Planilha de Preços ---
st.markdown("### 1. Tabela de Preços")
arquivo_excel = st.file_uploader("Carregue a planilha atualizada (Excel)", type=["xlsx"])

if arquivo_excel:
    # Lendo os dados
    df = pd.read_excel(arquivo_excel, sheet_name="Tabela_Precos")
    
    # --- 2. Dados do Cliente ---
    st.markdown("### 2. Dados do Cliente")
    cliente = st.text_input("Nome do Cliente")
    cidade = st.text_input("Cidade")
    area = st.number_input("Área a Tratar (ha)", min_value=0.0, step=1.0)
    
    if area > 0 and cliente != "":
        st.markdown("### 3. Adicionar Produtos")
        
        # Filtro de Grupo e Produto
        grupos = df['Grupo'].dropna().unique()
        grupo_selecionado = st.selectbox("Selecione o Grupo", grupos)
        
        # Filtra os produtos com base no grupo
        df_produtos = df[df['Grupo'] == grupo_selecionado]
        produto_selecionado = st.selectbox("Selecione o Produto", df_produtos['Descricao'].unique())
        
        # Pegando os dados do produto selecionado
        dados_produto = df_produtos[df_produtos['Descricao'] == produto_selecionado].iloc[0]
        dose = float(dados_produto['Dose'])
        embalagem = float(dados_produto['Embalagem'])
        preco_venda = float(dados_produto['Valor Venda'])
        paridade = float(dados_produto['Paridade']) # Considerado aqui como o Preço da Saca
        
        # Cálculos Matemáticos
        qtde_exata = area * dose
        # Arredondando para o múltiplo da embalagem
        qtde_ajustada = math.ceil(qtde_exata / embalagem) * embalagem if embalagem > 0 else qtde_exata
        
        # Regra de negócio: Valor em Sacas = (Quantidade * Preço do Produto) / Valor da Saca (Paridade)
        valor_total_rs = qtde_ajustada * preco_venda
        valor_em_sacas = valor_total_rs / paridade if paridade > 0 else 0
        
        # Mostrando um resumo antes de adicionar
        st.info(f"**Cálculo:** Área {area}ha x Dose {dose} = {qtde_exata}\n"
                f"**Ajuste Embalagem ({embalagem}):** {qtde_ajustada}\n"
                f"**Valor do Item:** {valor_em_sacas:.2f} sacas")
        
        if st.button("➕ Adicionar ao Pedido"):
            st.session_state.pedido.append({
                "Produto": produto_selecionado,
                "Dose": dose,
                "Embalagem": embalagem,
                "Qtde Ajustada": qtde_ajustada,
                "Valor em Sacas": valor_em_sacas
            })
            st.success("Produto adicionado!")
            st.rerun() # Atualiza a tela
            
    # --- 4. Resumo e Regra dos 5 Itens ---
    st.markdown("---")
    st.markdown(f"### 🛒 Itens no Pedido: {len(st.session_state.pedido)}")
    
    if len(st.session_state.pedido) > 0:
        df_pedido = pd.DataFrame(st.session_state.pedido)
        st.dataframe(df_pedido) # Mostra a tabela de itens
        
        total_sacas = df_pedido["Valor em Sacas"].sum()
        st.markdown(f"**Total do Pedido:** {total_sacas:.2f} sacas")
        
        # Regra de negócio: Exigir 5 itens para fechar pedido
        if len(st.session_state.pedido) >= 5:
            st.success("✅ Pedido validado! (5 ou mais itens). Você já pode gerar o PDF.")
            
            # Botão de Gerar/Baixar PDF
            pdf_bytes = gerar_pdf(cliente, cidade, area, st.session_state.pedido, total_sacas)
            
            st.download_button(
                label="📄 Exportar Pedido para PDF",
                data=pdf_bytes,
                file_name=f"Pedido_{cliente.replace(' ', '_')}.pdf",
                mime="application/pdf"
            )
        else:
            faltam = 5 - len(st.session_state.pedido)
            st.warning(f"⚠️ Atenção: Faltam {faltam} itens. O PDF e o fechamento do pedido só são liberados a partir de 5 itens inseridos.")
            
        if st.button("🗑️ Limpar Pedido"):
            st.session_state.pedido = []
            st.rerun()

else:
    st.info("👆 Por favor, faça o upload da planilha 'Pedido_Troca.xlsx' criada anteriormente para iniciar.")
