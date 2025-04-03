from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from pymongo import MongoClient
import json
from bson import json_util

# Connect to MongoDB
client = MongoClient('localhost', 27017)
db = client['Rail_madad']
complaints_collection = db['complaints']
users_collection = db['user_passenger']

@api_view(['GET'])
def get_user_all_complaints(request):
    user_id = request.query_params.get('user_id', None)
    
    if not user_id:
        return Response(
            {"error": "User ID is required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if user exists
    user = users_collection.find_one({'userid': user_id})
    if not user:
        return Response(
            {"error": "User not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Find all complaints for the user
    complaints = complaints_collection.find({'reported_by.userid': user_id})
    
    # Format the response with only required fields
    result = []
    for complaint in complaints:
        result.append({
            'complaint_id': complaint['complaint_id'],
            'type': complaint['type'],
            'description': complaint['description'],
            'status': complaint['status']
        })
    
    return Response(result)