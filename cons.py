import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# Configurar o layout da página como "wide" para maximizar a largura
st.set_page_config(layout="wide")

# Reduzir as margens laterais do conteúdo principal usando CSS
st.markdown(
    """
    <style>
    .main .block-container {
        padding-left: 0;
        padding-right: 0;
        max-width: 100%;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("Simulação de Consórcio vs Financiamento vs Renda Fixa")

# Exibir a data e hora
st.write("Data e hora: 12:29 PM -03, Wednesday, May 28, 2025")

# Barra Lateral para Filtros (Pré-editados)
st.sidebar.header("Parâmetros")
V = st.sidebar.number_input("Valor do Bem (R$)", value=1.0, step=1000.0, help="Digite o valor do bem desejado.")
duration_months = st.sidebar.number_input("Prazo (Meses)", value=60, step=1, help="Prazo em meses para consórcio, financiamento e renda fixa.")
F_percent = st.sidebar.number_input("Taxa Administrativa (%)", value=25.0, step=0.1, help="Percentual da taxa administrativa do consórcio.")
taxa_juros_anual = st.sidebar.number_input("Taxa de Juros do Financiamento Anual (%)", value=25.0, step=0.1, help="Taxa de juros anual do financiamento.")
lance_percent = st.sidebar.number_input("Lance Embutido (% do Valor do Bem)", value=0.0, step=0.1, max_value=100.0, help="Percentual do lance embutido, que reduz o crédito recebido.")
lance_livre_percent = st.sidebar.number_input("Lance Livre (% do Valor do Bem)", value=0.0, step=0.1, max_value=100.0, help="Percentual do lance livre, pago com recursos próprios.")
taxa_retorno_anual = st.sidebar.number_input("Taxa de Retorno Anual da Renda Fixa (%)", value=10.0, step=0.1, help="Taxa de retorno anual da aplicação em renda fixa.")

if V and F_percent and duration_months and taxa_juros_anual and taxa_retorno_anual:
    # Cálculos do Consórcio
    F = F_percent / 100
    M = V / (duration_months * (1 - F))  # Valor mensal pago no consórcio
    V_ajustado = V * (1 - lance_percent / 100)
    lance_embutido = V * (lance_percent / 100)
    lance_livre = V * (lance_livre_percent / 100)
    total_pago_sem_lance = duration_months * M
    total_pago_consorcio = max(total_pago_sem_lance - lance_embutido - lance_livre, 0)
    valor_liquido_consorcio = V_ajustado - lance_livre

    # Calcular o CET do Consórcio
    cet_consorcio = (total_pago_consorcio / valor_liquido_consorcio - 1) * 100 if valor_liquido_consorcio > 0 else 0

    months = list(range(1, duration_months + 1))
    cumulative_contributions_consorcio = [min(k * M, total_pago_consorcio) for k in months]

    # Cálculos do Financiamento
    taxa_juros_mensal = (1 + taxa_juros_anual / 100) ** (1 / 12) - 1
    P = V * taxa_juros_mensal / (1 - (1 + taxa_juros_mensal) ** (-duration_months))
    total_pago_financiamento = P * duration_months

    # Calcular o CET do Financiamento
    cet_financiamento = (total_pago_financiamento / V - 1) * 100 if V > 0 else 0

    cumulative_payments_financiamento = [P * k for k in months]

    # Cálculos da Aplicação em Renda Fixa
    taxa_retorno_mensal = (1 + taxa_retorno_anual / 100) ** (1 / 12) - 1  # Converter taxa anual para mensal
    montante_renda_fixa = []
    montante_acumulado = 0
    for k in range(duration_months):
        montante_acumulado = (montante_acumulado + M) * (1 + taxa_retorno_mensal)
        montante_renda_fixa.append(montante_acumulado)
    total_renda_fixa = montante_renda_fixa[-1] if montante_renda_fixa else 0  # Valor final acumulado

    # Criar DataFrame para o gráfico
    df = pd.DataFrame({'Mês': months})
    df['Contribuições Acumuladas (Consórcio)'] = cumulative_contributions_consorcio
    df['Pagamentos Acumulados (Financiamento)'] = cumulative_payments_financiamento
    df['Montante Acumulado (Renda Fixa)'] = montante_renda_fixa

    # Gráfico de comparação
    st.header("Comparação: Consórcio vs Financiamento vs Renda Fixa")
    fig = go.Figure()

    # Determinar qual é o menor valor final e ajustar a opacidade
    valores_finais = {
        "Consórcio": total_pago_consorcio,
        "Financiamento": total_pago_financiamento,
        "Renda Fixa": total_renda_fixa
    }
    menor_valor = min(valores_finais.values())
    
    opacity_consorcio = 1.0 if valores_finais["Consórcio"] == menor_valor else 0.6
    opacity_financiamento = 1.0 if valores_finais["Financiamento"] == menor_valor else 0.6
    # A opacidade da renda fixa será mantida em 1.0, já que não tem área preenchida
    opacity_renda_fixa = 1.0

    # Linha do Consórcio (Área) com opacidade ajustada
    fig.add_trace(go.Scatter(
        x=df['Mês'],
        y=df['Contribuições Acumuladas (Consórcio)'],
        mode='lines',
        name=f"Consórcio<br>Valor líquido recebido: R${valor_liquido_consorcio:,.2f}",
        line=dict(color='blue'),
        fill='tozeroy',
        opacity=opacity_consorcio,
        showlegend=True
    ))
    
    # Linha do Financiamento (Área) com opacidade ajustada
    fig.add_trace(go.Scatter(
        x=df['Mês'],
        y=df['Pagamentos Acumulados (Financiamento)'],
        mode='lines',
        name=f"Financiamento<br>Valor recebido: R${V:,.2f}",
        line=dict(color='red'),
        fill='tozeroy',
        opacity=opacity_financiamento,
        showlegend=True
    ))

    # Linha da Renda Fixa (apenas linha tracejada, sem área)
    fig.add_trace(go.Scatter(
        x=df['Mês'],
        y=df['Montante Acumulado (Renda Fixa)'],
        mode='lines',
        name=f"Renda Fixa<br>Valor final acumulado: R${total_renda_fixa:,.2f}",
        line=dict(color='green', dash='dash'),  # Linha tracejada
        fill=None,  # Sem preenchimento
        opacity=opacity_renda_fixa,
        showlegend=True
    ))

    # Definir a posição dos valores (5 meses antes do final)
    label_position = max(1, duration_months - 5)
    consorcio_value_at_label = df['Contribuições Acumuladas (Consórcio)'][label_position - 1]
    financiamento_value_at_label = df['Pagamentos Acumulados (Financiamento)'][label_position - 1]
    renda_fixa_value_at_label = df['Montante Acumulado (Renda Fixa)'][label_position - 1]

    # Adicionar o texto do Consórcio (total pago e CET)
    fig.add_trace(go.Scatter(
        x=[label_position],
        y=[consorcio_value_at_label * 0.95],
        mode='text',
        text=[f"R${total_pago_consorcio:,.2f}"],
        textposition='middle center',
        textfont=dict(size=14, color='black', family="Arial"),
        showlegend=False
    ))
    fig.add_trace(go.Scatter(
        x=[label_position + 0.2],
        y=[consorcio_value_at_label * 0.95 - 0.02],
        mode='text',
        text=[f"R${total_pago_consorcio:,.2f}"],
        textposition='middle center',
        textfont=dict(size=14, color='black', family="Arial"),
        showlegend=False
    ))
    fig.add_annotation(
        x=label_position,
        y=consorcio_value_at_label * 0.95,
        text=f"R${total_pago_consorcio:,.2f}",
        showarrow=False,
        font=dict(size=14, color='blue', family="Arial"),
        bgcolor='white',
        borderpad=4
    )
    fig.add_trace(go.Scatter(
        x=[label_position],
        y=[consorcio_value_at_label * 0.85],
        mode='text',
        text=[f"CET: {cet_consorcio:,.2f}%"],
        textposition='middle center',
        textfont=dict(size=12, color='black', family="Arial"),
        showlegend=False
    ))
    fig.add_trace(go.Scatter(
        x=[label_position + 0.2],
        y=[consorcio_value_at_label * 0.85 - 0.02],
        mode='text',
        text=[f"CET: {cet_consorcio:,.2f}%"],
        textposition='middle center',
        textfont=dict(size=12, color='black', family="Arial"),
        showlegend=False
    ))
    fig.add_annotation(
        x=label_position,
        y=consorcio_value_at_label * 0.85,
        text=f"CET: {cet_consorcio:,.2f}%",
        showarrow=False,
        font=dict(size=12, color='blue', family="Arial"),
        bgcolor='white',
        borderpad=4
    )
    
    # Adicionar o texto do Financiamento (total pago e CET)
    fig.add_trace(go.Scatter(
        x=[label_position],
        y=[financiamento_value_at_label * 0.95],
        mode='text',
        text=[f"R${total_pago_financiamento:,.2f}"],
        textposition='middle center',
        textfont=dict(size=14, color='black', family="Arial"),
        showlegend=False
    ))
    fig.add_trace(go.Scatter(
        x=[label_position + 0.2],
        y=[financiamento_value_at_label * 0.95 - 0.02],
        mode='text',
        text=[f"R${total_pago_financiamento:,.2f}"],
        textposition='middle center',
        textfont=dict(size=14, color='black', family="Arial"),
        showlegend=False
    ))
    fig.add_annotation(
        x=label_position,
        y=financiamento_value_at_label * 0.95,
        text=f"R${total_pago_financiamento:,.2f}",
        showarrow=False,
        font=dict(size=14, color='red', family="Arial"),
        bgcolor='white',
        borderpad=4
    )
    fig.add_trace(go.Scatter(
        x=[label_position],
        y=[financiamento_value_at_label * 0.85],
        mode='text',
        text=[f"CET: {cet_financiamento:,.2f}%"],
        textposition='middle center',
        textfont=dict(size=12, color='black', family="Arial"),
        showlegend=False
    ))
    fig.add_trace(go.Scatter(
        x=[label_position + 0.2],
        y=[financiamento_value_at_label * 0.85 - 0.02],
        mode='text',
        text=[f"CET: {cet_financiamento:,.2f}%"],
        textposition='middle center',
        textfont=dict(size=12, color='black', family="Arial"),
        showlegend=False
    ))
    fig.add_annotation(
        x=label_position,
        y=financiamento_value_at_label * 0.85,
        text=f"CET: {cet_financiamento:,.2f}%",
        showarrow=False,
        font=dict(size=12, color='red', family="Arial"),
        bgcolor='white',
        borderpad=4
    )

    # Adicionar o texto da Renda Fixa (total acumulado)
    fig.add_trace(go.Scatter(
        x=[label_position],
        y=[renda_fixa_value_at_label * 0.95],
        mode='text',
        text=[f"R${total_renda_fixa:,.2f}"],
        textposition='middle center',
        textfont=dict(size=14, color='black', family="Arial"),
        showlegend=False
    ))
    fig.add_trace(go.Scatter(
        x=[label_position + 0.2],
        y=[renda_fixa_value_at_label * 0.95 - 0.02],
        mode='text',
        text=[f"R${total_renda_fixa:,.2f}"],
        textposition='middle center',
        textfont=dict(size=14, color='black', family="Arial"),
        showlegend=False
    ))
    fig.add_annotation(
        x=label_position,
        y=renda_fixa_value_at_label * 0.95,
        text=f"R${total_renda_fixa:,.2f}",
        showarrow=False,
        font=dict(size=14, color='green', family="Arial"),
        bgcolor='white',
        borderpad=4
    )
    
    # Ajustar o layout para que o eixo Y acompanhe o maior valor individual
    max_y = max(total_pago_consorcio, total_pago_financiamento, total_renda_fixa) * 1.2
    fig.update_layout(
        title='Contribuições Acumuladas (Consórcio) vs Pagamentos Acumulados (Financiamento) vs Montante Acumulado (Renda Fixa)',
        xaxis_title='Mês',
        yaxis_title='Valor (R$)',
        yaxis=dict(range=[0, max_y]),
        hovermode='x unified',
        height=600
    )
    # Usar a largura total do contêiner principal
    st.plotly_chart(fig, use_container_width=True)

    # Resumos em formato de tabela, lado a lado
    st.header("Resumo")
    col1, col2, col3 = st.columns(3, gap="small")

    # Resumo do Consórcio (Tabela)
    with col1:
        st.subheader("Resumo do Consórcio")
        consorcio_data = {
            "Descrição": [
                "Total pago por participante",
                "Valor líquido recebido",
                "Taxas pagas por participante",
                "Custo Efetivo Total (CET)"
            ],
            "Valor (R$)": [
                f"{total_pago_consorcio:,.2f}",
                f"{valor_liquido_consorcio:,.2f}",
                f"{F * total_pago_sem_lance:,.2f}",
                f"{cet_consorcio:,.2f}%"
            ]
        }
        if lance_percent > 0:
            consorcio_data["Descrição"].append("Lance embutido")
            consorcio_data["Valor (R$)"].append(f"{lance_embutido:,.2f} ({lance_percent}% do valor do bem)")
        if lance_livre_percent > 0:
            consorcio_data["Descrição"].append("Lance livre")
            consorcio_data["Valor (R$)"].append(f"{lance_livre:,.2f} ({lance_livre_percent}% do valor do bem)")
        consorcio_df = pd.DataFrame(consorcio_data)
        st.table(consorcio_df)

    # Resumo do Financiamento (Tabela)
    with col2:
        st.subheader("Resumo do Financiamento")
        financiamento_data = {
            "Descrição": [
                "Parcela mensal",
                "Total pago",
                "Juros pagos",
                "Valor recebido",
                "Custo Efetivo Total (CET)"
            ],
            "Valor (R$)": [
                f"{P:,.2f}",
                f"{total_pago_financiamento:,.2f}",
                f"{total_pago_financiamento - V:,.2f}",
                f"{V:,.2f}",
                f"{cet_financiamento:,.2f}%"
            ]
        }
        financiamento_df = pd.DataFrame(financiamento_data)
        st.table(financiamento_df)

    # Resumo da Renda Fixa (Tabela)
    with col3:
        st.subheader("Resumo da Renda Fixa")
        renda_fixa_data = {
            "Descrição": [
                "Investimento mensal",
                "Taxa de retorno anual",
                "Montante final acumulado"
            ],
            "Valor": [
                f"R${M:,.2f}",
                f"{taxa_retorno_anual}%",
                f"R${total_renda_fixa:,.2f}"
            ]
        }
        renda_fixa_df = pd.DataFrame(renda_fixa_data)
        st.table(renda_fixa_df)

else:
    st.warning("Por favor, preencha todos os parâmetros para visualizar a simulação.")