from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.urls import reverse


def send_company_invite_email(request, invite):
    invite_path = reverse('company_invite_accept', args=[invite.token])
    invite_url = request.build_absolute_uri(invite_path)

    context = {
        'company_name': invite.company.name,
        'admin_name': f'{invite.first_name} {invite.last_name}'.strip(),
        'admin_email': invite.email,
        'invite_url': invite_url,
        'expires_at': invite.expires_at,
        'invited_by_name': invite.invited_by.full_name if invite.invited_by else 'Platform Admin',
        'invited_by_email': invite.invited_by.email if invite.invited_by else '',
    }

    subject = f'You are invited as Company Admin for {invite.company.name}'
    html_body = render_to_string('emails/company_invite_email.html', context)
    text_body = strip_tags(html_body)
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com')

    try:
        message = EmailMultiAlternatives(subject, text_body, from_email, [invite.email])
        message.attach_alternative(html_body, 'text/html')
        message.send(fail_silently=False)
        return True, None
    except Exception as exc:
        return False, str(exc)
