from django import forms
from accounts.models import CustomUser
from .models import DoctorProfile

class DoctorProfileForm(forms.ModelForm):
    first_name = forms.CharField(required=False, label="Prénom")
    last_name = forms.CharField(required=False, label="Nom de famille")
    email = forms.EmailField(required=True, label="Adresse email")
    phone_number = forms.CharField(required=False, label="Numéro de téléphone personnel")
    profile_picture = forms.ImageField(required=False, label="Photo de profil / Avatar")
    
    # Champs du profil médecin
    speciality = forms.CharField(required=False, label="Spécialité médicale (ex: Cardiologue, Pédiatre)")
    license_number = forms.CharField(required=False, label="Numéro d'Ordre National / Licence")
    about = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4}),
        required=False,
        label="Présentation et Biographie professionnelle"
    )
    schedule = forms.CharField(required=False, label="Horaires de consultation (ex: Lun - Ven, 08h - 18h)")
    years_of_experience = forms.IntegerField(required=False, label="Années d'expérience professionnelle", min_value=0)
    consulted_patients_count = forms.IntegerField(required=False, label="Nombre approximatif de patients consultés", min_value=0)
    clinic_name = forms.CharField(required=False, label="Nom du Cabinet / Clinique / Centre Hospitalier")
    clinic_address = forms.CharField(required=False, label="Adresse complète du cabinet (Ville, Quartier, Rue)")
    clinic_phone = forms.CharField(required=False, label="Téléphone de secrétariat / cabinet")

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'profile_picture']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            profile, created = DoctorProfile.objects.get_or_create(user=self.instance)
            self.fields['speciality'].initial = profile.speciality
            self.fields['license_number'].initial = profile.license_number
            self.fields['about'].initial = profile.about
            self.fields['schedule'].initial = profile.schedule
            self.fields['years_of_experience'].initial = profile.years_of_experience
            self.fields['consulted_patients_count'].initial = profile.consulted_patients_count
            self.fields['clinic_name'].initial = profile.clinic_name
            self.fields['clinic_address'].initial = profile.clinic_address
            self.fields['clinic_phone'].initial = profile.clinic_phone
            self.fields['first_name'].initial = self.instance.first_name
            self.fields['last_name'].initial = self.instance.last_name

    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower().strip()
        qs = CustomUser.objects.filter(email__iexact=email)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Cette adresse email est déjà utilisée par un autre utilisateur.")
        return email

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            user.first_name = self.cleaned_data.get('first_name', '')
            user.last_name = self.cleaned_data.get('last_name', '')
            user.save()
            profile, created = DoctorProfile.objects.get_or_create(user=user)
            profile.speciality = self.cleaned_data.get('speciality')
            profile.license_number = self.cleaned_data.get('license_number')
            profile.about = self.cleaned_data.get('about')
            profile.schedule = self.cleaned_data.get('schedule')
            profile.years_of_experience = self.cleaned_data.get('years_of_experience')
            profile.consulted_patients_count = self.cleaned_data.get('consulted_patients_count')
            profile.clinic_name = self.cleaned_data.get('clinic_name')
            profile.clinic_address = self.cleaned_data.get('clinic_address')
            profile.clinic_phone = self.cleaned_data.get('clinic_phone')
            profile.save()
        return user
