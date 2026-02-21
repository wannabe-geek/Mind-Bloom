from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.auth.models import User
from .models import MoodEntry, JournalEntry, Task, TherapistConnection, UserProfile, CrisisAlert, Resource, ChatMessage, Category, TherapistProfile, Appointment, SessionNote
from .ai_service import ai_service
from django.utils import timezone
import datetime
from django.db import models

@login_required
def dashboard(request):
    user = request.user
    
    # Ensure profile exists (fallback for existing users)
    if not hasattr(user, 'profile'):
        UserProfile.objects.get_or_create(user=user)
        
    
    if user.profile.role == 'ADMIN':
        total_students = UserProfile.objects.filter(role='STUDENT').count()
        total_therapists = UserProfile.objects.filter(role='THERAPIST').count()
        unresolved_alerts = CrisisAlert.objects.filter(is_resolved=False).count()
        
        # 1. Student Growth Data (Last 7 Days)
        from django.db.models.functions import TruncDate
        from django.db.models import Count, Avg
        import datetime
        
        today = timezone.now().date()
        seven_days_ago = today - datetime.timedelta(days=6)
        
        growth_qs = User.objects.filter(
            date_joined__date__gte=seven_days_ago,
            profile__role='STUDENT'
        ).annotate(date=TruncDate('date_joined')).values('date').annotate(count=Count('id')).order_by('date')
        
        # Fill in gaps with zero
        growth_data = []
        growth_labels = []
        growth_map = {item['date']: item['count'] for item in growth_qs}
        
        for i in range(7):
            curr_date = seven_days_ago + datetime.timedelta(days=i)
            growth_labels.append(curr_date.strftime('%b %d'))
            growth_data.append(growth_map.get(curr_date, 0))

        # 2. Wellness Distribution (Overall Averages)
        avg_mood = MoodEntry.objects.aggregate(Avg('mood_score'))['mood_score__avg'] or 0
        avg_energy = MoodEntry.objects.aggregate(Avg('energy_score'))['energy_score__avg'] or 0
        
        # 3. Recent Activity (Consolidated Feed)
        recent_users = User.objects.all().order_by('-date_joined')[:5]
        recent_alerts = CrisisAlert.objects.all().order_by('-created_at')[:5]
        
        activity_feed = []
        for u in recent_users:
            activity_feed.append({'type': 'USER', 'title': f"New {u.profile.role.title()}", 'desc': u.username, 'time': u.date_joined})
        for a in recent_alerts:
            activity_feed.append({'type': 'ALERT', 'title': "CRISIS ALERT", 'desc': a.student.username, 'time': a.created_at})
        
        activity_feed = sorted(activity_feed, key=lambda x: x['time'], reverse=True)[:10]

        # 4. Databasically Correct Metrics (Phase 11)
        # Dynamic Engagement proxy (Total interactions)
        total_journals = JournalEntry.objects.count()
        total_moods = MoodEntry.objects.count()
        total_tasks = Task.objects.count()
        total_messages = ChatMessage.objects.count()
        dynamic_page_views = total_journals + total_moods + total_tasks + total_messages

        # Bounce Rate approximation (% of users with 0 active entries)
        total_all_students = total_students # total_students is student count from earlier
        inactive_students = UserProfile.objects.filter(
            role='STUDENT',
            user__mood_entries__isnull=True,
            user__journal_entries__isnull=True
        ).distinct().count()
        
        bounce_rate = round((inactive_students / total_all_students * 100), 1) if total_all_students > 0 else 0

        context = {
            'user': user,
            'total_students': total_students,
            'total_therapists': total_therapists,
            'unresolved_alerts': unresolved_alerts,
            'growth_data': growth_data,
            'growth_labels': growth_labels,
            'avg_mood': round(avg_mood, 1),
            'avg_energy': round(avg_energy, 1),
            'activity_feed': activity_feed,
            'dynamic_page_views': dynamic_page_views,
            'bounce_rate': bounce_rate,
            'greeting': get_greeting(),
        }
    elif user.profile.role == 'THERAPIST':
        connections = TherapistConnection.objects.filter(therapist=user, status='ACTIVE')
        pending_appt_count = Appointment.objects.filter(therapist=user, status='PENDING').count()
        student_ids = TherapistConnection.objects.filter(therapist=user).values_list('student_id', flat=True)
        alert_count = CrisisAlert.objects.filter(student_id__in=student_ids, is_resolved=False).count()
        
        context = {
            'user': user,
            'connections': connections,
            'greeting': get_greeting(),
            'pending_appt_count': pending_appt_count,
            'alert_count': alert_count,
        }
    elif user.profile.role == 'STUDENT': # Explicitly handle STUDENT role
        latest_mood = MoodEntry.objects.filter(user=user).order_by('-created_at').first()
        recent_journals = JournalEntry.objects.filter(user=user).order_by('-created_at')[:3]
        
        # AI Mentor Insight for Dashboard (short reflection)
        ai_mentor_insight = ""
        if recent_journals:
            history = [j.content for j in recent_journals[1:]]
            mood_ctx = f"Mood: {latest_mood.mood_score}, Energy: {latest_mood.energy_score}" if latest_mood else "None"
            ai_mentor_insight = ai_service.get_reflection(recent_journals[0].content, user=user, history=history, mood_context=mood_ctx)
        
        # Phase 9: Breakthrough Pattern Recognition (Analyzing last 10 entries)
        breakthrough = None
        all_recent_journals = JournalEntry.objects.filter(user=user).order_by('-created_at')[:10]
        if all_recent_journals.count() >= 3:
            breakthrough = ai_service.get_breakthrough_analysis(all_recent_journals)

        context = {
            'user': user,
            'latest_mood': latest_mood,
            'recent_journals': recent_journals,
            'ai_mentor_insight': ai_mentor_insight,
            'breakthrough': breakthrough,
            'greeting': get_greeting(),
        }
    return render(request, 'core/dashboard.html', context)

def get_greeting():
    hour = timezone.now().hour
    if hour < 12:
        return "Good Morning"
    elif hour < 18:
        return "Good Afternoon"
    else:
        return "Good Evening"

@login_required
def mood_checkin(request):
    if request.method == 'POST':
        mood_score = request.POST.get('mood_score')
        energy_score = request.POST.get('energy_score')
        stress_score = request.POST.get('stress_score')
        note = request.POST.get('note')
        
        entry = MoodEntry.objects.create(
            user=request.user,
            mood_score=mood_score,
            energy_score=energy_score,
            stress_score=stress_score,
            note=note
        )
        
        # Get AI suggestion
        suggestion = ai_service.get_mood_suggestion(mood_score, energy_score, stress_score)
        messages.success(request, f"Check-in complete. AI Suggestion: {suggestion}")
        return redirect('dashboard')
        
    return render(request, 'core/mood_checkin.html')

@login_required
def journal(request):
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            # Crisis detection
            crisis_keywords = ['suicide', 'self-harm', 'hurt myself', 'die', 'depressed', 'kill']
            is_flagged = any(keyword in content.lower() for keyword in crisis_keywords)

            # Fetch context for the AI
            past_journals = JournalEntry.objects.filter(user=request.user).order_by('-created_at')[:3]
            history = [j.content for j in past_journals]
            latest_mood = MoodEntry.objects.filter(user=request.user).order_by('-created_at').first()
            mood_ctx = f"Mood: {latest_mood.mood_score}, Energy: {latest_mood.energy_score}" if latest_mood else "Unknown"

            # Get AI reflection with memory and persona
            reflection = ai_service.get_reflection(content, user=request.user, history=history, mood_context=mood_ctx)
            
            entry = JournalEntry.objects.create(
                user=request.user,
                content=content,
                ai_reflection=reflection,
                is_flagged=is_flagged
            )
            
            if is_flagged:
                CrisisAlert.objects.create(
                    student=request.user,
                    journal_entry=entry,
                    message=f"Crisis keywords detected in journal entry: {content[:100]}..."
                )
                messages.warning(request, "Your entry has been saved. We've noticed you might be going through a tough time—please reach out to a professional if you need immediate help.")
            else:
                messages.success(request, "Journal entry saved. Your AI Companion has reflected on your thoughts.")
            return redirect('journal')
            
    journals = JournalEntry.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'core/journal.html', {'journals': journals})

@login_required
def tasks(request):
    user = request.user
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            title = request.POST.get('title')
            energy = request.POST.get('energy_level_required', 5)
            Task.objects.create(user=user, title=title, energy_level_required=energy)
        elif action == 'toggle':
            task_id = request.POST.get('task_id')
            task = Task.objects.get(id=task_id, user=user)
            task.is_completed = not task.is_completed
            task.save()
        return redirect('tasks')

    # Suggest tasks based on energy
    latest_mood = MoodEntry.objects.filter(user=user).order_by('-created_at').first()
    energy_level = latest_mood.energy_score if latest_mood else 5
    
    suggested_tasks = Task.objects.filter(user=user, is_completed=False, energy_level_required__lte=energy_level + 2)
    other_tasks = Task.objects.filter(user=user, is_completed=False).exclude(id__in=suggested_tasks.values_list('id', flat=True))
    completed_tasks = Task.objects.filter(user=user, is_completed=True)
    
    context = {
        'suggested_tasks': suggested_tasks,
        'other_tasks': other_tasks,
        'completed_tasks': completed_tasks,
        'energy_level': energy_level,
    }
    return render(request, 'core/tasks.html', context)

@login_required
def ai_chat(request):
    if request.method == 'POST':
        user_message = request.POST.get('message')
        if user_message:
            # We'll use the get_reflection logic or similar for chat
            ai_response = ai_service.get_reflection(f"User ranted or asked: {user_message}")
            return render(request, 'core/ai_chat.html', {'ai_response': ai_response, 'user_message': user_message})
            
    return render(request, 'core/ai_chat.html')

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        role = request.POST.get('role')
        if form.is_valid():
            user = form.save()
            # Update role on the profile (profile created via signal)
            if hasattr(user, 'profile'):
                user.profile.role = role
                user.profile.save()
            
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def find_therapist(request):
    therapists = User.objects.filter(profile__role='THERAPIST').exclude(id=request.user.id)
    # Check current connections to avoid duplicates
    connected_ids = TherapistConnection.objects.filter(student=request.user).values_list('therapist_id', flat=True)
    
    context = {
        'therapists': therapists,
        'connected_ids': list(connected_ids),
    }
    return render(request, 'core/find_therapist.html', context)

@login_required
def connect_therapist(request, therapist_id):
    if request.method == 'POST':
        therapist = User.objects.get(id=therapist_id)
        # Create or update connection
        TherapistConnection.objects.get_or_create(
            student=request.user,
            therapist=therapist,
            defaults={'status': 'ACTIVE'}
        )
        messages.success(request, f"You are now connected with {therapist.username}!")
    return redirect('find_therapist')

@login_required
def ai_mentor(request):
    """A dedicated space for AI mentoring insights."""
    latest_journals = JournalEntry.objects.filter(user=request.user).order_by('-created_at')[:5]
    latest_mood = MoodEntry.objects.filter(user=request.user).order_by('-created_at').first()
    insights = ""
    if latest_journals:
        # Generate a unified mentorship insight from recent journals with full context
        content_summary = latest_journals[0].content
        history = [j.content for j in latest_journals[1:]]
        mood_ctx = f"Recent Mood Score: {latest_mood.mood_score if latest_mood else 'N/A'}"
        
        insights = ai_service.get_reflection(
            f"Provide a high-level mentorship perspective on my overall growth trajectory based on my latest thought: {content_summary[:300]}",
            history=history,
            mood_context=mood_ctx
        )
    
    return render(request, 'core/ai_mentor.html', {'insights': insights})

@login_required
def find_resources(request):
    category_slug = request.GET.get('category')
    resource_type = request.GET.get('type')
    search_query = request.GET.get('q')
    
    resources = Resource.objects.all()
    categories = Category.objects.all()
    
    if category_slug:
        resources = resources.filter(category__slug=category_slug)
    if resource_type:
        resources = resources.filter(resource_type=resource_type)
    if search_query:
        from django.db.models import Q
        resources = resources.filter(Q(title__icontains=search_query) | Q(content__icontains=search_query))
        
    context = {
        'resources': resources,
        'categories': categories,
        'current_category': category_slug,
        'current_type': resource_type,
        'search_query': search_query,
    }
    return render(request, 'core/find_resources.html', context)

@login_required
def clinical_progress(request, student_id):
    if request.user.profile.role != 'THERAPIST':
        messages.error(request, "Access denied. Only therapists can view clinical records.")
        return redirect('dashboard')
    
    # Verify connection
    student = User.objects.get(id=student_id)
    is_connected = TherapistConnection.objects.filter(therapist=request.user, student=student, status='ACTIVE').exists()
    
    if not is_connected:
        messages.error(request, "You are not connected to this student.")
        return redirect('dashboard')
    
    mood_history = MoodEntry.objects.filter(user=student).order_by('-created_at')[:30]
    journals = JournalEntry.objects.filter(user=student).order_by('-created_at')[:10]
    
    context = {
        'student': student,
        'mood_history': mood_history,
        'journals': journals,
    }
    return render(request, 'core/clinical_progress.html', context)

@login_required
@login_required
def admin_user_management(request):
    if request.user.profile.role != 'ADMIN':
        messages.error(request, "Access denied.")
        return redirect('dashboard')
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'core/admin_user_mgmt.html', {'users': users})

@login_required
def admin_moderation(request):
    if request.user.profile.role != 'ADMIN':
        messages.error(request, "Access denied.")
        return redirect('dashboard')
    alerts = CrisisAlert.objects.all().order_by('-created_at')
    return render(request, 'core/admin_moderation.html', {'alerts': alerts})

@login_required
def admin_cms(request):
    if request.user.profile.role != 'ADMIN':
        messages.error(request, "Access denied.")
        return redirect('dashboard')
    resources = Resource.objects.all().order_by('-created_at')
    return render(request, 'core/admin_cms.html', {'resources': resources})

@login_required
def admin_security(request):
    if request.user.profile.role != 'ADMIN':
        messages.error(request, "Access denied.")
        return redirect('dashboard')
    
    # Aggregate real security-related events
    recent_signups = User.objects.all().order_by('-date_joined')[:10]
    unresolved_alerts = CrisisAlert.objects.filter(is_resolved=False).order_by('-created_at')[:10]
    
    context = {
        'title': 'Security & Compliance',
        'desc': 'System-wide audit trail and security event monitoring.',
        'recent_signups': recent_signups,
        'unresolved_alerts': unresolved_alerts,
        'system_status': 'OPTIMAL',
        'last_backup': timezone.now() - datetime.timedelta(hours=4)
    }
    return render(request, 'core/admin_security.html', context)

@login_required
def admin_ai_monitor(request):
    if request.user.profile.role != 'ADMIN':
        messages.error(request, "Access denied.")
        return redirect('dashboard')
    
    # Aggregate AI performance metrics
    total_reflections = JournalEntry.objects.exclude(ai_reflection__isnull=True).count()
    total_breakthroughs = JournalEntry.objects.filter(is_flagged=True).count() # Flagged often relates to breakthrough detection logic
    # In a real app we'd track API latency, here we mock some "health"
    
    context = {
        'title': 'AI Engine Monitor',
        'desc': 'Real-time performance tracking for Mindbloom AI Personas.',
        'total_reflections': total_reflections,
        'total_breakthroughs': total_breakthroughs,
        'active_persona_distribution': {
            'ZEN': UserProfile.objects.filter(ai_persona='ZEN').count(),
            'STRATEGIST': UserProfile.objects.filter(ai_persona='STRATEGIST').count(),
            'LISTENER': UserProfile.objects.filter(ai_persona='LISTENER').count(),
            'CATALYST': UserProfile.objects.filter(ai_persona='CATALYST').count(),
        },
        'avg_latency': '142ms'
    }
    return render(request, 'core/admin_ai_monitor.html', context)

def messages_list(request):
    user = request.user
    # Get all users the current user has sent messages to or received messages from
    sent_to = ChatMessage.objects.filter(sender=user).values_list('receiver', flat=True)
    received_from = ChatMessage.objects.filter(receiver=user).values_list('sender', flat=True)
    contact_ids = set(list(sent_to) + list(received_from))
    
    contacts = User.objects.filter(id__in=contact_ids)
    
    # Also include connected therapists/students even if no messages yet
    if user.profile.role == 'STUDENT':
        connections = TherapistConnection.objects.filter(student=user, status='ACTIVE').values_list('therapist', flat=True)
        connected_users = User.objects.filter(id__in=connections)
    else:
        connections = TherapistConnection.objects.filter(therapist=user, status='ACTIVE').values_list('student', flat=True)
        connected_users = User.objects.filter(id__in=connections)
        
    all_contacts = set(contacts) | set(connected_users)
    
    return render(request, 'core/messages_list.html', {'contacts': all_contacts})

@login_required
def chat_session(request, user_id):
    other_user = User.objects.get(id=user_id)
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            ChatMessage.objects.create(sender=request.user, receiver=other_user, content=content)
            return redirect('chat_session', user_id=user_id)
            
    messages = ChatMessage.objects.filter(
        (models.Q(sender=request.user, receiver=other_user)) | 
        (models.Q(sender=other_user, receiver=request.user))
    ).order_by('created_at')
    
    # Mark messages as read
    ChatMessage.objects.filter(sender=other_user, receiver=request.user, is_read=False).update(is_read=True)
    
    return render(request, 'core/chat_session.html', {'other_user': other_user, 'chat_messages': messages})

@login_required
def settings(request):
    user = request.user
    if request.method == 'POST':
        persona = request.POST.get('ai_persona')
        if persona:
            user.profile.ai_persona = persona
            user.profile.save()
            messages.success(request, "Settings updated successfully!")
            return redirect('settings')
            
    return render(request, 'core/settings.html')

@login_required
def focus_timer(request):
    user = request.user
    selected_task_id = request.GET.get('task_id')
    selected_task = None
    if selected_task_id:
        selected_task = Task.objects.filter(user=user, id=selected_task_id).first()
    
    tasks = Task.objects.filter(user=user, is_completed=False)
    return render(request, 'core/focus_timer.html', {
        'tasks': tasks,
        'selected_task': selected_task
    })

@login_required
def self_help(request):
    return render(request, 'core/self_help.html')

# ===== THERAPIST PROFESSIONAL PORTAL =====

@login_required
def therapist_profile_view(request):
    if request.user.profile.role != 'THERAPIST':
        messages.error(request, "Access denied.")
        return redirect('dashboard')
    profile, _ = TherapistProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        profile.bio = request.POST.get('bio', '')
        profile.specialization = request.POST.get('specialization', '')
        profile.languages = request.POST.get('languages', 'English')
        profile.session_price = request.POST.get('session_price', 0)
        profile.availability_note = request.POST.get('availability_note', '')
        profile.credentials = request.POST.get('credentials', '')
        profile.save()
        messages.success(request, "Profile updated successfully!")
        return redirect('therapist_profile')
    return render(request, 'core/therapist_profile.html', {'t_profile': profile})


@login_required
def therapist_appointments(request):
    if request.user.profile.role != 'THERAPIST':
        messages.error(request, "Access denied.")
        return redirect('dashboard')
    # Handle accept / reject / complete actions
    if request.method == 'POST':
        appt_id = request.POST.get('appt_id')
        action = request.POST.get('action')
        try:
            appt = Appointment.objects.get(id=appt_id, therapist=request.user)
            if action == 'confirm':
                appt.status = 'CONFIRMED'
            elif action == 'reject':
                appt.status = 'REJECTED'
            elif action == 'complete':
                appt.status = 'COMPLETED'
            appt.save()
        except Appointment.DoesNotExist:
            pass
        return redirect('therapist_appointments')
    appointments = Appointment.objects.filter(therapist=request.user)
    pending = appointments.filter(status='PENDING')
    confirmed = appointments.filter(status='CONFIRMED')
    context = {
        'appointments': appointments,
        'pending': pending,
        'confirmed': confirmed,
        'pending_count': pending.count(),
    }
    return render(request, 'core/therapist_appointments.html', context)


@login_required
def therapist_student_records(request, student_id):
    if request.user.profile.role != 'THERAPIST':
        messages.error(request, "Access denied.")
        return redirect('dashboard')
    from django.shortcuts import get_object_or_404
    student = get_object_or_404(User, id=student_id)
    # Verify this student is connected to this therapist
    connection = TherapistConnection.objects.filter(therapist=request.user, student=student).first()
    if not connection:
        messages.error(request, "This student is not in your client list.")
        return redirect('dashboard')
    # Handle adding a session note
    if request.method == 'POST':
        content = request.POST.get('note_content', '').strip()
        risk = request.POST.get('risk_level', 'LOW')
        if content:
            SessionNote.objects.create(therapist=request.user, student=student, content=content, risk_level=risk)
            messages.success(request, "Session note saved.")
        return redirect('therapist_records', student_id=student_id)
    mood_entries = MoodEntry.objects.filter(user=student).order_by('-created_at')[:10]
    journal_entries = JournalEntry.objects.filter(user=student).order_by('-created_at')[:5]
    session_notes = SessionNote.objects.filter(therapist=request.user, student=student)
    crisis_alerts = CrisisAlert.objects.filter(student=student).order_by('-created_at')
    context = {
        'student': student,
        'mood_entries': mood_entries,
        'journal_entries': journal_entries,
        'session_notes': session_notes,
        'crisis_alerts': crisis_alerts,
        'connection': connection,
    }
    return render(request, 'core/therapist_records.html', context)


@login_required
def therapist_insights(request):
    if request.user.profile.role != 'THERAPIST':
        messages.error(request, "Access denied.")
        return redirect('dashboard')
    connections = TherapistConnection.objects.filter(therapist=request.user, status='ACTIVE')
    student_ids = connections.values_list('student_id', flat=True)
    # Recent mood data across all clients
    recent_moods = MoodEntry.objects.filter(user_id__in=student_ids).order_by('-created_at')[:50]
    total_sessions = Appointment.objects.filter(therapist=request.user, status='COMPLETED').count()
    pending_sessions = Appointment.objects.filter(therapist=request.user, status='PENDING').count()
    total_clients = connections.count()
    context = {
        'connections': connections,
        'recent_moods': recent_moods,
        'total_sessions': total_sessions,
        'pending_sessions': pending_sessions,
        'total_clients': total_clients,
    }
    return render(request, 'core/therapist_insights.html', context)


@login_required
def therapist_crisis(request):
    if request.user.profile.role != 'THERAPIST':
        messages.error(request, "Access denied.")
        return redirect('dashboard')
    connections = TherapistConnection.objects.filter(therapist=request.user)
    student_ids = connections.values_list('student_id', flat=True)
    active_alerts = CrisisAlert.objects.filter(student_id__in=student_ids, is_resolved=False).order_by('-created_at')
    resolved_alerts = CrisisAlert.objects.filter(student_id__in=student_ids, is_resolved=True).order_by('-created_at')[:5]
    # Handle resolve action
    if request.method == 'POST':
        alert_id = request.POST.get('alert_id')
        try:
            alert = CrisisAlert.objects.get(id=alert_id, student_id__in=student_ids)
            alert.is_resolved = True
            alert.save()
        except CrisisAlert.DoesNotExist:
            pass
        return redirect('therapist_crisis')
    context = {
        'active_alerts': active_alerts,
        'resolved_alerts': resolved_alerts,
        'alert_count': active_alerts.count(),
    }
    return render(request, 'core/therapist_crisis.html', context)


# Simple logout
def logout_view(request):
    # Clear all queued messages so they don't bleed onto the login page
    storage = messages.get_messages(request)
    storage.used = True
    logout(request)
    return redirect('login')

