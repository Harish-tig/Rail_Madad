import os

from django.http import JsonResponse, HttpResponse
from rest_framework.decorators import api_view
from django.contrib.auth.hashers import make_password, check_password
from pymongo import MongoClient
from uuid import uuid4
from .app_mail import register_email


database_name = "Rail_madad"
passenger_collection = "user_passenger"
complaints_collection = "complaints"
pnr_collection = "pnr"
journey_collection = "journey"
user_idgen = lambda: uuid4().hex[:12]


def home(request):
    return HttpResponse("WELCOME TO DJANGO SERVER WE ARE BUILDING AN APP FOR RAIL MADAD")


def connection():
    client = MongoClient(os.getenv("HOST"))
    db = client.get_database(f'{database_name}')
    return db


@api_view(['POST'])
def register(request):
    db = connection()
    collection = db.get_collection(f'{passenger_collection}')
    if request.method == "POST":
        required_fields = ["username", "email", "password", "phonenumber"]

        # Check if all fields are present
        if not all(request.data.get(field) for field in required_fields):
            return JsonResponse({"error": "Missing required fields"}, status=400)

        passenger_data = {
            "user_id": user_idgen(),
            "username": request.data.get('username'),
            "email": request.data.get("email"),
            "password": make_password(password=request.data.get("password"),hasher="default"),
            "phonenumber": str(request.data.get('phonenumber')),
            "complaint_raised": [], #shall have collection of raised complaints though out his life
            "pnr": None,
        }
        email = request.data.get('email')
        if not collection.find_one({"email": email}):
            collection.insert_one(passenger_data)
            register_email(email)

        else:
            return JsonResponse({"error": "account already exits"})
        db.client.close()
        return JsonResponse({"status": "registeration successfull!"},status= 201)


#using dummy login as of now.
@api_view(['POST'])
def login(request):
    db = connection()
    collection = db.get_collection(passenger_collection)
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


@api_view(['POST'])
def raise_complaint(request):
    try:
        pnr = request.data.get("pnr")
        email = request.data.get("email")
        complaint_type = request.data.get("complaint_type")
        complaint_description = request.data.get("complaint_description")

        if not all([pnr, email, complaint_type, complaint_description]):  # Ensure all fields exist
            return JsonResponse({"error": "Missing required fields"}, status=400)

        db = connection()
        Passenger_collection = db.get_collection(passenger_collection)
        Pnr_collection = db.get_collection(pnr_collection)
        Complaint_collection = db.get_collection(complaints_collection)
        Journey_collection  = db.get_collection(journey_collection)



        # Fetch user data
        user_data = Passenger_collection.find_one({"email": email})
        if not user_data:
            return JsonResponse({"error": "User not found"}, status=404)

        # Fetch PNR data
        pnr_data = Pnr_collection.find_one({"Pnr": pnr})
        if not pnr_data:
            return JsonResponse({"error": "PNR not found"}, status=404)
        train_number = str(pnr_data.get("TrainNo"))

        current_train_manager_data = Journey_collection.find_one({"train_number": train_number})
        if not current_train_manager_data:
            return JsonResponse({"error": "Train manager not found"}, status=404)

        manager_name = current_train_manager_data.get("train_manager_name")
        manager_id = current_train_manager_data.get("manager_id")
        manager_number = current_train_manager_data.get("train_manager_number")

        complaint_data = {
            "complaint_id": user_idgen()[:6],
            "train_number": str(train_number),
            "reported_by": {
                "username": user_data.get("username"),
                "user_id": user_data.get("user_id"),  # Fix: It should be userid, not username
                "pnr": str(pnr)
            },
            "train_manager": {
                "name": manager_name,
                "manager_id": manager_id,
            },
            "complaint_type": complaint_type,  # security, emergency, cleanliness, overcrowding, others
            "complaint_description": complaint_description,
            "status": "reported"  # Default status
        }

        # Insert into MongoDB
        try:
            Complaint_collection.insert_one(complaint_data)
            Passenger_collection.update_one({"email": email}, {"$push": {"complaint_raised":{"complaint_id": complaint_data["complaint_id"],"complaint_type":complaint_type, "status": complaint_data['status'],"manager_number":manager_number}}})
            Journey_collection.update_one({"train_number":str(train_number)},{"$push": {"complaints": {"compliant_id": complaint_data["complaint_id"],"complaint_type":complaint_type, "status": complaint_data['status']}}})
            db.client.close()
            return JsonResponse({"status": "Complaint raised successfully"}, status=201)
        except Exception as e:
            db.client.close()
            return JsonResponse({"error": "Internal Server Error", "details": str(e)}, status=500)

    except Exception as e:
        return JsonResponse({"error": "Internal Server Error", "details": str(e)}, status=500)


