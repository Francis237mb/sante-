from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Adresse email")
    phone_number = forms.CharField(required=False, label="Numéro de téléphone")
    role = forms.ChoiceField(
        choices=CustomUser.ROLE_CHOICES[:-1],  # Exclure le rôle Admin
        required=True,
        label="Rôle"
    )
    terms_accepted = forms.BooleanField(
        required=True,
        label="Acceptation des CGU",
        error_messages={'required': "Vous devez obligatoirement lire et accepter les conditions générales d'utilisation pour créer votre compte."}
    )

    # Champs Étape 2 (Médecin)
    address = forms.CharField(required=False, label="Adresse complète")
    city = forms.CharField(required=False, label="Ville")
    region = forms.CharField(required=False, label="Région")
    hospital_affiliation = forms.CharField(required=False, label="Hôpital / Structure de rattachement")
    license_number = forms.CharField(required=False, label="Numéro de licence / ordre")
    speciality = forms.CharField(required=False, label="Spécialité médicale")

    # Champs Étape 3 (Médecin - Fichiers justificatifs)
    diploma_document = forms.FileField(required=False, label="Diplôme(s) médical(aux)")
    professional_card_document = forms.FileField(required=False, label="Carte professionnelle")
    identity_document = forms.FileField(required=False, label="Pièce d'identité")

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = UserCreationForm.Meta.fields + ('email', 'phone_number', 'role')

    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower().strip()
        if CustomUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Cette adresse email est déjà utilisée par un autre compte.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')

        if role == 'medecin':
            # 1. Validation des champs textuels professionnels (Étape 2)
            required_text_fields = {
                'license_number': "Le numéro d'ordre est obligatoire pour les médecins.",
                'speciality': "Veuillez sélectionner une spécialité médicale.",
                'address': "L'adresse complète est obligatoire.",
                'city': "La ville d'exercice est obligatoire.",
                'region': "La région d'exercice est obligatoire.",
                'hospital_affiliation': "L'établissement ou structure de rattachement est obligatoire.",
            }
            for field_name, error_msg in required_text_fields.items():
                if not cleaned_data.get(field_name):
                    self.add_error(field_name, error_msg)

            # 2. Vérification de l'unicité du numéro d'ordre
            license_number = cleaned_data.get('license_number')
            if license_number:
                from medecins.models import DoctorProfile
                if DoctorProfile.objects.filter(license_number__iexact=license_number.strip()).exists():
                    self.add_error('license_number', "Ce numéro d'ordre est déjà utilisé par un autre médecin sur la plateforme.")

            # 3. Validation des documents justificatifs (Étape 3)
            required_files = {
                'diploma_document': "Le justificatif de diplôme médical est obligatoire (PDF, JPG, PNG).",
                'professional_card_document': "La carte professionnelle ou attestation de l'Ordre est obligatoire.",
                'identity_document': "Une pièce d'identité en cours de validité est obligatoire.",
            }
            valid_extensions = ('.pdf', '.jpg', '.jpeg', '.png')
            max_size = 5 * 1024 * 1024  # 5 Mo en octets

            for field_name, error_msg in required_files.items():
                file_obj = cleaned_data.get(field_name)
                if not file_obj:
                    self.add_error(field_name, error_msg)
                else:
                    if file_obj.size > max_size:
                        size_mb = file_obj.size / (1024 * 1024)
                        self.add_error(field_name, f"Le fichier ne doit pas dépasser 5 Mo (poids actuel : {size_mb:.1f} Mo).")
                    if not any(file_obj.name.lower().endswith(ext) for ext in valid_extensions):
                        self.add_error(field_name, "Format de fichier non accepté. Formats acceptés : PDF, JPG, PNG.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.phone_number = self.cleaned_data['phone_number']
        user.role = self.cleaned_data['role']
        if commit:
            user.save()
            if user.role == 'medecin':
                from medecins.models import DoctorProfile
                DoctorProfile.objects.create(
                    user=user,
                    address=self.cleaned_data.get('address', '').strip() if self.cleaned_data.get('address') else None,
                    city=self.cleaned_data.get('city', '').strip() if self.cleaned_data.get('city') else None,
                    region=self.cleaned_data.get('region', '').strip() if self.cleaned_data.get('region') else None,
                    hospital_affiliation=self.cleaned_data.get('hospital_affiliation', '').strip() if self.cleaned_data.get('hospital_affiliation') else None,
                    license_number=self.cleaned_data.get('license_number', '').strip() if self.cleaned_data.get('license_number') else None,
                    speciality=self.cleaned_data.get('speciality'),
                    diploma_document=self.cleaned_data.get('diploma_document'),
                    professional_card_document=self.cleaned_data.get('professional_card_document'),
                    identity_document=self.cleaned_data.get('identity_document'),
                    is_verified=False,
                    verification_status='pending'
                )
        return user
