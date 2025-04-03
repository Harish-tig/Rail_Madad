from django.shortcuts import render

import os
from django.http import JsonResponse, HttpResponse
from rest_framework.decorators import api_view
from django.contrib.auth.hashers import make_password, check_password
from pymongo import MongoClient
from uuid import uuid4
from .app_mail import register_email


database_name = "Rail_madad"
manager_collection = "user_manager"
journey_collection = "journey"
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


#using dummy login as of now.
@api_view(['POST'])
def login(request):
    db = connection()
    collection = db.get_collection(manager_collection)
    if request.method == "POST":
        # uuid = request.data.get("userid") #TODO to add uuid
        # username = request.data.get("username")
        usermail = request.data.get("email")
        password = request.data.get("password")
        temp = collection.find_one({"email": usermail},{"_id":0,"username":1,"password":1})
        if usermail == "admin@gmail.com" and password == "1234":
            db.client.close()
            return JsonResponse({"message": "dummy Login successful", "status": "success","pass":password})
        elif temp:
            if check_password(password,temp.get("password")):
                db.client.close()
                return JsonResponse({"message": f"{temp.get('username')}'s Login successful", "status": "success"})
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
    try:
        db = connection()
        Journey_collection = db.get_collection(journey_collection)
        Manager_collection = db.get_collection(manager_collection)
        manager = Manager_collection.find_one({"manager_id": request.data.get("manager_id")},{"_id":0,"username":1,"phonenumber":1})

        if not manager:
            return JsonResponse({"error": "Manager not found or invalid manager ID"}, status=400)

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
