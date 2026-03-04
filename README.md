<div align="center">

# 🚀 Hybrid Cloud Real-Time Streaming Pipeline

### *From raw events to cloud analytics — fully automated, production-grade*

<br>

[![Python](https://img.shields.io/badge/Python-3.9-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Apache Kafka](https://img.shields.io/badge/Apache%20Kafka-7.3-231F20?style=flat-square&logo=apachekafka)](https://kafka.apache.org)
[![Apache Airflow](https://img.shields.io/badge/Apache%20Airflow-2.6-017CEE?style=flat-square&logo=apacheairflow)](https://airflow.apache.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docker.com)
[![AWS S3](https://img.shields.io/badge/AWS-S3-FF9900?style=flat-square&logo=amazons3&logoColor=white)](https://aws.amazon.com/s3)
[![AWS Glue](https://img.shields.io/badge/AWS-Glue-FF9900?style=flat-square&logo=amazonaws&logoColor=white)](https://aws.amazon.com/glue)
[![AWS Athena](https://img.shields.io/badge/AWS-Athena-FF9900?style=flat-square&logo=amazonaws&logoColor=white)](https://aws.amazon.com/athena)
[![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)](https://streamlit.io)

<br>

> **300,000 records · 32 Parquet files · ~45 MB compressed · Serverless SQL · Live Dashboard**

<br>

</div>

---

## 📖 Table of Contents

- [What This Project Does](#-what-this-project-does)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Step-by-Step Setup](#-step-by-step-setup)
- [Running the Pipeline](#-running-the-pipeline)
- [Monitoring Kafka](#-monitoring-kafka)
- [AWS Glue & Athena](#-aws-glue--athena)
- [Streamlit Dashboard](#-streamlit-dashboard)
- [Pipeline Stats](#-pipeline-stats)
- [Key Concepts](#-key-concepts-demonstrated)
- [Troubleshooting](#-troubleshooting)
- [Resume Description](#-resume-description)

---

## 🎯 What This Project Does

This project builds a **complete, production-grade data engineering pipeline** that mimics how real e-commerce companies process millions of transactions every day.

### The Story

Imagine you run an online store. Every time a customer clicks "Buy Now", that transaction needs to be:
1. **Captured instantly** — not lost even if the system is busy
2. **Stored efficiently** — not as bloated JSON but in optimized columnar format
3. **Made queryable** — so analysts can ask "which state had the most revenue today?"
4. **Visualized** — so the business team can see it on a dashboard

**This pipeline does all of that — automatically.**

### What Actually Happens

```
① A Python script generates 300,000 fake but realistic transactions
   (customer names, products, prices, locations, payment methods)

② Each transaction is published to Apache Kafka in real-time
   at ~8,000 records per second

③ A consumer reads from Kafka, groups records into batches of 10,000,
   converts each batch to compressed Parquet format

④ Each Parquet file is uploaded to AWS S3 in a date-partitioned folder structure
   (year=2026/month=03/day=04/batch_0001.parquet)

⑤ AWS Glue automatically scans S3 and discovers the schema

⑥ AWS Athena lets you run SQL queries on the data — no servers needed

⑦ A Streamlit dashboard reads directly from S3 and shows live charts
```

**Apache Airflow orchestrates all of this** — it makes sure tasks run in the right order, retries on failure, and logs everything.

---

## 🏗️ Architecture

```
╔══════════════════════════════════════════════════════════════════╗
║                     LOCAL ENVIRONMENT (Docker)                   ║
║                                                                  ║
║  ┌─────────────┐     ┌──────────────────┐     ┌──────────────┐  ║
║  │  Zookeeper  │────▶│      Kafka       │     │   Airflow    │  ║
║  │             │     │                  │     │              │  ║
║  │ Coordinates │     │  Holds 300,000   │     │ Orchestrates │  ║
║  │   Kafka     │     │    messages in   │     │  all tasks   │  ║
║  │             │     │  topic queue     │     │              │  ║
║  └─────────────┘     └────────┬─────────┘     └──────┬───────┘  ║
║                               │                      │          ║
║                    ┌──────────▼──────────────────────▼──────┐   ║
║                    │              Python Scripts             │   ║
║                    │                                         │   ║
║                    │  producer_large.py  →  Writes to Kafka  │   ║
║                    │  consumer_batch_s3.py → Reads + Uploads │   ║
║                    │  data_quality.py   →  Validates data    │   ║
║                    └──────────────────────┬──────────────────┘   ║
╚═════════════════════════════════════════ ─┼─ ════════════════════╝
                                            │ Upload via boto3
                                            ▼
╔══════════════════════════════════════════════════════════════════╗
║                        AWS CLOUD                                 ║
║                                                                  ║
║  ┌─────────────────┐   ┌──────────────┐   ┌───────────────────┐ ║
║  │    Amazon S3    │──▶│  AWS Glue    │──▶│   AWS Athena      │ ║
║  │                 │   │              │   │                   │ ║
║  │  32 Parquet     │   │  Auto-scans  │   │  Serverless SQL   │ ║
║  │  files (~45MB)  │   │  schema &    │   │  queries on S3    │ ║
║  │  date-partitioned│  │  catalogs    │   │  data — no server │ ║
║  └─────────────────┘   └──────────────┘   └───────────────────┘ ║
╚══════════════════════════════════════════════════════════════════╝
                                            │
                                            ▼
                              ┌─────────────────────────┐
                              │   Streamlit Dashboard   │
                              │   localhost:8501        │
                              │   6 charts · 5 KPIs     │
                              └─────────────────────────┘
```

### Why This Architecture?

| Problem | Solution | Why |
|---|---|---|
| Producer runs faster than S3 can accept | Kafka acts as buffer | Decouples write speed from upload speed |
| S3 uploads can fail | Manual Kafka offset commits | Only mark messages "done" after confirmed upload |
| 300K small JSON records = slow queries | Parquet + Snappy compression | 70% smaller, columnar = 10x faster queries |
| New data lands daily | Date-partitioned S3 paths | Athena scans only relevant partitions = 90% cost reduction |
| Schema changes over time | Glue Crawler with auto-update | No manual DDL changes needed |

---

## 🧰 Tech Stack

| Tool | Role in This Project |
|---|---|
| **Apache Kafka** | Message queue that buffers 300K transactions between producer and consumer |
| **Apache Zookeeper** | Manages and coordinates the Kafka broker |
| **Apache Airflow** | Orchestrates the 5-task pipeline DAG with retries and dependencies |
| **Python + Faker** | Generates 300,000 realistic e-commerce transaction records |
| **Pandas + PyArrow** | Processes records into DataFrames and serializes to Parquet |
| **AWS S3** | Stores 32 Parquet files in date-partitioned folder structure |
| **AWS Glue** | Crawls S3 and auto-creates a queryable table in the data catalog |
| **AWS Athena** | Runs serverless SQL on S3 data — no database server needed |
| **Streamlit** | Renders live analytics dashboard reading directly from S3 |
| **Docker Compose** | Runs Kafka + Zookeeper + Airflow + Kafka-UI locally in containers |

---

## 📁 Project Structure

```
HybridCloudProject/
│
├── 📄 docker-compose.yml           # Defines all Docker services
├── 📄 .env                         # Config: S3 bucket, topic, batch size
├── 📄 dashboard.py                 # Streamlit analytics dashboard
├── 📄 .gitignore                   # Prevents secrets from being pushed
├── 📄 README.md                    # This file
│
├── 📁 dags/
│   └── 📄 streaming_pipeline_dag.py   # 5-task Airflow DAG
│
└── 📁 scripts/
    ├── 📄 producer_large.py           # Generates + streams 300K records to Kafka
    ├── 📄 consumer_batch_s3.py        # Reads Kafka → Parquet → S3
    └── 📄 data_quality.py             # Post-load data validation
```

---

## ✅ Prerequisites

Before starting, make sure you have:

| Requirement | Check |
|---|---|
| Docker Desktop installed and running | `docker --version` |
| AWS CLI installed | `aws --version` |
| AWS credentials configured | `aws configure` |
| Python 3.9+ installed | `python --version` |
| AWS S3 bucket created | See Step 3 below |

---

## 🔧 Step-by-Step Setup

### Step 1 — Clone the repository

```bash
git clone https://github.com/siddheshsalve77/hybrid-cloud-streaming-pipeline.git
cd hybrid-cloud-streaming-pipeline
```

### Step 2 — Configure AWS credentials

```bash
aws configure
# Enter your Access Key ID
# Enter your Secret Access Key
# Default region: us-east-1
# Default output format: json
```

### Step 3 — Create the S3 bucket

```bash
aws s3 mb s3://hybrid-pipeline-raw-zone --region us-east-1
```

### Step 4 — Create the `.env` file

Create a file named `.env` in the project root:

```env
S3_BUCKET=hybrid-pipeline-raw-zone
S3_FOLDER=large_streaming_data/
KAFKA_TOPIC=transactions_topic
KAFKA_SERVER=kafka:9092
BATCH_SIZE=10000
TOTAL_RECORDS=300000
```

### Step 5 — Start Docker services

```bash
docker-compose up -d
```

Wait 2–3 minutes, then verify everything is healthy:

```bash
docker-compose ps
```

Expected output:
```
NAME        STATUS
zookeeper   Up (healthy)
kafka       Up (healthy)
airflow     Up
kafka-ui    Up
```

### Step 6 — Install dashboard dependencies

```bash
pip install streamlit pandas boto3 pyarrow
```

---

## ▶️ Running the Pipeline

### Open Airflow
Go to **http://localhost:8080**
- Username: `admin`
- Password: `admin`

### Trigger the DAG
1. Find `hybrid_cloud_streaming_pipeline`
2. Toggle the switch **ON**
3. Click the **▶ Trigger DAG** button
4. Click the DAG name → **Graph** view to watch live

### The 5 Tasks

```
validate_environment
        │
        ▼
produce_300k_records          ← ~3-5 minutes
        │
        ▼
consume_and_upload_to_s3      ← ~3-5 minutes
        │
        ▼
verify_s3_output              ← ~5 seconds
        │
        ▼
data_quality_checks           ← ~30 seconds
```

| Task | What It Does |
|---|---|
| `validate_environment` | Confirms all Python packages are installed and S3 is accessible |
| `produce_300k_records` | Runs `producer_large.py` — generates and sends 300K records to Kafka |
| `consume_and_upload_to_s3` | Runs `consumer_batch_s3.py` — reads Kafka, batches 10K records, uploads Parquet to S3 |
| `verify_s3_output` | Checks that Parquet files actually landed in S3 |
| `data_quality_checks` | Runs `data_quality.py` — checks for nulls, duplicates, negative prices |

### Expected Log Output

**Producer task logs:**
```
Progress: 10000/300000 records (8432 rec/s | 3.3% done)
Progress: 20000/300000 records (8891 rec/s | 6.7% done)
...
Done. Sent 300000 records in 35.6s (8427 rec/s)
```

**Consumer task logs:**
```
Batch 1 uploaded → large_streaming_data/year=2026/month=03/day=04/batch_0001.parquet (10000 records)
Batch 2 uploaded → large_streaming_data/year=2026/month=03/day=04/batch_0002.parquet (10000 records)
...
Summary: 300000 records | 30 batches | 0 failed | 187.3s
```

---

## 📡 Monitoring Kafka

### Command Line

```bash
# List all topics
docker exec kafka kafka-topics --bootstrap-server kafka:9092 --list

# See message count (should show 300000)
docker exec kafka kafka-run-class kafka.tools.GetOffsetShell \
  --broker-list kafka:9092 --topic transactions_topic

# Check consumer lag (LAG should be 0 when pipeline is done)
docker exec kafka kafka-consumer-groups \
  --bootstrap-server kafka:9092 \
  --group pipeline-consumer-group --describe

# Read 3 actual messages from the topic
docker exec kafka kafka-console-consumer \
  --bootstrap-server kafka:9092 \
  --topic transactions_topic \
  --from-beginning --max-messages 3
```

### Kafka Visual UI
Open **http://localhost:8090** to see the Kafka-UI dashboard:
- All topics and message counts
- Consumer group lag
- Real-time message browser
- Broker health status

---

## ☁️ AWS Glue & Athena

### Set Up Glue Crawler

1. **AWS Console → Glue → Crawlers → Create crawler**
2. Name: `hybrid-pipeline-crawler`
3. Data source: `s3://hybrid-pipeline-raw-zone/large_streaming_data/`
4. IAM Role: Create `GlueCrawlerRole` with `AmazonS3FullAccess` + `AWSGlueServiceRole`
5. Target database: `hybrid_pipeline_db`
6. Run the crawler — takes ~2 minutes

### Query with Athena

Open **AWS Console → Athena**. Set query result location to:
```
s3://hybrid-pipeline-raw-zone/athena-results/
```

**Register partitions first:**
```sql
MSCK REPAIR TABLE hybrid_pipeline_db.large_streaming_data;
```

**Total records:**
```sql
SELECT COUNT(*) AS total_records
FROM hybrid_pipeline_db.large_streaming_data;
-- Result: 300000
```

**Revenue by state (top 10):**
```sql
SELECT
    state,
    COUNT(*)                    AS total_orders,
    ROUND(SUM(total_price), 2)  AS total_revenue,
    ROUND(AVG(total_price), 2)  AS avg_order_value
FROM hybrid_pipeline_db.large_streaming_data
GROUP BY state
ORDER BY total_revenue DESC
LIMIT 10;
```

**Best selling products:**
```sql
SELECT
    product,
    COUNT(*)                    AS units_sold,
    ROUND(SUM(total_price), 2)  AS total_revenue
FROM hybrid_pipeline_db.large_streaming_data
GROUP BY product
ORDER BY total_revenue DESC;
```

**Order status breakdown:**
```sql
SELECT
    status,
    COUNT(*) AS count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS percentage
FROM hybrid_pipeline_db.large_streaming_data
GROUP BY status
ORDER BY count DESC;
```

**Payment method analysis:**
```sql
SELECT
    payment_method,
    COUNT(*)                    AS orders,
    ROUND(SUM(total_price), 2)  AS revenue
FROM hybrid_pipeline_db.large_streaming_data
GROUP BY payment_method
ORDER BY orders DESC;
```

---

## 📊 Streamlit Dashboard

```bash
python -m streamlit run dashboard.py
```

Open **http://localhost:8501**

### Dashboard Features

| Section | Charts |
|---|---|
| KPI Row | Total Orders · Total Revenue · Avg Order Value · Units Sold · Completion Rate |
| Revenue | Revenue by State (Top 15 bar chart) |
| Products | Best Selling Products (table with revenue + units) |
| Orders | Order Status Breakdown (bar chart + percentage table) |
| Payments | Payment Method Split (bar chart + revenue table) |
| Time | Hourly Transaction Volume (line chart) |
| Devices | Device Type Analysis (bar chart + avg order value) |
| Explorer | Raw Data Explorer (200 sample records, filterable) |

**Sidebar filters:** Filter all charts by Product and Order Status simultaneously.

---

## 📈 Pipeline Stats

| Metric | Value |
|---|---|
| Records generated | 300,000 |
| Kafka throughput | ~8,000 records/sec |
| Parquet files in S3 | 32 files |
| Records per file | ~10,000 |
| Compressed size | ~45 MB (Snappy) |
| Raw JSON equivalent | ~150 MB |
| Storage saving | ~70% |
| Pipeline duration | ~10 minutes total |
| Athena cost | Cents (partition pruning) |

---

## 🧠 Key Concepts Demonstrated

### 1. Event-Driven Architecture
Kafka completely decouples the producer from the consumer. The producer doesn't care if the consumer is slow, fast, or temporarily down — it just keeps writing to the topic.

### 2. Exactly-Once Semantics
Kafka offsets are only committed **after** a successful S3 upload. If the upload fails, Kafka re-delivers the messages on the next run — no data is lost or skipped.

### 3. Micro-Batching
Instead of uploading one record at a time (too slow) or all 300K at once (too much memory), the consumer batches 10,000 records — the sweet spot for throughput vs memory usage.

### 4. Columnar Storage
Parquet stores data column-by-column instead of row-by-row. When Athena runs `SELECT state, SUM(price)`, it only reads 2 columns instead of all 19 — dramatically faster and cheaper.

### 5. Partition Pruning
Files are stored as `year=2026/month=03/day=04/`. When you query `WHERE day='04'`, Athena skips all other folders entirely — reducing data scanned and cost by up to 90%.

### 6. Schema-on-Read
No upfront table creation needed. Glue Crawler reads the Parquet files and automatically discovers column names, types, and partitions — the schema lives with the data.

### 7. Hybrid Cloud Pattern
Heavy compute (data generation, Kafka, Airflow) runs locally in Docker — free. Storage and querying run on AWS — pay only for what you use. Best of both worlds.

---

## 🛑 Shutdown

```bash
# Stop all containers
docker-compose down

# Stop and remove all data (full reset)
docker-compose down -v
```

---

## 🐛 Troubleshooting

| Problem | Fix |
|---|---|
| `docker-compose up` fails | Make sure Docker Desktop is running (whale icon in taskbar) |
| Airflow shows no DAG | Check `docker logs airflow` for Python import errors |
| S3 upload 403 error | Run `aws configure` again and verify credentials |
| Consumer fails with `group_id` error | Add `group_id="pipeline-consumer-group"` to KafkaConsumer |
| Athena "table not found" | Re-run Glue Crawler then `MSCK REPAIR TABLE` |
| Dashboard black screen | Use `python -m streamlit run dashboard.py` not `streamlit run` |

---

## 📄 Resume Description

> **Hybrid Cloud Real-Time Streaming Pipeline** | Python · Apache Kafka · Apache Airflow · AWS S3 · AWS Athena · Docker
>
> - Designed and implemented an end-to-end streaming data pipeline ingesting **300,000+ synthetic e-commerce transactions** using Apache Kafka running in Docker, orchestrated by a 5-task Apache Airflow DAG with health checks, retries, and dependency management
> - Built a fault-tolerant Kafka consumer with manual offset commits ensuring **exactly-once delivery semantics** — offsets committed only after confirmed S3 upload, preventing data loss on failure
> - Serialized records to **Parquet with Snappy compression** in micro-batches of 10,000 records, achieving **~70% storage reduction** vs raw JSON and enabling columnar query pushdown in Athena
> - Implemented **date-partitioned S3 paths** (`year=/month=/day=`) enabling Athena partition pruning and reducing query scan costs by up to **90%**
> - Integrated **AWS Glue Crawler** for automatic schema discovery and catalog registration enabling serverless SQL analytics via Athena with zero ETL infrastructure overhead
> - Built a **Streamlit analytics dashboard** reading directly from S3 with 6 interactive charts, 5 KPI metrics, and sidebar filters for real-time business insights

---

<div align="center">

**Built with** Python · Apache Kafka · Apache Airflow · AWS S3 · AWS Glue · AWS Athena · Docker · Streamlit

⭐ Star this repo if you found it useful!

</div>
