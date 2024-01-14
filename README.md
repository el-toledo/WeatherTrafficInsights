# Weather Traffic Insights

## Visão Geral

O projeto WeatherTrafficInsights integra dados de clima e tráfego para fornecer insights para o planejamento de viagens. Ele utiliza as APIs do Google Maps e OpenWeatherMap para obter direções, detalhes de tráfego e previsões do tempo tanto para o local de partida quanto para o destino.

## Dependências

- `googlemaps`: Biblioteca cliente em Python para a API do Google Maps
- `requests`: Biblioteca HTTP para fazer requisições a APIs
- `googletrans`: API do Google Translate para tradução de idiomas
- `pyspark`: Biblioteca Apache Spark para processamento distribuído de dados
- `decouple`: Gerenciamento de configurações para separar chaves de API e informações sensíveis

## Utilização

1. **Configurar chaves de API:** Obtenha chaves de API para o Google Maps (`GMAPS_API_KEY`) e OpenWeatherMap (`OPENWEATHER_API_KEY`). Armazene-as em um arquivo `.env` usando o `decouple`.

   ```plaintext
   GMAPS_API_KEY=sua_chave_api_do_google_maps
   OPENWEATHER_API_KEY=sua_chave_api_do_openweather

## Funcionalidades

### 1. Obtenção de Direções

Utiliza a API do Google Maps para obter as coordenadas da rota, distância e tempo de viagem estimado entre a origem e o destino especificados.

### 2. Previsão do Tempo

Recupera previsões do tempo da API do OpenWeatherMap para os horários de partida e chegada. As descrições são traduzidas para o português usando o Google Translate.

### 3. Processamento de Dados com Spark

O script utiliza o Apache Spark para criar DataFrames para dados de tráfego e clima, facilitando análises e visualizações.

## Padrões de Branches e Commits

### Branches

1. **Branch Principal (`main`):**
   - A branch principal do repositório. Todas as alterações estáveis e de produção residem aqui.

2. **Branch de Desenvolvimento (`dev`):**
   - A branch de desenvolvimento, onde novas funcionalidades são integradas antes de serem mescladas na branch principal.

### Commits

Ao criar commits, siga o formato [Conventional Commits](https://www.conventionalcommits.org/) para manter mensagens de commit consistentes e informativas.

Exemplo de mensagens de commit:
- `feat: implementar nova funcionalidade`
- `fix: corrigir bug na autenticação`
- `chore: atualizar dependências`
- `test: adicionar testes de integração`
- `docs: atualizar README`


---