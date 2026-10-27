"""Test set for the Jira RAG evaluation harness.

Each Test is an informal, user-style description (deliberately *not* a copy of
the ground-truth ticket's summary, so retrieval has to work off overlapping
vocabulary rather than an exact string match) mapped to the Jira issue key(s)
in jira_fictitious_data.csv that should come back as relevant precedent.

`category` is the Jira project key, so the evaluation dashboard's per-category
breakdown lines up with the project boundaries in the CSV.
"""

from dataclasses import dataclass, field


@dataclass
class Test:
    query: str
    category: str
    expected_keys: list[str]
    expected_keywords: list[str] = field(default_factory=list)


TESTS = [
    Test(
        query="When a user's access token expires mid-session, our API gateway just throws a 401 instead of refreshing it automatically",
        category="PLAT",
        expected_keys=["PLAT-4521"],
        expected_keywords=["oauth2", "token", "refresh", "gateway"],
    ),
    Test(
        query="Our websocket pool servers keep leaking memory and we have to restart them every few hours to keep them alive",
        category="PLAT",
        expected_keys=["PLAT-4519"],
        expected_keywords=["memory leak", "websocket", "connection pool"],
    ),
    Test(
        query="We need our Postgres JDBC driver updated so we can use logical replication for a new CDC pipeline",
        category="PLAT",
        expected_keys=["PLAT-4515"],
        expected_keywords=["postgresql", "driver", "logical replication", "cdc"],
    ),
    Test(
        query="Add dark mode toggle to the notifications settings page",
        category="UXD",
        expected_keys=["UXD-2103", "UXD-2104", "UXD-2105"],
        expected_keywords=["dark mode", "design tokens", "component"],
    ),
    Test(
        query="Customers are seeing old profile info show up in search results even after they update their profile",
        category="CUST",
        expected_keys=["CUST-7832"],
        expected_keywords=["search", "stale", "elasticsearch", "profile"],
    ),
    Test(
        query="We need to add rate limiting on our public API so people can't hammer it with requests",
        category="PLAT",
        expected_keys=["PLAT-4510"],
        expected_keywords=["rate limiting", "public api"],
    ),
    Test(
        query="Move our user notification preference system over to an event-driven architecture using Kafka",
        category="CUST",
        expected_keys=["CUST-7820"],
        expected_keywords=["notification", "event-driven", "kafka"],
    ),
    Test(
        query="Users want to export the analytics dashboard as a PDF",
        category="RPT",
        expected_keys=["RPT-1205"],
        expected_keywords=["pdf", "export", "dashboard"],
    ),
    Test(
        query="The payment processing service went down in production, turned out a TLS cert expired without any alert firing",
        category="PLAT",
        expected_keys=["PLAT-4525", "PLAT-4526", "PLAT-4527"],
        expected_keywords=["payment", "certificate", "outage", "monitoring"],
    ),
    Test(
        query="The customer activity feed page is really slow to load, seems like a database query issue",
        category="CUST",
        expected_keys=["CUST-7815"],
        expected_keywords=["slow query", "activity feed", "performance"],
    ),
    Test(
        query="We need our email templates to support multiple languages, not just English",
        category="CUST",
        expected_keys=["CUST-7825"],
        expected_keywords=["multi-language", "email template", "i18n"],
    ),
    Test(
        query="We're seeing random 502 errors on the orders API endpoint and can't figure out why",
        category="PLAT",
        expected_keys=["PLAT-4518"],
        expected_keywords=["502", "orders", "endpoint"],
    ),
    Test(
        query="Enterprise customer wants single sign-on through Okta with automatic user provisioning",
        category="CUST",
        expected_keys=["CUST-7810", "CUST-7811", "CUST-7812"],
        expected_keywords=["sso", "okta", "saml", "provisioning"],
    ),
    Test(
        query="Add real-time change data capture for order events in the data pipeline",
        category="DATA",
        expected_keys=["DATA-3301"],
        expected_keywords=["cdc", "data pipeline", "order events", "real-time"],
    ),
    Test(
        query="We need a dashboard to monitor data quality issues across our pipelines",
        category="DATA",
        expected_keys=["DATA-3305"],
        expected_keywords=["data quality", "monitoring", "dashboard"],
    ),
    Test(
        query="Refactor our authentication middleware so it can support more than one auth strategy",
        category="PLAT",
        expected_keys=["PLAT-4508"],
        expected_keywords=["authentication", "middleware", "refactor"],
    ),
    Test(
        query="Push notifications aren't being delivered reliably on Android 14 devices",
        category="MOB",
        expected_keys=["MOB-892"],
        expected_keywords=["push notification", "android", "delivery"],
    ),
    Test(
        query="Set up new AWS infrastructure with Terraform for expanding into a new region, including VPC and EKS",
        category="INFRA",
        expected_keys=["INFRA-501", "INFRA-502", "INFRA-503"],
        expected_keywords=["terraform", "aws", "vpc", "eks"],
    ),
    Test(
        query="The mobile app crashes on iOS 17 whenever someone tries to scan a document with the camera",
        category="MOB",
        expected_keys=["MOB-888"],
        expected_keywords=["ios", "crash", "camera", "document"],
    ),
    Test(
        query="We need to let customers export all of their personal data for GDPR compliance",
        category="CUST",
        expected_keys=["CUST-7835"],
        expected_keywords=["gdpr", "data export", "compliance"],
    ),
    Test(
        query="Add Prometheus metrics and distributed tracing across all our microservices",
        category="INFRA",
        expected_keys=["INFRA-498", "INFRA-510"],
        expected_keywords=["prometheus", "metrics", "tracing", "microservices"],
    ),
    Test(
        query="Build a feature flags service so we can do gradual rollouts of new functionality",
        category="PLAT",
        expected_keys=["PLAT-4500"],
        expected_keywords=["feature flags", "gradual rollout"],
    ),
    Test(
        query="Our CI/CD pipeline is slow, can we optimize the Docker images to speed it up",
        category="INFRA",
        expected_keys=["INFRA-505"],
        expected_keywords=["docker", "ci/cd", "optimize"],
    ),
    Test(
        query="The sprint velocity report is showing the wrong story point totals",
        category="RPT",
        expected_keys=["RPT-1210"],
        expected_keywords=["sprint velocity", "story points", "report"],
    ),
    Test(
        query="Add end-to-end encryption for files that customers upload to us",
        category="CUST",
        expected_keys=["CUST-7850"],
        expected_keywords=["encryption", "file upload", "security"],
    ),
]
