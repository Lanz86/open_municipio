from django.views.generic import DetailView, ListView, TemplateView
from django.shortcuts import get_object_or_404

from open_municipio.taxonomy.views import AddTagsView, RemoveTagView  

from open_municipio.acts.models import Act, Agenda, Deliberation, Interpellation, Interrogation, Motion
from open_municipio.acts.forms import TagAddForm

class ActListView(ListView):
    model = Act
    template_name = 'acts/act_list.html'

class ActEditorView(TemplateView):
    pass

class ActDetailView(DetailView):
    model = Act
    context_object_name = 'act' 
    
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(ActDetailView, self).get_context_data(**kwargs)
        # mix-in tab-related context
        self.tab = self.kwargs.get('tab', 'default')
        extra_context = getattr(self, 'get_related_%(tab)s' % {'tab': self.tab})()
        if extra_context:
            context.update(extra_context)
        # Add in a form for adding tags
        context['tag_add_form'] = TagAddForm()
        return context
    
    def get_related_default(self):
        """
        Retrieve context needed for populating the default tab.
        """
        pass
    
    def get_related_emendations(self):
        """
        Retrieve context needed for populating the *emendations* tab.
        """
        pass

    def get_related_documents(self):
        """
        Retrieve context needed for populating the *documents* tab.
        """
        pass
        
    def get_related_votes(self):
        """
        Retrieve context needed for populating the *votes* tab.
        """
        pass
    
    def get_template_names(self):
        if self.tab == 'default': # default tab selected
            return 'acts/%(model)s_detail.html' % {'model': self.model.__name__.lower()}
        else:
            return 'acts/%(model)s_detail_%(tab)s.html' % {'model': self.model.__name__.lower(), 'tab': self.tab}


class AgendaDetailView(ActDetailView):
    model = Agenda
    context_object_name = 'agenda'


class DeliberationDetailView(ActDetailView):
    model = Deliberation
    context_object_name = 'deliberation'


class InterpellationDetailView(ActDetailView):
    model = Interpellation
    context_object_name = 'interpellation'


class InterrogationDetailView(ActDetailView):
    model = Interrogation
    context_object_name = 'interrogation'

class MotionDetailView(ActDetailView):
    model = Motion
    context_object_name = 'motion'
    

## Tag management
class ActAddTagsView(AddTagsView):
    form_class = TagAddForm
    context_object_name = 'act'
    template_name = 'acts/act_detail.html'
  
    def get_object(self):
        """
        Returns the ``Act`` instance being tagged.
        """
        act = get_object_or_404(Act, pk=self.kwargs['pk'])
        return act
    
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(ActAddTagsView, self).get_context_data(**kwargs)
        # Just an alias for ``form`` context variable
        context['tag_add_form'] = kwargs['form']
        return context
 
    
class ActRemoveTagView(RemoveTagView):
    def get_object(self):
        """
        Returns the ``Act`` instance being un-tagged.
        """
        act = get_object_or_404(Act, pk=self.kwargs.get('act_pk'))
        return act
