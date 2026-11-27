import logging
from pathlib import Path
from email.utils import make_msgid
from email.message import MIMEPart
from email.mime.image import MIMEImage

import django
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.staticfiles import finders
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


class ReabitechPasswordResetForm(PasswordResetForm):
    """Recuperacao de senha com identidade visual REABITECH."""

    def send_mail(
        self,
        subject_template_name,
        email_template_name,
        context,
        from_email,
        to_email,
        html_email_template_name=None,
    ):
        context = context.copy()

        subject = render_to_string(
            subject_template_name,
            context,
        )

        subject = "".join(subject.splitlines())

        body = render_to_string(
            email_template_name,
            context,
        )

        message = EmailMultiAlternatives(
            subject=subject,
            body=body,
            from_email=from_email,
            to=[to_email],
        )

        if html_email_template_name:
            context["email_logo_cid"] = None

            try:
                logo_path = finders.find(
                    "images/logo-email.png"
                )

                if logo_path:
                    logo_data = Path(logo_path).read_bytes()
                    cid = make_msgid()

                    if django.VERSION >= (6, 0):
                        image = MIMEPart()
                        image.set_content(
                            logo_data,
                            maintype="image",
                            subtype="png",
                            disposition="inline",
                            cid=cid,
                        )
                    else:
                        image = MIMEImage(
                            logo_data,
                            _subtype="png",
                        )
                        image.add_header("Content-ID", cid)
                        image.add_header(
                            "Content-Disposition",
                            "inline",
                        )

                    message.attach(image)

                    context["email_logo_cid"] = cid[1:-1]

            except Exception:
                logger.warning(
                    "Nao foi possivel incorporar a logo.",
                    exc_info=True,
                )

            html = render_to_string(
                html_email_template_name,
                context,
            )

            message.attach_alternative(
                html,
                "text/html",
            )

        try:
            message.send()
        except Exception:
            logger.exception(
                "Falha no envio do email de recuperacao."
            )
