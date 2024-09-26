import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import mysql.connector
from datetime import datetime, timedelta

# Function to establish a database connection
def connect_db():
    try:
        connection = mysql.connector.connect(
            host="****",
            user="*****",
            password="*********",
            database='******',
        )
        return connection
    except mysql.connector.Error as err:
        st.error(f"Error: {err}")
        return None

# Function to fetch data from the database
def fetch_data(query, connection):
    cursor = connection.cursor()
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    return data

# Fetch and process decision data
def process_decision_data(data):
    manter, comprar, vender, datas, precos = [], [], [], [], []
    for row in data:
        datas.append(row[4])
        precos.append(row[8])
        if row[6] == 0:
            manter.append(row[8])
            comprar.append(None)
            vender.append(None)
        elif row[6] == 1:
            manter.append(None)
            comprar.append(row[8])
            vender.append(None)
        elif row[6] == -1:
            manter.append(None)
            comprar.append(None)
            vender.append(row[8])
    return pd.DataFrame({
        'DataHora': datas,
        'Manter': manter,
        'Comprar': comprar,
        'Vender': vender,
        'Preco': precos
    })

# Add labels to the chart
def add_labels(fig, df, column_name):
    try:
        last_idx = df[column_name].last_valid_index()
        if pd.isna(last_idx):
            raise ValueError(f"No valid index found for column {column_name}")
        last_value = df[column_name].iloc[last_idx]

        fig.add_trace(go.Scatter(
            x=[df['DataHora'].iloc[last_idx]],
            y=[last_value],
            text=[f'{last_value:.2f}'],
            mode='markers+text',
            textposition='bottom right',
            name=f'Último {column_name}',
            showlegend=False
        ))

        max_value = df[column_name].max()
        max_idx = df[column_name].idxmax()

        fig.add_trace(go.Scatter(
            x=[df['DataHora'].iloc[max_idx]],
            y=[max_value],
            text=[f'{max_value:.2f}'],
            mode='markers+text',
            textposition='top right',
            name=f'Max {column_name}',
            showlegend=False
        ))

        min_value = df[column_name].min()
        min_idx = df[column_name].idxmin()

        fig.add_trace(go.Scatter(
            x=[df['DataHora'].iloc[min_idx]],
            y=[min_value],
            text=[f'{min_value:.2f}'],
            mode='markers+text',
            textposition='bottom right',
            name=f'Min {column_name}',
            showlegend=False
        ))
    except Exception as e:
        st.error(f"Error adding labels: {e}")

# Create decision chart
def create_decision_chart(df, title):
    df['DataHora'] = pd.to_datetime(df['DataHora'])
    df = df[df['DataHora'] >= datetime.now() - timedelta(hours=24)]  # Select data from last 24 hours
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['DataHora'], y=df['Manter'], mode='lines', name='Manter'))
    fig.add_trace(go.Scatter(x=df['DataHora'], y=df['Comprar'], mode='lines', name='Comprar'))
    fig.add_trace(go.Scatter(x=df['DataHora'], y=df['Vender'], mode='lines', name='Vender'))
    
    add_labels(fig, df, 'Manter')
    add_labels(fig, df, 'Comprar')
    add_labels(fig, df, 'Vender')
    
    fig.update_layout(
        title=title,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",  # Ajustar posição da legenda para a direita
            x=0.95  # Ajustar posição da legenda para a direita
        ),
        xaxis=dict(
            showline=False,
            showgrid=False,
            zeroline=False
        ),
        yaxis=dict(
            showline=False,
            showgrid=False,
            zeroline=False,
            showticklabels=False
        ),
        margin=dict(l=0, r=0, t=30, b=0),
        height=300,
        width=800
    )
    return fig

# Create index chart
def create_index_chart(data):
    datas, valores = [], []
    for row in data:
        datas.append(row[4])
        valores.append(row[5])
    
    df = pd.DataFrame({
        'DataHora': datas,
        'Valor': valores
    })
    
    fig = px.line(df, x='DataHora', y='Valor', title='Índice das Decisões')
    fig.update_yaxes(range=[-1.5, 1.5])
    fig.add_hline(y=0.9, line_dash="dash", line_color="orange", annotation_text="Limite Superior (+0.9)")
    fig.add_hline(y=-0.9, line_dash="dash", line_color="green", annotation_text="Limite Inferior (-0.9)")

    fig.update_layout(height=300, width=800)
    return fig

# Create rentability chart
def create_rentability_chart(data):
    DataTimeDec, rentab, quantid = [], [], []
    for row in data:
        DataTimeDec.append(row[0])
        rentab.append(row[1])
        quantid.append(row[2])
    
    df = pd.DataFrame({
        'DataTimeDec': DataTimeDec,
        'Rentab': rentab,
        'Quantid': quantid
    })
    df['DataTimeDec'] = pd.to_datetime(df['DataTimeDec'])
    
    fig = px.bar(df, x='DataTimeDec', y='Rentab', title='Rentabilidade e Quantidade ao Longo do Tempo', 
                 labels={'Rentab': 'Rentabilidade', 'DataTimeDec': 'Data'}, text='Rentab')
    fig.add_trace(go.Scatter(
        x=df['DataTimeDec'],
        y=df['Quantid'],
        mode='lines+markers',
        name='Quantidade',
        line=dict(color='firebrick'),
        yaxis='y2'
    ))
    fig.update_layout(
        xaxis_title='Data',
        yaxis_title='Rentabilidade',
        title_x=0.5,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        yaxis2=dict(
            title='Quantidade',
            overlaying='y',
            side='right',
            showgrid=False,
            zeroline=False,
            showticklabels=False
        ),
        xaxis=dict(showline=False, showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showline=False, showgrid=False, zeroline=False, showticklabels=False),
        height=300,
        width=800
    )
    
    fig.update_traces(textposition='outside', selector=dict(type='bar'))
    return fig

# Create log chart
def create_log_chart(data):
    DsProcesso, tempomedio = [], []
    for row in data:
        DsProcesso.append(row[0])
        tempomedio.append(row[1])
    
    df = pd.DataFrame({
        'DsProcesso': DsProcesso,
        'tempomedio': [f'{val:.2f}' for val in tempomedio]
    })
    
    fig = px.bar(df, x='DsProcesso', y='tempomedio', title='Execução dos Módulos em Minutos', text='tempomedio')
    fig.update_layout(
        xaxis_title='Processo',
        yaxis_title='Tempo Médio (min)',
        title_x=0.5,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        xaxis=dict(showline=False, showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showline=False, showgrid=False, zeroline=False, showticklabels=False),
        height=300,
        width=800
    )
    
    fig.update_traces(textposition='outside', selector=dict(type='bar'))
    return fig

# Main function to run the app
def main():
    st.set_page_config(layout="wide")
    
    connection = connect_db()
    if not connection:
        st.stop()

    query_decision = "SELECT * FROM riabd.dadosdecisao WHERE DataTimeDec >= NOW() - INTERVAL 1 DAY ORDER BY DataTimeDec DESC LIMIT 1000"
    SelDadosDecisao = fetch_data(query_decision, connection)
    if not SelDadosDecisao:
        st.warning("Nenhum dado foi encontrado, a execução foi interrompida.")
        st.stop()

    df_decision = process_decision_data(SelDadosDecisao)
    fig1 = create_decision_chart(df_decision, 'Gráfico de Preços e Decisões')
    fig2 = create_decision_chart(df_decision, 'Gráfico de Preços e Decisões Teste')
    fig3 = create_index_chart(SelDadosDecisao)

    query_rentability = "SELECT DATE(DataTimeDec) as DataDec, sum(VarDec) as rentab, count(DSAtivo) as quantid FROM riabd.dadosdecisao WHERE CdDecF=-1 AND (DataTimeDec >= NOW() - INTERVAL 5 DAY) GROUP BY DATE(DataTimeDec) ORDER BY DATE(DataTimeDec)"
    SelDadosRentabilidade = fetch_data(query_rentability, connection)
    fig4 = create_rentability_chart(SelDadosRentabilidade)

    query_log = "SELECT DsProcesso, avg(TempoMin) as tempomedio FROM riabd.dadoslog WHERE DatatempoFim >= NOW() - INTERVAL 1 DAY GROUP BY DsProcesso"
    SelDadoslog = fetch_data(query_log, connection)
    fig5 = create_log_chart(SelDadoslog)
    
    connection.close()

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(fig1)
        st.plotly_chart(fig3)
        st.plotly_chart(fig5)
    with col2:
        st.plotly_chart(fig2)
        st.plotly_chart(fig4)

if __name__ == "__main__":
    main()
