from django.db import models
from django.db.models import permalink
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import slugify
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic

from taggit.models import TagBase, ItemBase
from open_municipio.monitoring.models import Monitoring


class Tag(TagBase):
    class Meta:
        verbose_name = _("Tag")
        verbose_name_plural = _("Tags")

    def __unicode__(self):
        return self.name

    @permalink
    def get_absolute_url(self):
        return 'om_tag_detail', (), { 'slug': self.slug }


class TaggedAct(ItemBase):
    """
    A intermediate model to record associations between tags and ``Act`` model instances.
    
    It's a `custom version`_ of ``taggit.TaggedItem``, adding a few tagging metadata:
    
    * ``tagger``: the user (an ``auth.User`` instance) who tagged the act
    * ``tagging_time``: a timestamp specifying when the act was tagged
    
    Note that, contrarily to ``taggit.TaggedItem``, this model ONLY allows tagging of ``Act`` 
    instances. 
    
    .. _`custom version`: http://readthedocs.org/docs/django-taggit/en/latest/custom_tagging.html
    """
    content_object = models.ForeignKey('acts.Act')
    tag = models.ForeignKey(Tag, related_name='tagged_acts')
    tagger = models.ForeignKey(User, null=True, blank=True, editable=False)
    tagging_time = models.DateTimeField(null=True, auto_now_add=True, editable=False)    
                                       
    class Meta:
        verbose_name = _("tagged act")
        verbose_name_plural = _("tagged acts")
    
    @classmethod
    def tags_for(cls, model, instance=None):
        if instance is not None:
            return cls.tag_model().objects.filter(**{
                '%s__content_object' % cls.tag_relname(): instance
            })
        return cls.tag_model().objects.filter(**{
            '%s__content_object__isnull' % cls.tag_relname(): False
        }).distinct()


class Category(models.Model):
    """
    A label that can be used to categorize content objects.
    
    Categories differ from tags in that the former are pre-defined at the application level,
    while tags are assigned (and created, if not already existing) on a per-instance basis. 
    """
    name = models.CharField(verbose_name=_('Name'), max_length=100)
    slug = models.SlugField(verbose_name=_('Slug'), blank=True, unique=True, max_length=100)
    tag_set = models.ManyToManyField(Tag, related_name='category_set', null=True, blank=True)
  
    # manager to handle the list of monitoring having as content_object this instance
    monitoring_set = generic.GenericRelation(Monitoring, object_id_field='object_pk')
  
    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')
        
    def __unicode__(self):
        return u'%s' % self.name
    
    @permalink
    def get_absolute_url(self):
        return 'om_category_detail', (), { 'slug': self.slug }
    
    def save(self, *args, **kwargs):
        # auto-generate a slug, if needed 
        if not self.pk and not self.slug:
            self.slug = self.calculate_slug()
        return super(Category, self).save(*args, **kwargs)
    
    def slugify(self, tag, i=None):
        slug = slugify(tag)
        if i is not None:
            slug += "_%d" % i
        return slug
     
    def calculate_slug(self):
        """
        Calculate a slug for a given category name.
        
        If a calculated slug already exists in the DB, add a numerical prefix until is OK.
        """
        slug = self.slugify(self.name)
        i = 0
        while True:
            i += 1
            try:
                Category.objects.get(slug=slug)
                slug = self.slugify(self.name, i)
            except Category.DoesNotExist:
                return slug
        
    @property
    def tags(self):
        return self.tag_set.all()
    
    @property
    def monitorings(self):
        """
        Returns the monitorings associated with this category (as a QuerySet).
        """
        return self.monitoring_set.all()
    
    @property
    def monitoring_users(self):
        """
        Returns the list of users monitoring this argument (category).
        """
        # FIXME: This method should return a QuerySet for efficiency reasons
        # (an argument could be monitored by a large number of people;
        # moreover, often we are only interested in the total number of 
        # monitoring users, so building a list in memory may result in a waste of resources). 
        return [m.user for m in self.monitorings]