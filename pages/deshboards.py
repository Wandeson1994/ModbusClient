import streamlit as st
from pymodbus.client import ModbusTcpClient
import sqlite3
import time
import threading
import pandas as pd


def sanitize_ip(ip):
    """Converte o IP em um nome válido para tabela SQL"""
    cleaned_ip = ''.join([c for c in ip if c.isdigit() or c == '.'])
    return 'dados_' + cleaned_ip.replace('.', '_')


def ler_modbus(ip):
    """Lê dados Modbus e armazena em tabela específica do IP"""
    table_name = sanitize_ip(ip)

    with sqlite3.connect('dados_modbus.db', timeout=10) as conn:
        cursor = conn.cursor()

        # Cria tabela para o IP se não existir
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS "{table_name}" (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endereco INTEGER,
                valor INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

        client = ModbusTcpClient(ip, port=502)

        try:
            client.connect()
            st.success(f"Conexão com {ip} estabelecida com sucesso!")
        except Exception as e:
            st.error(f"Erro na conexão com {ip}: {str(e)}")
            return

        while True:
            try:
                resposta = client.read_holding_registers(0, 10)
                if resposta.isError():
                    st.error(f"Erro na leitura do {ip}")
                    break

                # Insere dados na tabela específica
                for i, valor in enumerate(resposta.registers):
                    cursor.execute(f'''
                        INSERT INTO "{table_name}" (endereco, valor)
                        VALUES (?, ?)
                    ''', (i, valor))

                conn.commit()
                time.sleep(5)

            except Exception as e:
                st.error(f"Erro no {ip}: {str(e)}")
                break

        client.close()


# Interface Streamlit
st.title("📡 Dados Modbus")

# Gerenciamento de estado
if 'ips' not in st.session_state:
    st.session_state.ips = set()

# Controles de entrada
col1, col2 = st.columns(2, vertical_alignment="bottom")
ip_servidor = col1.text_input("Digite o IP do servidor Modbus:")

if col2.button("▶ Iniciar Leitura") and ip_servidor:
    try:
        # Testa conexão antes de iniciar thread
        with ModbusTcpClient(ip_servidor, port=502) as client:
            if client.connect():
                st.session_state.ips.add(ip_servidor)
                threading.Thread(
                    target=ler_modbus,
                    args=(ip_servidor,),
                    daemon=True
                ).start()
                st.toast(f"Monitorando {ip_servidor}")
            else:
                st.error("Conexão falhou")
    except Exception as e:
        st.error(f"Erro de conexão: {str(e)}")

col3, col4 = st.columns(2, vertical_alignment="bottom")
# Visualização de dados
if st.session_state.ips:
    selected_ip = col3.selectbox("IPs monitorados:", list(st.session_state.ips))

    if col4.button("📊 Mostrar Dados"):
        table_name = sanitize_ip(selected_ip)

        try:
            with sqlite3.connect('dados_modbus.db', timeout=10) as conn:
                df = pd.read_sql_query(f'''
                    SELECT endereco, valor, timestamp 
                    FROM "{table_name}" 
                    ORDER BY timestamp DESC 
                    LIMIT 100
                ''', conn)

                if not df.empty:
                    st.subheader(f"Tabela de Daods do IP - {selected_ip}")

                    # Exibe tabela
                    st.dataframe(df, use_container_width=True)

                    # Prepara dados para o gráfico
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df_pivot = df.pivot(index='timestamp',
                                        columns='endereco',
                                        values='valor')

                    # Exibe gráfico
                    st.subheader("Variação dos Valores por Endereço")
                    st.line_chart(df_pivot)

                else:
                    st.info("Nenhum dado encontrado para este IP")

        except sqlite3.Error as e:
            st.error(f"Erro no banco de dados: {str(e)}")

else:
    st.info("Adicione um IP para começar o monitoramento")