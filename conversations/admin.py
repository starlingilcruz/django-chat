"""
Admin configuration for conversations app
"""

from django.contrib import admin

from .models import Conversation, Participant


class ParticipantInline(admin.TabularInline):
    model = Participant
    extra = 1


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_by", "created_at")
    list_filter = ("created_at",)
    search_fields = ("name", "slug")
    readonly_fields = ("id", "slug", "created_at", "updated_at")
    inlines = [ParticipantInline]


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ("user", "conversation", "role", "joined_at")
    list_filter = ("role", "joined_at")
    search_fields = ("user__email", "conversation__name")
