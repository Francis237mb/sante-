from django import forms
from accounts.models import CustomUser
from .models import PatientProfile

class PatientProfileForm(forms.ModelForm):
    email = forms.EmailField(required=True, label="Adresse email")
    phone_number = forms.CharField(required=False, label="Numéro de téléphone")
    profile_picture = forms.ImageField(required=False, label="Photo de profil")
    
    # Champs du profil patient
    gender = forms.ChoiceField(
        choices=[('', 'Sélectionnez le sexe')] + PatientProfile.GENDER_CHOICES,
        required=False,
        label="Sexe"
    )
    additional_notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        label="Notes supplémentaires (allergie, diabétique...)"
    )
    city = forms.CharField(required=False, label="Ville")
    neighborhood = forms.CharField(required=False, label="Quartier")
    occupation = forms.CharField(required=False, label="Occupation")
    civil_status = forms.ChoiceField(
        choices=[('', 'Sélectionnez l\'état civil')] + PatientProfile.CIVIL_STATUS_CHOICES,
        required=False,
        label="État civil"
    )
    height = forms.IntegerField(required=False, label="Taille (en cm)")
    weight = forms.IntegerField(required=False, label="Poids (en Kg)")
    blood_group = forms.ChoiceField(
        choices=[('', 'Sélectionnez le groupe sanguin')] + PatientProfile.BLOOD_GROUP_CHOICES,
        required=False,
        label="Groupe sanguin"
    )

    class Meta:
        model = CustomUser
        fields = ['email', 'phone_number', 'profile_picture']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Récupérer ou créer le profil lié à cet utilisateur
            profile, created = PatientProfile.objects.get_or_create(user=self.instance)
            # Pré-remplir les champs
            self.fields['gender'].initial = profile.gender
            self.fields['additional_notes'].initial = profile.additional_notes
            self.fields['city'].initial = profile.city
            self.fields['neighborhood'].initial = profile.neighborhood
            self.fields['occupation'].initial = profile.occupation
            self.fields['civil_status'].initial = profile.civil_status
            self.fields['height'].initial = profile.height
            self.fields['weight'].initial = profile.weight
            self.fields['blood_group'].initial = profile.blood_group

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Cette adresse email est déjà utilisée.")
        return email

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            # Enregistrer le profil lié
            profile, created = PatientProfile.objects.get_or_create(user=user)
            profile.gender = self.cleaned_data.get('gender')
            profile.additional_notes = self.cleaned_data.get('additional_notes')
            profile.city = self.cleaned_data.get('city')
            profile.neighborhood = self.cleaned_data.get('neighborhood')
            profile.occupation = self.cleaned_data.get('occupation')
            profile.civil_status = self.cleaned_data.get('civil_status')
            profile.height = self.cleaned_data.get('height')
            profile.weight = self.cleaned_data.get('weight')
            profile.blood_group = self.cleaned_data.get('blood_group')
            profile.save()
        return user
