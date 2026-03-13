from django.db import models


class AnalyticsSnapshot(models.Model):
    metric_name = models.CharField(max_length=100)
    metric_date = models.DateField()
    payload_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-metric_date", "metric_name"]
        unique_together = ("metric_name", "metric_date")

    def __str__(self):
        return f"{self.metric_name} @ {self.metric_date}"
