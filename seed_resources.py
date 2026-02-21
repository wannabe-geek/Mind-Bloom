import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MindBloomProject.settings')
django.setup()

from core.models import Category, Resource

def seed():
    # Categories
    cat_anxiety, _ = Category.objects.get_or_create(name='Anxiety & Stress', slug='anxiety-stress', icon='🌪️')
    cat_mindfulness, _ = Category.objects.get_or_create(name='Mindfulness', slug='mindfulness', icon='🧘')
    cat_productivity, _ = Category.objects.get_or_create(name='Focus & Productivity', slug='productivity', icon='🎯')
    
    # Resources
    Resource.objects.get_or_create(
        title='Understanding Anxiety',
        resource_type='ARTICLE',
        category=cat_anxiety,
        content='Anxiety is your body’s natural response to stress. It’s a feeling of fear or apprehension about what’s to come...',
        is_featured=True
    )
    
    Resource.objects.get_or_create(
        title='10 Minute Morning Meditation',
        resource_type='AUDIO',
        category=cat_mindfulness,
        media_url='https://www.youtube.com/watch?v=inpok4MKVLM',  # Example link
        content='A quick meditation to start your day with clarity and focus.'
    )
    
    Resource.objects.get_or_create(
        title='The Science of Focus',
        resource_type='VIDEO',
        category=cat_productivity,
        media_url='https://www.youtube.com/watch?v=Hu4Yvq-g7_Y',
        content='Learn how your brain handles focus and how to improve it.'
    )

    print("Seeding complete!")

if __name__ == '__main__':
    seed()
