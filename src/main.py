from datetime import datetime, timedelta
from decouple import config
from googletrans import Translator
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, IntegerType, FloatType, StringType, ArrayType
import pyspark.sql.functions as F
import googlemaps
import json
import requests
import re
import pandas as pd
import mysql.connector as connection

# Criando a Spark Session
spark = SparkSession.builder.appName("WeatherTrafficInsights").getOrCreate()

gmaps_api_key = config('GMAPS_API_KEY')
gmaps = googlemaps.Client(key=gmaps_api_key)

openweather_api_key = config('OPENWEATHER_API_KEY')

def traduzir_condicao(descricao):
    tradutor = Translator()
    traducao = tradutor.translate(descricao, dest='pt').text

    return traducao

def extrair_tempo(tempo_string):
    # Usando expressões regulares para extrair valores numéricos e unidades
    tempo = re.findall(r'(\d+)\s*(dia|hora|minuto)', tempo_string)

    tempo_total = 0

    for valor, unidade in tempo:
        valor = int(valor)

        if unidade == 'dia':
            tempo_total += valor * 24 * 60
        elif unidade == 'hora':
            tempo_total += valor * 60
        elif unidade == 'minuto':
            tempo_total += valor

    return tempo_total

def obter_previsao_tempo_origem(latitude, longitude, data_partida):
    url_api = 'http://api.openweathermap.org/data/2.5/forecast?units=metric&lat=' \
              + str(latitude) + '&lon=' + str(longitude) + '&APPID=' + openweather_api_key
    resposta = requests.get(url_api)
    dados_previsao = json.loads(resposta.text)

    if 'list' in dados_previsao:
        # Encontrar o intervalo mais próximo a data de partida
        previsao_data_desejada = min(
            dados_previsao['list'],
            key=lambda x: abs(datetime.utcfromtimestamp(x['dt']) - data_partida)
        )

        previsao_tempo = {
            'timestamp': data_partida,
            'temperatura': previsao_data_desejada['main']['temp'],
            'condicao': traduzir_condicao(previsao_data_desejada['weather'][0]['description'])
        }

        temperatura = previsao_tempo['temperatura']
        condicao_clima = previsao_tempo['condicao']

        return temperatura, condicao_clima
    else:
        print("Chave 'list' não encontrada no JSON. Atribuindo valores nulos.")
        return None, None

def obter_previsao_tempo_destino(latitude, longitude, data_partida, tempo_viagem_minutos):
    url_api = 'http://api.openweathermap.org/data/2.5/forecast?units=metric&lat=' \
              + str(latitude) + '&lon=' + str(longitude) + '&APPID=' + openweather_api_key
    resposta = requests.get(url_api)
    dados_previsao = json.loads(resposta.text)

    if 'list' in dados_previsao:
        # Encontrar o intervalo mais próximo a data de chegada
        data_chegada = data_partida + timedelta(minutes=tempo_viagem_minutos)
        previsao_data_desejada = min(
            dados_previsao['list'],
            key=lambda x: abs(datetime.utcfromtimestamp(x['dt']) - data_chegada)
        )

        previsao_tempo = {
            'timestamp': data_chegada,
            'temperatura': previsao_data_desejada['main']['temp'],
            'condicao': traduzir_condicao(previsao_data_desejada['weather'][0]['description'])
        }

        temperatura = previsao_tempo['temperatura']
        condicao_clima = previsao_tempo['condicao']

        return temperatura, condicao_clima
    else:
        print("Chave 'list' não encontrada no JSON. Atribuindo valores nulos.")
        return None, None

def obter_direcoes_com_coords(origem, destino, veiculo_de_preferencia):
    modo = 'driving' if veiculo_de_preferencia in ['Carro', 'Moto'] else 'transit'

    resultados_rota = gmaps.directions(origem, destino, mode=modo, language="pt-BR", region="BR")

    coordenadas_rota = []

    if resultados_rota:
        for leg in resultados_rota[0]['legs']:
            for passo in leg['steps']:
                local_origem = passo['start_location']
                coordenadas_rota.append({
                    "latitude": local_origem['lat'],
                    "longitude": local_origem['lng'],
                    "distancia": float(re.sub(r',', '.', re.sub(r'[^\d,]', '', leg['distance']['text']))),
                    "tempo": extrair_tempo(leg['duration']['text'])
                })

    return coordenadas_rota


usuario = config('DATABASE_USER')
senha = config('DATABASE_PASSWORD')
host = config('DATABASE_HOST')
nome_bd = config('DATABASE_NAME')

database = connection.connect(host=host, database=nome_bd, user=usuario, passwd=senha, use_pure=True)
query_pessoas = "SELECT * from Pessoas;"
df_pessoas_pd = pd.read_sql(query_pessoas, database)
df_pessoas = spark.createDataFrame(df_pessoas_pd)

query_rotas = "SELECT * from Rotas;"
df_rotas_pd = pd.read_sql(query_rotas, database)
df_rotas = spark.createDataFrame(df_rotas_pd)

database.close()

# Definindo o schema do DataFrame de Trânsito
schema_transito = StructType([
    StructField("cod_rota", IntegerType(), False),
    StructField("latitude", FloatType(), True),
    StructField("longitude", FloatType(), True),
    StructField("distancia", FloatType(), True),
    StructField("tempo", IntegerType(), True),
    StructField("direcao_rota", IntegerType(), True),
])

# Definindo o schema do DataFrame de Clima
schema_clima = StructType([
    StructField("cod_rota", IntegerType(), False),
    StructField("temperatura_origem", FloatType(), True),
    StructField("condicao_clima_origem", StringType(), True),
    StructField("temperatura_destino", FloatType(), True),
    StructField("condicao_clima_destino", StringType(), True),
])

# Criando DataFrames vazios
df_transito = spark.createDataFrame([], schema=schema_transito)
df_clima = spark.createDataFrame([], schema=schema_clima)

# Criando UDFs
obter_direcoes_com_coords_udf = F.udf(obter_direcoes_com_coords, ArrayType(StructType([
    StructField("latitude", FloatType(), True),
    StructField("longitude", FloatType(), True),
    StructField("distancia", FloatType(), True),
    StructField("tempo", IntegerType(), True),
])))

obter_previsao_tempo_origem_udf = F.udf(obter_previsao_tempo_origem, StructType([
    StructField("temperatura_origem", FloatType(), True),
    StructField("condicao_clima_origem", StringType(), True),
]))

obter_previsao_tempo_destino_udf = F.udf(obter_previsao_tempo_destino, StructType([
    StructField("temperatura_destino", FloatType(), True),
    StructField("condicao_clima_destino", StringType(), True),
]))

# Realizando join entre as bases de Pessoas e Rotas para obtenção do campo 'veiculo_de_preferencia'
df_pessoas_rotas = df_rotas.join(df_pessoas, df_rotas["cod_pessoa"] == df_pessoas["cod_pessoa"])

# Obtendo as coordenadas, distância e tempo da rota
df_rotas_com_dados = df_pessoas_rotas.withColumn("dados_rota", obter_direcoes_com_coords_udf("origem_rota", "destino_rota", "veiculo_de_preferencia"))

# Explodindo a coluna 'dados_rota' para criar múltiplas linhas
df_rotas_explodido = df_rotas_com_dados.select(
    "cod_rota",
    "origem_rota",
    "destino_rota",
    "data_rota",
    F.explode_outer("dados_rota").alias("dados_explodidos")
)

# Separando os dados explodidos
df_transito = df_rotas_explodido.groupBy(
    "cod_rota",
    "data_rota",
    F.col("dados_explodidos.distancia").alias("distancia_rota"),
    F.col("dados_explodidos.tempo").alias("tempo_rota")
).agg(
    F.first("dados_explodidos.latitude").alias("origem_latitude"),
    F.first("dados_explodidos.longitude").alias("origem_longitude"),
    F.last("dados_explodidos.latitude").alias("destino_latitude"),
    F.last("dados_explodidos.longitude").alias("destino_longitude"),
).orderBy("cod_rota")

# Adicionando as colunas ao DataFrame df_clima
df_clima = df_transito.select(
    "cod_rota",
    "data_rota",
    "origem_latitude",
    "origem_longitude",
    "destino_latitude",
    "destino_longitude",
    "tempo_rota"
).select(
    "cod_rota",
    obter_previsao_tempo_origem_udf("origem_latitude", "origem_longitude", "data_rota").alias("origem"),
    obter_previsao_tempo_destino_udf("destino_latitude", "destino_longitude", "data_rota", "tempo_rota").alias("destino")
).select(
    "cod_rota",
    "origem.temperatura_origem",
    "origem.condicao_clima_origem",
    "destino.temperatura_destino",
    "destino.condicao_clima_destino"
).orderBy("cod_rota")

# Criando visualizações dos DataFrames para utilização na query
df_pessoas.createOrReplaceTempView("pessoas")
df_rotas.createOrReplaceTempView("rotas")
df_transito.createOrReplaceTempView("transito")
df_clima.createOrReplaceTempView("clima")

# Criando tabela principal para insights
df_weather_traffic = spark.sql("""
    SELECT
      p.cod_pessoa,
      r.cod_rota,
      p.nome,
      p.sexo,
      p.idade,
      p.veiculo_de_preferencia,
      r.origem_rota,
      r.destino_rota,
      r.data_rota AS data_partida,
      r.finalidade_rota,
      t.origem_latitude,
      t.origem_longitude,
      t.destino_latitude,
      t.destino_longitude,
      t.distancia_rota,
      t.tempo_rota,
      c.temperatura_origem,
      c.condicao_clima_origem,
      c.temperatura_destino,
      c.condicao_clima_destino
    FROM pessoas p
    INNER JOIN rotas r
      ON p.cod_pessoa = r.cod_pessoa
    INNER JOIN transito t
      ON r.cod_rota = t.cod_rota
      AND t.distancia_rota IS NOT NULL -- Tirando os dados nulos de viagens de Ônibus que não tem como serem realizadas
    INNER JOIN clima c
      ON t.cod_rota = c.cod_rota
    ORDER BY cod_pessoa, cod_rota
""")