# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import
import uuid

from django.utils import timezone
from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

# just brainstorming so we can start playing with this,
# be nice to make this a 3rd party django installable app ?


# users rfid card to user mapping, user can have more than one card
class Rfid(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        # related_name='rfid_user'
    )
    code = models.PositiveIntegerField()
    description = models.CharField(_('Short rfid description'), blank=True, max_length=255)

    def __str__(self):
        return self.description


# description of a device like door, print, laser cutter
class Device(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        # related_name='rfid_user'
    )
    # user = models.ManyToMany(settings.AUTH_USER_MODEL)
    identifier = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(_('Device name'), max_length=255)
    description = models.CharField(_('Short description of what the device does'), blank=True, max_length=255)
    added_date = models.DateTimeField(default=timezone.now, editable=False)

    def __str__(self):
        return self.name


# many to many, lookup user from rfid model then get there user_id and the device to check if auth allowed
# class DeviceAuth(models.Model):
#     user = models.ForeignKey(
#         settings.AUTH_USER_MODEL,
#         null=True, blank=True,
#         default=None,
#         related_name='user_auth'
#     )

#     device = models.ForeignKey(
#         Device,
#         null=True, blank=True,
#         default=None,
#         related_name='device'
#     )
