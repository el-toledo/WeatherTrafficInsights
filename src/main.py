from datetime import datetime, timedelta
from decouple import config
from googletrans import Translator
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, IntegerType, FloatType, StringType, ArrayType
from pyspark.sql.window import Window
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
    print(type(latitude))
    url_api = 'http://api.openweathermap.org/data/2.5/forecast?units=metric&lat=' \
              + str(latitude) + '&lon=' + str(longitude) + '&APPID=' + openweather_api_key
    resposta = requests.get(url_api)
    dados_previsao = json.loads(resposta.text)

    # Encontrar o intervalo mais próximo a data de partida
    # data_partida = datetime.strptime(data_partida, "%Y-%m-%d %H:%M:%S")
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

def obter_previsao_tempo_destino(latitude, longitude, data_partida, tempo_viagem_minutos):
    url_api = 'http://api.openweathermap.org/data/2.5/forecast?units=metric&lat=' \
              + str(latitude) + '&lon=' + str(longitude) + '&APPID=' + openweather_api_key
    resposta = requests.get(url_api)
    dados_previsao = json.loads(resposta.text)

    # Encontrar o intervalo mais próximo a data de partida
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

def obter_direcoes_com_coords(origin, destination, mode='driving'):
    resultados_rota = gmaps.directions(origin, destination, mode=mode, language="pt-BR", region="BR")

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
    StructField("latitude", FloatType(), False),
    StructField("longitude", FloatType(), False),
    StructField("distancia", FloatType(), False),
    StructField("tempo", IntegerType(), False),
    StructField("direcao_rota", IntegerType(), False),
])

# Definindo o schema do DataFrame de Clima
schema_clima = StructType([
    StructField("cod_rota", IntegerType(), False),
    StructField("temperatura_origem", FloatType(), False),
    StructField("condicao_clima_origem", StringType(), False),
    StructField("temperatura_destino", FloatType(), False),
    StructField("condicao_clima_destino", StringType(), False),
])

# Criando DataFrames vazios
df_transito = spark.createDataFrame([], schema=schema_transito)
df_clima = spark.createDataFrame([], schema=schema_clima)

# Criando UDFs
obter_direcoes_com_coords_udf = F.udf(obter_direcoes_com_coords, ArrayType(StructType([
    StructField("latitude", FloatType(), False),
    StructField("longitude", FloatType(), False),
    StructField("distancia", FloatType(), False),
    StructField("tempo", IntegerType(), False),
])))

obter_previsao_tempo_origem_udf = F.udf(obter_previsao_tempo_origem, StructType([
    StructField("temperatura_origem", FloatType(), False),
    StructField("condicao_clima_origem", StringType(), False),
]))

obter_previsao_tempo_destino_udf = F.udf(obter_previsao_tempo_destino, StructType([
    StructField("temperatura_destino", FloatType(), False),
    StructField("condicao_clima_destino", StringType(), False),
]))

# Obtendo as coordenadas, distância e tempo da rota
df_rotas_com_dados = df_rotas.withColumn("dados_rota", obter_direcoes_com_coords_udf("origem_rota", "destino_rota"))

# Explodindo a coluna 'dados_rota' para criar múltiplas linhas
df_rotas_explodido = df_rotas_com_dados.select(
    "cod_rota",
    "origem_rota",
    "destino_rota",
    "data_rota",
    F.explode_outer("dados_rota").alias("dados_explodidos")
)

# Separando os dados explodidos na criação do DataFrame Trânsito
df_transito = df_rotas_explodido.select(
    "cod_rota",
    "data_rota",
    F.col("dados_explodidos.latitude").alias("latitude"),
    F.col("dados_explodidos.longitude").alias("longitude"),
    F.col("dados_explodidos.distancia").alias("distancia"),
    F.col("dados_explodidos.tempo").alias("tempo")
)

# Criando coluna 'direcao_rota'
window_spec_transito = Window.partitionBy("cod_rota").orderBy("cod_rota")
df_transito = df_transito.withColumn("direcao_rota", F.row_number().over(window_spec_transito))

window_spec_clima_coordenadas = Window.partitionBy("cod_rota").orderBy("direcao_rota").rowsBetween(Window.unboundedPreceding, Window.unboundedFollowing)

# Selecionando as coordenadas de origem para cada rota
df_primeira_coordenada = df_transito.withColumn("primeira_coordenada", F.first("direcao_rota").over(window_spec_clima_coordenadas)).filter(
    F.col("direcao_rota") == F.col("primeira_coordenada")
).select(
    "cod_rota",
    "direcao_rota",
    "primeira_coordenada",
    "data_rota",
    "latitude",
    "longitude",
    "tempo"
).withColumnRenamed("latitude", "origem_latitude").withColumnRenamed("longitude", "origem_longitude")

# Selecionando as coordenadas de destino para cada rota
df_ultima_coordenada = df_transito.withColumn("ultima_coordenada", F.last("direcao_rota").over(window_spec_clima_coordenadas)).filter(
    F.col("direcao_rota") == F.col("ultima_coordenada")
).select(
    "cod_rota",
    "direcao_rota",
    "ultima_coordenada",
    "data_rota",
    "latitude",
    "longitude",
    "tempo"
).withColumnRenamed("latitude", "destino_latitude").withColumnRenamed("longitude", "destino_longitude")

# Criando o DataFrame clima com base nas coordenadas de origem e destino
df_clima = df_primeira_coordenada.join(df_ultima_coordenada, "cod_rota", "left").select(
    "cod_rota",
    df_primeira_coordenada["data_rota"],
    "origem_latitude",
    "origem_longitude",
    "destino_latitude",
    "destino_longitude",
    df_primeira_coordenada["tempo"].alias("tempo_rota")
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
)

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
    t.direcao_rota,
    t.latitude,
    t.longitude,
    t.distancia,
    t.tempo,
    c.temperatura_origem,
    c.condicao_clima_origem,
    c.temperatura_destino,
    c.condicao_clima_destino
  FROM pessoas p
  INNER JOIN rotas r
    ON p.cod_pessoa = r.cod_pessoa
  INNER JOIN transito t
    ON r.cod_rota = t.cod_rota
  INNER JOIN clima c
    ON t.cod_rota = c.cod_rota
""")