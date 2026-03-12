# Vigil360 — KYC & Continuous Risk Screening

> **5th place out of 23 teams at InterIIT TechMeet 14.0, IIT Patna** 

The problem statement asked teams to build an end-to-end financial product on top of [Pathway](https://pathway.com/) capable of handling high-velocity streaming data. We built **Vigil360** - a KYC screener with continuous risk evaluation that combines live sanctions/adverse-media data with transaction-pattern matching to flag suspicious entities in real time with enriched context of the person from the KYC and online information seamlessly integrated into a compliance dashboard.

## What it does

- Ingests KYC form data and runs it through a multi-signal risk pipeline (sanctions lists, adverse media, transaction behavior)
- Assigns a **Risk Propensity Score (RPS)** using an ensemble of rule-based and ML models (CatBoost, logistic regression)
- Streams updates via Kafka + Pathway so risk scores update continuously — not just at onboarding
- Surfaces flags and explanations through a Next.js dashboard for compliance teams

## Architecture

![Vigil360 Architecture](https://raw.githubusercontent.com/Quantum-Codes/Pathway-InterIIT-14/refs/heads/main/architecture.png)

## Stack

- **Pipeline** — Pathway, Apache Kafka, PostgreSQL, Debezium, Docker, Pathway MCP Server
- **Backend** — FastAPI, SQLAlchemy
- **Frontend** — Next.js 15, React 19, TypeScript, Tailwind CSS
- **ML** — CatBoost, logistic regression ensemble, RAG (ChromaDB + Mistral)
- **Data sources** — OpenSanctions API, adverse media scraping with news source authenticity judging, OFAC lists

## Getting Started

```bash
git clone https://github.com/Quantum-Codes/Pathway-InterIIT-14.git
cd Pathway-InterIIT-14
```

Start the three components in order:

### 1. Backend
```bash
cd backend
# See backend/README.md
```

### 2. Pipeline
```bash
cd pipeline
# See pipeline/README.md — sets up Kafka, PostgreSQL, Pathway streams
```

### 3. Frontend
```bash
cd frontend
# See frontend/README.md
```
