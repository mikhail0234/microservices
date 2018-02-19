import json
import re
import logging
from django.views import View
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.http import QueryDict
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import HttpResponse
from django.shortcuts import render

from django.urls import reverse
from threading import Event

from requests.exceptions import ConnectionError


from .functions import ProductRequester
from .functions import CartRequester
from .functions import CheckoutRequester
from .functions import AuthRequester

from .queue import MyThread
from .queue import storage

from .conf import HOST_URL_CARD
from .conf import HOST_URL_CHECKOUT
from .conf import HOST_URL_PRODUCT
from .conf import HOST_URL_GATEWAY
from .conf import MAX_COOKIES_AGE
from .conf import HOST_URL_AUTH


logger = logging.getLogger(__name__)


stopFlag = Event()
thread = MyThread(stopFlag)
thread.start()


class BaseView(View):
    def __init__(self, product_host=HOST_URL_PRODUCT,
                 cart_host=HOST_URL_CARD,
                 checkout_host=HOST_URL_CHECKOUT, auth_host=HOST_URL_AUTH):

        self.product = ProductRequester(product_host, service_name="product")
        self.cart = CartRequester(cart_host, service_name="cart")
        self.checkout = CheckoutRequester(checkout_host, service_name="checkout")
        self.auth = AuthRequester(auth_host, service_name="auths")

    def error_response(self, status, json_body):
        return HttpResponse(status=status,
                            content=json.dumps(json_body),
                            content_type='application/json')



class ProductsListView(BaseView):
    def get(self, request):
        context = {}
        try:
            logger.info("GET ALL Products")
            page = request.GET.get('page', '1')
            match = re.match(r'\d+', page)

            if not match or page == '0':
                status_code = 400

                context['status_code'] = status_code
                context['error_short'] = u"Некорректный запрос страницы"
                context['error_description'] = u"Номер страницы должен быть положительным целым числом"
                return render(request, 'gateway/error.html', context, status=status_code)

            response =  self.product.product_get(page=page)
            if response.status_code == 200:
                response_json = json.loads(response.content)
                products = response_json["results"]
                print('\n products',products)
                context['products'] = products

            return render(request, 'gateway/product_list.html', context)

        except ConnectionError:
            status_code = 503
            context['status_code'] = status_code
            context['error_short'] = u"Сервис недоступен"
            context['error_description'] = u"Сервис продуктов временно недоступен"
            return render(request, 'gateway/error.html', context, status=status_code)


        except Exception as e:
            status_code = 500
            context['status_code'] = status_code
            context['error_short'] = u"Внутреняя ошибка сервера"
            context[
                'error_description'] = u"Что-то пошло не так, работоспособность будет восстановлена в ближайшее время"
            return render(request, 'gateway/error.html', context, status=status_code)



@method_decorator(csrf_exempt, name='dispatch')
class ProductDetailView(BaseView):
    def get(self, request, product_id):
        context = {}
        try:
            logger.info("GET One Product")
            # return self.product.product_get_one_json(product_id)
            one_product_json = self.product.product_get_one_json(product_id)
            error = one_product_json.get('detail')
            if error and error == 'Not found.':
                status_code = 404
                context['status_code'] = status_code
                context['error_short'] = u"Некорректный запрос страницы"
                context['error_description'] = u"Данный продукт не найден"
                return render(request, 'gateway/error.html', context, status=status_code)
            context['product'] = one_product_json

            return render(request, 'gateway/product_detail.html', context)

        except ConnectionError:
            status_code = 503
            context['status_code'] = status_code
            context['error_short'] = u"Сервис недоступен"
            context['error_description'] = u"Сервис продуктов временно недоступен"
            return render(request, 'gateway/error.html', context, status=status_code)
        except Exception as e:
            status_code = 500
            context['status_code'] = status_code
            context['error_short'] = u"Внутреняя ошибка сервера"
            context[
                'error_description'] = u"Что-то пошло не так, работоспособность будет восстановлена в ближайшее время"

            return render(request, 'gateway/error.html', context, status=status_code)




            # def delete(self, request, product_id):
    #     logger.info("Delete One Product")
    #
    #     rn = self.product.product_delete_one(product_id)
    #     cart_all_json = self.cart.cart_get_all_json()
    #
    #     for obj in cart_all_json:
    #         print('\n \n', obj)
    #         for i in obj["items"]:
    #             item_id = i["item_id"]
    #             if i["product_id"] == product_id:
    #
    #                 self.cart.delete_one(item_id)
    #     return rn
    #





# class CategoryListView(BaseView):
#     def get(self, request):
#         logger.info("GET ALL Categories")
#         return self.product.product_category_get()
#
#
# class CategoryDetailView(BaseView):
#     def get(self, request, category_id):
#         logger.info("GET One Category")
#         return self.product.category_get_one(category_id)
#
class CartListView(BaseView):
    def get(self, request):

        try:
            logger.info("GET ALL Carts")
            return self.cart.cart_get()


        except ConnectionError:

            status_code = 503
            context['status_code'] = status_code
            context['error_short'] = u"Сервис недоступен"
            context['error_description'] = u"Сервис корзины временно недоступен"
            return render(request, 'gateway/error.html', context, status=status_code)
        except Exception as e:
            status_code = 500
            error_data = {"server error": "internal server error"}
            return self.error_response(status_code, error_data)



@method_decorator(csrf_exempt, name='dispatch')
class CartDetailView(BaseView):
    def get(self, request, cart_id):
        context = {}

        access_token = request.COOKIES.get("access_token")
        refresh_token = request.COOKIES.get("refresh_token")

        print('access token', access_token)
        print('refresh token', refresh_token)
        try:
            token_is_valid = self.auth.check_access_token(access_token)
            print("Check access token:", token_is_valid)
            if not token_is_valid:
                print("Try to refresh access token")
                print("Old access:", access_token, "Old refresh:", refresh_token)
                access_token, refresh_token = self.auth.refresh_token(refresh_token)
                print("New access:", access_token, "New refresh:", refresh_token)
                if not access_token or not refresh_token:
                    print("Invalid access and refresh tokens, go to authorization")
                    print("Go to authorization link:", self.auth.create_authorization_link())
                    print('not passed')
                    # return HttpResponseRedirect(self.auth.create_authorization_link())
                    status_code = 403
                    context['status_code'] = status_code
                    context['error_short'] = u"Нет доступа"
                    context['error_description'] = u"У вас недостаточно прав, необходимо авторизоваться"
                    r = render(request, 'gateway/error.html', context, status=status_code)
                    r.set_cookie('access_token', access_token, max_age=MAX_COOKIES_AGE)
                    r.set_cookie('refresh_token', refresh_token, max_age=MAX_COOKIES_AGE)
                    return r


            print('passed', cart_id)
            logger.info("GET ONE CART")
            one_cart_json = self.cart.cart_get_one_json(cart_id)
            error = one_cart_json.get('detail')
            print('PASSSED', cart_id)
            print(one_cart_json)


            if error and error == 'Not found.':
                status_code = 404
                context['status_code'] = status_code
                context['error_short'] = u"Не найдено корзины"
                context['error_description'] = u"Невозможно отобразить корзины"
                return render(request, 'gateway/error.html', context, status=status_code)

            if one_cart_json.get("service not available"):
                status_code = 503
                context['status_code'] = status_code
                context['error_short'] = u"Сервис недоступен"
                context['error_description'] = u"Сервис корзины временно недоступен"
                return render(request, 'gateway/error.html', context, status=status_code)
            print("Vse ok:")
            for i in one_cart_json["items"]:
                product_id = i.get('product_id')

                logger.info("GET One Product")
                one_product_json = self.product.product_get_one_json(product_id)
                error = one_product_json.get('service not available')
                error2 = one_product_json.get('detail')

                if (error and error == 'connection error') :
                    pass
                elif (error2 and error2 == 'Not found.'):
                    pass
                else:
                    print('\n', one_product_json)
                    i["product"] = one_product_json
            context['cart_items'] = one_cart_json
            return render(request, 'gateway/cart_index.html', context, status=200)

        except ConnectionError:
            status_code = 503
            context['status_code'] = status_code
            context['error_short'] = u"Сервис недоступен"
            context['error_description'] = u"Сервис корзины временно недоступен"
            return render(request, 'gateway/error.html', context, status=status_code)

        except Exception as e:
            status_code = 500
            context['status_code'] = status_code
            context['error_short'] = u"Внутреняя ошибка сервера корзины"
            context[
                'error_description'] = u"Что-то пошло не так, работоспособность будет восстановлена в ближайшее время"
            return render(request, 'gateway/error.html', context, status=status_code)




    def post(self, request, cart_id):
        context = {}
        access_token = request.COOKIES.get("access_token")
        refresh_token = request.COOKIES.get("refresh_token")

        print('access token', access_token)
        print('refresh token', refresh_token)
        try:
            token_is_valid = self.auth.check_access_token(access_token)
            print("Check access token:", token_is_valid)
            if not token_is_valid:
                print("Try to refresh access token")
                print("Old access:", access_token, "Old refresh:", refresh_token)
                access_token, refresh_token = self.auth.refresh_token(refresh_token)
                print("New access:", access_token, "New refresh:", refresh_token)
                if not access_token or not refresh_token:
                    print("Invalid access and refresh tokens, go to authorization")
                    print("Go to authorization link:", self.auth.create_authorization_link())
                    print('not passed')
                    # return HttpResponseRedirect(self.auth.create_authorization_link())
                    status_code = 403
                    context['status_code'] = status_code
                    context['error_short'] = u"Нет доступа"
                    context['error_description'] = u"У вас недостаточно прав, необходимо авторизоваться"
                    r = render(request, 'gateway/error.html', context, status=status_code)
                    r.set_cookie('access_token', access_token, max_age=MAX_COOKIES_AGE)
                    r.set_cookie('refresh_token', refresh_token, max_age=MAX_COOKIES_AGE)
                    return r


            quantity = request.POST.get('quantity')
            match = re.match(r'\d+', quantity)
            if not match or quantity == '0':
                status_code = 400
                error_data = {"Validation error": "Quantity must be positive integer"}
                return self.error_response(status_code, error_data)

            product_id = request.POST.get('product_id')
            print(product_id)

            match = re.match(r'\d+', product_id)
            if not match or product_id == '0':
                status_code = 400
                error_data = {"Validation error": "Product_id must be positive integer"}
                return self.error_response(status_code, error_data)
            r = {'cart': cart_id, 'product_id': product_id, 'quantity': quantity}
            logger.info("POST ADD NEW PRODUCT")
            self.cart.cart_add(r)
            context['status_code'] = 200
            context['error_short'] = u""
            context['error_description'] = u"Продукт успешно добавился в корзину"
            return render(request, 'gateway/success.html', context)


        except ConnectionError:
            status_code = 503
            context['status_code'] = status_code
            context['error_short'] = u"Сервис недоступен"
            context['error_description'] = u"Сервис корзины временно недоступен"
            return render(request, 'gateway/error.html', context, status=status_code)

        except Exception as e:
            status_code = 500
            context['status_code'] = status_code
            context['error_short'] = u"Внутреняя ошибка сервера корзины"
            context[
                'error_description'] = u"Что-то пошло не так, работоспособность будет восстановлена в ближайшее время"
            return render(request, 'gateway/error.html', context, status=status_code)

        # resp_cart_check = self.cart.check()
        # print(resp_cart_check)
        # if (resp_cart_check.status_code != 200 and resp_cart_check.status_code != 404):
        #     resp_data = {
        #         "error": "service cart is not available"
        #     }
        #     return JsonResponse(resp_data)
        # else:
        #
        #     quantity = request.POST.get('quantity')
        #     print(quantity)
        #
        #     match = re.match(r'\d+', quantity)
        #     if not match or quantity == '0':
        #         status_code = 400
        #         error_data = {"Validation error": "Quantity must be positive integer"}
        #         return self.error_response(status_code, error_data)
        #
        #     product_id = request.POST.get('product_id')
        #     print(product_id)
        #
        #     match = re.match(r'\d+', product_id)
        #     if not match or product_id == '0':
        #         status_code = 400
        #         error_data = {"Validation error": "Product_id must be positive integer"}
        #         return self.error_response(status_code, error_data)
        #
        #     r = {'cart': cart_id, 'product_id': product_id, 'quantity': quantity}
        #     logger.info("POST ADD NEW PRODUCT")
        #     return self.cart.cart_add(r)


@method_decorator(csrf_exempt, name='dispatch')
class CartItem(BaseView):
    def get(self, request, item_id):
        try:
            logger.info("GET one Item")
            return self.cart.item_get_one(item_id)
        except ConnectionError:
            print("ConnectionError")
            status_code = 503
            error_data = {"get cart error": "cart service unavailable"}
            return self.error_response(status_code, error_data)
        except Exception as e:
            status_code = 500
            error_data = {"server error": "internal server error"}
            return self.error_response(status_code, error_data)


    def post(self, request, item_id):
        context = {}
        access_token = request.COOKIES.get("access_token")
        refresh_token = request.COOKIES.get("refresh_token")

        print('access token', access_token)
        print('refresh token', refresh_token)
        try:
            token_is_valid = self.auth.check_access_token(access_token)
            print("Check access token:", token_is_valid)
            if not token_is_valid:
                print("Try to refresh access token")
                print("Old access:", access_token, "Old refresh:", refresh_token)
                access_token, refresh_token = self.auth.refresh_token(refresh_token)
                print("New access:", access_token, "New refresh:", refresh_token)
                if not access_token or not refresh_token:
                    print("Invalid access and refresh tokens, go to authorization")
                    print("Go to authorization link:", self.auth.create_authorization_link())
                    print('not passed')
                    # return HttpResponseRedirect(self.auth.create_authorization_link())
                    status_code = 403
                    context['status_code'] = status_code
                    context['error_short'] = u"Нет доступа"
                    context['error_description'] = u"У вас недостаточно прав, необходимо авторизоваться"
                    r = render(request, 'gateway/error.html', context, status=status_code)
                    r.set_cookie('access_token', access_token, max_age=MAX_COOKIES_AGE)
                    r.set_cookie('refresh_token', refresh_token, max_age=MAX_COOKIES_AGE)
                    return r

            logger.info("DELETE one Item")
            self.cart.delete_one(item_id)
            context['status_code'] = 200
            context['error_short'] = u""
            context['error_description'] = u"Продукт успешно удалился из корзины"
            return render(request, 'gateway/success.html', context)


        except ConnectionError:

            status_code = 503
            context['status_code'] = status_code
            context['error_short'] = u"Сервис недоступен"
            context['error_description'] = u"Сервис корзины временно недоступен"
            return render(request, 'gateway/error.html', context, status=status_code)
        except Exception as e:
            status_code = 500
            context['status_code'] = status_code
            context['error_short'] = u"Внутреняя ошибка сервера корзины"
            context[
                'error_description'] = u"Что-то пошло не так, работоспособность будет восстановлена в ближайшее время"
            return render(request, 'gateway/error.html', context, status=status_code)



@method_decorator(csrf_exempt, name='dispatch')
class CheckoutListView(BaseView):
    def get(self, request):
        context = {}
        return render(request, 'gateway/checkout_post.html', context)

        # try:
        #     logger.info("GET ALL Orders")
        #     return self.checkout.order_get()
        # except ConnectionError:
        #     print("ConnectionError")
        #     status_code = 503
        #     error_data = {"get checkout error": "checkout service unavailable"}
        #     return self.error_response(status_code, error_data)
        # except Exception as e:
        #     status_code = 500
        #     error_data = {"server error": "internal server error"}
        #     return self.error_response(status_code, error_data)


    def post(self, request):
        context = {}
        access_token = request.COOKIES.get("access_token")
        refresh_token = request.COOKIES.get("refresh_token")

        print('access token', access_token)
        print('refresh token', refresh_token)


        try:
            token_is_valid = self.auth.check_access_token(access_token)
            print("Check access token:", token_is_valid)
            if not token_is_valid:
                print("Try to refresh access token")
                print("Old access:", access_token, "Old refresh:", refresh_token)
                access_token, refresh_token = self.auth.refresh_token(refresh_token)
                print("New access:", access_token, "New refresh:", refresh_token)
                if not access_token or not refresh_token:
                    print("Invalid access and refresh tokens, go to authorization")
                    print("Go to authorization link:", self.auth.create_authorization_link())
                    print('not passed')
                    # return HttpResponseRedirect(self.auth.create_authorization_link())
                    status_code = 403
                    context['status_code'] = status_code
                    context['error_short'] = u"Нет доступа"
                    context['error_description'] = u"У вас недостаточно прав, необходимо авторизоваться"
                    r = render(request, 'gateway/error.html', context, status=status_code)
                    r.set_cookie('access_token', access_token, max_age=MAX_COOKIES_AGE)
                    r.set_cookie('refresh_token', refresh_token, max_age=MAX_COOKIES_AGE)
                    return r



            cart_id = request.POST.get('cart_id')
            match = re.match(r'\d+', cart_id)
            if not match or cart_id == '0':
                status_code = 400
                error_data = {"Validation error": "cart_id must be positive integer"}
                return self.error_response(status_code, error_data)

            full_name = request.POST.get('full_name')
            if not full_name or full_name == '':
                status_code = 400
                error_data = {"Validation error": "full_name parameter must not be blank"}
                return self.error_response(status_code, error_data)

            email = request.POST.get('email')
            if not email or email == '':
                status_code = 400
                error_data = {"Validation error": "email parameter must not be blank"}
                return self.error_response(status_code, error_data)

            phone = request.POST.get('phone')
            if not match or phone == '0':
                status_code = 400
                error_data = {"Validation error": " phone must be positive integer"}
                return self.error_response(status_code, error_data)

            status = request.POST.get('status')
            if not status or status == '':
                status_code = 400
                error_data = {"Validation error": "status parameter must not be blank"}
                return self.error_response(status_code, error_data)

            city = request.POST.get('city')
            if not city or city == '':
                status_code = 400
                error_data = {"Validation error": "city parameter must not be blank"}
                return self.error_response(status_code, error_data)

            street = request.POST.get('street')
            if not street or street == '':
                status_code = 400
                error_data = {"Validation error": "street parameter must not be blank"}
                return self.error_response(status_code, error_data)

            r = {'cart_id': cart_id, 'full_name': full_name, 'email': email, 'phone': phone, 'status': status,
                 'city': city, 'street': street}

            self.checkout.order_post(r)
            context['status_code'] = 200
            context['error_short'] = u""
            context['error_description'] = u"Заказ успешно оформлен"
            return render(request, 'gateway/success.html', context)


        except ConnectionError:
            status_code = 503
            context['status_code'] = status_code
            context['error_short'] = u"Сервис недоступен"
            context['error_description'] = u"Сервис заказов временно недоступен"
            return render(request, 'gateway/error.html', context, status=status_code)

        except Exception as e:
            status_code = 500
            context['status_code'] = status_code
            context['error_short'] = u"Внутреняя ошибка сервера корзины"
            context['error_description'] = u"Что-то пошло не так, работоспособность будет восстановлена в ближайшее время"
            return render(request, 'gateway/error.html', context, status=status_code)

@method_decorator(csrf_exempt, name='dispatch')
class CheckoutChangeStatus(BaseView):
    def post(self, request, order_id):
        context = {}
        access_token = request.COOKIES.get("access_token")
        refresh_token = request.COOKIES.get("refresh_token")

        print('access token', access_token)
        print('refresh token', refresh_token)

        data = QueryDict(request.body)
        status = data.get('status')
        if not status or status == '':
            status_code = 400
            error_data = {"Validation error": "text parameter must not be blank"}
            return self.error_response(status_code, error_data)

        logger.info("PATCH Order Status")
        try:
            token_is_valid = self.auth.check_access_token(access_token)
            print("Check access token:", token_is_valid)
            if not token_is_valid:
                print("Try to refresh access token")
                print("Old access:", access_token, "Old refresh:", refresh_token)
                access_token, refresh_token = self.auth.refresh_token(refresh_token)
                print("New access:", access_token, "New refresh:", refresh_token)
                if not access_token or not refresh_token:
                    print("Invalid access and refresh tokens, go to authorization")
                    print("Go to authorization link:", self.auth.create_authorization_link())
                    print('not passed')
                    # return HttpResponseRedirect(self.auth.create_authorization_link())
                    status_code = 403
                    context['status_code'] = status_code
                    context['error_short'] = u"Нет доступа"
                    context['error_description'] = u"У вас недостаточно прав, необходимо авторизоваться"
                    r = render(request, 'gateway/error.html', context, status=status_code)
                    r.set_cookie('access_token', access_token, max_age=MAX_COOKIES_AGE)
                    r.set_cookie('refresh_token', refresh_token, max_age=MAX_COOKIES_AGE)
                    return r

            order_json = self.checkout.order_get_one_json(order_id)
            order_json["status"] = status
            self.checkout.order_patch(order_id, order_json)

            context['status_code'] = 200
            context['error_short'] = u""
            context['error_description'] = u"Статус заказа успешно изменен"
            return render(request, 'gateway/success.html', context)



        except ConnectionError:
            status_code = 503
            context['status_code'] = status_code
            context['error_short'] = u"Сервис недоступен"
            context['error_description'] = u"Сервис заказов временно недоступен"
            return render(request, 'gateway/error.html', context, status=status_code)

        except Exception as e:
            status_code = 500
            context['status_code'] = status_code
            context['error_short'] = u"Внутреняя ошибка сервера корзины"
            context[
                'error_description'] = u"Что-то пошло не так, работоспособность будет восстановлена в ближайшее время"
            return render(request, 'gateway/error.html', context, status=status_code)


@method_decorator(csrf_exempt, name='dispatch')
class CheckoutDetailView(BaseView):
    def get(self, request, order_id):
        context = {}
        access_token = request.COOKIES.get("access_token")
        refresh_token = request.COOKIES.get("refresh_token")

        print('access token', access_token)
        print('refresh token', refresh_token)

        try:
            token_is_valid = self.auth.check_access_token(access_token)
            print("Check access token:", token_is_valid)
            if not token_is_valid:
                print("Try to refresh access token")
                print("Old access:", access_token, "Old refresh:", refresh_token)
                access_token, refresh_token = self.auth.refresh_token(refresh_token)
                print("New access:", access_token, "New refresh:", refresh_token)
                if not access_token or not refresh_token:
                    print("Invalid access and refresh tokens, go to authorization")
                    print("Go to authorization link:", self.auth.create_authorization_link())
                    print('not passed')
                    # return HttpResponseRedirect(self.auth.create_authorization_link())
                    status_code = 403
                    context['status_code'] = status_code
                    context['error_short'] = u"Нет доступа"
                    context['error_description'] = u"У вас недостаточно прав, необходимо авторизоваться"
                    r = render(request, 'gateway/error.html', context, status=status_code)
                    r.set_cookie('access_token', access_token, max_age=MAX_COOKIES_AGE)
                    r.set_cookie('refresh_token', refresh_token, max_age=MAX_COOKIES_AGE)
                    return r


            logger.info("GET One Order")

            response = self.checkout.order_get_one(order_id)
            one_checkout_json = json.loads(response.content)
            error = one_checkout_json.get('detail')
            if error and error == 'Not found.':
                status_code = 404
                context['status_code'] = status_code
                context['error_short'] = u"Некорректный запрос страницы"
                context['error_description'] = u"Данный заказ не найден"
                return render(request, 'gateway/error.html', context, status=status_code)

            cart_id = one_checkout_json.get('cart_id')
            one_cart_json = self.cart.cart_get_one_json(cart_id)

            error = one_cart_json.get('service not available')
            error2 = one_cart_json.get('detail')

            if (error and error == 'connection error'):
                context['order'] = one_checkout_json
                print('context', context)
                return render(request, 'gateway/order_index.html', context)
            elif (error2 and error2 == 'Not found.'):
                context['order'] = one_checkout_json
                print('context', context)
                return render(request, 'gateway/order_index.html', context)
            else:
                one_checkout_json['cart'] = one_cart_json

            for i in one_checkout_json["cart"]["items"]:
                product_id = i.get('product_id')

                one_product_json = self.product.product_get_one_json(product_id)
                print("!!!!!!!",one_product_json)
                error = one_product_json.get('service not available')
                error2 = one_product_json.get('detail')

                if (error and error == 'connection error'):
                    pass
                if (error2 and error2 == 'Not found.'):
                    pass
                else:
                    print('\n', one_product_json)
                    i["product"] = one_product_json
                    print('\n',i)
            context['order'] = one_checkout_json
            print('context',context)
            return render(request, 'gateway/order_index.html', context)
                # print("XXXXXX",one_checkout_json)

        except ConnectionError:
            status_code = 503
            context['status_code'] = status_code
            context['error_short'] = u"Сервис недоступен"
            context['error_description'] = u"Сервис офрмления заказа временно недоступен"
            return render(request, 'gateway/error.html', context, status=status_code)
        except Exception as e:
            status_code = 500
            context['status_code'] = status_code
            context['error_short'] = u"Внутреняя ошибка сервера оформления заказа"
            context['error_description'] = u"Что-то пошло не так, работоспособность будет восстановлена в ближайшее время"

            return render(request, 'gateway/error.html', context, status=status_code)



    def delete(self, request, order_id):
        context = {}
        access_token = request.COOKIES.get("access_token")
        refresh_token = request.COOKIES.get("refresh_token")

        print('access token', access_token)
        print('refresh token', refresh_token)

        try:
            token_is_valid = self.auth.check_access_token(access_token)
            print("Check access token:", token_is_valid)
            if not token_is_valid:
                print("Try to refresh access token")
                print("Old access:", access_token, "Old refresh:", refresh_token)
                access_token, refresh_token = self.auth.refresh_token(refresh_token)
                print("New access:", access_token, "New refresh:", refresh_token)
                if not access_token or not refresh_token:
                    print("Invalid access and refresh tokens, go to authorization")
                    print("Go to authorization link:", self.auth.create_authorization_link())
                    print('not passed')
                    # return HttpResponseRedirect(self.auth.create_authorization_link())
                    status_code = 403
                    context['status_code'] = status_code
                    context['error_short'] = u"Нет доступа"
                    context['error_description'] = u"У вас недостаточно прав, необходимо авторизоваться"
                    r = render(request, 'gateway/error.html', context, status=status_code)
                    r.set_cookie('access_token', access_token, max_age=MAX_COOKIES_AGE)
                    r.set_cookie('refresh_token', refresh_token, max_age=MAX_COOKIES_AGE)
                    return r

            logger.info("DELETE one Order")
            self.checkout.order_delete_one(order_id)
            context['status_code'] = 200
            context['error_short'] = u""
            context['error_description'] = u"Заказ успешно удалился"
            return render(request, 'gateway/success.html', context)


        except ConnectionError:
            status_code = 503
            context['status_code'] = status_code
            context['error_short'] = u"Сервис недоступен"
            context['error_description'] = u"Сервис заказа временно недоступен"
            return render(request, 'gateway/error.html', context, status=status_code)

        except Exception as e:
            status_code = 500
            context['status_code'] = status_code
            context['error_short'] = u"Внутреняя ошибка сервера корзины"
            context[
                'error_description'] = u"Что-то пошло не так, работоспособность будет восстановлена в ближайшее время"
            return render(request, 'gateway/error.html', context, status=status_code)


    def patch(self, request, order_id):
        context = {}
        access_token = request.COOKIES.get("access_token")
        refresh_token = request.COOKIES.get("refresh_token")

        print('access token', access_token)
        print('refresh token', refresh_token)

        data = QueryDict(request.body)
        status = data.get('status')
        if not status or status == '':
            status_code = 400
            error_data = {"Validation error": "text parameter must not be blank"}
            return self.error_response(status_code, error_data)

        logger.info("PATCH Order Status")
        try:
            token_is_valid = self.auth.check_access_token(access_token)
            print("Check access token:", token_is_valid)
            if not token_is_valid:
                print("Try to refresh access token")
                print("Old access:", access_token, "Old refresh:", refresh_token)
                access_token, refresh_token = self.auth.refresh_token(refresh_token)
                print("New access:", access_token, "New refresh:", refresh_token)
                if not access_token or not refresh_token:
                    print("Invalid access and refresh tokens, go to authorization")
                    print("Go to authorization link:", self.auth.create_authorization_link())
                    print('not passed')
                    # return HttpResponseRedirect(self.auth.create_authorization_link())
                    status_code = 403
                    context['status_code'] = status_code
                    context['error_short'] = u"Нет доступа"
                    context['error_description'] = u"У вас недостаточно прав, необходимо авторизоваться"
                    r = render(request, 'gateway/error.html', context, status=status_code)
                    r.set_cookie('access_token', access_token, max_age=MAX_COOKIES_AGE)
                    r.set_cookie('refresh_token', refresh_token, max_age=MAX_COOKIES_AGE)
                    return r

            order_json = self.checkout.order_get_one_json(order_id)
            order_json["status"] = status
            self.checkout.order_patch(order_id, order_json)
            context['status_code'] = 200
            context['error_short'] = u""
            context['error_description'] = u"Заказ успешно изменен"
            return render(request, 'gateway/success.html', context)


        except ConnectionError:
            status_code = 503
            context['status_code'] = status_code
            context['error_short'] = u"Сервис недоступен"
            context['error_description'] = u"Сервис заказов временно недоступен"
            return render(request, 'gateway/error.html', context, status=status_code)
        except Exception as e:
            status_code = 500
            context['status_code'] = status_code
            context['error_short'] = u"Внутреняя ошибка сервера корзины"
            context[
                'error_description'] = u"Что-то пошло не так, работоспособность будет восстановлена в ближайшее время"
            return render(request, 'gateway/error.html', context, status=status_code)


    def post(self, request, order_id):
        logger.info("POST WITCH DELETE ITEM FROM CART AND CHANGE STATUS")
        context ={}

        access_token = request.COOKIES.get("access_token")
        refresh_token = request.COOKIES.get("refresh_token")

        print('access token', access_token)
        print('refresh token', refresh_token)


        try:
            token_is_valid = self.auth.check_access_token(access_token)
            print("Check access token:", token_is_valid)
            if not token_is_valid:
                print("Try to refresh access token")
                print("Old access:", access_token, "Old refresh:", refresh_token)
                access_token, refresh_token = self.auth.refresh_token(refresh_token)
                print("New access:", access_token, "New refresh:", refresh_token)
                if not access_token or not refresh_token:
                    print("Invalid access and refresh tokens, go to authorization")
                    print("Go to authorization link:", self.auth.create_authorization_link())
                    print('not passed')
                    # return HttpResponseRedirect(self.auth.create_authorization_link())
                    status_code = 403
                    context['status_code'] = status_code
                    context['error_short'] = u"Нет доступа"
                    context['error_description'] = u"У вас недостаточно прав, необходимо авторизоваться"
                    r = render(request, 'gateway/error.html', context, status=status_code)
                    r.set_cookie('access_token', access_token, max_age=MAX_COOKIES_AGE)
                    r.set_cookie('refresh_token', refresh_token, max_age=MAX_COOKIES_AGE)
                    return r


            item_id = request.POST.get('item_id')
            match = re.match(r'\d+', item_id)
            if not match or item_id == '0':
                status_code = 400
                context['status_code'] = status_code
                context['error_short'] = u"Некорректный id"
                context['error_description'] = u"Item_id должен быть положительным числом"
                return render(request, 'gateway/error.html', context, status=status_code)

            order_json = self.checkout.order_get_one_json(order_id)
            print(order_json)
            error = order_json.get('detail')
            error2 = order_json.get('service not available')
            if error2 and error2 == 'connection error':
                status_code = 503
                context['status_code'] = status_code
                context['error_short'] = u"Сервис недоступен"
                context['error_description'] = u"Сервис офрмления заказа временно недоступен"
                return render(request, 'gateway/error.html', context, status=status_code)

            elif error and error == 'Not found.':
                status_code = 404
                context['status_code'] = status_code
                context['error_short'] = u"Некорректный запрос страницы"
                context['error_description'] = u"Данный заказ не найден"
                return render(request, 'gateway/error.html', context, status=status_code)

            else:
                status = order_json.get('status')
                order_json["status"] = 'pending'
                self.checkout.order_patch(order_id, order_json)

            try:

                r1 = self.cart.delete_one(item_id)
                if (r1.status_code != 204):
                    order_json["status"] = status
                    self.checkout.order_patch(order_id, order_json)
                    status_code = 100
                    context['status_code'] = status_code
                    context['error_short'] = u"Откат данных"
                    context['error_description'] = u"Операция изменения на двух сервисах не прошла"
                    return render(request, 'gateway/error.html', context, status=status_code)
                else:
                    print ('r1111111',r1)
                    status_code = 200
                    context['status_code'] = status_code
                    context['error_short'] = u""
                    context['error_description'] = u"Продукт удалился и поменялся статус у заказа"
                    return render(request, 'gateway/success.html', context, status=status_code)

            except ConnectionError:
                print("ConnectionError")
                order_json["status"] = status
                self.checkout.order_patch(order_id, order_json)
                context['status_code'] = status_code
                context['error_short'] = u"Сервис недоступен"
                context['error_description'] = u"Произошел откат"
                return render(request, 'gateway/error.html', context, status=status_code)
            except Exception as e:
                print("ConnectionError")
                order_json["status"] = status
                self.checkout.order_patch(order_id, order_json)
                context['status_code'] = status_code
                context['error_short'] = u"Сервис недоступен"
                context['error_description'] = u"Произошел откат"
                return render(request, 'gateway/error.html', context, status=status_code)

        except ConnectionError:
            status_code = 503
            context['status_code'] = status_code
            context['error_short'] = u"Сервис недоступен"
            context['error_description'] = u"Сервис корзины временно недоступен"
            return render(request, 'gateway/error.html', context, status=status_code)

        except Exception as e:
            status_code = 500
            context['status_code'] = status_code
            context['error_short'] = u"Внутреняя ошибка сервера корзины"
            context[
                'error_description'] = u"Что-то пошло не так, работоспособность будет восстановлена в ближайшее время"
            return render(request, 'gateway/error.html', context, status=status_code)






@method_decorator(csrf_exempt, name='dispatch')
class CheckoutDetailView2(BaseView):
    def post(self, request, order_id):
        context = {}

        access_token = request.COOKIES.get("access_token")
        refresh_token = request.COOKIES.get("refresh_token")

        print('access token', access_token)
        print('refresh token', refresh_token)

        try:
            token_is_valid = self.auth.check_access_token(access_token)
            print("Check access token:", token_is_valid)
            if not token_is_valid:
                print("Try to refresh access token")
                print("Old access:", access_token, "Old refresh:", refresh_token)
                access_token, refresh_token = self.auth.refresh_token(refresh_token)
                print("New access:", access_token, "New refresh:", refresh_token)
                if not access_token or not refresh_token:
                    print("Invalid access and refresh tokens, go to authorization")
                    print("Go to authorization link:", self.auth.create_authorization_link())
                    print('not passed')
                    # return HttpResponseRedirect(self.auth.create_authorization_link())
                    status_code = 403
                    context['status_code'] = status_code
                    context['error_short'] = u"Нет доступа"
                    context['error_description'] = u"У вас недостаточно прав, необходимо авторизоваться"
                    r = render(request, 'gateway/error.html', context, status=status_code)
                    r.set_cookie('access_token', access_token, max_age=MAX_COOKIES_AGE)
                    r.set_cookie('refresh_token', refresh_token, max_age=MAX_COOKIES_AGE)
                    return r


            logger.info("POST WITCH DELETE ITEM FROM CART AND CHANGE STATUS")
            item_id = request.POST.get('item_id')

            print('item_id',item_id)
            match = re.match(r'\d+', item_id)
            if not match or item_id == '0':
                status_code = 400
                error_data = {"Validation error": "Item_id must be positive integer"}
                return self.error_response(status_code, error_data)


            order_json = self.checkout.order_get_one_json(order_id)
            error = order_json.get('detail')
            error2 = order_json.get('service not available')
            print ("order_json", order_json)
            if error2 and error2 == 'connection error':
                data = {'status': "pending"}
                storage.put(("PATCH", HOST_URL_GATEWAY + reverse('gateway:order-detail', kwargs={'order_id': order_id}), data))
                print('storage = ', storage)

            elif error and error == 'Not found.':
                status_code = 404
                error_data = {"Order error": "Not found. orders with id = %s" % order_id}
                return self.error_response(status_code, error_data)
            else:
                order_json["status"] = 'pending'
                r2 = self.checkout.order_patch(order_id, order_json)


            try:
                r1 = self.cart.delete_one(item_id)
                r = {"deleting_result": r1.status_code, "status_result": r2.status_code}
                return JsonResponse(r)
            except ConnectionError:
                # storage 2
                data = {}
                storage.put(("POST", HOST_URL_GATEWAY + reverse('gateway:cart-item', kwargs={'item_id': item_id}), data))
                print('storage = ',storage)
                r = {"deleting_result": 503, "status_result": 503}
                return JsonResponse(r)
            except Exception as e:
                status_code = 500
                data = {}
                storage.put(("POST", HOST_URL_GATEWAY + reverse('gateway:cart-item', kwargs={'item_id': item_id}), data))
                print('storage = ', storage)
                error_data = {"server error": "internal server error"}
                return self.error_response(status_code, error_data)
        except ConnectionError:
            status_code = 503
            context['status_code'] = status_code
            context['error_short'] = u"Сервис недоступен"
            context['error_description'] = u"Сервис корзины временно недоступен"
            return render(request, 'gateway/error.html', context, status=status_code)
        except Exception as e:
            status_code = 500
            context['status_code'] = status_code
            context['error_short'] = u"Внутреняя ошибка сервера корзины"
            context[
                'error_description'] = u"Что-то пошло не так, работоспособность будет восстановлена в ближайшее время"
            return render(request, 'gateway/error.html', context, status=status_code)


#Authorization

@method_decorator(csrf_exempt, name='dispatch')
class TokenView(BaseView):
    def get(self, request):
        code = request.GET.get('code')
        print("Got authorization code:", code)
        print("Try to get access and refresh tokens")
        redirect_uri = HOST_URL_GATEWAY + 'token/'
        access_token, refresh_token = self.auth.get_token_oauth(code, redirect_uri)
        print("Access token:", access_token)
        print("Refresh token:", refresh_token)
        response = HttpResponseRedirect(reverse('gateway:product-list'))
        response.set_cookie('access_token', access_token, max_age=MAX_COOKIES_AGE)
        response.set_cookie('refresh_token', refresh_token, max_age=MAX_COOKIES_AGE)
        print('response', response)
        return response


@method_decorator(csrf_exempt, name='dispatch')
class TokenAPIView(BaseView):

    def post(self, request):
        def check(data):
            assert data.get("code", None)           , "code is required"
            assert data.get("redirect_uri", None)   , "redirect_uri is required"
            assert data.get("client_id", None)      , "client_id is required"
            assert data.get("client_secret", None)  , "client_secret is required"

        data = json.loads(request.body.decode("utf-8"))
        try:
            check(data)
            response = self.auth.get_token_oauth_json(**data)
            return JsonResponse(data=response.json(), status=response.status_code)
        except Exception as e:
            return JsonResponse(data={"error": str(e)}, status=400)


@method_decorator(csrf_exempt, name='dispatch')
class AuthView(BaseView):
    def get(self, request):
        return HttpResponseRedirect(self.auth.create_authorization_link())


@method_decorator(csrf_exempt, name='dispatch')
class AuthAPIView(BaseView):
    def get(self, request):
        client_id = request.GET.get("client_id", None)
        if client_id:
            data = {"auth_link": self.auth.create_authorization_link_json(client_id)}
            return JsonResponse(data)
        else:
            return JsonResponse(data={"error": "client_id is required"} ,status=400)







###########################___API___#####################################



class ProductsListApiView(BaseView):
    def get(self, request):
        try:
            logger.info("GET ALL Products")
            page = request.GET.get('page', '1')
            match = re.match(r'\d+', page)

            if not match or page == '0':
                description = {"error": "incorrect query"}
                return self.error_response(status=400, json_body=description)

            response =  self.product.product_get(page=page)
            response = response.json()
            return JsonResponse(response)

        except ConnectionError:
            description = {"error": "service is not avalibale"}
            return self.error_response(status=503, json_body=description)
        except Exception as e:
            description = {"error": "internal service error"}
            return self.error_response(status=500, json_body=description)




@method_decorator(csrf_exempt, name='dispatch')
class ProductDetailApiView(BaseView):
    def get(self, request, product_id):
        try:
            logger.info("GET One Product")
            # return self.product.product_get_one_json(product_id)
            one_product_json = self.product.product_get_one_json(product_id)
            error = one_product_json.get('detail')
            if error and error == 'Not found.':
                description = {"error": "page not found"}
                return self.error_response(status=404, json_body=description)

            return JsonResponse(one_product_json)

        except ConnectionError:
            description = {"error": "service is not avalibale"}
            return self.error_response(status=503, json_body=description)

        except Exception as e:
            description = {"error": "internal service error"}
            return self.error_response(status=500, json_body=description)





@method_decorator(csrf_exempt, name='dispatch')
class CartDetailApiView(BaseView):
    def get(self, request, cart_id):
        try:
            access_token = request.GET.get("access_token")
            refresh_token = request.GET.get("refresh_token")

            print('access token', access_token)
            print('refresh token', refresh_token)

            token_is_valid = self.auth.check_access_token(access_token)
            print("Check access token:", token_is_valid)
            if not token_is_valid:
                print("Try to refresh access token")
                print("Old access:", access_token, "Old refresh:", refresh_token)
                access_token, refresh_token = self.auth.refresh_token(refresh_token)
                print("New access:", access_token, "New refresh:", refresh_token)
                if not access_token or not refresh_token:
                    print("Invalid access and refresh tokens, go to authorization")
                    print("Go to authorization link:", self.auth.create_authorization_link())
                    print('not passed')
                    # return HttpResponseRedirect(self.auth.create_authorization_link())
                    status_code = 403
                    error_data = {"Forbidden": "No rights to this API"}
                    return self.error_response(status_code, error_data)



            print('passed', cart_id)
            logger.info("GET ONE CART")
            one_cart_json = self.cart.cart_get_one_json(cart_id)
            error = one_cart_json.get('detail')
            print('PASSSED', cart_id)
            print(one_cart_json)


            if error and error == 'Not found.':
                status_code = 404
                error_data = {"Error": "Page not found"}
                return self.error_response(status_code, error_data)

            if one_cart_json.get("service not available"):
                status_code = 503
                error_data = {"Error": "Service not available"}
                return self.error_response(status_code, error_data)
            print("Vse ok:")
            for i in one_cart_json["items"]:
                product_id = i.get('product_id')

                logger.info("GET One Product")
                one_product_json = self.product.product_get_one_json(product_id)
                error = one_product_json.get('service not available')
                error2 = one_product_json.get('detail')

                if (error and error == 'connection error') :
                    pass
                elif (error2 and error2 == 'Not found.'):
                    pass
                else:
                    print('\n', one_product_json)
                    i["product"] = one_product_json

            return JsonResponse(one_cart_json)

        except Exception as e:
            description = {"error": "internal service error"}
            return self.error_response(status=500, json_body=description)



    def post(self, request, cart_id):
        try:
            access_token = request.GET.get("access_token")
            refresh_token = request.GET.get("refresh_token")

            print('access token', access_token)
            print('refresh token', refresh_token)

            token_is_valid = self.auth.check_access_token(access_token)
            print("Check access token:", token_is_valid)
            if not token_is_valid:
                print("Try to refresh access token")
                print("Old access:", access_token, "Old refresh:", refresh_token)
                access_token, refresh_token = self.auth.refresh_token(refresh_token)
                print("New access:", access_token, "New refresh:", refresh_token)
                if not access_token or not refresh_token:
                    print("Invalid access and refresh tokens, go to authorization")
                    print("Go to authorization link:", self.auth.create_authorization_link())
                    print('not passed')
                    # return HttpResponseRedirect(self.auth.create_authorization_link())
                    status_code = 403
                    error_data = {"Forbidden": "No rights to this API"}
                    return self.error_response(status_code, error_data)


            quantity = request.POST.get('quantity')
            match = re.match(r'\d+', quantity)
            if not match or quantity == '0':
                status_code = 400
                error_data = {"Validation error": "Quantity must be positive integer"}
                return self.error_response(status_code, error_data)

            product_id = request.POST.get('product_id')
            print(product_id)

            match = re.match(r'\d+', product_id)
            if not match or product_id == '0':
                status_code = 400
                error_data = {"Validation error": "Product_id must be positive integer"}
                return self.error_response(status_code, error_data)
            r = {'cart': cart_id, 'product_id': product_id, 'quantity': quantity}
            logger.info("POST ADD NEW PRODUCT")
            self.cart.cart_add(r)
            status_code = 200
            error_data = {"Success": "Product added to the cart"}
            return self.error_response(status_code, error_data)

        except Exception as e:
            description = {"error": "internal service error"}
            return self.error_response(status=500, json_body=description)




@method_decorator(csrf_exempt, name='dispatch')
class CartItemApi(BaseView):
    def get(self, request, item_id):
        try:
            logger.info("GET one Item")
            response = self.cart.item_get_one(item_id)
            response = response.json()
            return JsonResponse(response)

        except ConnectionError:
            description = {"error": "cart service is not availbale"}
            return self.error_response(status=503, json_body=description)
        except Exception as e:
            description = {"error": "internal service error"}
            return self.error_response(status=500, json_body=description)



    def post(self, request, item_id):
        try:
            access_token = request.GET.get("access_token")
            refresh_token = request.GET.get("refresh_token")

            print('access token', access_token)
            print('refresh token', refresh_token)

            token_is_valid = self.auth.check_access_token(access_token)
            print("Check access token:", token_is_valid)
            if not token_is_valid:
                print("Try to refresh access token")
                print("Old access:", access_token, "Old refresh:", refresh_token)
                access_token, refresh_token = self.auth.refresh_token(refresh_token)
                print("New access:", access_token, "New refresh:", refresh_token)
                if not access_token or not refresh_token:
                    print("Invalid access and refresh tokens, go to authorization")
                    print("Go to authorization link:", self.auth.create_authorization_link())
                    print('not passed')
                    # return HttpResponseRedirect(self.auth.create_authorization_link())
                    status_code = 403
                    error_data = {"Forbidden": "No rights to this API"}
                    return self.error_response(status_code, error_data)

            logger.info("DELETE one Item")
            self.cart.delete_one(item_id)
            status_code = 200
            error_data = {"Success": "Product deleted from the cart"}
            return self.error_response(status_code, error_data)

        except ConnectionError:
            print("ConnectionError")
            status_code = 503
            error_data = {"get cart error": "cart service unavailable"}
            return self.error_response(status_code, error_data)
        except Exception as e:
            status_code = 500
            error_data = {"server error": "internal server error"}
            return self.error_response(status_code, error_data)




@method_decorator(csrf_exempt, name='dispatch')
class CheckoutListApiView(BaseView):

    def post(self, request):
        try:

            access_token = request.GET.get("access_token")
            refresh_token = request.GET.get("refresh_token")

            print('access token', access_token)
            print('refresh token', refresh_token)

            token_is_valid = self.auth.check_access_token(access_token)
            print("Check access token:", token_is_valid)
            if not token_is_valid:
                print("Try to refresh access token")
                print("Old access:", access_token, "Old refresh:", refresh_token)
                access_token, refresh_token = self.auth.refresh_token(refresh_token)
                print("New access:", access_token, "New refresh:", refresh_token)
                if not access_token or not refresh_token:
                    print("Invalid access and refresh tokens, go to authorization")
                    print("Go to authorization link:", self.auth.create_authorization_link())
                    print('not passed')
                    # return HttpResponseRedirect(self.auth.create_authorization_link())
                    status_code = 403
                    error_data = {"Forbidden": "No rights to this API"}
                    return self.error_response(status_code, error_data)

            cart_id = request.POST.get('cart_id')
            match = re.match(r'\d+', cart_id)
            if not match or cart_id == '0':
                status_code = 400
                error_data = {"Validation error": "cart_id must be positive integer"}
                return self.error_response(status_code, error_data)

            full_name = request.POST.get('full_name')
            if not full_name or full_name == '':
                status_code = 400
                error_data = {"Validation error": "full_name parameter must not be blank"}
                return self.error_response(status_code, error_data)

            email = request.POST.get('email')
            if not email or email == '':
                status_code = 400
                error_data = {"Validation error": "email parameter must not be blank"}
                return self.error_response(status_code, error_data)

            phone = request.POST.get('phone')
            if not match or phone == '0':
                status_code = 400
                error_data = {"Validation error": " phone must be positive integer"}
                return self.error_response(status_code, error_data)

            status = request.POST.get('status')
            if not status or status == '':
                status_code = 400
                error_data = {"Validation error": "status parameter must not be blank"}
                return self.error_response(status_code, error_data)

            city = request.POST.get('city')
            if not city or city == '':
                status_code = 400
                error_data = {"Validation error": "city parameter must not be blank"}
                return self.error_response(status_code, error_data)

            street = request.POST.get('street')
            if not street or street == '':
                status_code = 400
                error_data = {"Validation error": "street parameter must not be blank"}
                return self.error_response(status_code, error_data)

            r = {'cart_id': cart_id, 'full_name': full_name, 'email': email, 'phone': phone, 'status': status,
                 'city': city, 'street': street}

            self.checkout.order_post(r)
            status_code = 200
            error_data = {"Success": "Order placed"}
            return self.error_response(status_code, error_data)

        except ConnectionError:
            print("ConnectionError")
            status_code = 503
            error_data = {"checkout error": "checkout service unavailable"}
            return self.error_response(status_code, error_data)

        except Exception as e:
            status_code = 500
            error_data = {"server error": "internal server error"}
            return self.error_response(status_code, error_data)


@method_decorator(csrf_exempt, name='dispatch')
class CheckoutChangeStatusApi(BaseView):
    def post(self, request, order_id):

        data = QueryDict(request.body)
        status = data.get('status')
        if not status or status == '':
            status_code = 400
            error_data = {"Validation error": "text parameter must not be blank"}
            return self.error_response(status_code, error_data)

        logger.info("PATCH Order Status")
        try:
            access_token = request.GET.get("access_token")
            refresh_token = request.GET.get("refresh_token")

            print('access token', access_token)
            print('refresh token', refresh_token)

            token_is_valid = self.auth.check_access_token(access_token)
            print("Check access token:", token_is_valid)
            if not token_is_valid:
                print("Try to refresh access token")
                print("Old access:", access_token, "Old refresh:", refresh_token)
                access_token, refresh_token = self.auth.refresh_token(refresh_token)
                print("New access:", access_token, "New refresh:", refresh_token)
                if not access_token or not refresh_token:
                    print("Invalid access and refresh tokens, go to authorization")
                    print("Go to authorization link:", self.auth.create_authorization_link())
                    print('not passed')
                    # return HttpResponseRedirect(self.auth.create_authorization_link())
                    status_code = 403
                    error_data = {"Forbidden": "No rights to this API"}
                    return self.error_response(status_code, error_data)


            order_json = self.checkout.order_get_one_json(order_id)
            order_json["status"] = status
            self.checkout.order_patch(order_id, order_json)
            status_code = 200
            error_data = {"Success": "Order status changed"}
            return self.error_response(status_code, error_data)


        except ConnectionError:
            print("ConnectionError")
            status_code = 503
            error_data = {"get checkout error": "checkout service unavailable"}
            return self.error_response(status_code, error_data)
        except Exception as e:
            status_code = 500
            error_data = {"server error": "internal server error"}
            return self.error_response(status_code, error_data)




@method_decorator(csrf_exempt, name='dispatch')
class CheckoutDetailApiView(BaseView):
    def get(self, request, order_id):
        try:

            access_token = request.GET.get("access_token")
            refresh_token = request.GET.get("refresh_token")

            print('access token', access_token)
            print('refresh token', refresh_token)

            token_is_valid = self.auth.check_access_token(access_token)
            print("Check access token:", token_is_valid)
            if not token_is_valid:
                print("Try to refresh access token")
                print("Old access:", access_token, "Old refresh:", refresh_token)
                access_token, refresh_token = self.auth.refresh_token(refresh_token)
                print("New access:", access_token, "New refresh:", refresh_token)
                if not access_token or not refresh_token:
                    print("Invalid access and refresh tokens, go to authorization")
                    print("Go to authorization link:", self.auth.create_authorization_link())
                    print('not passed')
                    # return HttpResponseRedirect(self.auth.create_authorization_link())
                    status_code = 403
                    error_data = {"Forbidden": "No rights to this API"}
                    return self.error_response(status_code, error_data)

            logger.info("GET One Order")

            response = self.checkout.order_get_one(order_id)
            one_checkout_json = json.loads(response.content)
            error = one_checkout_json.get('detail')
            if error and error == 'Not found.':
                status_code = 404
                error_data = {"Error": "Page not found"}
                return self.error_response(status_code, error_data)

            cart_id = one_checkout_json.get('cart_id')
            one_cart_json = self.cart.cart_get_one_json(cart_id)

            error = one_cart_json.get('service not available')
            error2 = one_cart_json.get('detail')

            if (error and error == 'connection error'):
                status_code = 503
                error_data = {"Error": "connection error"}
                return self.error_response(status_code, error_data)

            elif (error2 and error2 == 'Not found.'):
                status_code = 404
                error_data = {"Error": "Page not found"}
                return self.error_response(status_code, error_data)
            else:
                one_checkout_json['cart'] = one_cart_json

            for i in one_checkout_json["cart"]["items"]:
                product_id = i.get('product_id')

                one_product_json = self.product.product_get_one_json(product_id)
                print("!!!!!!!",one_product_json)
                error = one_product_json.get('service not available')
                error2 = one_product_json.get('detail')

                if (error and error == 'connection error'):
                    pass
                if (error2 and error2 == 'Not found.'):
                    pass
                else:
                    print('\n', one_product_json)
                    i["product"] = one_product_json
                    print('\n',i)
            print('context',one_checkout_json)
            return JsonResponse(one_checkout_json)

        except ConnectionError:
            print("ConnectionError")
            status_code = 503
            error_data = {"get checkout error": "checkout service unavailable"}
            return self.error_response(status_code, error_data)
        except Exception as e:
            status_code = 500
            error_data = {"server error": "internal server error"}
            return self.error_response(status_code, error_data)



    def delete(self, request, order_id):
        try:
            access_token = request.GET.get("access_token")
            refresh_token = request.GET.get("refresh_token")

            print('access token', access_token)
            print('refresh token', refresh_token)

            token_is_valid = self.auth.check_access_token(access_token)
            print("Check access token:", token_is_valid)
            if not token_is_valid:
                print("Try to refresh access token")
                print("Old access:", access_token, "Old refresh:", refresh_token)
                access_token, refresh_token = self.auth.refresh_token(refresh_token)
                print("New access:", access_token, "New refresh:", refresh_token)
                if not access_token or not refresh_token:
                    print("Invalid access and refresh tokens, go to authorization")
                    print("Go to authorization link:", self.auth.create_authorization_link())
                    print('not passed')
                    # return HttpResponseRedirect(self.auth.create_authorization_link())
                    status_code = 403
                    error_data = {"Forbidden": "No rights to this API"}
                    return self.error_response(status_code, error_data)


            logger.info("DELETE one Order")
            self.checkout.order_delete_one(order_id)
            status_code = 200
            error_data = {"Success": "Order deleted"}
            return self.error_response(status_code, error_data)

        except ConnectionError:
            print("ConnectionError")
            status_code = 503
            error_data = {"get checkout error": "cart service unavailable"}
            return self.error_response(status_code, error_data)
        except Exception as e:
            status_code = 500
            error_data = {"server error": "internal server error"}
            return self.error_response(status_code, error_data)


    def patch(self, request, order_id):

        data = QueryDict(request.body)
        status = data.get('status')
        if not status or status == '':
            status_code = 400
            error_data = {"Validation error": "text parameter must not be blank"}
            return self.error_response(status_code, error_data)

        logger.info("PATCH Order Status")
        try:
            access_token = request.GET.get("access_token")
            refresh_token = request.GET.get("refresh_token")

            print('access token', access_token)
            print('refresh token', refresh_token)

            token_is_valid = self.auth.check_access_token(access_token)
            print("Check access token:", token_is_valid)
            if not token_is_valid:
                print("Try to refresh access token")
                print("Old access:", access_token, "Old refresh:", refresh_token)
                access_token, refresh_token = self.auth.refresh_token(refresh_token)
                print("New access:", access_token, "New refresh:", refresh_token)
                if not access_token or not refresh_token:
                    print("Invalid access and refresh tokens, go to authorization")
                    print("Go to authorization link:", self.auth.create_authorization_link())
                    print('not passed')
                    # return HttpResponseRedirect(self.auth.create_authorization_link())
                    status_code = 403
                    error_data = {"Forbidden": "No rights to this API"}
                    return self.error_response(status_code, error_data)


            order_json = self.checkout.order_get_one_json(order_id)
            order_json["status"] = status
            self.checkout.order_patch(order_id, order_json)
            status_code = 200
            error_data = {"Success": "Order status changed"}
            return self.error_response(status_code, error_data)

        except ConnectionError:
            print("ConnectionError")
            status_code = 503
            error_data = {"get checkout error": "checkout service unavailable"}
            return self.error_response(status_code, error_data)
        except Exception as e:
            status_code = 500
            error_data = {"server error": "internal server error"}
            return self.error_response(status_code, error_data)



    def post(self, request, order_id):
        logger.info("POST WITCH DELETE ITEM FROM CART AND CHANGE STATUS")
        try:
            access_token = request.GET.get("access_token")
            refresh_token = request.GET.get("refresh_token")

            print('access token', access_token)
            print('refresh token', refresh_token)

            token_is_valid = self.auth.check_access_token(access_token)
            print("Check access token:", token_is_valid)
            if not token_is_valid:
                print("Try to refresh access token")
                print("Old access:", access_token, "Old refresh:", refresh_token)
                access_token, refresh_token = self.auth.refresh_token(refresh_token)
                print("New access:", access_token, "New refresh:", refresh_token)
                if not access_token or not refresh_token:
                    print("Invalid access and refresh tokens, go to authorization")
                    print("Go to authorization link:", self.auth.create_authorization_link())
                    print('not passed')
                    # return HttpResponseRedirect(self.auth.create_authorization_link())
                    status_code = 403
                    error_data = {"Forbidden": "No rights to this API"}
                    return self.error_response(status_code, error_data)


            item_id = request.POST.get('item_id')
            match = re.match(r'\d+', item_id)
            if not match or item_id == '0':
                status_code = 400
                error_data = {"Error": "incorrect id"}
                return self.error_response(status_code, error_data)

            order_json = self.checkout.order_get_one_json(order_id)
            print(order_json)
            error = order_json.get('detail')
            error2 = order_json.get('service not available')
            if error2 and error2 == 'connection error':
                status_code = 503
                error_data = {"Error": "checkout service unavailable"}
                return self.error_response(status_code, error_data)

            elif error and error == 'Not found.':
                status_code = 404
                error_data = {"Error": "Order not found"}
                return self.error_response(status_code, error_data)

            else:
                status = order_json.get('status')
                order_json["status"] = 'pending'
                self.checkout.order_patch(order_id, order_json)

            try:

                r1 = self.cart.delete_one(item_id)
                if (r1.status_code != 204):
                    order_json["status"] = status
                    self.checkout.order_patch(order_id, order_json)
                    status_code = 100
                    error_data = {"Error": "operation didn`t pass"}
                    return self.error_response(status_code, error_data)
                else:
                    status_code = 200
                    error_data = {"Success": "Product deleted and order status was changed"}
                    return self.error_response(status_code, error_data)

            except ConnectionError:
                print("ConnectionError")
                order_json["status"] = status
                self.checkout.order_patch(order_id, order_json)
                status_code = 503
                error_data = {"Otkat": "proizoshol otkat"}
                return self.error_response(status_code, error_data)
            except Exception as e:
                print("ConnectionError")
                order_json["status"] = status
                self.checkout.order_patch(order_id, order_json)
                status_code = 500
                error_data = {"Otkat": "proizoshol otkat"}
                return self.error_response(status_code, error_data)

        except ConnectionError:
            print("ConnectionError")
            status_code = 503
            error_data = {"get checkout error": "auth service unavailable"}
            return self.error_response(status_code, error_data)
        except Exception as e:
            status_code = 500
            error_data = {"server error": "auth server error"}
            return self.error_response(status_code, error_data)



@method_decorator(csrf_exempt, name='dispatch')
class CheckoutDetailApiView2(BaseView):
    def post(self, request, order_id):

        try:
            access_token = request.GET.get("access_token")
            refresh_token = request.GET.get("refresh_token")

            print('access token', access_token)
            print('refresh token', refresh_token)

            token_is_valid = self.auth.check_access_token(access_token)
            print("Check access token:", token_is_valid)
            if not token_is_valid:
                print("Try to refresh access token")
                print("Old access:", access_token, "Old refresh:", refresh_token)
                access_token, refresh_token = self.auth.refresh_token(refresh_token)
                print("New access:", access_token, "New refresh:", refresh_token)
                if not access_token or not refresh_token:
                    print("Invalid access and refresh tokens, go to authorization")
                    print("Go to authorization link:", self.auth.create_authorization_link())
                    print('not passed')
                    # return HttpResponseRedirect(self.auth.create_authorization_link())
                    status_code = 403
                    error_data = {"Forbidden": "No rights to this API"}
                    return self.error_response(status_code, error_data)

            logger.info("POST WITCH DELETE ITEM FROM CART AND CHANGE STATUS")
            item_id = request.POST.get('item_id')

            print('item_id',item_id)
            match = re.match(r'\d+', item_id)
            if not match or item_id == '0':
                status_code = 400
                error_data = {"Validation error": "Item_id must be positive integer"}
                return self.error_response(status_code, error_data)


            order_json = self.checkout.order_get_one_json(order_id)
            error = order_json.get('detail')
            error2 = order_json.get('service not available')
            print ("order_json", order_json)
            if error2 and error2 == 'connection error':
                data = {'status': "pending"}
                storage.put(("PATCH", HOST_URL_GATEWAY + reverse('gateway:order-detail', kwargs={'order_id': order_id}), data))
                print('storage = ', storage)

            elif error and error == 'Not found.':
                status_code = 404
                error_data = {"Order error": "Not found. orders with id = %s" % order_id}
                return self.error_response(status_code, error_data)
            else:
                order_json["status"] = 'pending'
                r2 = self.checkout.order_patch(order_id, order_json)


            try:
                r1 = self.cart.delete_one(item_id)
                r = {"deleting_result": r1.status_code, "status_result": r2.status_code}
                return JsonResponse(r)


            except ConnectionError:
                # storage 2
                data = {}
                storage.put(("POST", HOST_URL_GATEWAY + reverse('gateway:cart-item', kwargs={'item_id': item_id}), data))
                print('storage = ',storage)
                r = {"deleting_result": 503, "status_result": 503}
                return JsonResponse(r)
            except Exception as e:
                status_code = 500
                data = {}
                storage.put(("POST", HOST_URL_GATEWAY + reverse('gateway:cart-item', kwargs={'item_id': item_id}), data))
                print('storage = ', storage)
                error_data = {"server error": "internal server error"}
                return self.error_response(status_code, error_data)


        except ConnectionError:
            print("ConnectionError")
            status_code = 503
            error_data = {"get checkout error": "auth service unavailable"}
            return self.error_response(status_code, error_data)
        except Exception as e:
            status_code = 500
            error_data = {"server error": "auth server error"}
            return self.error_response(status_code, error_data)


