from django import forms
from accounts.models import CustomUser

class PatientProfileForm(forms.ModelForm):
    email = forms.EmailField(required=True, label="Adresse email")
    phone_number = forms.CharField(required=False, label="Numéro de téléphone")
    profile_picture = forms.ImageField(required=False, label="Photo de profil")

    class Meta:
        model = CustomUser
        fields = ['email', 'phone_number', 'profile_picture']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # S'assurer que l'email n'est pas déjà pris par un autre utilisateur
        if CustomUser.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Cette adresse email est déjà utilisée.")
        return email
