import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fransick.settings')
django.setup()

from django.contrib.auth import get_user_model
from medecins.models import DoctorProfile, HealthVideo, VideoComment

User = get_user_model()

# Ensure we have doctor accounts
doc1, _ = User.objects.get_or_create(
    username="dr_wada",
    defaults={
        "first_name": "Wada",
        "last_name": "Sylvain",
        "email": "dr.wada@fransick.com",
        "role": "medecin"
    }
)
if doc1.role != 'medecin':
    doc1.role = 'medecin'
    doc1.save()

profile1, _ = DoctorProfile.objects.get_or_create(
    user=doc1,
    defaults={
        "speciality": "Cardiologue & Prévention",
        "years_of_experience": 12,
        "rating": 4.9,
        "about": "Spécialiste de la santé cardiovasculaire et de l'hypertension artérielle."
    }
)

doc2, _ = User.objects.get_or_create(
    username="dr_sophie",
    defaults={
        "first_name": "Sophie",
        "last_name": "Kouassi",
        "email": "dr.sophie@fransick.com",
        "role": "medecin"
    }
)
if doc2.role != 'medecin':
    doc2.role = 'medecin'
    doc2.save()

profile2, _ = DoctorProfile.objects.get_or_create(
    user=doc2,
    defaults={
        "speciality": "Pédiatre & Nutritionniste",
        "years_of_experience": 9,
        "rating": 5.0,
        "about": "Passionnée par la médecine préventive et le bien-être de l'enfant et de la famille."
    }
)

doc3, _ = User.objects.get_or_create(
    username="dr_alain",
    defaults={
        "first_name": "Alain",
        "last_name": "Mensah",
        "email": "dr.alain@fransick.com",
        "role": "medecin"
    }
)
if doc3.role != 'medecin':
    doc3.role = 'medecin'
    doc3.save()

profile3, _ = DoctorProfile.objects.get_or_create(
    user=doc3,
    defaults={
        "speciality": "Médecin Généraliste",
        "years_of_experience": 15,
        "rating": 4.8,
        "about": "Conseils pratiques pour la gestion du stress, du sommeil et de la médecine de famille."
    }
)

sample_videos_data = [
    {
        "author": doc1,
        "title": "🫀 5 réflexes essentiels pour protéger votre cœur au quotidien",
        "description": "L'hypertension est le tueur silencieux N°1. Voici 5 gestes simples à appliquer dès aujourd'hui : réduire le sel, marcher 30 min, bien dormir et éviter le tabac. Abonnez-vous pour plus de conseils !",
        "file": "videos/sto_1.mp4",
        "likes": 142,
        "comments": [
            ("Merci Docteur pour ces conseils très utiles !", doc2),
            ("Est-ce que le café augmente la tension ?", doc3)
        ]
    },
    {
        "author": doc2,
        "title": "🥗 Nutrition & Hydratation : Les erreurs à éviter absolument !",
        "description": "Boire 2 Litres d'eau par jour est indispensable pour vos reins et votre peau. Évitez les sodas très sucrés et privilégiez les jus naturels d'agrumes bio. 🍊🍋 #Hydratation #SantéAuNaturel #Fransick",
        "file": "videos/sto_1.mp4",
        "likes": 98,
        "comments": [
            ("Super capsule vidéo, très claire !", doc1)
        ]
    },
    {
        "author": doc3,
        "title": "😴 Comment retrouver un sommeil réparateur sans médicaments ?",
        "description": "Écrans éteints 45 min avant de dormir, tisane de camomille et température fraîche dans la chambre. Essayez cette routine pendant 7 jours ! 🌙✨ #Sommeil #BienEtre #ConseilsDoc",
        "file": "videos/sto_1.mp4",
        "likes": 215,
        "comments": [
            ("Je confirme, la routine sans écran a changé mes nuits !", doc2)
        ]
    },
    {
        "author": doc1,
        "title": "🩺 Quand faut-il consulter en urgence pour un mal de tête ?",
        "description": "Attention aux signaux d'alarme : maux de tête soudains et violents, raideur dans la nuque ou troubles de la vision. Ne négligez jamais ces symptômes ! 🚨 #UrgenceSanté #CardioDoc",
        "file": "videos/sto_1.mp4",
        "likes": 310,
        "comments": [
            ("Information capitale, merci pour la prévention !", doc3)
        ]
    }
]

for item in sample_videos_data:
    v, created = HealthVideo.objects.get_or_create(
        title=item["title"],
        author=item["author"],
        defaults={
            "description": item["description"],
            "video_file": item["file"],
            "likes_count": item["likes"]
        }
    )
    if created:
        for c_text, c_author in item["comments"]:
            VideoComment.objects.create(
                video=v,
                author=c_author,
                text=c_text
            )

print("🎉 Base de données capsules vidéo seeded avec succès !")
