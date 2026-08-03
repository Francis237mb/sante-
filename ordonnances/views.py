from django.views.generic import View, DetailView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import Http404
from .models import Ordonnance
from consultations.models import RendezVous

class CreateOrdonnanceView(LoginRequiredMixin, View):
    def get(self, request, rdv_id=None, *args, **kwargs):
        if request.user.role != 'medecin':
            messages.error(request, "Seuls les médecins peuvent rédiger une ordonnance.")
            return redirect('core:home')
        
        rdv = None
        patient = None
        if rdv_id:
            rdv = get_object_or_404(RendezVous, pk=rdv_id, doctor=request.user)
            patient = rdv.patient

        context = {
            'rdv': rdv,
            'patient': patient,
        }
        return render(request, 'ordonnances/ordonnance_form.html', context)

    def post(self, request, rdv_id=None, *args, **kwargs):
        if request.user.role != 'medecin':
            messages.error(request, "Seuls les médecins peuvent émettre une ordonnance.")
            return redirect('core:home')

        rdv = None
        patient_id = request.POST.get('patient_id')
        if rdv_id:
            rdv = get_object_or_404(RendezVous, pk=rdv_id, doctor=request.user)
            patient = rdv.patient
        else:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            patient = get_object_or_404(User, pk=patient_id)

        patient_age = request.POST.get('patient_age', '30 ans')
        diagnostic = request.POST.get('diagnostic', '')
        prescription_details = request.POST.get('prescription_details', '')

        # Vérification si une ordonnance existe déjà pour ce rdv
        ordonnance = None
        if rdv and hasattr(rdv, 'ordonnance'):
            ordonnance = rdv.ordonnance
            ordonnance.patient_age = patient_age
            ordonnance.diagnostic = diagnostic
            ordonnance.prescription_details = prescription_details
            ordonnance.save()
        else:
            ordonnance = Ordonnance.objects.create(
                rendez_vous=rdv,
                doctor=request.user,
                patient=patient,
                patient_age=patient_age,
                diagnostic=diagnostic,
                prescription_details=prescription_details
            )

        messages.success(request, "L'ordonnance électronique a été générée et transmise au patient !")
        return redirect('ordonnances:detail', pk=ordonnance.id)


class OrdonnanceDetailView(LoginRequiredMixin, DetailView):
    model = Ordonnance
    template_name = 'ordonnances/ordonnance_detail.html'
    context_object_name = 'ordonnance'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if self.request.user != obj.doctor and self.request.user != obj.patient:
            raise Http404("Ordonnance non trouvée ou accès refusé.")
        return obj


class OrdonnanceListView(LoginRequiredMixin, ListView):
    model = Ordonnance
    template_name = 'ordonnances/ordonnance_list.html'
    context_object_name = 'ordonnances'

    def get_queryset(self):
        if self.request.user.role == 'medecin':
            return Ordonnance.objects.filter(doctor=self.request.user)
        return Ordonnance.objects.filter(patient=self.request.user)


class SendOrdonnanceToPatientView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        ordonnance = get_object_or_404(Ordonnance, pk=pk, doctor=request.user)
        messages.success(request, f"📩 L'ordonnance #{ordonnance.id} a été transmise avec succès au patient {ordonnance.patient.username} !")
        return redirect('medecins:dashboard')

