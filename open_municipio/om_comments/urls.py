from django.conf.urls.defaults import patterns, url

from django.contrib.auth.decorators import login_required
from django.contrib.comments.views.comments import comment_done, post_comment

from open_municipio.om_comments.views import DeleteOwnCommentView, RecordVoteOnCommentView



urlpatterns = patterns('',
  # Since in OpenMunicipio only authenticated users are allowed to post comments,                       
  # we have to wrap some views provided by Django's comment framework with the
  # ``login_required`` decorator.
  url(r'^post/$', login_required(post_comment), name='comments-post-comment'),
  url(r'^posted/$', login_required(comment_done), name='comments-comment-done'),
  url(r'^delete-own/(?P<pk>\d+)/$', DeleteOwnCommentView.as_view(), name='comments-delete-own-comment'),
  # Users can vote comments
  url(r'^(?P<pk>\d+)/vote/(?P<direction>up|down|clear)/$', RecordVoteOnCommentView.as_view(), name='om_comments_record_user_vote'),
)
