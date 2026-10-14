# Pipeline de Dados com IoT e Docker

Pipeline de dados que processa leituras de temperatura de dispositivos IoT, armazena em um banco **PostgreSQL** rodando no **Docker** e exibe os resultados em um **dashboard interativo (Streamlit)**.

Projeto da disciplina **Disruptive Architectures: IoT, Big Data e IA** (UniFECAF).

**Autor:** Gabriel Silva de Medeiros

## Tecnologias

|Tecnologia|Uso no projeto|
|-|-|
|Python 3|Script de ingestão e dashboard|
|pandas|Leitura, limpeza e transformação do CSV|
|SQLAlchemy + psycopg2|Conexão com o PostgreSQL|
|PostgreSQL 16 (Docker)|Armazenamento e views SQL|
|Docker / Docker Compose|Banco de dados em container|
|Streamlit + Plotly|Dashboard com gráficos interativos|
|Git / GitHub|Versionamento e entrega|

## Arquitetura

```
CSV (Kaggle) → src/ingest.py (pandas) → PostgreSQL (Docker) → Views SQL → src/dashboard.py (Streamlit)
```

## Estrutura do projeto

```
pipeline-iot/
├── data/                  # CSV do Kaggle (IOT-temp.csv)
├── docs/                  # Capturas de tela do dashboard
├── sql/01\_views.sql       # Views SQL
├── src/
│   ├── config.py          # Conexão com o banco
│   ├── ingest.py          # Ingestão: CSV → PostgreSQL
│   └── dashboard.py       # Dashboard Streamlit
├── docker-compose.yml     # PostgreSQL em container
├── requirements.txt
└── README.md
```

## Base de dados

**Temperature Readings: IoT Devices** (Kaggle):
https://www.kaggle.com/datasets/atulanandjha/temperature-readings-iot-devices

Colunas do CSV original e como são usadas no banco:

|CSV|Tabela `temperature\_readings`|Descrição|
|-|-|-|
|`id`|`log\_id` (chave primária)|Identificador único da leitura|
|`room\_id/id`|`room\_id`|Identificador da sala|
|`noted\_date`|`noted\_at`|Data e hora da leitura (`dd-mm-aaaa hh:mm`)|
|`temp`|`temperature`|Temperatura (°C)|
|`out/in`|`location`|`In` (sensor interno) ou `Out` (sensor externo)|

**Tratamento aplicado na ingestão:** conversão das datas para `timestamp`, remoção de linhas inválidas e remoção de leituras duplicadas (mesmo `log\_id`).

## Como executar

### Pré-requisitos

* [Python 3.9+](https://www.python.org/downloads/)
* [Docker Desktop](https://www.docker.com/products/docker-desktop/) (aberto e com o engine rodando)
* [Git](https://git-scm.com/downloads)

### 1\. Clonar o repositório

```bash
git clone URL\_DO\_SEU\_REPOSITORIO
cd pipeline-iot
```

### 2\. Baixar a base de dados

Baixe o CSV no Kaggle (link acima) e salve como `data/IOT-temp.csv`.

### 3\. Criar o ambiente virtual e instalar as dependências

```bash
python -m venv .venv
.venv\\Scripts\\activate          # Windows
# source .venv/bin/activate     # Linux / Mac
pip install -r requirements.txt
```

### 4\. Subir o PostgreSQL com Docker

```bash
docker compose up -d
docker ps                       # o container "postgres-iot" deve aparecer
```

Alternativa sem Compose:

```bash
docker run --name postgres-iot -e POSTGRES\_PASSWORD=postgres123 -e POSTGRES\_DB=iot\_db -p 5432:5432 -d postgres:16
```

### 5\. Executar a ingestão

```bash
python src/ingest.py
```

O script lê o CSV, limpa os dados, carrega a tabela `temperature\_readings` e cria as 3 views.

### 6\. Verificar os dados no PostgreSQL

```bash
docker exec -it postgres-iot psql -U postgres -d iot\_db -c "SELECT COUNT(\*) FROM temperature\_readings;"
docker exec -it postgres-iot psql -U postgres -d iot\_db -c "SELECT \* FROM avg\_temp\_por\_dispositivo;"
```

### 7\. Rodar o dashboard

```bash
streamlit run src/dashboard.py
```

Abra http://localhost:8501 no navegador.

### Encerrar

```bash
docker compose down        # para o container (mantém os dados)
docker compose down -v     # para e apaga os dados
```

> \*\*Credenciais:\*\* os valores padrão (usuário `postgres`, senha `postgres123`, banco `iot\_db`) servem apenas para uso local/didático. Podem ser alterados com as variáveis de ambiente `DB\_USER`, `DB\_PASSWORD`, `DB\_HOST`, `DB\_PORT` e `DB\_NAME`.

## Views SQL

Definidas em [`sql/01\_views.sql`](sql/01_views.sql).

### 1\. `avg\_temp\_por\_dispositivo`

Calcula a **temperatura média** e o **total de leituras** de cada dispositivo. Como o dataset tem uma única sala, cada dispositivo é representado pelo par sala + posição do sensor (`Room Admin - In` e `Room Admin - Out`). **Propósito:** comparar o comportamento do sensor interno com o externo.

### 2\. `leituras\_por\_hora`

Conta quantas leituras foram registradas em cada **hora do dia** (0 a 23). **Propósito:** verificar a distribuição do volume de dados ao longo do dia e identificar horários com maior ou menor coleta.

### 3\. `temp\_max\_min\_por\_dia`

Retorna a **temperatura máxima, mínima e média por dia**. **Propósito:** acompanhar a variação diária e identificar dias com picos ou amplitude térmica elevada.

## Capturas de tela do dashboard

**Visão geral e média de temperatura por dispositivo**
!\[Dashboard - visão geral e média por dispositivo](docs/dashboard-1.png)

**Leituras por hora do dia**
!\[Dashboard - leituras por hora](docs/dashboard-2.png)

**Temperaturas máximas e mínimas por dia**
!\[Dashboard - máximas e mínimas por dia](docs/dashboard-3.png)

## Resultados da ingestão

|Indicador|Valor|
|-|-|
|Linhas lidas do CSV|97.606|
|Linhas inválidas removidas|0|
|Linhas duplicadas removidas|1|
|Registros carregados no PostgreSQL|97.605|
|Período dos dados|28/07/2018 a 08/12/2018|
|Temperatura média geral|35,1 °C|

## Insights obtidos dos dados

> Os números de gráficos são aproximados; os valores exatos podem ser consultados nas views.

* **O ambiente externo é mais quente que o interno.** Média de 30,45 °C no sensor interno (`In`) contra 36,27 °C no externo (`Out`), uma diferença de 5,82 °C.
* **O volume de leituras varia ao longo do dia.** O pico ocorre às 14h (cerca de 7,2 mil leituras), seguido das 15h (cerca de 6 mil). Os menores volumes aparecem às 4h, 8h e 23h (entre 2,7 mil e 3 mil). Isso pode refletir a frequência de registro dos sensores ou maior atividade à tarde (hipótese a confirmar).
* **As temperaturas máximas subiram no segundo semestre.** De julho ao início de setembro ficaram entre cerca de 32 °C e 35 °C; em meados de setembro subiram rapidamente, chegando a cerca de 51 °C no fim do mês, ficaram entre aproximadamente 46 °C e 50 °C até novembro e recuaram para perto de 41 °C a 43 °C em dezembro.
* **A amplitude térmica diária aumentou.** As mínimas oscilaram mais (de cerca de 21 °C a 36 °C) e, em alguns dias de outubro, a diferença entre a máxima e a mínima do mesmo dia passou de 25 °C.
* **Qualidade dos dados.** Foi removida 1 leitura duplicada. Trechos retos no gráfico de máximas e mínimas sugerem períodos sem leituras, indicando possíveis lacunas na coleta.

### Sugestões de uso prático

* Alertas automáticos quando a temperatura ultrapassar limites definidos.
* Uso da diferença entre sensor interno e externo para avaliar isolamento e ajustar a climatização.
* Monitoramento dos sensores para detectar falhas de coleta e acionar manutenção preventiva.
* Aplicação em ambientes críticos (data centers, câmaras frias, estufas, armazéns).
* Evolução para coleta em tempo real (MQTT/Kafka), banco de séries temporais, nuvem e modelos de previsão e detecção de anomalias.

### Limitações

Como o dataset tem uma única sala, o "dispositivo" foi construído a partir da posição do sensor (interno e externo). A view de máximas e mínimas por dia combina os dois sensores; uma análise separada por sensor seria um próximo passo.

## Comandos Git utilizados

```bash
git config --global user.name "Seu Nome"
git config --global user.email "seu.email@exemplo.com"

git init
git add .
git commit -m "Projeto inicial: Pipeline de Dados IoT"
git branch -M main
git remote add origin URL\_DO\_SEU\_REPOSITORIO
git push -u origin main

# Atualizar o repositório local com as mudanças do remoto
git pull
```

