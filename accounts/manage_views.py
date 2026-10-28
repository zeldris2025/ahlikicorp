"""Staff portal screens for reviewing trade account applications.

These live here rather than in products.manage_views because they are an
accounts concern; they are wired into the same ``manage`` URL namespace so the
portal stays one place.

Approval is restricted to the Admin role: it creates a login and emails out a
password, which is a wider power than maintaining the catalogue.
"""

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import DetailView, ListView

from .models import CustomerApplication
from .permissions import AdminOnlyMixin, is_admin
from .services import approve_application, reject_application


class ApplicationListView(AdminOnlyMixin, ListView):
    model = CustomerApplication
    template_name = 'manage/application_list.html'
    context_object_name = 'applications'
    paginate_by = 25

    def get_queryset(self):
        queryset = CustomerApplication.objects.select_related('user', 'reviewed_by')
        status = self.request.GET.get('status', CustomerApplication.Status.PENDING)
        if status in CustomerApplication.Status.values:
            queryset = queryset.filter(status=status)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status'] = self.request.GET.get('status', CustomerApplication.Status.PENDING)
        context['counts'] = {
            value: CustomerApplication.objects.filter(status=value).count()
            for value, _ in CustomerApplication.Status.choices
        }
        return context


class ApplicationDetailView(AdminOnlyMixin, DetailView):
    model = CustomerApplication
    template_name = 'manage/application_detail.html'
    context_object_name = 'application'


def application_decide(request, pk):
    """Approve or decline one application.

    POST only: both outcomes send email and one creates an account, so neither
    may happen because a link was followed or a page was prefetched.
    """
    if not is_admin(request.user):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied('Approving accounts is restricted to administrators.')

    if request.method != 'POST':
        return redirect('manage:application_detail', pk=pk)

    application = get_object_or_404(CustomerApplication, pk=pk)
    notes = request.POST.get('review_notes', '').strip()
    if notes != application.review_notes:
        application.review_notes = notes
        application.save(update_fields=['review_notes'])

    decision = request.POST.get('decision')

    if decision == 'approve':
        if application.user_id:
            messages.warning(request, f'{application.full_name} already has an account.')
        else:
            user, _ = approve_application(application, reviewer=request.user)
            messages.success(
                request,
                f'Approved {application.full_name}. Sign-in details were emailed to {application.email}.',
            )
    elif decision == 'decline':
        if application.status == CustomerApplication.Status.APPROVED:
            messages.warning(request, 'That application was already approved; decline it in Django Admin if this is wrong.')
        else:
            reject_application(
                application,
                reviewer=request.user,
                notify=request.POST.get('notify') == 'on',
                include_notes=request.POST.get('include_notes') == 'on',
            )
            messages.success(request, f'Declined the application from {application.full_name}.')
    else:
        messages.error(request, 'No decision was given.')

    return redirect('manage:application_list')
