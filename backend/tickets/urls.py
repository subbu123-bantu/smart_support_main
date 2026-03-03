from tickets.views import TicketViewSet,CategoryViewSet
from rest_framework.routers import DefaultRouter

router=DefaultRouter()
router.register(r'tickets',TicketViewSet)
router.register(r'categories',CategoryViewSet)

urlpatterns = router.urls
