from django.db import models
from django.utils.translation import ugettext_lazy as _

from django.contrib.auth.models import User

from open_municipio.om_utils.models import SlugModel



class Location(SlugModel):
    """
    A concise description of a town's location.
    
    ``Location`` instances may be used as labels to provide a geographic-aware taxonomy 
    for content objects (particularly, ``Act`` instances).       
    """
    name = models.CharField(verbose_name=_('Name'), max_length=100)
    slug = models.SlugField(verbose_name=_('Slug'), blank=True, unique=True, max_length=100)
    address = models.CharField(verbose_name=_('Address'), max_length=100, blank=True)
    # FIXME: choose the right number of significant digits
    latitude = models.FloatField(verbose_name=_('Latitude'), blank=True, null=True)
    # FIXME: choose the right number of significant digits
    longitude = models.FloatField(verbose_name=_('Longitude'), blank=True, null=True)
    
    class Meta:
        verbose_name = _('location')
        verbose_name_plural = _('locations')
    
    def __unicode__(self):
        return u'%s' % self.name
        
    @property
    def acts(self):
        """
        Returns the ``QuerySet`` of all acts tagged with this location.  
        """
        return self.tagged_act_set.all()

    @models.permalink
    def get_absolute_url(self):
        return 'om_location_detail', (), { 'slug': self.slug }
    
    
class TaggedActByLocation(models.Model):
    """
    A intermediate model to record associations between locations and acts.
    
    Beyond the act being tagged and the location being associated to it, 
    a few tagging metadata are also recorded:
    
    * ``tagger``: the user (an ``auth.User`` instance) who tagged the act
    * ``tagging_time``: a timestamp specifying when the act was tagged
    
    """
    act = models.ForeignKey('acts.Act')
    location = models.ForeignKey(Location, related_name='tagged_act_set')
    tagger = models.ForeignKey(User, null=True, blank=True, editable=False)
    tagging_time = models.DateTimeField(null=True, auto_now_add=True, editable=False)    
                                       
    class Meta:
        verbose_name = _("tagged act by location")
        verbose_name_plural = _("tagged acts by location")
        
    def __unicode__(self):
        params = {
                  'tagger': self.tagger, 
                  'location': self.location,
                  'act_id': self.act.pk,
                  'time': self.tagging_time,
                  }
        return u"User '%(tagger)s' added location '%(location)s' to act #%(act_id)s at %(time)s" % params 