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
train_manager_collection = "train_manager"
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
            "userid": user_idgen(),
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

from rest_framework.decorators import api_view
from django.http import JsonResponse
from pymongo import MongoClient

@api_view(['POST'])
def raise_complaint(request):
    try:
        pnr = request.data.get("pnr")
        email = request.data.get("email")
        type = request.data.get("type")
        description = request.data.get("description")

        if not all([pnr, email, type, description]):  # Ensure all fields exist
            return JsonResponse({"error": "Missing required fields"}, status=400)

        db = connection()
        pass_collection = db.get_collection(passenger_collection)
        Pnr_collection = db.get_collection(pnr_collection)
        comp_collection = db.get_collection(complaints_collection)
        train_manager  = db.get_collection(train_manager_collection)



        # Fetch user data
        user_data = pass_collection.find_one({"email": email})
        if not user_data:
            return JsonResponse({"error": "User not found"}, status=404)

        # Fetch PNR data
        pnr_data = Pnr_collection.find_one({"Pnr": pnr})
        if not pnr_data:
            return JsonResponse({"error": "PNR not found"}, status=404)

        train_number = str(pnr_data.get("TrainNo"))
        train_manager_data = train_manager.find_one({"train_number": train_number})

        if not train_manager_data:
            return JsonResponse({"error": "Train manager not found"}, status=404)

        manager_name = train_manager_data.get("manager_name")
        manager_id = train_manager_data.get("manager_id")

        complaint_data = {
            "complaint_id": user_idgen()[:6],
            "train_number": str(train_number),
            "reported_by": {
                "username": user_data.get("username"),
                "userid": user_data.get("userid"),  # Fix: It should be userid, not username
                "pnr": str(pnr)
            },
            "train_manager": {
                "name": manager_name,
                "manager_id": manager_id,
            },
            "type": type,  # security, emergency, cleanliness, overcrowding, others
            "description": description,
            "status": "reported"  # Default status
        }

        # Insert into MongoDB
        try:
            comp_collection.insert_one(complaint_data)
            pass_collection.update_one({"email": email}, {"$push": {"complaint_raised": complaint_data["complaint_id"]}})
            db.client.close()
            return JsonResponse({"status": "Complaint raised successfully"}, status=201)
        except Exception as e:
            db.client.close()
            return JsonResponse({"error": "Internal Server Error", "details": str(e)}, status=500)



    except Exception as e:
        return JsonResponse({"error": "Internal Server Error", "details": str(e)}, status=500)


