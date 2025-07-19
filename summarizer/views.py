from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from .serializers import UserSerializer, SummarySerializer, SummaryHistorySerializer
from .utils import summarize_text
from .models import SummaryHistory
import io
from reportlab.pdfgen import canvas

class RegisterView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SummarizeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SummarySerializer(data=request.data)
        if serializer.is_valid():
            input_text = serializer.validated_data['input_text']
            if len(input_text.strip()) == 0:
                return Response({"error": "Input text cannot be empty"}, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                summary = summarize_text(input_text)
                # Save to history
                SummaryHistory.objects.create(
                    user=request.user,
                    input_text=input_text,
                    summary_text=summary
                )
                return Response({"summary": summary}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        # Download latest summary as PDF (A4, multiline)
        latest = SummaryHistory.objects.filter(user=request.user).order_by('-created_at').first()
        if not latest:
            return Response({"error": "No summary found."}, status=status.HTTP_404_NOT_FOUND)
        buffer = io.BytesIO()
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        y = height - 30
        p.setFont("Helvetica", 12)
        p.drawString(30, y, "Summary:")
        y -= 20
        for line in latest.summary_text.splitlines():
            for subline in [line[i:i+100] for i in range(0, len(line), 100)]:
                p.drawString(30, y, subline)
                y -= 15
                if y < 30:
                    p.showPage()
                    y = height - 30
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
        return Response({"message": "All history deleted."}, status=status.HTTP_200_OK)

class HistoryDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        # Delete single history by id
        try:
            history = SummaryHistory.objects.get(pk=pk, user=request.user)
            history.delete()
            return Response({"message": "History deleted."}, status=status.HTTP_200_OK)
        except SummaryHistory.DoesNotExist:
            return Response({"error": "History not found."}, status=status.HTTP_404_NOT_FOUND)

    def get(self, request, pk):
        # Download specific summary as PDF (A4, multiline)
        try:
            history = SummaryHistory.objects.get(pk=pk, user=request.user)
            buffer = io.BytesIO()
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.units import mm
            from reportlab.pdfgen import canvas
            p = canvas.Canvas(buffer, pagesize=A4)
            width, height = A4
            y = height - 30
            p.setFont("Helvetica", 12)
            p.drawString(30, y, "Summary:")
            y -= 20
            for line in history.summary_text.splitlines():
                for subline in [line[i:i+100] for i in range(0, len(line), 100)]:
                    p.drawString(30, y, subline)
                    y -= 15
                    if y < 30:
                        p.showPage()
                        y = height - 30
            p.save()
            buffer.seek(0)
            response = HttpResponse(buffer, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="summary_{pk}.pdf"'
            return response
        except SummaryHistory.DoesNotExist:
            return Response({"error": "History not found."}, status=status.HTTP_404_NOT_FOUND)