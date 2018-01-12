from django.views import View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

import logging
import ast

from .conf import HOST_URL_CARD, HOST_URL_CHECKOUT, HOST_URL_PRODUCT

from .functions import ProductRequester
from .functions import CartRequester
from .functions import CheckoutRequester

logger = logging.getLogger(__name__)

def byte_string_to_dict(data):
    try:
        assert isinstance(data, bytes), 'This is not byte string'
        assert data != b'', 'Byte string is empty'

        data = data.decode('utf-8')
        data = ast.literal_eval(data)
    except AssertionError as e:
        data = {}

    return data



class BaseView(View):
    def __init__(self, product_host=HOST_URL_PRODUCT,
                 cart_host=HOST_URL_CARD,
                 checkout_host=HOST_URL_CHECKOUT):
        self.product = ProductRequester(product_host)
        self.cart = CartRequester(cart_host)
        self.checkout = CheckoutRequester(checkout_host)


class ProductsListView(BaseView):
    def get(self, request):
        logger.info("GET ALL Products")
        page = request.GET.get('page', 1)
        return self.product.product_get(page=page)

class ProductDetailView(BaseView):
    def get(self, request, product_id):
        logger.info("GET One Products")
        return self.product.product_get_one(product_id)

class CategoryListView(BaseView):
    def get(self, request):
        logger.info("GET ALL Categories")
        return self.product.product_category_get()


class CategoryDetailView(BaseView):
    def get(self, request, category_id):
        logger.info("GET One Category")
        return self.product.category_get_one(category_id)


class CartListView(BaseView):
    def get(self, request):
        logger.info("GET ALL Carts")
        return self.cart.cart_get()

@method_decorator(csrf_exempt, name='dispatch')
class CartDetailView(BaseView):
    def get(self, request, cart_id):
        one_cart_json = self.cart.cart_get_one_json(cart_id)

        for i in one_cart_json["items"]:
            product_id = i.pop('product_id')
            one_product_json = self.product.product_get_one_json(product_id)
            i['product'] = one_product_json

        # print('product', one_cart_json)
        logger.info("GET ONE CART")
        return JsonResponse(one_cart_json)

    def post(self, request, cart_id):
        # product_id = request.GET['product_id']
        # quantity = request.GET['quantity']
        quantity = request.POST.get('quantity')
        product_id = request.POST.get('product_id')


        # data = byte_string_to_dict(request.body)
        # print('data =', data)
        # print('request = ', request.body)

        print(product_id)
        print(quantity)
        cart_json = self.cart.cart_get_one_json(cart_id)

        print('cart_json1', cart_json)

        r = {'cart': cart_id, 'product_id': product_id, 'quantity': quantity}
        rn = self.cart.cart_add(r)

        # cart_json["items"].append({'product_id': 1, 'date_added': '2017-11-10T22:29:21.633920Z', 'quantity': 2})
        #
        #
        #
        # # print('object', obj)
        # print('\n cart_json2', cart_json)
        # rn = self.cart.cart_set(cart_id, cart_json)
        #
        #
        # logger.info("POST ADD ONE PRODUCT")
        return JsonResponse(r)


@method_decorator(csrf_exempt, name='dispatch')
class CartItem(BaseView):
    def get(self, request, item_id):
        logger.info("GET one Item")
        return self.cart.item_get_one(item_id)


    def delete(self, request, item_id):
        logger.info("DELETE one Item")
        return self.cart.delete_one(item_id)


@method_decorator(csrf_exempt, name='dispatch')
class CheckoutListView(BaseView):
    def get(self, request):
        logger.info("GET ALL Orders")
        return self.checkout.order_get()

    def post(self, request):
        cart_id = request.POST.get('cart_id')
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        status = request.POST.get('status')
        city = request.POST.get('city')
        street = request.POST.get('city')

        r = {'cart_id': cart_id, 'full_name': full_name, 'email': email, 'phone': phone, 'status':status, 'city': city, 'street':street}
        return self.checkout.order_post(r)




class CheckoutDetailView(BaseView):
    def get(self, request, order_id):
        logger.info("GET One Order")
        return self.checkout.order_get_one(order_id)


