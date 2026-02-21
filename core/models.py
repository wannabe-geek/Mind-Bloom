from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class MoodEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mood_entries')
    mood_score = models.IntegerField(default=5)  # 1-10
    energy_score = models.IntegerField(default=5)  # 1-10
    stress_score = models.IntegerField(default=5)  # 1-10
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username} - {self.created_at.date()} - Mood: {self.mood_score}"

class JournalEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='journal_entries')
    content = models.TextField()
    ai_reflection = models.TextField(blank=True, null=True)
    detected_emotion = models.CharField(max_length=100, blank=True, null=True)
    is_flagged = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username} - {self.created_at.date()} - {self.content[:30]}..."

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('STUDENT', 'Student'),
        ('THERAPIST', 'Therapist'),
        ('ADMIN', 'Admin'),
    ]
    PERSONA_CHOICES = [
        ('ZEN', 'Zen Guide (Mindfulness & Breath)'),
        ('STRATEGIST', 'Practical Strategist (Action & Goals)'),
        ('LISTENER', 'Empathetic Listener (Validation & Kindness)'),
        ('CATALYST', 'Growth Catalyst (Patterns & Reframing)'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='STUDENT')
    ai_persona = models.CharField(max_length=20, choices=PERSONA_CHOICES, default='ZEN')
    avatar_color = models.CharField(max_length=7, default='#769891')

    def get_initial(self):
        """Returns the first alphanumeric character of the username or '?'."""
        import re
        match = re.search(r'[a-zA-Z0-9]', self.user.username)
        return match.group(0).upper() if match else "?"

    def __str__(self):
        return f"{self.user.username} - {self.role}"

class TherapistConnection(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='therapist_connections')
    therapist = models.ForeignKey(User, on_delete=models.CASCADE, related_name='student_connections')
    status = models.CharField(max_length=20, default='ACTIVE')  # PENDING, ACTIVE, COMPLETED
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.username} connected to {self.therapist.username}"

from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()

class Task(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    energy_level_required = models.IntegerField(default=5)  # 1-10
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    deadline = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.title}"

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=50, default='📚')

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class Resource(models.Model):
    RESOURCE_TYPES = [
        ('ARTICLE', 'Article'),
        ('VIDEO', 'Video'),
        ('AUDIO', 'Meditation Audio'),
    ]
    title = models.CharField(max_length=255)
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPES)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='resources')
    content = models.TextField(blank=True, null=True)  # For articles
    media_url = models.URLField(blank=True, null=True)  # For videos/audios (e.g. YouTube, S3)
    thumbnail = models.ImageField(upload_to='resources/thumbnails/', blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title

class CrisisAlert(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='crisis_alerts')
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.SET_NULL, null=True, blank=True)
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"CRISIS: {self.student.username} - {self.created_at.date()}"

class ChatMessage(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"From {self.sender.username} to {self.receiver.username}"


class TherapistProfile(models.Model):
    """Extended professional profile for therapists."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='therapist_profile')
    bio = models.TextField(blank=True, default='')
    specialization = models.CharField(max_length=200, blank=True, default='General Counseling')
    languages = models.CharField(max_length=200, default='English')
    session_price = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    availability_note = models.TextField(blank=True, default='')
    credentials = models.TextField(blank=True, default='')

    def __str__(self):
        return f"TherapistProfile: {self.user.username}"


class Appointment(models.Model):
    """Scheduled session between a student and a therapist."""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('REJECTED', 'Rejected'),
        ('COMPLETED', 'Completed'),
        ('RESCHEDULED', 'Rescheduled'),
    ]
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments')
    therapist = models.ForeignKey(User, on_delete=models.CASCADE, related_name='therapist_appointments')
    scheduled_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-scheduled_at']

    def __str__(self):
        return f"Appt: {self.student.username} w/ {self.therapist.username} @ {self.scheduled_at}"


class SessionNote(models.Model):
    """Private clinical notes written by a therapist about a student."""
    RISK_CHOICES = [('LOW', 'Low'), ('MEDIUM', 'Medium'), ('HIGH', 'High')]
    therapist = models.ForeignKey(User, on_delete=models.CASCADE, related_name='session_notes')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_notes')
    content = models.TextField()
    risk_level = models.CharField(max_length=20, choices=RISK_CHOICES, default='LOW')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Note by {self.therapist.username} on {self.student.username} [{self.risk_level}]"
