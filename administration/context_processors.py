from .models import SiteAppearance

def site_appearance(request):
    """
    Context processor pour injecter les paramètres d'apparence globale
    dans tous les templates du site.
    """
    appearance = SiteAppearance.objects.first()
    if not appearance:
        # Création d'une apparence par défaut si elle n'existe pas
        appearance = SiteAppearance.objects.create()
    
    return {
        'site_appearance': appearance
    }
