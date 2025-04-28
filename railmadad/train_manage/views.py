from django.shortcuts import render
from .utils import decoder
import os
from django.http import JsonResponse, HttpResponse
from rest_framework.decorators import api_view
from django.contrib.auth.hashers import make_password, check_password
from pymongo import MongoClient
from uuid import uuid4
from .app_mail import register_email
from rest_framework.decorators import api_view
from django.http import JsonResponse
from datetime import datetime, timezone, timedelta
import jwt
from django.conf import settings

database_name = "Rail_madad"
manager_collection = "user_manager"
journey_collection = "journey"
complaint_collection = "complaints"
passenger_collection = "user_passenger"
user_idgen = lambda: uuid4().hex[:12]

def connection():
    client = MongoClient(os.getenv("HOST"))
    db = client.get_database(f'{database_name}')
    return db


@api_view(['POST'])
def register(request):
    db = connection()
    collection = db.get_collection(f'{manager_collection}')
    if request.method == "POST":
        required_fields = ["username", "email", "password", "phonenumber"]
        # Check if all fields are present
        if not all(request.data.get(field) for field in required_fields):
            return JsonResponse({"error": "Missing required fields"}, status=400)

        if collection.find_one({"email": request.data.get("email")}):
            return JsonResponse({"error": "account already exists"}, status=400)

        manager_data = {
            "manager_id": f"{request.data.get('username')}_"+user_idgen()[:6],
            "user_id": user_idgen(),
            "username": request.data.get('username'),
            "email": request.data.get("email"),
            "password": make_password(password=request.data.get("password"),hasher="default"),
            "phonenumber": str(request.data.get('phonenumber'))
                    }
        email = request.data.get('email')
        if not collection.find_one({"email": email}):
            collection.insert_one(manager_data)
            register_email(email)
        else:
            return JsonResponse({"error": "account already exits"})
        db.client.close()
        return JsonResponse({"status": "registeration successfull!", "manager_id": manager_data['manager_id']},status= 201)



@api_view(['POST'])
def login(request):
    db = connection()
    collection = db.get_collection(manager_collection)
    if request.method == "POST":
        usermail = request.data.get("email")
        password = request.data.get("password")
        temp = collection.find_one({"email": usermail},{"_id":0})
        if usermail == "admin@gmail.com" and password == "1234":
            db.client.close()
            return JsonResponse({"message": "dummy Login successful", "status": "success","pass":password})
        elif temp:
            if check_password(password,temp.get("password")):
                user_id = temp.get("user_id")
                username = temp.get("username")

                # Create access and refresh tokens manually
                access_payload = {
                    'user_id': user_id,
                    'manager_id': temp.get("manager_id"),
                    'email': usermail,
                    'username': username,
                    'exp': datetime.now(timezone.utc) + timedelta(minutes=120),  # access token expires in 15 mins
                    'iat': datetime.now(timezone.utc)
                }
                access_token = jwt.encode(access_payload, settings.SECRET_KEY, algorithm='HS256')

                refresh_payload = {
                    'user_id': user_id,
                    'email': usermail,
                    'exp': datetime.now(timezone.utc) + timedelta(days=7),  # refresh token expires in 7 days
                    'iat': datetime.now(timezone.utc)
                }
                refresh_token = jwt.encode(refresh_payload, settings.SECRET_KEY, algorithm='HS256')

                db.client.close()
                return JsonResponse({
                    "message": f"{username}'s Login successful",
                    "status": "success",
                    "user_id": user_id,
                    "access": access_token,
                    # "refresh": refresh_token
                })

            else:
                return JsonResponse({"message": f"{temp.get('username')}'s Login failed", "status": "wrong credentials"})
        else:
            db.client.close()
            return JsonResponse({"message": "Invalid credentials", "status": "error"}, status=400)
    db.client.close()
    return JsonResponse({"error": "Invalid request method"}, status=405)


def verify(request):
    return HttpResponse("verify")


@api_view(["POST"])
def start_journey(request):

    decoded = decoder(request)

    if 'error' in decoded:
        return JsonResponse({"error": decoded.get('error')})

    usermail = decoded.get('email')
    try:
        db = connection()
        Journey_collection = db.get_collection(journey_collection)
        Manager_collection = db.get_collection(manager_collection)
        manager = Manager_collection.find_one({"email": usermail},{"_id":0,"username":1,"phonenumber":1})

        if not manager:
            return JsonResponse({"error": "Manager not found or invalid mail id"}, status=400)

        data = {
            "train_name": request.data.get("train_name"),
            "train_number": request.data.get("train_number"),
            "train_manager_name": manager.get("username"),
            "train_manager_number": manager.get("phonenumber"),
            "manager_id": request.data.get("manager_id"),
            "department_details": {
                "medical": {
                    "head": request.data.get("medical_head_name"),
                    "head_number": request.data.get("medical_head_number")
                },
                "electrical": {
                    "head": request.data.get("electrical_head_name"),
                    "head_number": request.data.get("electrical_head_number")
                },
                "security": {
                    "head": request.data.get("security_head_name"),
                    "head_number": request.data.get("security_head_number")
                },
                "emergency": {
                    "head": request.data.get("emergency_head_name"),
                    "head_number": request.data.get("emergency_head_number")
                },
                "general_staff": {
                    "head": request.data.get("general_staff_head_name"),
                    "head_number": request.data.get("general_staff_head_number")
                }
            },
            "complaints": []
        }

        # Ensure all required fields are present
        if not all([data["train_name"], data["train_number"], data["manager_id"]]):
            return JsonResponse({"error": "Missing required train details"}, status=400)

        Journey_collection.insert_one(data)
        return JsonResponse({"status": "details saved"}, status=201)
    except Exception as e:
        return JsonResponse({"error": "something went wrong"+f"error --> {e}"}, status=400)

    finally:
        db.client.close()



@api_view(["PUT"])
def set_status(request):

    decoded = decoder(request)

    status_to_set = request.data.get("status_to_set")
    manager_id = decoded.get("manager_id")
    complaint_id = request.data.get("complaint_id")

    # Step 1: Validate required fields
    if not all([status_to_set, manager_id, complaint_id]):
        return JsonResponse({"error": "Missing required fields"}, status=400)

    try:
        db = connection()
        Journey_collection = db.get_collection(journey_collection)
        Complaint_collection = db.get_collection(complaint_collection)
        # Passenger_collection = db.get_collection(passenger_collection)

        # Step 2: Update status in Journey collection
        journey_result = Journey_collection.update_one(
            {
                "manager_id": manager_id,
                "complaints.compliant_id": complaint_id  # Find document where this complaint_id exists
            },
            {
                "$set": {
                    "complaints.$.status": status_to_set  # Update the matched complaint's status
                }
            }
        )

        # Step 3: Update status in Complaint collection
        complaint_result = Complaint_collection.update_one(
            {
                "complaint_id": complaint_id
            },
            {
                "$set": {
                    "status": status_to_set
                }
            }
        )
        # Passenger_collection.update_one({"user_id": })
        # Step 4: Check if any document was actually updated
        if journey_result.modified_count == 0 and complaint_result.modified_count == 0:
            return JsonResponse({"message": "No matching document found or already updated"}, status=404)

        return JsonResponse({"status": "updated successfully"}, status=200)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
