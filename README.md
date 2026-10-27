# End-to-End Train Data Engineering Pipeline
An end-to-end data engineering pipeline for processing train datasets from raw ingestion to analytics-ready data.

## Project Architecture
![Train Data Engineering Pipeline](diagrams/train_pipeline.png)


## Overview
This project ingests raw train schedule data, cleans and validates it, transforms it using Python, and loads it into a warehouse for analytics.

## Tech Stack
- Python, Pandas
- SQL
- ETL Pipeline
- Git & GitHub

## Project Workflow
1. Data Ingestion from CSV/API
2. Data Cleaning & Validation
3. Data Transformation
4. Data Loading into Database
5. Ready for Dashboarding

## How to Run
```bash
git clone https://github.com/Poojasutar040/End-to-End-Train-Data-Engineering-Pipeline.git
pip install -r requirements.txt
python main.py
