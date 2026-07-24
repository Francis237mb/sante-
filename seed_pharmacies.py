import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fransick.settings.dev')
try:
    django.setup()
except Exception:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'fransick.settings'
    django.setup()

from django.contrib.auth import get_user_model
from pharmacies.models import PharmacyProfile

User = get_user_model()

# Création des pharmacies d'exemple
pharmacies_data = [
    {
        'username': 'PK8',
        'pharmacy_name': 'Pharmacie PK8',
        'address': 'PK8 A COTE DU CENAT, Douala',
        'hours': '24h/24, 7j/7',
        'phone': '+237 677 88 99 00'
    },
    {
        'username': 'OUAMBO_VICTOR',
        'pharmacy_name': 'Pharmacie OUAMBO VICTOR',
        'address': 'BONALOKA, Douala',
        'hours': '08:00 - 22:00',
        'phone': '+237 699 11 22 33'
    },
    {
        'username': 'NKOUG_FI',
        'pharmacy_name': 'Pharmacie NKOUG\'FI',
        'address': 'RUE DU ROI NJOYA NEW BELL, Douala',
        'hours': '08:00 - 21:30',
        'phone': '+237 655 44 33 22'
    },
    {
        'username': 'LOUXIA',
        'pharmacy_name': 'Pharmacie LOUXIA',
        'address': 'AKWA, Douala',
        'hours': '24h/24, 7j/7',
        'phone': '+237 688 55 66 77'
    }
]

for p_data in pharmacies_data:
    user, created = User.objects.get_or_create(
        username=p_data['username'],
        defaults={
            'email': f"{p_data['username'].lower()}@fransick.com",
            'role': 'pharmacie'
        }
    )
    if created:
        user.set_password('password123')
        user.save()
        print(f"Utilisateur pharmacie créé: {user.username}")
    else:
        user.role = 'pharmacie'
        user.save()
        print(f"Utilisateur pharmacie existant: {user.username}")

    profile, p_created = PharmacyProfile.objects.get_or_create(
        user=user,
        defaults={
            'pharmacy_name': p_data['pharmacy_name'],
            'address': p_data['address'],
            'phone': p_data['phone'],
            'opening_hours': p_data['hours']
        }
    )
    if not p_created:
        profile.pharmacy_name = p_data['pharmacy_name']
        profile.address = p_data['address']
        profile.phone = p_data['phone']
        profile.opening_hours = p_data['hours']
        profile.save()
        print(f"Profil de pharmacie mis à jour: {profile.pharmacy_name}")
    else:
        print(f"Profil de pharmacie créé: {profile.pharmacy_name}")

print("Opération de seeding des pharmacies terminée avec succès !")
