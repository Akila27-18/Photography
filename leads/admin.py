from django import forms
from django.contrib import admin, messages
from django.utils.safestring import mark_safe
from .models import Lead

class LeadAdminForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        event_start_date = cleaned_data.get('event_start_date')

        if status == Lead.STATUS_ACCEPTED and event_start_date:
            # Find other accepted events on the same date
            qs = Lead.objects.filter(
                status=Lead.STATUS_ACCEPTED,
                event_start_date=event_start_date
            )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                # Highlight the field in red
                self.fields['event_start_date'].widget.attrs.update(
                    {'style': 'border: 2px solid red; background-color: #ffe6e6;'}
                )

                event_list = ", ".join(f"{e.name} (ID: {e.pk})" for e in qs)
                # Add a warning message
                if self.request:
                    messages.warning(
                        self.request,
                        mark_safe(
                            f"⚠ You already have the following accepted event(s) on {event_start_date}: <b>{event_list}</b>. "
                            "Ensure you have enough staff to handle multiple events on the same day."
                        )
                    )

        return cleaned_data


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    form = LeadAdminForm
    list_display = ('name', 'event_start_date', 'status')
    list_filter = ('status', 'event_start_date')
    search_fields = ('name', 'email', 'event_type')

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Pass request to the form so messages can be shown
        class FormWithRequest(form):
            def __new__(cls, *args, **kwargs2):
                kwargs2['request'] = request
                return form(*args, **kwargs2)
        return FormWithRequest
