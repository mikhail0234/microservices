from django.http import HttpResponse
from requests.exceptions import ConnectionError
from rest_framework import status
import json


import requests
import functools
from requests.auth import HTTPBasicAuth


from .conf import APP_ID
from .conf import APP_SECRET
from .conf import SUCCESS_CHECK
from .conf import CLIENT_ID
from .conf import CLIENT_SECRET
from .conf import CLIENT_ID_JSON
from .conf import CLIENT_SECRET_JSON



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
    def __init__(self, host, service_name = 'base-name', app_id=APP_ID, app_secret=APP_SECRET):
        self.host = host
        self.service_name = service_name
        self.app_id = app_id
        self.app_secret = app_secret
        self.token = None

    def get_token(self):
        r = requests.post(self.host + 'token/', {"username": self.app_id, "password": self.app_secret})
        r = r.json()
        self.token = r.get('token')

    @property
    def headers(self):
        return {"Authorization": "Token %s" % self.token}

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





    def get(self, query_string, headers=None):
        if headers:
            if not headers.get("Authorization"):
                headers["Authorization"] = "Token %s" % self.token
        else:
            headers = self.headers
        response = requests.get(self.host + query_string, headers=headers)


        if response.status_code == 401:
            self.get_token()
            headers["Authorization"] = "Token %s" % self.token
            response = requests.get(self.host + query_string, headers=headers)
        return response

    #
    # def get(self, query_string="", params=None):
    #     response = requests.get(self.host + query_string, params=params)
    #     return self.response_convert(response)


    @ConvertExceptions(ConnectionError, {"service not available": "connection error"})
    def get_json(self, query_string, headers=None):
        if headers:
            if not headers.get("Authorization"):
                headers["Authorization"] = "Token %s" % self.token
        else:
            headers = self.headers
        response = requests.get(self.host + query_string, headers=headers)
        if response.status_code == 401:
            self.get_token()
            headers["Authorization"] = "Token %s" % self.token
            response = requests.get(self.host + query_string, headers=headers)
        return response.json()


    def post(self, query_string, json, auth=None, headers=None):

        if headers:
            if not headers.get("Authorization"):
                headers["Authorization"] = "Token %s" % self.token
        else:
            headers = self.headers
        response = requests.post(self.host + query_string, data=json, auth=auth, headers=headers)

        if response.status_code == 401:
            self.get_token()
            headers["Authorization"] = "Token %s" % self.token
            response = requests.post(self.host + query_string, data=json, auth=auth, headers=headers)
        return response


    def patch(self, query_string, data, auth=None, headers = None):

        if headers:
            if not headers.get("Authorization"):
                headers["Authorization"] = "Token %s" % self.token
        else:
            headers = self.headers
        response = requests.patch(self.host + query_string, json=data, auth=auth, headers=headers)

        if response.status_code == 401:
            self.get_token()
            headers["Authorization"] = "Token %s" % self.token
            response = requests.patch(self.host + query_string, json=data, auth=auth, headers=headers)
        return response


    def delete(self, query_string, headers = None):
        if headers:
            if not headers.get("Authorization"):
                headers["Authorization"] = "Token %s" % self.token
        else:
            headers = self.headers
        print("TOOOOKKKKEENN", self.token)
        response = requests.delete(self.host + query_string, headers=headers)
        if response.status_code == 401:
            self.get_token()
            headers["Authorization"] = "Token %s" % self.token
            response = requests.delete(self.host + query_string, headers=headers)
        return response




class ProductRequester(BaseRequester):


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
        return self.get()

    def cart_get(self):
        return self.get('cart/')

    def cart_get_all_json(self):
        return self.get_json('cart/')

    def cart_get_one(self, cart_id):
        return self.get('cart/%s/' % cart_id)

    def cart_get_one_json(self, cart_id):
        print('xxxxxxxxxxxx')
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



class AuthRequester(BaseRequester):

    def get_user(self, access_token):
        headers = {'Authorization': 'Bearer %s' % access_token}
        response = self.get('user', headers=headers)
        return response
    """
    def authorize(self, username, password):
        next = self.create_authorization_link_json()
        url = "http://localhost:8065/accounts/login/"
        print(username)
        print(password)
        data = {
            'username': username,
            'password': password,
            'next': next
        }
        response = requests.post(url,data, auth=(username,password), allow_redirects=True)
        return response
    """

    def check_access_token(self, access_token):
        headers = {'Authorization': 'Bearer %s' % access_token}
        check = self.get('secret', headers=headers)
        return check.text == SUCCESS_CHECK

    def check_access_token_json(self, access_token):
        headers = {'Authorization': 'Bearer %s' % access_token}
        check = self.get('secret', headers=headers)
        return check.text == SUCCESS_CHECK

    def create_authorization_link(self):
        return self.host + 'o/authorize/?state=random_state_stringfgsfds&client_id=%s&response_type=code' % CLIENT_ID

    def create_authorization_link_json(self, client_id):
        return self.host + 'o/authorize/?state=random_state_stringfgsfds&client_id=%s&response_type=code' % client_id

    def get_token_oauth(self, code, redirect_uri):
        post_json = {'code': code, 'grant_type': 'authorization_code', 'redirect_uri': redirect_uri}
        response = requests.post(self.host + 'o/token/', post_json, auth=(CLIENT_ID, CLIENT_SECRET))
        answer = response.json()
        return answer.get('access_token'), answer.get('refresh_token')

    def get_token_oauth_json(self, code, redirect_uri, client_id, client_secret):
        post_json = {'code': code, 'grant_type': 'authorization_code', 'redirect_uri': redirect_uri}
        response = requests.post(self.host + 'o/token/', post_json, auth=(CLIENT_ID_JSON, CLIENT_SECRET_JSON))
        return response

    def refresh_token(self, refresh_token):
        post_json = {'refresh_token': refresh_token, 'grant_type': 'refresh_token'}
        response = requests.post(self.host + 'o/token/', post_json, auth=(CLIENT_ID, CLIENT_SECRET))
        answer = response.json()
        return answer.get('access_token'), answer.get('refresh_token')

    def refresh_token_json(self, refresh_token):
        post_json = {'refresh_token': refresh_token, 'grant_type': 'refresh_token'}
        response = requests.post(self.host + 'o/token/', post_json, auth=(CLIENT_ID_JSON, CLIENT_SECRET_JSON))
        answer = response.json()
        return answer.get('access_token'), answer.get('refresh_token')

