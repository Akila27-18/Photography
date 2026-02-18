from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from django.shortcuts import get_object_or_404
from .models import Invoice

def download_invoice(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)

    html_string = render_to_string(
        "invoice_pdf.html",
        {"invoice": invoice}
    )

    html = HTML(string=html_string)
    pdf = html.write_pdf()

    response = HttpResponse(pdf, content_type="application/pdf")
    response['Content-Disposition'] = f'attachment; filename="{invoice.invoice_number}.pdf"'

    return response
