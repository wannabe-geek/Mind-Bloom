from django.contrib import admin
from .models import MoodEntry, JournalEntry, UserProfile, Task, TherapistConnection, Category, Resource, CrisisAlert

admin.site.register(UserProfile)
admin.site.register(MoodEntry)
admin.site.register(JournalEntry)
admin.site.register(Task)
admin.site.register(TherapistConnection)
admin.site.register(Category)
admin.site.register(Resource)
admin.site.register(CrisisAlert)
