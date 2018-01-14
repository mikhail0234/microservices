import json
import re
import logging
from django.views import View
from django.http import JsonResponse
from django.http import QueryDict
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import HttpResponse

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
        try:
            logger.info("GET ALL Products")
            page = request.GET.get('page', '1')
            match = re.match(r'\d+', page)
            if not match or page == '0':
                status_code = 400
                error_data = {"Validation error": "Page must be positive integer"}
                return self.error_response(status_code, error_data)
            return self.product.product_get(page=page)
        except ConnectionError:
            status_code = 503
            error_data = {"get products error": "products service unavailable"}
            return self.error_response(status_code, error_data)
        except Exception as e:
            status_code = 500
            error_data = {"server error": "internal server error"}
            return self.error_response(status_code, error_data)


@method_decorator(csrf_exempt, name='dispatch')
class ProductDetailView(BaseView):
    def get(self, request, product_id):
        try:
            logger.info("GET One Product")

            return self.product.product_get_one_json(product_id)
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
        # logger.info("GET ALL Carts")
        # return self.cart.cart_get()

        try:
            logger.info("GET ALL Carts")
            # page = request.GET.get('page', '1')
            # match = re.match(r'\d+', page)

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


            print(one_cart_json)




            if error and error == 'Not found.':
                status_code = 404
                error_data = {"Cart error": "Not found. cart with id = %s" % cart_id}
                return self.error_response(status_code, error_data)

            resp_products_check = self.cart.check()
            if (resp_products_check.status_code != 200 and resp_products_check.status_code != 404):

                return JsonResponse(one_cart_json)
            else:



                for i in one_cart_json["items"]:


                    product_id = i.get('product_id')

                    try:
                        logger.info("GET One Product")
                        one_product_json = self.product.product_get_one_json(product_id)

                        error = one_product_json.get('service product is not available')
                        if (error and error == 'service product is not available') :
                            pass
                        else:
                            print('\n', one_product_json)
                            i["product"] = one_product_json



                    except ConnectionError:
                        status_code = 503
                        error_data = {"get product error": "products service unavailable"}
                        # return self.cart.cart_get_one(cart_id)
                        return JsonResponse(one_cart_json)
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
            print(one_product_json)
            # return one_product_json
            return self.error_response(status_code, error_data)


        # resp_cart_check = self.cart.check()
        #
        # print(resp_cart_check)
        # if (resp_cart_check.status_code != 200 and resp_cart_check.status_code != 404):
        #     resp_data = {
        #         "error": "service cart is not available"
        #     }
        #     return JsonResponse(resp_data)
        # else:
        #     print('cart', resp_cart_check)
        #     resp_product_check = self.product.check()
        #     print('product', resp_product_check)
        #
        #     if (resp_product_check.status_code != 200 ):
        #
        #         one_cart_json = self.cart.cart_get_one_json(cart_id)
        #         error = one_cart_json.get('detail')
        #
        #         print('error',error)
        #         print(one_cart_json)
        #
        #         if error and error == 'Not found.':
        #             status_code = 404
        #             error_data = {"Cart error": "Not found. cart with id = %s" % cart_id}
        #             return self.error_response(status_code, error_data)
        #         else:
        #             return one_cart_json
        #     else:
        #         status_code = 404
        #         print(resp_cart_check)
        #         error_data = {"wtf": "service cart is not available"}
        #         return self.error_response(status_code, error_data)

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
        try:
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

        except ConnectionError:
            status_code = 503
            error_data = {"change checkout status error": "cart service unavailable"}
            return self.error_response(status_code, error_data)
        except Exception as e:
            status_code = 500
            error_data = {"server error": "internal server error"}
            return self.error_response(status_code, error_data)





    def post(self, request, order_id):

        try:
            item_id = request.POST.get('item_id')

            match = re.match(r'\d+', item_id)
            if not match or item_id == '0':
                status_code = 400
                error_data = {"Validation error": "Item_id must be positive integer"}
                return self.error_response(status_code, error_data)

            try:
                logger.info("GET One Order")
                order_json = self.checkout.order_get_one_json(order_id)
                error = order_json.get('detail')
                if error and error == 'Not found.':
                    status_code = 404
                    error_data = {"Order error": "Not found. orders with id = %s" % order_id}
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

            try:
                r1 = self.cart.delete_one(item_id)
            except ConnectionError:
                status_code = 503
                error_data = {"cart connection error": "cart service unavailable"}
                return self.error_response(status_code, error_data)
            except Exception as e:
                status_code = 500
                error_data = {"server error": "internal server error"}
                return self.error_response(status_code, error_data)
            print(r1.status_code)
            if (r1.status_code != 200 and r1.status_code != 204):
                # storage.put(( HOST_URL_GATEWAY + reverse('gateway:order-detail', kwargs={'news_id': news_id}),
                #              {'text': text}))
                #
                # storage.put((HOST_URL_GATEWAY + reverse('gateway:comment_news', kwargs={'news_id': news_id}),
                #              {'text': text}))


                status_code = 503
            else:
                status_code = 200
                order_json["status"] = 'pending'
                r2 = self.checkout.order_patch(order_id, order_json)

            r = {"deleting_result": r1.status_code, "status_result": status_code}
            logger.info("POST WITCH DELETE ITEM FROM CART AND CHANGE STATUS")
            return JsonResponse(r)

        except ConnectionError:
            status_code = 503
            error_data = {"post checkout  error": "checkout service unavailable"}
            return self.error_response(status_code, error_data)
        except Exception as e:
            status_code = 500
            error_data = {"server error": "internal server error"}
            return self.error_response(status_code, error_data)



            # resp_cart_check = self.cart.check()
        # resp_checkout_check = self.checkout.check()
        #
        # print(resp_cart_check)
        # print(resp_checkout_check)
        #
        # if (resp_cart_check.status_code != 200 or resp_checkout_check.status_code != 200) or (resp_cart_check.status_code != 404 or resp_checkout_check.status_code != 404):
        #     # store_request.put(("POST", HOST_URL_GATEWAY + reverse('servise:orders-list'), data))
        #     resp_data = {
        #         "cart": {
        #             "status_code": 201
        #         },
        #         "checkout": {
        #             "status_code": 200
        #         }
        #     }
        #     return JsonResponse(resp_data)
        # else:
        #
        #
        #     try:
        #         item_id = request.POST.get('item_id')
        #
        #         match = re.match(r'\d+', item_id)
        #         if not match or item_id == '0':
        #             status_code = 400
        #             error_data = {"Validation error": "Item_id must be positive integer"}
        #             return self.error_response(status_code, error_data)
        #
        #     except ConnectionError:
        #         status_code = 503
        #         error_data = {"post checkout  error": "checkout service unavailable"}
        #         return self.error_response(status_code, error_data)
        #
        #     except Exception as e:
        #         status_code = 500
        #         error_data = {"server error": "internal server error"}
        #         return self.error_response(status_code, error_data)
        #
        #     try:
        #         logger.info("GET One Order")
        #         order_json = self.checkout.order_get_one_json(order_id)
        #         error = order_json.get('detail')
        #         if error and error == 'Not found.':
        #             status_code = 404
        #             error_data = {"Order error": "Not found. orders with id = %s" % order_id}
        #             return self.error_response(status_code, error_data)
        #
        #     except ConnectionError:
        #         print("ConnectionError")
        #         status_code = 503
        #         error_data = {"get checkout error": "checkout service unavailable"}
        #         return self.error_response(status_code, error_data)
        #     except Exception as e:
        #         status_code = 500
        #         error_data = {"server error": "internal server error"}
        #         return self.error_response(status_code, error_data)
        #
        #
        #     try:
        #         r1 = self.cart.delete_one(item_id)
        #     except ConnectionError:
        #         status_code = 503
        #         error_data = {"cart connection error": "cart service unavailable"}
        #         return self.error_response(status_code, error_data)
        #     except Exception as e:
        #         status_code = 500
        #         error_data = {"server error": "internal server error"}
        #         return self.error_response(status_code, error_data)
        #
        #     order_json["status"] = 'pending'
        #     r2 = self.checkout.order_patch(order_id, order_json)
        #
        #     r = {"deleting_result": r1.status_code, "status_result": r2.status_code}
        #     logger.info("POST WITCH DELETE ITEM FROM CART AND CHANGE STATUS")
        #     return JsonResponse(r)

@method_decorator(csrf_exempt, name='dispatch')
class CheckoutDetailView2(BaseView):
    def post(self, request, order_id):
        try:
            item_id = request.POST.get('item_id')

            match = re.match(r'\d+', item_id)
            if not match or item_id == '0':
                status_code = 400
                error_data = {"Validation error": "Item_id must be positive integer"}
                return self.error_response(status_code, error_data)

            try:
                logger.info("GET One Order")
                order_json = self.checkout.order_get_one_json(order_id)
                error = order_json.get('detail')
                if error and error == 'Not found.':
                    status_code = 404
                    error_data = {"Order error": "Not found. orders with id = %s" % order_id}
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

            try:
                r1 = self.cart.delete_one(item_id)
            except ConnectionError:
                status_code = 503
                error_data = {"cart connection error": "cart service unavailable"}
                return self.error_response(status_code, error_data)
            except Exception as e:
                status_code = 500
                error_data = {"server error": "internal server error"}
                return self.error_response(status_code, error_data)
            print(r1.status_code)
            if (r1.status_code != 200 and r1.status_code != 204):

                print("yyyy")
                print('storage',storage)
                storage.put(("POST", HOST_URL_GATEWAY + reverse('gateway:order-detail2', kwargs={'item_id': item_id})))
                print(storage)
                status_code = 503
            else:
                status_code = 200

                print("xxxx")
                order_json["status"] = 'pending'
                r2 = self.checkout.order_patch(order_id, order_json)

            r = {"deleting_result": r1.status_code, "status_result": status_code}
            logger.info("POST WITCH DELETE ITEM FROM CART AND CHANGE STATUS")
            return JsonResponse(r)

        except ConnectionError:
            status_code = 503
            error_data = {"post checkout  error": "checkout service unavailable"}
            return self.error_response(status_code, error_data)
        except Exception as e:
            status_code = 500
            error_data = {"server error": "internal server errorr"}
            return self.error_response(status_code, error_data)