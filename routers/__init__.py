from routers.FilterRouter import filter_router
from routers.ProfileRouter import profile_router
from routers.ReferralRouter import referral_router
from routers.RegisterRouter import register_router
from routers.TaskRouter import task_router
from routers.VipRouter import vip_router

routers = [profile_router, register_router, task_router, referral_router, vip_router, filter_router]  #filter_router всегда идет последним
