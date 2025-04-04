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
journeys_collection = db['journeys']  # Assuming you have a journeys collection

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
    complaints = complaints_collection.find({'reported_by.user_id': user_id})
    
    # Format the response with only required fields
    result = []
    for complaint in complaints:
        result.append({
            'complaint_id': complaint['complaint_id'],
            'complaint_type': complaint['complaint_type'],
            'complaint_description': complaint['complaint_description'],
            'status': complaint['status']
        })
    
    return Response(result)

@api_view(['GET'])
def get_user_journey_details(request):
    train_number = request.query_params.get('train_number', None)
    
    if not train_number:
        return Response(
            {"error": "User ID is required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if user exists
    user = users_collection.find_one({'userid': train_number})
    if not user:
        return Response(
            {"error": "User not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Find the user's current journey (you might need to adjust this query based on your schema)
    journey = journeys_collection.find_one({'train_number': train_number})
    
    if not journey:
        return Response(
            {"error": "No journey found for this user"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Format the response to match your expected structure
    response_data = {
        "_id": str(journey['_id']),
        "train_name": journey.get('train_name', ''),
        "train_number": journey.get('train_number', ''),
        "train_manager_name": journey.get('train_manager_name', ''),
        "train_manager_number": journey.get('train_manager_number', ''),
        "manager_id": journey.get('manager_id', ''),
        "department_details": journey.get('department_details', {}),
        "complaints": list(complaints_collection.find(
            {'reported_by.train_number': train_number},
            {'complaint_id': 1, 'complaint_type': 1, 'status': 1, '_id': 0}
        ))
    }
    
    return Response(response_data)