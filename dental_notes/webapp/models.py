from django.db import models
from django.contrib.auth.models import User

class Note(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    transcription = models.TextField()
    summary = models.TextField(null=True, blank=True)
    language = models.CharField(max_length=10)
    recording_time = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.user.username}"

class AudioRecording(models.Model):
    note = models.OneToOneField(Note, on_delete=models.CASCADE, related_name='audio_recording')
    file_path = models.FileField(upload_to='recordings/')
    duration = models.IntegerField()  # Duration in seconds
    file_size = models.IntegerField()  # Size in bytes
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Recording for {self.note.title}"

class TeethDescription(models.Model):
    note = models.ForeignKey(Note, on_delete=models.CASCADE)
    tooth_number = models.IntegerField()
    tooth_name = models.CharField(max_length=100)
    description = models.TextField()

    class Meta:
        unique_together = ['note', 'tooth_number']

    def __str__(self):
        return f"Tooth {self.tooth_number} - {self.note.title}"
