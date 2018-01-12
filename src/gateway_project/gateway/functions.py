import requests
from django.http import HttpResponse



# def pack_one_cart(news, source, comments):
#     one_cart = news
#     one_news["source"] = source
#     one_news["comments"] = comments
#     return one_news




class BaseRequester():
    def __init__(self, host):
        self.host = host

    def response_convert(self, requests_response):
        django_response = HttpResponse(
            content=requests_response.content,
            status=requests_response.status_code,
            content_type=requests_response.headers.get('Content-Type')
        )
        return django_response

    def get(self, query_string):
        r = requests.get(self.host + query_string)
        return self.response_convert(r)

    def get_json(self, query_string):
        r = requests.get(self.host + query_string)
        return r.json()

    def post(self, query_string, json):
        r = requests.post(self.host + query_string, json=json)
        return self.response_convert(r)

    def patch(self, query_string, json):
        r = requests.patch(self.host + query_string, json=json)
        return self.response_convert(r)

    def delete(self, query_string):
        r = requests.delete(self.host + query_string)
        return self.response_convert(r)



class ProductRequester(BaseRequester):
    def product_get(self, page=1):
        return self.get('products/?page=%s' % page)

    def product_category_get(self):
        return self.get('category/')

    def product_get_one(self, product_id):
        return self.get('products/%s/' % product_id)

    def product_get_one_json(self, product_id):
        return self.get_json('products/%s/' % product_id)

    def category_get_one(self, category_id):
        return self.get('category/%s/' % category_id)

    def category_get_one_json(self, category_id):
        return self.get_json('category/%s/' % category_id)


class CartRequester(BaseRequester):
    def cart_get(self):
        return self.get('cart/')

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

    def order_get(self):
        return self.get('orders/')

    def order_post(self, order_json):
        return self.post('orders/', json=order_json)

    def order_get_one(self, order_id):
        return self.get('orders/%s/' % order_id)

    def order_get_one_json(self, order_id):
        return self.get_json('orders/%s/' % order_id)

