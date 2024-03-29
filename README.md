# Weather Traffic Insights

## Visão Geral

O projeto WeatherTrafficInsights integra dados de clima e tráfego para fornecer insights para o planejamento de viagens. Ele utiliza as APIs do Google Maps e OpenWeatherMap para obter direções, detalhes de tráfego e previsões do tempo tanto para o local de partida quanto para o destino.

## Arquitetura do Projeto
![Arquitetura do Projeto](/assets/WeatherTrafficInsights-arquitetura.svg)

A arquitetura de dados apresentada é simples, porém altamente eficiente e escalável. Ela é composta por Amazon RDS, AWS Glue, Amazon S3, Amazon Redshift e integração com o Power BI para análise e visualização de dados.

## Visão Geral da Arquitetura

1. **Amazon RDS (Relational Database Service):**
   - O Amazon RDS é utilizado como um banco de dados relacional gerenciado, proporcionando escalabilidade, alta disponibilidade e segurança para armazenamento de dados estruturados.

2. **AWS Glue:**
   - O AWS Glue é empregado para a integração e transformação de dados. Ele permite a descoberta automática de metadados, facilitando a construção de pipelines de dados eficientes. Com o AWS Glue, a preparação e limpeza de dados tornam-se automatizadas, acelerando o processo de análise.

3. **Amazon S3 (Simple Storage Service):**
   - O Amazon S3 é utilizado como um repositório de armazenamento de dados altamente escalável e durável. Ele atua como o ponto central para armazenar os dados transformados, facilitando a integração e compartilhamento de dados entre os diferentes componentes da arquitetura.

4. **Amazon Redshift:**
   - O Amazon Redshift é empregado como um data warehouse para análises de alto desempenho. Ele permite consultas rápidas e complexas em grandes conjuntos de dados, fornecendo insights valiosos para suportar decisões estratégicas.

5. **Power BI:**
   - O Power BI é utilizado para a visualização e análise de dados. Ele se integra de maneira eficiente com o Amazon Redshift, permitindo a criação de dashboards interativos e relatórios personalizados para melhor compreensão e comunicação dos dados.

## Vantagens da Arquitetura

1. **Escalabilidade:**
   - A arquitetura é altamente escalável, permitindo o processamento eficiente de grandes volumes de dados à medida que a demanda aumenta.

2. **Automatização:**
   - A utilização do AWS Glue automatiza tarefas de integração e transformação de dados, reduzindo o tempo e esforço necessário para preparar os dados para análise.

3. **Segurança:**
   - O Amazon RDS e o Amazon Redshift oferecem recursos avançados de segurança, garantindo a proteção dos dados armazenados e processados na arquitetura.

4. **Integração:**
   - A integração perfeita entre os serviços, como o Power BI e os armazenamentos S3 e Redshift, facilita a análise e visualização de dados, proporcionando uma experiência integrada para os usuários.

5. **Desempenho:**
   - O Amazon Redshift oferece consultas de alto desempenho, permitindo análises rápidas e eficientes, mesmo em grandes conjuntos de dados.

Esta arquitetura proporciona uma base sólida para a construção de soluções analíticas escaláveis e eficientes, auxiliando a extrair insights valiosos a partir de seus dados de maneira ágil e confiável.

## Integração Contínua/Entrega Contínua

Este repositório é configurado com CI/CD (Continuous Integration/Continuos Delivery) para automatizar a atualização do código que irá executar o AWS Glue Job diariamente às 00:00. Isso permite uma integração contínua, garantindo que as mudanças de código sejam testadas e implantadas automaticamente no ambiente do AWS Glue.

### Fluxo de Trabalho

O fluxo de trabalho é acionado automaticamente quando há um push para a branch `main`. O processo é dividido em dois jobs: `build` e `deploy`.

### Job de Build

O job de build é responsável por preparar o código para implantação. Ele realiza as seguintes etapas:

1. **Checkout do Código**: Usa o GitHub Actions para fazer o checkout do código no ambiente de execução.
2. **Configurar o Ambiente Python**: Usa a ação `actions/setup-python` para configurar a versão específica do Python.
3. **Persistir o Script Python**: Usa a ação `actions/upload-artifact` para persistir o script Python no diretório `src/`.

### Job de Deploy

O job de deploy é acionado após o job de build e é responsável por atualizar o código do AWS Glue Job. Ele realiza as seguintes etapas:

1. **Baixar o Script Python do Build**: Usa a ação `actions/download-artifact` para baixar o script Python persistido durante o job de build.
2. **Configurar Credenciais AWS**: Configura as credenciais AWS necessárias para acessar o S3 e atualizar o Glue Job (as credenciais foram armazenadas nos secrets do repositório).
3. **Copiar o Arquivo para o Bucket S3**: Usa o comando `aws s3 cp` para copiar o script Python atualizado para o bucket S3.
4. **Atualizar o Job Glue**: Usa o comando `aws glue update-job` para atualizar o Glue Job com o novo script Python.
5. **Remover Arquivo de Credenciais Armazenado**: Remove as credenciais AWS do ambiente de execução.

## Dependências

- `googlemaps`: Biblioteca cliente em Python para a API do Google Maps
- `googletrans`: API do Google Translate para tradução de idiomas
- `mysql.connector`: Biblioteca em Python para conectar e interagir com bancos de dados MySQL.
- `boto3`: SDK (Software Development Kit) da Amazon Web Services (AWS) para Python, permitindo interação com serviços da AWS, como armazenamento em nuvem, computação em nuvem e outros recursos.

## Utilização

1. **Configurar credenciais:** 
- Obtenha chaves de API para o Google Maps (`GMAPS_API_KEY`) e OpenWeatherMap (`OPENWEATHER_API_KEY`). 
- Coloque as juntos com as demais credenciais de acesso do banco no AWS Secrets Manager

   ```plaintext
   GMAPS_API_KEY=sua_chave_api_do_google_maps
   OPENWEATHER_API_KEY=sua_chave_api_do_openweather
   DATABASE_USER=usuario_do_banco_de_dados
   DATABASE_PASSWORD=senha_do_banco_de_dados
   DATABASE_HOST=host_do_banco_de_dados
   DATABASE_NAME=nome_do_banco_de_dados
   ```

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

## Modelagem do Banco de Dados
![Modelagem do Banco de Dados](/assets/modelagem-dados.png)

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
## Configuração do Glue
### 1. Instale as bibliotecas externas do script para o Glue Job

Execute o seguinte comando na sua máquina local para obter as bibliotecas externas do Glue:

```bash
pip install googletrans==4.0.0-rc1 googlemaps mysql.connector -t "/caminho/para/salvar/as/bibliotecas"
cd "/caminho/para/salvar/as/bibliotecas"
rm -rf "/caminho/para/salvar/as/bibliotecas/urllib3"
zip -r dependencies.zip .
```

`Obs: É necessário remover a pasta urllib3 antes de zipar as bibliotecas pois o boto3 será carregado manualmente pelo Job Parameter do Glue Job, se não remover o urllib3 retornará um erro.`

### 2. Faça o upload do arquivo zip para o S3

Carregue o arquivo zip gerado ("dependencies.zip") em um bucket do Amazon S3. Copie o URI do S3 do arquivo, pois será necessário posteriormente.

### 3. Configuração do Glue Job

- Acesse o console do AWS Glue.
- Crie um novo job ETL ou selecione um existente.

### 4. Configuração Avançada

- No detalhe do job, vá até o final da página e expanda as "Advanced Properties".

### 5. Configuração do Python Library Path

- No campo "Python library path" na seção de "Libraries", insira o URI do S3 do arquivo zip que você carregou no passo 2.
![Carregando bibliotecas externas no Glue Job](/assets/libraries-dependencies-glue.png)

### 6. Configuração do Job Parameters

- Crie um parâmetro de job com a chave --JOB_NAME e o valor WeatherTraffic.
- Crie um outro parâmetro de job com a chave --additional-python-modules e o valor boto3.
![Criando um parâmetro de job no Glue Job](/assets/job-parametes-glue.png)


### 7. Configuração da Role do IAM

Certifique-se de que a role do IAM associada ao Glue Job tenha as permissões adequadas:

- Acesso ao Amazon S3 para ler o arquivo zip e salvar a tabela final. Pode ser feito com a política criada pela AWS chamada ***AmazonS3FullAccess***.
- Acesso ao Amazon CloudWatch para enviar logs de informações e erros. Pode ser feito com a política criada pela AWS chamada ***CloudWatchFullAccess***.
- Acesso ao Secret do AWS Secrets Manager pela seguinte política:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "secretsmanager:GetSecretValue",
            "Resource": "arn:aws:secretsmanager:<region-name>:<account-id>:secret:<secret-name>"
        }
    ]
}
```
### 8. Configuração do Trigger do Job

- Vá na seção de Triggers dentro da seção "Data Integration and ETL".
- Adicione um trigger.
- Coloque o tipo do trigger para Schedule.
- Coloque a frequência para Daily, hora de início para 3 (00:00 no Brasil), e minuto da hora para 0.
![Adicionando Trigger diário ao Glue Job](/assets/trigger-glue-job.png)

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

### 5. Crie a tabela no Redshift correspondente ao arquivo CSV salvo no S3
```sql
CREATE TABLE WeatherTraffic (
   cod_pessoa BIGINT,
   cod_rota BIGINT,
   nome VARCHAR(255),
   sexo VARCHAR(10),
   idade BIGINT,
   veiculo_de_preferencia VARCHAR(50),
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
   condicao_clima_origem VARCHAR(50),
   temperatura_destino FLOAT,
   condicao_clima_destino VARCHAR(50)
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

## Visualização dos Dados

Abaixo é possível visualizar os dados integrados num relatório do PowerBI. Nele foram analisados os as métricas de Trânsito e de Clima.

![Relatório do PowerBI](/assets/relatorio-pwbi.png)

Acesse o relátorio [aqui](https://app.powerbi.com/links/xwKbI1VtUa?ctid=0bb39120-50db-4f9f-a488-fca5a4f342f4&pbi_source=linkShare).

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