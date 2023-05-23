import json
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.views.decorators.csrf import csrf_exempt
from .utils import soup_data
from rest_framework.response import Response
from rest_framework.decorators import (api_view)
from .models import Trade

User = get_user_model()

@api_view(["GET"])
def scrape_soup_data(request, ticker):
    data = soup_data(ticker)
    return Response(data)


@csrf_exempt
def register_view(request):
    if request.method == "POST":
        data = json.loads(request.body)
        username = data.get("username")
        password = make_password(data.get("password"))  # hash the password
        zip_code = data.get("zip_code")

        user = User.objects.create(
            username=username, password=password, zip_code=zip_code
        )
        if user:
            return JsonResponse({"message": "User registered successfully"}, status=201)
        else:
            return JsonResponse({"error": "Unable to register user"}, status=400)

@csrf_exempt
def create_trade(request):
    if request.method == "POST":
        data = json.loads(request.body)
        total_price = data.get("quantity") * data.get("price") # calculates total price for the trade
        if data.get("trade_type") == "BUY":
            if request.user.funds < total_price:
                return JsonResponse({"error": "Not enough funds for this trade"}, status=400)
            else:
                request.user.funds -= total_price # subtract total price from user's funds
                request.user.save()
        else: # trade_type is 'SELL'
            request.user.funds += total_price # add total price to user's funds
            request.user.save()
            
        trade = Trade.objects.create(
            user=request.user,
            asset_type=data.get("asset_type"),
            ticker=data.get("ticker"),
            quantity=data.get("quantity"),
            price=data.get("price"),
            trade_type=data.get("trade_type"),
        )
        if trade:
            return JsonResponse({"message": "Trade created successfully"}, status=201)
        else:
            return JsonResponse({"error": "Unable to create trade"}, status=400)

@csrf_exempt
def search_asset(request, ticker):
    if request.method == "GET":
        try:
            # assets = search_assets(ticker)
            assets = soup_data(ticker)
            return JsonResponse(assets, safe=False)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

def users_stocks(request):
    if request.method == 'GET':
        try:
            stocks = Trade.objects.all().values()
            print(stocks)
            return JsonResponse(list(stocks), safe=False)
        except Trade.DoesNotExist:
            return JsonResponse({"message": "User stocks not found"}, status=404)

@csrf_exempt
def add_stock(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            new_trade = Trade(
                asset_type=data['asset_type'],
                ticker=data['ticker'],
                quantity=data['quantity'],
                price=data['price'],
                trade_type=data['trade_type'],
                user_id=data['user_id']
            )

            new_trade.save()

            return JsonResponse({"message": "Stock added successfully"}, status=201)
        except Exception as e:
            return JsonResponse({"message": str(e)}, status=400)