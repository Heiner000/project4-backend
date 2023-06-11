from decimal import Decimal
import json
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import make_password
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum, F
from django.core.exceptions import ObjectDoesNotExist
from .utils import soup_data
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import User, Trade, Follower

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
            refresh = RefreshToken.for_user(user)
            res_data = {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "message": "User got in",
            }

            return JsonResponse(res_data, status=201)
        else:
            return JsonResponse({"error": "Unable to register user"}, status=400)


@csrf_exempt
def search_asset(request, ticker):
    if request.method == "GET":
        try:
            # assets = search_assets(ticker)
            assets = soup_data(ticker)
            return JsonResponse(assets, safe=False)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


def trade_history(request):
    if request.method == "GET":
        try:
            # retrieve user_id from request
            user_id = request.GET.get("user_id")
            if not user_id:
                raise KeyError("user_id not provided")

            # get the user
            user = User.objects.get(id=user_id)

            # get trades related to the user
            trades = Trade.objects.filter(user=user).values()

            return JsonResponse(list(trades), safe=False)
        except KeyError as e:
            return JsonResponse({"message": str(e)}, status=400)
        except User.DoesNotExist:
            return JsonResponse({"message": "User not found"}, status=404)
        except Trade.DoesNotExist:
            return JsonResponse({"message": "User trades not found"}, status=404)


@csrf_exempt
def trade_stock(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            new_trade = Trade(
                asset_type=data["asset_type"],
                ticker=data["ticker"],
                quantity=data["quantity"],
                price=data["price"],
                trade_type=data["trade_type"],
                user_id=data["user_id"],
            )

            new_trade.save()

            # get the user
            user = User.objects.get(id=data["user_id"])

            # calculate the total cost or gain from the trade
            total = Decimal(data["price"] * data["quantity"])

            # update the user's funds
            if data["trade_type"] == "SELL":
                user.funds += total
            elif data["trade_type"] == "BUY":
                user.funds -= total

            # save the updated user info
            user.save()

            print("new funds:", user.funds)

            return JsonResponse(
                {"message": "Trade added successfully", "funds": user.funds}, status=201
            )
        except Exception as e:
            return JsonResponse({"message": str(e)}, status=400)


@csrf_exempt
def add_to_watchlist(request):
    if request.method == "POST":
        try:
            print(request.body)
            data = json.loads(request.body)
            print(data)
            user_id = data.get("user_id")
            new_stock = data.get("new_stock")
            user = User.objects.get(id=user_id)

            if user.watchlist is None:
                user.watchlist = {}

            user.watchlist.append(new_stock)
            user.save()

            return JsonResponse({"message": "Stock added successfully"}, status=201)
        except User.DoesNotExist:
            return JsonResponse({"message": "User not found"}, status=404)
        except Exception as e:
            return JsonResponse({"message": str(e)}, status=400)


@csrf_exempt
def remove_watchlist(request, ticker, userId):
    if request.method == "DELETE":
        print(ticker)
        print(userId)
        try:
            user = User.objects.get(id=userId)
            user.watchlist.remove(ticker)
            user.save()
            return JsonResponse("good job removing it", safe=False)
        except ObjectDoesNotExist:
            return JsonResponse({"error": "User not found"}, safe=False)


def array_watchlist(request):
    if request.method == "GET":
        try:
            user_id = request.GET.get("user_id")
            user = User.objects.get(id=user_id)
            watchlist = user.watchlist
            watchlist_data = []
            for ticker in watchlist:
                ticker_data = soup_data(ticker)
                watchlist_data.append({"ticker": ticker})
            return JsonResponse(watchlist_data, safe=False)
        except Exception as e:
            return JsonResponse({"message": str(e)}, status=400)


def user_watchlist(request):
    if request.method == "GET":
        try:
            user_id = request.GET.get("user_id")
            user = User.objects.get(id=user_id)
            watchlist = user.watchlist

            # fetch each ticker's data using the soup_data function
            watchlist_data = []
            for ticker in watchlist:
                ticker_data = soup_data(ticker)
                watchlist_data.append({"ticker": ticker, "percentage": ticker_data[2]})

            return JsonResponse(watchlist_data, safe=False)
        except Exception as e:
            return JsonResponse({"message": str(e)}, status=400)


def get_user(request):
    if request.method == "GET":
        try:
            user_id = request.GET.get("user_id")
            print(user_id)
            user = User.objects.get(id=user_id)
            user_data = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "funds": user.funds,
                "zip_code": user.zip_code,
            }
            return JsonResponse(user_data, safe=False)
        except Exception as e:
            return JsonResponse({"message": str(e)}, status=400)


def user_shares(request):
    if request.method == "GET":
        try:
            # retrieve user from request
            user_id = request.GET.get("user_id")
            user = User.objects.get(id=user_id)

            # retrieve ticker from request (if sent)
            ticker = request.GET.get("ticker", None)

            # get user's trades of that ticker
            trades = Trade.objects.filter(user=user)
            if ticker:
                trades = trades.filter(ticker=ticker)

            # calculate total buy quantity
            buy_quantity = (
                trades.filter(trade_type="BUY").aggregate(
                    total_quantity=Sum("quantity")
                )["total_quantity"]
                or 0
            )

            # calculate total sell quantity
            sell_quantity = (
                trades.filter(trade_type="SELL").aggregate(
                    total_quantity=Sum("quantity")
                )["total_quantity"]
                or 0
            )

            # calculate the difference for total shares
            total_shares_owned = buy_quantity - sell_quantity

            # return the total shares
            return JsonResponse({"total_shares_owned": total_shares_owned})

        except Exception as e:
            return JsonResponse({"message": str(e)}, status=400)


@csrf_exempt
def update_funds(request):
    if request.method == "PUT":
        data = json.loads(request.body)
        user_id = data["userId"]
        funds = data["funds"]
        user = User.objects.get(id=user_id)
        print("old funds", user.funds)
        user.funds = funds
        user.save()
        return JsonResponse({"msg": "success"})


def user_all_shares(request):
    if request.method == "GET":
        try:
            # retrieve user from request
            user_id = request.GET.get("user_id")
            user = User.objects.get(id=user_id)

            # get user's trades
            trades = Trade.objects.filter(user=user)

            # get unique tickers
            tickers = trades.values_list("ticker", flat=True).distinct()

            total_shares_owned_list = []

            for ticker in tickers:
                # filter trades for current ticker
                ticker_trades = trades.filter(ticker=ticker)

                # calculate total buy quantity
                buy_quantity = (
                    ticker_trades.filter(trade_type="BUY").aggregate(
                        total_quantity=Sum("quantity")
                    )["total_quantity"]
                    or 0
                )

                # calculate total sell quantity
                sell_quantity = (
                    ticker_trades.filter(trade_type="SELL").aggregate(
                        total_quantity=Sum("quantity")
                    )["total_quantity"]
                    or 0
                )

                # calculate the difference for total shares
                total_shares_owned = buy_quantity - sell_quantity

                # append ticker and total shares to the list
                total_shares_owned_list.append({ticker: total_shares_owned})

            # return the total shares list
            return JsonResponse(total_shares_owned_list, safe=False)

        except Exception as e:
            return JsonResponse({"message": str(e)}, status=400)


def user_portfolio_values(request):
    if request.method == "GET":
        try:
            # retrieve user from request
            user_id = request.GET.get("user_id")
            user = User.objects.get(id=user_id)

            # gett user's trades
            trades = Trade.objects.filter(user=user)

            # get unique tickers
            tickers = trades.values_list("ticker", flat=True).distinct()

            portfolio_value_list = []
            unrealized_change_percentage_list = []
            total_portfolio_value = Decimal(0)
            total_cost_basis = Decimal(0)

            for ticker in tickers:
                # filter trades for current ticker
                ticker_trades = trades.filter(ticker=ticker)

                # calculate total buy quantity
                buy_quantity = (
                    ticker_trades.filter(trade_type="BUY").aggregate(
                        total_quantity=Sum("quantity")
                    )["total_quantity"]
                    or 0
                )

                # calculate total sell quantity
                sell_quantity = (
                    ticker_trades.filter(trade_type="SELL").aggregate(
                        total_quantity=Sum("quantity")
                    )["total_quantity"]
                    or 0
                )

                # calculate the difference for total shares
                total_shares_owned = buy_quantity - sell_quantity

                # compute the average cost basis
                total_cost = ticker_trades.filter(trade_type="BUY").aggregate(
                    total_cost=Sum(F("quantity") * F("price"))
                )["total_cost"] or Decimal(0)
                avg_cost_per_share = (
                    total_cost / buy_quantity if buy_quantity != 0 else Decimal(0)
                )

                # add total cost to total cost basis
                total_cost_basis += total_cost

                # get teh current price for the ticker
                asset_info = soup_data(ticker)
                current_price = Decimal(asset_info[0][1].replace(",", ""))

                # calculate unrealized gain/loss percentage
                unrealized_change = (
                    round(((current_price - avg_cost_per_share) / avg_cost_per_share) * 100, 2,)
                    if avg_cost_per_share != 0
                    else Decimal(0)
                )
                unrealized_change_percentage_list.append(
                    {ticker: str(unrealized_change)}
                )
                # print(unrealized_change_percentage_list)

                # calculate the total value for this ticker and append to portfolio list
                total_value = current_price * total_shares_owned
                portfolio_value_list.append({ticker: (f"{total_value:,.2f}")})

                # update total portfolio value
                total_portfolio_value += total_value
                # print('total port value: ', total_portfolio_value)

                # calculate total portfolio gain/loss percentage
                total_portfolio_gain = (
                    (total_portfolio_value - total_cost_basis) / total_cost_basis * 100
                    if total_cost_basis != 0
                    else Decimal(0)
                )

                total_portfolio_gain_percentage = f"{total_portfolio_gain:.2f} %"

            # return the portfolio values list & total portfolio value
            return JsonResponse(
                {
                    "portfolio_values": portfolio_value_list,
                    "total_portfolio_value": (f"{total_portfolio_value:,.2f}"),
                    "unrealized_change_percentage": unrealized_change_percentage_list,
                    "total_portfolio_gain_percentage": str(total_portfolio_gain_percentage),
                },
                safe=False,
            )

        except Exception as e:
            return JsonResponse({"message": str(e)}, status=400)


@api_view(["GET"])
def users_and_stocks(request):
    try:
        # fetch all users
        users = User.objects.all()

        users_and_stocks = []

        # iterate over each user
        for user in users:
            # fetch the user's trades
            trades = Trade.objects.filter(user=user)

            # get unique tickers from users trades
            tickers = trades.values_list("ticker", flat=True).distinct()

            users_and_stocks.append(
                {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "zip_code": user.zip_code,
                    "stocks": list(tickers),
                }
            )

        return JsonResponse(users_and_stocks, safe=False)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def follow_user(request, user_id, followed_user_id):
    print(f"Request method: {request.method}")

    if request.method == "POST":
        try:
            user = User.objects.get(id=user_id)
            followed_user = User.objects.get(id=followed_user_id)

            follower = Follower(user=user, followed_user=followed_user)
            follower.save()

            return JsonResponse({"message": "Followed successfully"}, status=200)
        except User.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    elif request.method == "DELETE":
        try:
            user = User.objects.get(id=user_id)
            followed_user = User.objects.get(id=followed_user_id)

            follower = Follower.objects.get(user=user, followed_user=followed_user)
            follower.delete()

            return JsonResponse({"message": "Unfollowed successfully"}, status=200)
        except Follower.DoesNotExist:
            return JsonResponse(
                {"error": "Follower relationship not found"}, status=404
            )
        except User.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


def followers(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)

    followers = Follower.objects.filter(user=user)

    followers_data = []
    for follower in followers:
        followed_user = follower.followed_user
        stocks = followed_user.trades.values_list("ticker", flat=True).distinct()
        followers_data.append(
            {
                "id": followed_user.id,
                "username": followed_user.username,
                "stocks": list(stocks),
            }
        )

    return JsonResponse(followers_data, safe=False)
