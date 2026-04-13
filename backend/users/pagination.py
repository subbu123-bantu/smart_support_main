from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class CustomPagination(PageNumberPagination):
    page_size = 7            #  was missing entirely
    page_size_query_param = 'page-size'
    page_query_param = 'page'
    max_page_size = 100 

    def get_paginated_response(self, data):
        return Response({
            'next':self.get_next_link(),
            'previous':self.get_previous_link(),
            'count':self.page.paginator.count,
            'page_size':self.page_size,
            'results':data
        })