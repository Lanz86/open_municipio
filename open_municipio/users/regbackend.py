from django.conf import settings
from django.contrib.auth import login, get_backends
from django.contrib.auth.models import User

from open_municipio.users.forms import UserRegistrationForm
from open_municipio.users.models import UserProfile


def user_created(sender, user, request, **kwargs):
    form = UserRegistrationForm(request.POST)
    user.first_name = form.data['first_name']
    user.last_name = form.data['last_name']
    user.save()
    
    extra_data = UserProfile(user=user)
    extra_data.says_is_politician = form.data['says_is_politician']
    extra_data.uses_nickname = form.data['uses_nickname']
    extra_data.privacy_level = form.data['privacy_level']
    extra_data.wants_newsletter = False
    if 'wants_newsletter' in request.POST:
        extra_data.wants_newsletter = form.data['wants_newsletter']
    extra_data.city = form.data['city']
    extra_data.save()

   
from registration.signals import user_registered
user_registered.connect(user_created)


def log_in_user(sender, user, request, **kwargs):
    if getattr(settings, 'REGISTRATION_AUTO_LOGIN', False):
        backend = get_backends()[0] # A bit of a hack to bypass `authenticate()`.
        user.backend = "%s.%s" % (backend.__module__, backend.__class__.__name__)
        login(request, user)

from registration.signals import user_activated
user_activated.connect(log_in_user)
