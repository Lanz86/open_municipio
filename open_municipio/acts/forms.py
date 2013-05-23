from django import forms
from django.utils.translation import ugettext_lazy as _

from open_municipio.acts.models import Act, Transition, ActHasSpeech, Interrogation
from open_municipio.people.models import Institution, InstitutionCharge

class ActTitleForm(forms.ModelForm):
    class Meta:
        model = Act
        fields = ('id', 'title',)


class ActDescriptionForm(forms.ModelForm):
    class Meta:
        model = Act
        fields = ('id', 'description',)


class ActTransitionForm(forms.ModelForm):
    """
    A form to change status of act
    """
    def save(self, commit=True):
        instance = super(forms.ModelForm, self).save(commit=False)
        instance.act = instance.act.downcast()
        if commit:
            instance.save()
        return instance

    class Meta:
        model = Transition
        fields = ('transition_date', 'note', 'final_status', 'act')
        widgets = {
            'act': forms.HiddenInput(),
            'final_status': forms.HiddenInput(),
            'transition_date': forms.DateTimeInput(attrs={'class':'datepicker'})
        }


class ActFinalTransitionForm(ActTransitionForm):
    """
    Extends ActTransitionForm to provide a vote selection
    """

    class Meta(ActTransitionForm.Meta):
        fields = ('transition_date', 'note', 'final_status', 'act', 'votation')
        widgets = {
            'act': forms.HiddenInput(),
            'final_status': forms.Select(choices=[]),
            'transition_date': forms.DateTimeInput(attrs={'class':'datepicker'})
        }

class SpeechAdminForm(forms.ModelForm):

    def is_valid(self):
        if not super(SpeechAdminForm,self).is_valid():
            return False

        author = self.cleaned_data["author"]
        author_external = self.cleaned_data["author_name_when_external"]

        if author == None and (author_external == None or len(author_external) == 0):
            self._errors['author'] = self.error_class([ _("If the author is present in Open Municipio, search it") ])
            self._errors['author_name_when_external'] = self.error_class([ _("Populate the full author name when not present in Open Municipio") ])
            return False

        return True

    class Meta:
        fields = ( 'author', 'author_name_when_external', 'sitting_item','seq_order','title','text','text_url','file','file_url','audio_url','audio_file','votation','initial_time','duration',)


class SpeechInActInlineFormSet(forms.models.BaseInlineFormSet):
    def clean(self):
        super(SpeechInActInlineFormSet,self).clean()

        if len(self.forms) > 2:
            raise forms.ValidationError(_("A maximum of two speech is allowed for each act"))
 
        found_speeches = ()
        speech_types = ()

        for form in self.forms:
            try:
                if "speech" not in form.cleaned_data:
                    continue


                curr_speech = form.cleaned_data["speech"]
                if curr_speech in found_speeches:
                    raise forms.ValidationError(_("The same speech cannot be referred twice by an act"))
                
                found_speeches += (curr_speech, )

                curr_type = form.cleaned_data["relation_type"]
                if curr_type in speech_types:
                    raise forms.ValidationError(_("Speeches must be of different types"))
                if curr_type == u"REF":
                    raise forms.ValidationError(_("Speeches of type REF not allowed in this context"))
                speech_types += (curr_type, )

            except AttributeError:
                # invalid data
                pass

class InterpellationAdminForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(InterpellationAdminForm, self).__init__(*args, **kwargs)
    
        # interpellation targets can be the mayor or members of city government
        self.fields["recipient_set"].queryset = InstitutionCharge.objects.filter(institution__institution_type__in=( Institution.MAYOR, Institution.CITY_GOVERNMENT )).order_by("institution__institution_type","person__last_name","person__first_name")

class InterrogationAdminForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(InterrogationAdminForm, self).__init__(*args, **kwargs)
   
        # interrogation targets can be the mayor or members of city government
        self.fields["recipient_set"].queryset = InstitutionCharge.objects.filter(institution__institution_type__in=( Institution.MAYOR, Institution.CITY_GOVERNMENT )).order_by("institution__institution_type","person__last_name","person__first_name")

    class Meta:
        model = Interrogation

