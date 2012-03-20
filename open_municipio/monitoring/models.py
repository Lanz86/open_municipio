from django.db import models
from django.core.urlresolvers import reverse 
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.template.context import Context
from open_municipio.newscache.models import News

class Monitoring(models.Model):
    """
    This model maps the monitoring of a content object by a user.
    
    This monitoring relation is *polymorphic* (generic),
    i.e. every content type may be monitored by a given user.
    
    An example of a user monitoring an object::
    
        a = Act.objects.get(pk=3)
        u = User.objects.get(username='guglielmo')
        m = Monitoring(content_object=a, user=u)
        m.save()
 
    """
    
    # What's being monitored
    content_type   = models.ForeignKey(ContentType,
                                       verbose_name=_('content type'),
                                       related_name="content_type_set_for_%(class)s")
    object_pk      = models.PositiveIntegerField(_('object ID'))
    content_object = generic.GenericForeignKey(ct_field="content_type", fk_field="object_pk")
    
    # Who's monitoring
    user           = models.ForeignKey(User, verbose_name=_('user'),
                                       related_name="%(class)s_set")
    # Is it a public monitoring ? (visibility)
    # defaults to True
    is_public      = models.BooleanField(default=True)
    
    # When monitoring started (auto-set at the current datetime, on creation)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __unicode__(self):
        return u'user %s is monitoring %s since %s' % (self.user, self.content_object, self.created_at)

    def get_content_object_url(self):
        """
        Get a URL suitable for redirecting to the content object.
        """
        return reverse('om_monitoring_url_redirect', args=(), kwargs=(self.content_type.pk, self.object_pk))


#
# Signals handlers
#

@receiver(post_save, sender=Monitoring)
def new_monitoring(**kwargs):
    """
    generates a record in newscache, when someone starts monitoring something
    """
    # generates news only if not in raw mode (fixtures)
    # and for objects creation
    if not kwargs.get('raw', False) and kwargs.get('created', False):
        generating_item = kwargs['instance']
        monitored_object = generating_item.content_object
        monitoring_user = generating_item.user
        # define context for textual representation of the news
        ctx = Context({ 'monitored_object': monitored_object, 'monitoring_user': monitoring_user })

        # two news are generated

        # first news related to the monitored object, with priority 3
        News.objects.create(
            generating_object=generating_item, related_object=monitored_object,
            priority=3, news_type=News.NEWS_TYPE.community,
            text=News.get_text_for_news(ctx, 'newscache/object_monitored.html')
        )
        # second news related to the monitoring user, with priority 2
        News.objects.create(
            generating_object=generating_item, related_object=monitoring_user,
            priority=2, news_type=News.NEWS_TYPE.community,
            text=News.get_text_for_news(ctx, 'newscache/user_monitoring.html')
        )


@receiver(pre_delete, sender=Monitoring)
def remove_monitoring(**kwargs):
    """
    removes records in newscache, when someone stops monitoring something
    """
    generating_item = kwargs['instance']
    monitored_object = generating_item.content_object
    monitoring_user = generating_item.user

    # first remove news related to the monitored object
    News.objects.filter(
        generating_content_type=ContentType.objects.get_for_model(generating_item),
        generating_object_pk = generating_item.pk,
        related_content_type=ContentType.objects.get_for_model(monitored_object),
        related_object_pk=monitored_object.pk
    ).delete()
    # second remove news related to the monitoring user, with priority 2
    News.objects.filter(
        generating_content_type=ContentType.objects.get_for_model(generating_item),
        generating_object_pk = generating_item.pk,
        related_content_type=ContentType.objects.get_for_model(monitoring_user),
        related_object_pk=monitoring_user.pk
    ).delete()
