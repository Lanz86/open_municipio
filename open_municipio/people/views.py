from os import sys

from django.views.generic import TemplateView, DetailView
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render

from open_municipio.people.models import Institution, InstitutionCharge, Person, municipality
from open_municipio.monitoring.forms import MonitoringForm
from open_municipio.acts.models import Act, Deliberation, Interrogation, Interpellation, Motion, Agenda
from open_municipio.events.models import Event


class CouncilView(TemplateView):
    """
    Renders the Council page
    """
    template_name = 'people/institution_council.html'

    mayor = municipality.mayor.as_charge.person
    president = municipality.council.members.get(
        charge_type=InstitutionCharge.COUNCIL_PRES_CHARGE).person
    vice_president = municipality.council.members.get(
        charge_type=InstitutionCharge.COUNCIL_VICE_CHARGE).person
    groups = municipality.council.groups
    committees = municipality.committees.as_institution
    latest_acts_by_council = Act.objects.filter(
        emitting_institution__institution_type=Institution.COUNCIL
        ).order_by('-presentation_date')[:3]
    events = Event.objects.filter(
        institution__institution_type=Institution.COUNCIL
        )

    num_acts = dict()
    act_types = [
        'Deliberation', 'Motion', 'Interrogation', 'Interpellation',
        'Motion', 'Agenda'
        ]
    for act_type in act_types:
        # FIXME: I am not sure "eval" is considered a good practice,
        # check it out
        current_class = eval(act_type)
        num_acts[act_type] = current_class.objects.filter(
            emitting_institution__institution_type=Institution.COUNCIL
            ).count()

    extra_context = {
        'mayor': mayor,
        'president': president,
        'vice_president': vice_president,
        'groups': groups,
        'committees': committees,
        'latest_acts_by_council': latest_acts_by_council,
        'num_acts': num_acts,
        'events': events,
        }

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(CouncilView, self).get_context_data(**kwargs)
        # Update context with extra values we need
        context.update(self.extra_context)
        return context


class CityGovernmentView(TemplateView):
    """
    Renders the City Government page
    """
    template_name = 'people/institution_citygov.html'

    citygov = municipality.gov.members
    latest_acts_by_citygov = Act.objects.filter(
        emitting_institution__institution_type=Institution.CITY_GOVERNMENT
        ).order_by('-presentation_date')[:3]
    events = Event.objects.filter(
        institution__institution_type=Institution.CITY_GOVERNMENT
        )

    num_acts = dict()
    act_types = [
        'Deliberation', 'Motion', 'Interrogation', 'Interpellation',
        'Motion', 'Agenda'
        ]
    for act_type in act_types:
        # FIXME: I am not sure "eval" is considered a good practice,
        # check it out
        current_class = eval(act_type)
        num_acts[act_type] = current_class.objects.filter(
            emitting_institution__institution_type=Institution.CITY_GOVERNMENT
            ).count()

    extra_context = {
        'citygov': citygov,
        'latest_acts_by_citygov': latest_acts_by_citygov,
        'num_acts': num_acts,
        'events': events,
        }

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(CityGovernmentView, self).get_context_data(**kwargs)
        # Update context with extra values we need
        context.update(self.extra_context)
        return context


class CommissionView(DetailView):
    model = Institution
    context_object_name = 'commission'


class PersonDetailView(DetailView):
    model = Person
    context_object_name = 'person'

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(PersonDetailView, self).get_context_data(**kwargs)
        # Add in a QuerySet of all the institutions
        context['institution_list'] = Institution.objects.all()

        print  >> sys.stderr, "context: %s" % context

        # is the user monitoring the act?
        context['is_user_monitoring'] = False
        try:
            if self.request.user.is_authenticated():
                # add a monitoring form, to context,
                # to switch monitoring on and off
                context['monitoring_form'] = MonitoringForm(data = {
                    'content_type_id': context['person'].content_type_id,
                    'object_pk': context['person'].id,
                    'user_id': self.request.user.id
                })

                if context['person'] in self.request.user.get_profile().monitored_objects:
                    context['is_user_monitoring'] = True
        except ObjectDoesNotExist:
            context['is_user_monitoring'] = False
        return context



def person_list(request):
    return render_to_response('people/person_list.html',{
        'municipality': municipality
    },context_instance=RequestContext(request) )
