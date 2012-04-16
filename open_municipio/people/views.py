from django.http import Http404
from django.views.generic import TemplateView, DetailView, ListView, RedirectView
from django.core.exceptions import ObjectDoesNotExist

from open_municipio.people.models import Institution, InstitutionCharge, Person, municipality, InstitutionResponsability, Resource
from open_municipio.monitoring.forms import MonitoringForm
from open_municipio.acts.models import Act, Deliberation, Interrogation, Interpellation, Motion, Agenda
from open_municipio.events.models import Event

from os import sys



class InstitutionListView(ListView):
    model = Institution
    template_name = 'people/institution_list.html'
    
    
class MayorDetailView(RedirectView):
    def get_redirect_url(self, **kwargs):
        return municipality.mayor.as_charge.person.get_absolute_url()


class CouncilDetailView(TemplateView):
    """
    Renders the Council page
    """
    template_name = 'people/institution_council.html'

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(CouncilDetailView, self).get_context_data(**kwargs)

        mayor = municipality.mayor.as_charge
        president = municipality.council.president
        vicepresidents = municipality.council.vicepresidents
        groups = municipality.council.groups
        committees = municipality.committees.as_institution
        latest_acts = Act.objects.filter(
            emitting_institution__institution_type=Institution.COUNCIL
            ).order_by('-presentation_date')[:3]
        events = Event.future.filter(
            institution__institution_type=Institution.COUNCIL
            )
        num_acts = dict()
        act_types = [
            Deliberation, Motion, Interrogation, Interpellation, Agenda
            ]
        for act_type in act_types:
            num_acts[act_type.__name__.lower()] = act_type.objects.filter(
                emitting_institution__institution_type=Institution.COUNCIL
                ).count()

        extra_context = {
            'mayor': mayor,
            'president': president,
            'vicepresidents': vicepresidents,
            'groups': groups,
            'committees': committees,
            'latest_acts': latest_acts,
            'num_acts': num_acts,
            'events': events,
            }
        
        # Update context with extra values we need
        context.update(extra_context)
        return context


class CityGovernmentView(TemplateView):
    """
    Renders the City Government page
    """
    template_name = 'people/institution_citygov.html'

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(CityGovernmentView, self).get_context_data(**kwargs)

        mayor = municipality.mayor.as_charge
        firstdeputy = municipality.gov.firstdeputy.charge
        citygov = municipality.gov
        latest_acts = Act.objects.filter(
            emitting_institution__institution_type=Institution.CITY_GOVERNMENT
            ).order_by('-presentation_date')[:3]
        events = Event.future.filter(
            institution__institution_type=Institution.CITY_GOVERNMENT
            )
        num_acts = dict()
        act_types = [
            Deliberation, Motion, Interrogation, Interpellation, Agenda
            ]
        for act_type in act_types:
            num_acts[act_type.__name__.lower()] = act_type.objects.filter(
                emitting_institution__institution_type=Institution.CITY_GOVERNMENT
                ).count()
            
        extra_context = {
            'mayor': mayor,
            'firstdeputy': firstdeputy,
            'citygov': citygov,
            'latest_acts': latest_acts,
            'num_acts': num_acts,
            'events': events,
            }

        # Update context with extra values we need
        context.update(extra_context)
        return context


class CommitteeDetailView(DetailView):
    """
    Renders the Committee page
    """
    model = Institution
    template_name = 'people/institution_committee.html'
    context_object_name = "committee"

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(CommitteeDetailView, self).get_context_data(**kwargs)

        # Are we given a real Committee institution as input? If no,
        # raise 404 exception.
        if self.object.institution_type != Institution.COMMITTEE:
            raise Http404

        committee_list = municipality.committees.as_institution()

        # fetch charges and add group
        president = self.object.president
        if president:
            president.group = InstitutionCharge.objects.select_related().\
                                  get(pk=president.charge.original_charge_id).council_group
        vicepresidents = self.object.vicepresidents
        for vp in vicepresidents:
            if vp:
                vp.group = InstitutionCharge.objects.select_related().\
                    get(pk=vp.charge.original_charge_id).council_group
        members = self.object.members.order_by('person__last_name')
        for m in members:
            m.group = InstitutionCharge.objects.select_related().\
                get(pk=m.original_charge_id).council_group


        resources = self.object.resource_set.all()

        events = Event.future.filter(institution=self.object)

        extra_context = {
            'committee_list': committee_list,
            'members': members,
            'president': president,
            'resources': resources,
            'vice_presidents': vicepresidents,
            'events': events,
        }

        # Update context with extra values we need
        context.update(extra_context)
        return context


class PoliticianDetailView(DetailView):
    model = Person
    context_object_name = 'person'
    template_name='people/politician_detail.html'

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(PoliticianDetailView, self).get_context_data(**kwargs)
        # Add in a QuerySet of all the institutions
        context['institution_list'] = Institution.objects.all()

        context['resources'] = dict(
            (r['resource_type'], {'value': r['value'], 'description': r['description']})
            for r in self.object.resource_set.all().values('resource_type', 'value', 'description')
        )
        context['current_charges'] = self.object.current_institution_charges.exclude(
            institutionresponsability__charge_type__in=(
                InstitutionResponsability.CHARGE_TYPES.mayor,
            ),
            institutionresponsability__end_date__isnull=True
        )
        context['current_committee_charges'] = self.object.current_committee_charges

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


class PoliticianListView(TemplateView):
    """
    Renders the Politicians page
    """
    template_name = 'people/politician_list.html'

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(PoliticianListView, self).get_context_data(**kwargs)

        # municipality access point to internal API
        context['municipality'] = municipality

        # fetch mayor
        context['mayor'] = municipality.mayor.as_charge
        # exclude mayor from gov members
        context['gov_members'] = municipality.gov.charges.exclude(
            institutionresponsability__charge_type__in=(
                InstitutionResponsability.CHARGE_TYPES.mayor,
            ),
            institutionresponsability__end_date__isnull=True
        ).select_related().order_by('person__last_name')
        # exclude mayor from council members
        counselors = context['counselors'] = municipality.council.members.exclude(
            institutionresponsability__charge_type__in=(
                InstitutionResponsability.CHARGE_TYPES.mayor,
            ),
            institutionresponsability__end_date__isnull=True
        ).select_related().order_by('person__last_name')

        # fetch most or least
        context['most_rebellious'] = counselors.order_by('-n_rebel_votations')[0:3]
        context['least_absent'] = counselors.order_by('n_absent_votations')[0:3]
        context['most_absent'] = counselors.order_by('-n_absent_votations')[0:3]
        return context


def show_mayor(request):
    return HttpResponseRedirect( municipality.mayor.as_charge.person.get_absolute_url() )
