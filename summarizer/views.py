from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from .serializers import UserSerializer, SummarySerializer, SummaryHistorySerializer
from .utils import summarize_text
from .models import SummaryHistory, UserProfile
from reportlab.pdfgen import canvas

class RegisterView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # UserProfile is created automatically with role 'user'
            return Response({'message': 'User registered successfully.'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SummarizeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SummarySerializer(data=request.data)
        if serializer.is_valid():
            input_text = serializer.validated_data['input_text']
            summary = summarize_text(input_text)
            SummaryHistory.objects.create(user=request.user, input_text=input_text, summary_text=summary)
            return Response({'summary': summary}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        # Download latest summary as PDF (A4, multiline)
        latest = SummaryHistory.objects.filter(user=request.user).order_by('-created_at').first()
        if not latest:
            return Response({'error': 'No summary found.'}, status=status.HTTP_404_NOT_FOUND)
        import io
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        y = height - 30
        p.setFont("Helvetica", 12)
        p.drawString(30, y, "Summary:")
        y -= 20
        for line in latest.summary_text.splitlines():
            p.drawString(30, y, line)
            y -= 15
            if y < 40:
                p.showPage()
                y = height - 30
                p.setFont("Helvetica", 12)
        p.save()
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="summary.pdf"'
        return response

class HistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        summaries = SummaryHistory.objects.filter(user=request.user)[:5]
        serializer = SummaryHistorySerializer(summaries, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request):
        # Delete all history
        SummaryHistory.objects.filter(user=request.user).delete()
        return Response({'message': 'History deleted.'}, status=status.HTTP_204_NO_CONTENT)

class HistoryDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            summary = SummaryHistory.objects.get(pk=pk, user=request.user)
            summary.delete()
            return Response({'message': 'Summary deleted.'}, status=status.HTTP_204_NO_CONTENT)
        except SummaryHistory.DoesNotExist:
            return Response({'error': 'Summary not found.'}, status=status.HTTP_404_NOT_FOUND)

    def get(self, request, pk):
        try:
            summary = SummaryHistory.objects.get(pk=pk, user=request.user)
            serializer = SummaryHistorySerializer(summary)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except SummaryHistory.DoesNotExist:
            return Response({'error': 'Summary not found.'}, status=status.HTTP_404_NOT_FOUND)

class DownloadSummaryPDFView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            summary = SummaryHistory.objects.get(pk=pk, user=request.user)
        except SummaryHistory.DoesNotExist:
            return Response({'error': 'Summary not found.'}, status=status.HTTP_404_NOT_FOUND)
        import io
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_JUSTIFY
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=30, rightMargin=30, topMargin=30, bottomMargin=30)
        styles = getSampleStyleSheet()
        justify_style = ParagraphStyle('Justify', parent=styles['Normal'], alignment=TA_JUSTIFY, fontName='Helvetica', fontSize=11, leading=15)
        title_style = ParagraphStyle('Title', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=13, spaceAfter=10)
        elements = []
        elements.append(Paragraph("Original Input:", title_style))
        elements.append(Paragraph(summary.input_text.replace('\n', '<br/>'), justify_style))
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("Summary:", title_style))
        elements.append(Paragraph(summary.summary_text.replace('\n', '<br/>'), justify_style))
        doc.build(elements)
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="summary_{pk}.pdf"'
        return response