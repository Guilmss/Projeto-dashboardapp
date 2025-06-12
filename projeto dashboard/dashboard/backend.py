import pandas as pd
import os
import sys
import sqlite3

DATABASE_NAME = 'dashboard_data.db'
CSV_FILE_NAME = 'vendas.csv'

CSV_CATEGORY = 'category'
CSV_DISCOUNTED_PRICE = 'discounted_price'
CSV_PRODUCT_NAME = 'product_name'
CSV_RATING = 'rating'
CSV_RATING_COUNT = 'rating_count'
CSV_ACTUAL_PRICE = 'actual_price'
CSV_DISCOUNT_PERCENTAGE = 'discount_percentage'

COL_CATEGORIA = 'Categoria'
COL_NOME_PRODUTO = 'Nome do Produto'
COL_VALOR = 'Valor'
COL_AVALIACAO = 'Avaliação'
COL_CONTAGEM_AVALIACOES = 'Contagem de Avaliações'
COL_PERCENTUAL_DESCONTO = 'Percentual de Desconto'
COL_SENTIMENTO = 'Sentimento'
COL_PRECO = 'Preço Original'

#isso aqui é só para simular usuários (obs: eu faria um banco de dados real para ser mais seguro).
USUARIOS_FUNCIONARIOS = {
    "func1": {"password": "senha123", "can_see_details": True, "active": True},
    "ana.vendas": {"password": "vendas234", "can_see_details": False, "active": True}
}
USUARIOS_GERENTES = {
    "admin": "admin",
    "boss": "boss1337"
}

def resource_path_backend(relative_path):
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

def classificar_sentimento(rating):
    if pd.isna(rating):
        return "Não Avaliado"
    elif rating >= 4.0:
        return "Positivo"
    elif rating >= 3.0:
        return "Neutro"
    elif rating < 3.0 and rating >= 0:
        return "Negativo"
    return "Não Avaliado"

def get_db_connection(db_name=DATABASE_NAME):
    db_path = resource_path_backend(db_name)
    conn = sqlite3.connect(db_path)
    return conn, db_path

def inicializar_banco_de_dados():
    conn, db_path = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='vendas'")
    table_exists = cursor.fetchone()

    should_create_table = not table_exists
    should_attempt_import = True

    if table_exists:
        cursor.execute("SELECT COUNT(*) FROM vendas")
        count = cursor.fetchone()[0]
        if count > 0:
            should_attempt_import = False
            print(f"INFO: Tabela 'vendas' já existe e contém dados em '{db_path}'. Importação do CSV ignorada.")
        else:
            print(f"INFO: Tabela 'vendas' existe mas está vazia em '{db_path}'. Tentando importar do CSV '{CSV_FILE_NAME}'.")
    else:
        print(f"INFO: Tabela 'vendas' não existe em '{db_path}'. Será criada e os dados serão importados do CSV '{CSV_FILE_NAME}'.")

    if should_create_table:
        try:
            cursor.execute(f'''
            CREATE TABLE vendas (
                "{CSV_PRODUCT_NAME}" TEXT,
                "{CSV_CATEGORY}" TEXT,
                "{CSV_RATING}" TEXT,
                "{CSV_RATING_COUNT}" TEXT,
                "{CSV_DISCOUNTED_PRICE}" TEXT,
                "{CSV_ACTUAL_PRICE}" TEXT,
                "{CSV_DISCOUNT_PERCENTAGE}" TEXT
            )
            ''')
            print(f"INFO: Tabela 'vendas' criada em '{db_path}'.")
            conn.commit()
        except sqlite3.Error as e:
            print(f"ERRO ao criar tabela 'vendas' em '{db_path}': {e}")
            conn.close()
            return False

    if should_attempt_import:
        caminho_csv = resource_path_backend(CSV_FILE_NAME)

        if not os.path.exists(caminho_csv):
            expected_base_path = ""
            if hasattr(sys, '_MEIPASS'):
                expected_base_path = sys._MEIPASS
            else:
                expected_base_path = os.path.abspath(os.path.dirname(__file__))
            print(f"AVISO: Arquivo '{CSV_FILE_NAME}' não encontrado em '{expected_base_path}'. O caminho completo verificado foi '{caminho_csv}'. Não é possível importar dados para o banco '{db_path}'. A tabela 'vendas' pode estar vazia.")
        else:
            try:
                print(f"INFO: Lendo dados de '{caminho_csv}'...")
                df_csv = pd.read_csv(caminho_csv)

                if df_csv.empty:
                    print(f"AVISO: O arquivo CSV '{caminho_csv}' foi lido mas está vazio. Nenhum dado será importado para a tabela 'vendas'.")
                else:
                    print(f"INFO: Importando dados de '{caminho_csv}' para a tabela 'vendas' em '{db_path}'...")
                    colunas_definidas_na_tabela = [
                        CSV_PRODUCT_NAME, CSV_CATEGORY, CSV_RATING, CSV_RATING_COUNT,
                        CSV_DISCOUNTED_PRICE, CSV_ACTUAL_PRICE, CSV_DISCOUNT_PERCENTAGE
                    ]
                    
                    print(f"DEBUG: Colunas lidas do CSV '{CSV_FILE_NAME}': {df_csv.columns.tolist()}")
                    print(f"DEBUG: Colunas esperadas/definidas na tabela 'vendas' (baseado nas constantes CSV_): {colunas_definidas_na_tabela}")

                    colunas_faltantes_no_csv = [col_esperada for col_esperada in colunas_definidas_na_tabela if col_esperada not in df_csv.columns]
                    
                    if colunas_faltantes_no_csv:
                        print(f"ERRO CRÍTICO DE IMPORTAÇÃO: O arquivo CSV '{CSV_FILE_NAME}' não contém as seguintes colunas, que são necessárias para a tabela 'vendas': {colunas_faltantes_no_csv}.")
                        print(f"ERRO CRÍTICO DE IMPORTAÇÃO: Colunas encontradas no CSV: {df_csv.columns.tolist()}.")
                        print(f"ERRO CRÍTICO DE IMPORTAÇÃO: Verifique se os nomes das colunas no CSV correspondem exatamente às constantes CSV_... no backend.py.")
                        print(f"ERRO CRÍTICO DE IMPORTAÇÃO: A importação de dados foi abortada.")
                        conn.close()
                        return False

                    df_para_importar = df_csv[colunas_definidas_na_tabela]

                    df_para_importar.to_sql('vendas', conn, if_exists='append', index=False)
                    conn.commit()
                    print(f"INFO: Dados de '{CSV_FILE_NAME}' importados com sucesso para a tabela 'vendas'.")

            except pd.errors.EmptyDataError:
                print(f"AVISO: O arquivo CSV '{caminho_csv}' está vazio (EmptyDataError). Nenhum dado será importado.")
            except FileNotFoundError:
                print(f"ERRO: Arquivo CSV '{caminho_csv}' não encontrado ao tentar ler com pandas.")
                if conn: conn.close()
                return False
            except KeyError as e:
                print(f"ERRO CRÍTICO DE IMPORTAÇÃO (KeyError): Uma coluna esperada ('{e}') não foi encontrada no CSV ao tentar preparar os dados para o banco.")
                print(f"ERRO CRÍTICO DE IMPORTAÇÃO: Colunas lidas do CSV: {df_csv.columns.tolist() if 'df_csv' in locals() and hasattr(df_csv, 'columns') else 'Não foi possível ler as colunas do CSV'}.")
                print(f"ERRO CRÍTICO DE IMPORTAÇÃO: Verifique os nomes das colunas no '{CSV_FILE_NAME}' e as constantes CSV_... no backend.py.")
                if conn:
                    conn.rollback()
                    conn.close()
                return False
            except Exception as e:
                print(f"ERRO GERAL ao importar dados do CSV '{caminho_csv}' para o banco de dados '{db_path}': {type(e).__name__} - {e}")
                if conn:
                    conn.rollback()
                    conn.close()
                return False
    
    conn.close()
    return True

def carregar_dados():
    conn, db_path = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='vendas'")
        if not cursor.fetchone():
            print(f"ERRO: A tabela 'vendas' não existe no banco de dados '{db_path}'. Execute a inicialização primeiro.")
            return None

        df = pd.read_sql_query("SELECT * FROM vendas", conn)

        if df.empty:
            print(f"INFO: A tabela 'vendas' no banco de dados '{db_path}' está vazia.")
            return pd.DataFrame()

        colunas_db_originais_necessarias = [
            CSV_CATEGORY,
            CSV_DISCOUNTED_PRICE,
            CSV_PRODUCT_NAME
        ]
        colunas_faltantes_db = [col for col in colunas_db_originais_necessarias if col not in df.columns]

        if colunas_faltantes_db:
            print(f"ERRO: As seguintes colunas essenciais não foram encontradas na tabela 'vendas' do banco de dados: {', '.join(colunas_faltantes_db)}.\nINFO: Colunas encontradas na tabela: {df.columns.tolist()}")
            return None

        df = df.rename(columns={
            CSV_CATEGORY: COL_CATEGORIA,
            CSV_PRODUCT_NAME: COL_NOME_PRODUTO,
            CSV_DISCOUNTED_PRICE: COL_VALOR,
            CSV_RATING: COL_AVALIACAO,
            CSV_RATING_COUNT: COL_CONTAGEM_AVALIACOES,
            CSV_DISCOUNT_PERCENTAGE: COL_PERCENTUAL_DESCONTO,
            CSV_ACTUAL_PRICE: COL_PRECO
        })

        if COL_VALOR in df.columns:
            df[COL_VALOR] = df[COL_VALOR].astype(str).str.replace('₹', '', regex=False).str.replace(',', '', regex=False)
            df[COL_VALOR] = pd.to_numeric(df[COL_VALOR], errors='coerce')
            df.dropna(subset=[COL_VALOR], inplace=True)

        
        if COL_PRECO in df.columns:
            df[COL_PRECO] = df[COL_PRECO].astype(str).str.replace('₹', '', regex=False).str.replace(',', '', regex=False)
            df[COL_PRECO] = pd.to_numeric(df[COL_PRECO], errors='coerce')

        if COL_AVALIACAO in df.columns:
            df[COL_AVALIACAO] = df[COL_AVALIACAO].astype(str).str.extract(r'(\d+\.?\d*)').astype(float)
            df[COL_SENTIMENTO] = df[COL_AVALIACAO].apply(classificar_sentimento)

        if COL_CONTAGEM_AVALIACOES in df.columns:
            df[COL_CONTAGEM_AVALIACOES] = df[COL_CONTAGEM_AVALIACOES].astype(str).str.replace(',', '', regex=False)
            df[COL_CONTAGEM_AVALIACOES] = pd.to_numeric(df[COL_CONTAGEM_AVALIACOES], errors='coerce')

        if COL_PERCENTUAL_DESCONTO in df.columns:
            df[COL_PERCENTUAL_DESCONTO] = df[COL_PERCENTUAL_DESCONTO].astype(str).str.replace('%', '', regex=False)
            df[COL_PERCENTUAL_DESCONTO] = pd.to_numeric(df[COL_PERCENTUAL_DESCONTO], errors='coerce')

        if COL_CATEGORIA in df.columns:
            df[COL_CATEGORIA] = df[COL_CATEGORIA].astype(str).str.split('|').str[0]
        else:
            print(f"ERRO: Coluna '{COL_CATEGORIA}' (mapeada de '{CSV_CATEGORY}') não encontrada após o carregamento e renomeação.")
            return None
        
        if COL_NOME_PRODUTO not in df.columns:
            print(f"ERRO: Coluna '{COL_NOME_PRODUTO}' (mapeada de '{CSV_PRODUCT_NAME}') não encontrada após o carregamento e renomeação.")
            return None
            
        return df
        
    except sqlite3.Error as e:
        print(f"ERRO de Banco de Dados: Erro ao carregar dados de '{db_path}': {e}")
        return None
    except Exception as e:
        print(f"ERRO: Ocorreu um erro inesperado ao carregar os dados do banco de dados '{db_path}': {e}")
        return None
    finally:
        if conn:
            conn.close()
def verificar_login(username, password):
    if username in USUARIOS_FUNCIONARIOS:
        user_data = USUARIOS_FUNCIONARIOS[username]
        if user_data["password"] == password and user_data.get("active", False):
            return "funcionario"
    if username in USUARIOS_GERENTES and USUARIOS_GERENTES[username] == password:
        return "gerente"
    return None
