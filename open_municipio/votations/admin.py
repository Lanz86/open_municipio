from httplib import HTTP
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from open_municipio.votations.models import ChargeVote, GroupVote, Votation  



class GroupVoteInline(admin.TabularInline):
    model = GroupVote
    extra = 1

class ChargeVoteInline(admin.TabularInline):
    model = ChargeVote
    raw_id_fields = ('charge', )
    extra = 1

class VotationAdmin(admin.ModelAdmin):
    list_display = ('idnum', 'act_descr', 'sitting', 'is_linked', 'outcome')
    list_filter = ('act', 'sitting',)
    raw_id_fields = ['act']
    readonly_fields = ('act_descr', )
    ordering = ['-sitting__date']



    # add inlines only for superuser users
    def change_view(self, request, object_id, extra_context=None):

        if request.user.is_superuser:
            self.inlines = [GroupVoteInline, ChargeVoteInline]
        else:
            self.inlines = []

        self.inline_instances = []
        for inline_class in self.inlines:
            inline_instance = inline_class(self.model, self.admin_site)
            self.inline_instances.append(inline_instance)

        return super(VotationAdmin, self).change_view(request, object_id)


class VotationsInline(admin.TabularInline):
    model = Votation
    fields = ('n_legal', 'n_presents', 'n_maj', 'n_yes', 'n_no', 'n_abst', 'outcome')

admin.site.register(Votation, VotationAdmin)
admin.site.register(GroupVote)
admin.site.register(ChargeVote)
