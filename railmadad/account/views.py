import os

from django.http import JsonResponse, HttpResponse
from rest_framework.decorators import api_view
from django.contrib.auth.hashers import make_password, check_password
from pymongo import MongoClient
from uuid import uuid4
from .app_mail import register_email


database_name = "Rail_madad"
passenger_collection = "passenger"
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
        passenger_data = {
            "userid": user_idgen(),
            "username": request.data.get('username'),
            "email": request.data.get("email"),
            "password": make_password(password=request.data.get("password"),hasher="default"),
            "phonenumber": request.data.get('number'),
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

