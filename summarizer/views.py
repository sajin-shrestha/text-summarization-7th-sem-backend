from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import UserSerializer, SummarySerializer, SummaryHistorySerializer
from .utils import summarize_text
from .models import SummaryHistory

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

class HistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        summaries = SummaryHistory.objects.filter(user=request.user)[:5]
        serializer = SummaryHistorySerializer(summaries, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)