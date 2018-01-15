import requests
from django.http import HttpResponse
from requests.exceptions import ConnectionError
import functools
from rest_framework import status
import json


class ConvertExceptions():

    func = None

    def __init__(self, exceptions, replacement=None):
        self.exceptions = exceptions
        self.replacement = replacement

    def __get__(self, obj, objtype):

        return functools.partial(self.__call__, obj)

    def __call__(self, *args, **kwargs):
        if self.func is None:
            self.func = args[0]
            return self
        try:
            return self.func(*args, **kwargs)
        except self.exceptions:
            return self.replacement



class BaseRequester():
    def __init__(self, host, service_name):
        self.host = host
        self.service_name = service_name

    def response_convert(self, requests_response):
        django_response = HttpResponse(
            content=requests_response.content,
            status=requests_response.status_code,
            content_type=requests_response.headers.get('Content-Type')
        )
        return django_response

    def _error_response(self, status_code=503, description=None):
        return HttpResponse(
            status=status_code,
            content=json.dumps(description),
            content_type='application/json'
        )

    # def get(self, query_string):
    #     r = requests.get(self.host + query_string)
    #     return self.response_convert(r)

    def get_check(self, query_string="", params=None):
        try:
            response = requests.get(self.host + query_string, params=params)
            return self.response_convert(response)
        except requests.exceptions.ConnectionError:
            description = {
                "error": "service %s is not available" % self.service_name
            }
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            return self._error_response(status_code, description)

    def get(self, query_string="", params=None):
        response = requests.get(self.host + query_string, params=params)
        return self.response_convert(response)


    @ConvertExceptions(ConnectionError, {"service not available": "connection error"})
    def get_json(self, query_string):
        response = requests.get(self.host + query_string)
        return response.json()


        # except requests.exceptions.ConnectionError:
        #     description = {
        #         "error": "service %s is not available" % self.service_name
        #     }
        #     status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        #     return self._error_response(status_code, description)

            # try:
            #     response = requests.get(self.host_url + query_string)
            #     return response.json()
            # except requests.exceptions.ConnectionError:
            #     description = {
            #         "error": "servise %s is not available" % self._servise_name
            #     }
            #     return status.HTTP_503_SERVICE_UNAVAILABLE, description


        # r = requests.get(self.host + query_string)
        # return r.json()

    def post(self, query_string, json):

        response = requests.post(self.host + query_string, json=json)
        return self.response_convert(response)


    def patch(self, query_string, json):

        response = requests.patch(self.host + query_string, json=json)
        return self.response_convert(response)


    def delete(self, query_string):

        response = requests.delete(self.host + query_string)
        return self.response_convert(response)

        # r = requests.delete(self.host + query_string)
        # return self.response_convert(r)



class ProductRequester(BaseRequester):

    def check(self):
        return self.get_check()

    def product_get(self, page=1):
        return self.get('products/?page=%s' % page)

    def product_get_all_json(self, page=1):
        return self.get_json('products/?page=%s' % page)

    def product_category_get(self):
        return self.get('category/')

    def product_get_one(self, product_id):
        return self.get('products/%s/' % product_id)

    def product_delete_one(self, product_id):
        return self.delete('products/%s/' % product_id)

    def product_get_one_json(self, product_id):
        return self.get_json('products/%s/' % product_id)

    def category_get_one(self, category_id):
        return self.get('category/%s/' % category_id)

    def category_get_one_json(self, category_id):
        return self.get_json('category/%s/' % category_id)


class CartRequester(BaseRequester):

    def check(self):
        return self.get_check()

    def cart_get(self):
        return self.get('cart/')

    def cart_get_all_json(self):
        return self.get_json('cart/')

    def cart_get_one(self, cart_id):
        return self.get('cart/%s/' % cart_id)

    def cart_get_one_json(self, cart_id):
        return self.get_json('cart/%s/' % cart_id)

    def item_get_one(self, item_id):
        return self.get('item/%s/' % item_id)

    def item_get_one_json(self, item_id):
        return self.get_json('item/%s/' % item_id)

    def delete_one(self, item_id):
        return self.delete('item/%s/' % item_id)

    def cart_add(self, cart_json):
        return self.post('item/add/', json=cart_json)





    # def patch_one(self, cart_id, items ):
    #     patch_json = {'text': text}
    #     return self.patch('cart/%s/' % cart_id, json=patch_json)



    # def cart_add(self, cart_id, product_id):
    #     post_json = {'news_uid': news_uid, 'text': text}
    #     return self.post('cart/%s/' % (cart_id, product_id))
    #
    # def post_one(self, news_uid, text):
    #     post_json = {'news_uid': news_uid, 'text': text}
    #     return self.post('comments/', json=post_json)


class CheckoutRequester(BaseRequester):
    def check(self):
        return self.get()

    def order_get(self):
        return self.get('orders/')

    def order_post(self, order_json):
        return self.post('orders/', json=order_json)

    def order_patch(self, order_id, order_json):
        return self.patch('orders/%s/' % order_id, json=order_json)

    def order_get_one(self, order_id):
        return self.get('orders/%s/' % order_id)

    def order_delete_one(self, order_id):
        return self.delete('orders/%s/' % order_id)

    def order_get_one_json(self, order_id):
        return self.get_json('orders/%s/' % order_id)

