"""
Locust load test for DocForge non-AI API endpoints and health checks.
Target SLA: /health p95 < 10ms, non-AI endpoints p95 < 200ms.
"""

from locust import HttpUser, task, between


class DocForgeUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task(5)
    def check_health(self) -> None:
        self.client.get("/health")

    @task(3)
    def list_repos(self) -> None:
        self.client.get("/api/repos", headers={"Authorization": "Bearer mock_token"})

    @task(2)
    def get_docs(self) -> None:
        self.client.get("/api/repos/1/docs", headers={"Authorization": "Bearer mock_token"})
