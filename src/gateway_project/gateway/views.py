import json
import re
import logging
from django.views import View
from django.http import JsonResponse
from django.http import QueryDict
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import HttpResponse
from django.shortcuts import render

from django.urls import reverse
from threading import Event

from requests.exceptions import ConnectionError

from .conf import HOST_URL_CARD, HOST_URL_CHECKOUT, HOST_URL_PRODUCT

from .functions import ProductRequester
from .functions import CartRequester
from .functions import CheckoutRequester
from .queue import MyThread
from .queue import storage

from .conf import HOST_URL_GATEWAY


logger = logging.getLogger(__name__)


stopFlag = Event()
thread = MyThread(stopFlag)
thread.start()


class BaseView(View):
    def __init__(self, product_host=HOST_URL_PRODUCT,
                 cart_host=HOST_URL_CARD,
                 checkout_host=HOST_URL_CHECKOUT):
        self.product = ProductRequester(product_host,service_name="product")
        self.cart = CartRequester(cart_host, service_name="cart")
        self.checkout = CheckoutRequester(checkout_host, service_name="checkout")

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
                # print(response)
                response_json = json.loads(response.content)
                # print('JSON', response_json)
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
        try:
            logger.info("GET One Product")
            # return self.product.product_get_one_json(product_id)
            one_product_json = self.product.product_get_one_json(product_id)
            error = one_product_json.get('detail')
            if error and error == 'Not found.':
                status_code = 404
                error_data = {"Product error": "Not found. product with id = %s" % product_id}
                return self.error_response(status_code, error_data)
            return JsonResponse(one_product_json)

        except ConnectionError:
            status_code = 503
            error_data = {"get products error": "products service unavailable"}
            return self.error_response(status_code, error_data)
        except Exception as e:
            status_code = 500
            error_data = {"server error": "internal server error"}
            return self.error_response(status_code, error_data)



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
            print("ConnectionError")
            status_code = 503
            error_data = {"get cart error": "cart service unavailable"}
            return self.error_response(status_code, error_data)
        except Exception as e:
            status_code = 500
            error_data = {"server error": "internal server error"}
            return self.error_response(status_code, error_data)


@method_decorator(csrf_exempt, name='dispatch')
class CartDetailView(BaseView):
    def get(self, request, cart_id):

        try:
            logger.info("GET ONE CART")

            one_cart_json = self.cart.cart_get_one_json(cart_id)
            error = one_cart_json.get('detail')

            if error and error == 'Not found.':
                status_code = 404
                error_data = {"Cart error": "Not found. cart with id = %s" % cart_id}
                return self.error_response(status_code, error_data)

            resp_products_check = self.cart.check()

            print("Check", resp_products_check)
            if (resp_products_check.status_code != 200 and resp_products_check.status_code != 404):
                return JsonResponse(one_cart_json)
            else:
                for i in one_cart_json["items"]:
                    product_id = i.get('product_id')

                    try:
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

                    except ConnectionError:
                        print("ConnectionError")
                        status_code = 503
                        error_data = {"get cart error": "cart service unavailable"}
                        return self.error_response(status_code, error_data)
                        # return JsonResponse(one_cart_json)
                    except Exception as e:
                        status_code = 500
                        error_data = {"server error": "internal server error"}
                        print(error_data)
                        # return self.error_response(status_code, error_data)
                        return self.error_response(status_code, error_data)

                return JsonResponse(one_cart_json)

        except ConnectionError:
            print("ConnectionError")
            status_code = 503
            error_data = {"get cart error": "cart service unavailable"}
            return self.error_response(status_code, error_data)
        except Exception as e:
            status_code = 500
            error_data = {"server error": "internal server error1"}
            return self.error_response(status_code, error_data)


    def post(self, request, cart_id):

        resp_cart_check = self.cart.check()
        print(resp_cart_check)
        if (resp_cart_check.status_code != 200 and resp_cart_check.status_code != 404):
            resp_data = {
                "error": "service cart is not available"
            }
            return JsonResponse(resp_data)
        else:

            quantity = request.POST.get('quantity')
            print(quantity)

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
            return self.cart.cart_add(r)


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


    def delete(self, request, item_id):
        try:
            logger.info("DELETE one Item")
            return self.cart.delete_one(item_id)
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
class CheckoutListView(BaseView):
    def get(self, request):
        try:
            logger.info("GET ALL Orders")
            return self.checkout.order_get()
        except ConnectionError:
            print("ConnectionError")
            status_code = 503
            error_data = {"get checkout error": "cart service unavailable"}
            return self.error_response(status_code, error_data)
        except Exception as e:
            status_code = 500
            error_data = {"server error": "internal server error"}
            return self.error_response(status_code, error_data)


    def post(self, request):
        try:

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
            return self.checkout.order_post(r)

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
class CheckoutDetailView(BaseView):
    def get(self, request, order_id):
        try:
            logger.info("GET One Order")
            return self.checkout.order_get_one(order_id)
        except ConnectionError:
            print("ConnectionError")
            status_code = 503
            error_data = {"get checkout error": "cart service unavailable"}
            return self.error_response(status_code, error_data)
        except Exception as e:
            status_code = 500
            error_data = {"server error": "internal server error"}
            return self.error_response(status_code, error_data)


    def delete(self, request, order_id):
        try:
            logger.info("DELETE one Order")
            return self.checkout.order_delete_one(order_id)
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
            order_json = self.checkout.order_get_one_json(order_id)
            order_json["status"] = status
            return self.checkout.order_patch(order_id, order_json)
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
        item_id = request.POST.get('item_id')
        match = re.match(r'\d+', item_id)
        if not match or item_id == '0':
            status_code = 400
            error_data = {"Validation error": "Item_id must be positive integer"}
            return self.error_response(status_code, error_data)

        item_id = request.POST.get('item_id')
        match = re.match(r'\d+', item_id)
        if not match or item_id == '0':
            status_code = 400
            error_data = {"Validation error": "Item_id must be positive integer"}
            return self.error_response(status_code, error_data)

        logger.info("GET One Order")
        order_json = self.checkout.order_get_one_json(order_id)
        print(order_json)


        error = order_json.get('detail')
        error2 = order_json.get('service not available')
        if error2 and error2 == 'connection error':
            r = {"deleting_result": 503, "status_result": 503}
            # storage 1

            return JsonResponse(r)
        elif error and error == 'Not found.':
            status_code = 404
            error_data = {"Order error": "Not found. orders with id = %s" % order_id}
            return self.error_response(status_code, error_data)



        try:
            r1 = self.cart.delete_one(item_id)
            order_json["status"] = 'pending'
            r2 = self.checkout.order_patch(order_id, order_json)
            r = {"deleting_result": r1.status_code, "status_result": 200}
            return JsonResponse(r)


        except ConnectionError:
            # storage 2
            r = {"deleting_result": 503, "status_result": 503}
            return JsonResponse(r)
        except Exception as e:
            status_code = 500
            error_data = {"server error": "internal server error"}
            return self.error_response(status_code, error_data)





@method_decorator(csrf_exempt, name='dispatch')
class CheckoutDetailView2(BaseView):
    def post(self, request, order_id):
        logger.info("POST WITCH DELETE ITEM FROM CART AND CHANGE STATUS")
        item_id = request.POST.get('item_id')

        print('item_id',item_id)
        match = re.match(r'\d+', item_id)
        if not match or item_id == '0':
            status_code = 400
            error_data = {"Validation error": "Item_id must be positive integer"}
            return self.error_response(status_code, error_data)

        item_id = request.POST.get('item_id')
        match = re.match(r'\d+', item_id)
        if not match or item_id == '0':
            status_code = 400
            error_data = {"Validation error": "Item_id must be positive integer"}
            return self.error_response(status_code, error_data)

        logger.info("GET One Order")
        order_json = self.checkout.order_get_one_json(order_id)


        error = order_json.get('detail')
        error2 = order_json.get('service not available')
        if error2 and error2 == 'connection error':
            r = {"deleting_result": 503, "status_result": 503}
            # storage 1
            data = {'item_id': '51'}
            storage.put(("POST", HOST_URL_GATEWAY + reverse('gateway:order-detail2', kwargs={'order_id': order_id}), data))
            print('storage = ', storage)
            return JsonResponse(r)
        elif error and error == 'Not found.':
            status_code = 404
            error_data = {"Order error": "Not found. orders with id = %s" % order_id}
            return self.error_response(status_code, error_data)



        try:
            r1 = self.cart.delete_one(item_id)
            order_json["status"] = 'pending'
            r2 = self.checkout.order_patch(order_id, order_json)
            r = {"deleting_result": r1.status_code, "status_result": 200}
            return JsonResponse(r)


        except ConnectionError:
            # storage 2
            data = {'item_id': item_id}
            storage.put(("POST", HOST_URL_GATEWAY + reverse('gateway:order-detail2', kwargs={'order_id': order_id}), {"item_id": "51"}))
            print('storage = ',storage)
            r = {"deleting_result": 503, "status_result": 503}
            return JsonResponse(r)
        except Exception as e:
            status_code = 500
            error_data = {"server error": "internal server error"}
            return self.error_response(status_code, error_data)



