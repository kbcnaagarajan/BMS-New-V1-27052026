from django.conf import settings
from django.core.mail import get_connection
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.urls import reverse
from user_management.models import EmailSettings


def _resolve_email_settings(company=None):
    scoped = None
    if company:
        scoped = EmailSettings.objects.filter(company=company, is_active=True).first()
    if scoped:
        return scoped
    return EmailSettings.objects.filter(company__isnull=True, is_active=True).first()


def _get_email_connection(company=None):
    cfg = _resolve_email_settings(company)
    if cfg:
        return get_connection(
            backend=cfg.backend or 'django.core.mail.backends.smtp.EmailBackend',
            host=cfg.host,
            port=cfg.port,
            username=cfg.host_user or None,
            password=cfg.host_password or None,
            use_tls=cfg.use_tls,
            use_ssl=cfg.use_ssl,
            fail_silently=False,
        ), (cfg.default_from_email or cfg.host_user or 'noreply@example.com')
    return get_connection(fail_silently=False), getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com')


def _send_email(subject, html_body, to_email, company=None):
    text_body = strip_tags(html_body)
    connection, from_email = _get_email_connection(company)
    message = EmailMultiAlternatives(
        subject, text_body, from_email, [to_email], connection=connection
    )
    message.attach_alternative(html_body, 'text/html')
    message.send(fail_silently=False)


def send_company_invite_email(request, invite):
    invite_url = request.build_absolute_uri(reverse('company_invite_accept', args=[invite.token]))

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
    try:
        _send_email(subject, html_body, invite.email, company=invite.company)
        return True, None
    except Exception as exc:
        return False, str(exc)


def send_client_portal_invite_email(request, invite):
    invite_url = request.build_absolute_uri(reverse('client_invite_accept', args=[invite.token]))

    context = {
        'client_name': invite.client.name,
        'invitee_name': f'{invite.first_name} {invite.last_name}'.strip(),
        'invitee_email': invite.email,
        'invite_url': invite_url,
        'expires_at': invite.expires_at,
        'invited_by_name': invite.invited_by.full_name if invite.invited_by else 'Company Admin',
        'invited_by_email': invite.invited_by.email if invite.invited_by else '',
    }
    subject = f'You are invited to Client Portal for {invite.client.name}'
    html_body = render_to_string('emails/client_portal_invite_email.html', context)

    try:
        _send_email(subject, html_body, invite.email, company=invite.client.company)
        return True, None
    except Exception as exc:
        return False, str(exc)
