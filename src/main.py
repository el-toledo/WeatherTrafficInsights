from datetime import datetime, timedelta
from decouple import config
from googletrans import Translator
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, IntegerType, FloatType, StringType
import googlemaps
import json
import requests
import re

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

# def obter_clima(coordenadas):
#     url_api = 'http://api.openweathermap.org/data/2.5/weather?units=metric&lat=' \
#               + str(coordenadas[0]) + '&lon=' + str(coordenadas[1]) + '&APPID=' + openweather_api_key
#     resposta = requests.get(url_api)
#     return json.loads(resposta.text)

def obter_previsao_tempo_origem(coordenadas, data_partida):
    url_api = 'http://api.openweathermap.org/data/2.5/forecast?units=metric&lat=' \
              + str(coordenadas[0]) + '&lon=' + str(coordenadas[1]) + '&APPID=' + openweather_api_key
    resposta = requests.get(url_api)
    dados_previsao = json.loads(resposta.text)

    # Encontra o intervalo mais próximo a data de partida
    data_partida = datetime.strptime(data_partida, "%Y-%m-%d %H:%M:%S")
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

def obter_previsao_tempo_destino(coordenadas, data_partida, tempo_viagem_minutos):
    url_api = 'http://api.openweathermap.org/data/2.5/forecast?units=metric&lat=' \
              + str(coordenadas[0]) + '&lon=' + str(coordenadas[1]) + '&APPID=' + openweather_api_key
    resposta = requests.get(url_api)
    dados_previsao = json.loads(resposta.text)

    # Encontra o intervalo mais próximo a data de partida
    data_chegada = datetime.strptime(data_partida, "%Y-%m-%d %H:%M:%S") + timedelta(minutes=tempo_viagem_minutos)
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

def obter_direcoes_com_coords(origem, destino, modo='driving'):
    resultados_rota = gmaps.directions(origem, destino, mode=modo, language="pt-BR", region="BR")
    
    coordenadas_rota = []
    
    if resultados_rota:
        for leg in resultados_rota[0]['legs']:
            for passo in leg['steps']:
                local_origem = passo['start_location']
                coordenadas_rota.append((local_origem['lat'], local_origem['lng']))
                
    distancia_rota = resultados_rota[0]['legs'][0]['distance']['text']
    tempo_rota = resultados_rota[0]['legs'][0]['duration']['text']

    distancia_rota = int(re.sub(r'\D', '', distancia_rota).replace(',', '.'))

    tempo_rota = extrair_tempo(tempo_rota)

    return coordenadas_rota, distancia_rota, tempo_rota


def teste_api():
# Teste para obter direções
    origem = "Taubaté- SP, Brasil"
    destino = "R. Justino Cobra, 61 - Vila Ema, São José dos Campos - SP, Brasil"
    data_partida = "2024-01-15 08:00:00"

    # Obtendo coordenadas, distância e tempo da rota
    coordenadas_rota, distancia_rota, tempo_rota = obter_direcoes_com_coords(origem, destino)

    # Definindo coordenadas de Origem
    coordenadas_origem = (
        coordenadas_rota[0][0],
        coordenadas_rota[0][1]
    )

    # Definindo coordenadas de Destino
    coordenadas_destino = (
        coordenadas_rota[-1][0],
        coordenadas_rota[-1][1]
    )

    # Definindo o schema do DataFrame de Trânsito
    schema_transito = StructType([
        StructField("latitude", FloatType(), False),
        StructField("longitude", FloatType(), False),
        StructField("distancia", IntegerType(), False),
        StructField("tempo", IntegerType(), False)
    ])

    # Definindo o schema do DataFrame de Clima
    schema_clima = StructType([
        StructField("temperatura_origem", FloatType(), False),
        StructField("condicao_clima_origem", StringType(), False),
        StructField("temperatura_destino", FloatType(), False),
        StructField("condicao_clima_destino", StringType(), False)
    ])

    # Obtendo os dados de Trânsito
    dados_transito = [(coord[0], coord[1], distancia_rota, tempo_rota) for coord in coordenadas_rota]
    df_transito = spark.createDataFrame(dados_transito, schema=schema_transito)

    # Obtendo a Temperatura e Condição do Clima para a Origem e o Destino
    temperatura_origem, condicao_clima_origem = obter_previsao_tempo_origem(coordenadas_origem, data_partida)
    temperatura_destino, condicao_clima_destino = obter_previsao_tempo_destino(coordenadas_destino, data_partida, tempo_rota)

    # Obtendo os dados de Trânsito
    dados_clima = [(temperatura_origem, condicao_clima_origem, temperatura_destino, condicao_clima_destino)]
    df_clima = spark.createDataFrame(dados_clima, schema=schema_clima)

    # Mostrando os dados dos DataFrames de Trânsito e Clima
    df_transito.show(truncate=False)
    df_clima.show(truncate=False)

if __name__ == '__main__':
    teste_api()