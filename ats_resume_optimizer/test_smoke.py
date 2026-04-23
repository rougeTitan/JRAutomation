import requests
import io

RESUME = """John Doe | john@email.com | linkedin.com/in/johndoe

SUMMARY
Data engineer with 4 years of experience building scalable ETL pipelines, data warehouses, and real-time streaming systems.

EXPERIENCE
Senior Data Engineer - Acme Corp (2021-Present)
- Designed and maintained Apache Spark pipelines processing 10TB/day
- Built REST APIs using Python FastAPI and deployed on AWS Lambda
- Managed PostgreSQL and Snowflake data warehouses
- Implemented CI/CD with GitHub Actions and Docker

SKILLS
Python, Apache Spark, SQL, AWS (S3, Lambda, Glue), Snowflake, PostgreSQL, FastAPI, Docker, Git
"""

JD = """
We are looking for a Senior Data Engineer with:
- 3+ years of experience with Python and SQL
- Experience with Apache Kafka, Apache Spark, or similar streaming tools
- Knowledge of cloud platforms: AWS, GCP, or Azure
- Experience with dbt, Airflow, or similar orchestration tools
- Strong understanding of data modeling and data warehousing concepts
- Experience with Snowflake or BigQuery
- Familiarity with Docker and Kubernetes
"""

r = requests.post(
    "http://localhost:8000/api/analyze",
    files={"resume": ("resume.txt", io.BytesIO(RESUME.encode()), "text/plain")},
    data={"job_description": JD},
)

d = r.json()
print(f"Status     : {r.status_code}")
print(f"Overall    : {d['overall_score']}%")
print(f"Keyword    : {d['keyword_score']}%")
print(f"Semantic   : {d['semantic_score']}%")
print(f"Verdict    : {d['verdict']}")
print(f"Matched ({len(d['matched_keywords'])}): {d['matched_keywords'][:8]}")
print(f"Missing ({len(d['missing_keywords'])}): {d['missing_keywords'][:8]}")
