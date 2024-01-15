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

## Configuração do Banco de Dados no RDS
1. **Criação do Banco de Dados:**
   - Utilize a versão gratuita do RDS para testar as funcionalidades.
   - Ao criar o banco, configure as regras de segurança para acesso público (apenas para fins de teste).

2. **Configuração das Regras de Entrada:**
   - Acesse o painel do RDS e vá para a aba "Segurança e Conexão".
   ![Imagem da aba Segurança e Conexão](/assets/sg-rds-seg-conn.png)

   - Abra as configurações do security group associado ao banco de dados como mostrado na imagem acima.

   - Em "Inbound rules", clique em "Edit inbound rules" e adicione uma nova regra.
   ![Imagem dos Securities Groups](/assets/sg-inbound-rules.png)

   - Selecione "Custom TCP" como tipo, insira a porta 3306 e defina a origem como "Anywhere-IPv4".
   ![Imagem da edição de regras de entrada](/assets/rds-inbound-rules-edit.png)

3. **Conexão ao MySQL Workbench:**
   - No MySQL Workbench, vá para `Database -> Manage Connections`.
   - Preencha as informações necessárias, como nome da conexão, método de conexão (Standard TCP/IP), hostname (endpoint do banco de dados), porta (3306), nome de usuário e senha. O endpoint e a porta se obtém na aba de "Segurança e Conexão", como mostrado na imagem abaixo.
    ![Imagem da aba Segurança e Conexão](/assets/rds-endpoint.png)

## Estrutura do Banco de Dados
### Tabela Pessoas
```sql
CREATE TABLE Pessoas (
    cod_pessoa INT PRIMARY KEY,
    nome VARCHAR(255),
    sexo VARCHAR(10),
    idade INT,
    veiculo_de_preferencia VARCHAR(50)
);
```

## Tabela Rotas

```sql
CREATE TABLE Rotas (
    cod_rota INT PRIMARY KEY,
    cod_pessoa INT,
    origem_rota VARCHAR(255),
    destino_rota VARCHAR(255),
    data_rota TIMESTAMP,
    finalidade_rota VARCHAR(255),
    FOREIGN KEY (cod_pessoa) REFERENCES Pessoas(cod_pessoa)
);
```

## Inserção de Dados de Exemplo
### Tabela Pessoas
```sql
INSERT INTO Pessoas (cod_pessoa, nome, sexo, idade, veiculo_de_preferencia) VALUES
(1, 'Maria Silva', 'Feminino', 30, 'Carro'),
(2, 'José Santos', 'Masculino', 25, 'Moto'),
...
(10, 'Gustavo Almeida', 'Masculino', 31, 'Carro');
```

### Tabela Rotas
```sql
INSERT INTO Rotas (cod_rota, cod_pessoa, origem_rota, destino_rota, data_rota, finalidade_rota) VALUES
(1, 1, 'Campinas - SP', 'São Paulo - SP', '2024-01-15 08:00:00', 'Trabalho'),
(2, 2, 'Belo Horizonte - MG', 'Rio de Janeiro - RJ', '2024-01-16 10:30:00', 'Estudo'),
...
(10, 10, 'Vitória - ES', 'Cuiabá - MT', '2024-01-24 10:00:00', 'Estudo');
```

## Configuração do Redshift
### 1. Criando um Namespace no Redshift Serverless

- Acesse o console do Redshift e crie um namespace para o seu ambiente, será preciso vincular a Role de acesso ao S3 na hora da criação do namespace.
- Certifique-se de configurar o acesso público (atenção: não recomendado para produção).

### 3. Configurando as Regras de Segurança

1. No console do Redshift, acesse o namespace criado e então o workgroup associado ao namespace.
2. Na aba "Network and Security," clique em "Security Group."
![Imagem da aba Network and Security](/assets/sg-redshift-net-sec.png)
3. Edite as regras de entrada, adicione uma nova regra com o Type como TCP custom, porta 5439, e Source, Anywhere-IPv4.
![Imagem da edição de regras de entrada](/assets/redshift-inbound-rules-edit.png)
4. Salve as alterações nas regras de segurança.

### 4. Acessando o Editor de Consultas

1. Retorne ao namespace criado.
2. Clique no botão "Query data" para acessar o editor de consultas do Redshift.
![Imagem do namespace para o Query data](/assets/redshift-query-data.png)

### 5. Crie a tabela no Redshift correspondente ao DataFrame df_weather_traffic
```sql
CREATE TABLE WeatherTraffic (
   cod_pessoa BIGINT,
   cod_rota BIGINT,
   nome VARCHAR(255),
   sexo VARCHAR(255),
   idade BIGINT,
   veiculo_de_preferencia VARCHAR(255),
   origem_rota VARCHAR(255),
   destino_rota VARCHAR(255),
   data_partida TIMESTAMP,
   finalidade_rota VARCHAR(255),
   origem_latitude FLOAT,
   origem_longitude FLOAT,
   destino_latitude FLOAT,
   destino_longitude FLOAT,
   distancia_rota FLOAT,
   tempo_rota INT,
   temperatura_origem FLOAT,
   condicao_clima_origem VARCHAR(255),
   temperatura_destino FLOAT,
   condicao_clima_destino VARCHAR(255)
);
```
### 6. Copie os dados do arquivo CSV no S3 para a tabela no Redshift

```sql
COPY WeatherTraffic
FROM 's3://weathertrafficinsights/weather/weather_traffic_data.csv'
IAM_ROLE 'arn:aws:iam::<account-id>:role/service-role/<role_name>'
CSV
IGNOREHEADER 1;
```

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