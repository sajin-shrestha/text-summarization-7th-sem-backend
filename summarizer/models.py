from django.db import models
from django.contrib.auth.models import User

class SummaryHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='summaries')
    input_text = models.TextField()
    summary_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Keep only the last 5 summaries for the user
        summaries = SummaryHistory.objects.filter(user=self.user).order_by('-created_at')
        if summaries.count() > 5:
            summaries[5:].delete()