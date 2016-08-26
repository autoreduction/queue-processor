import datetime
from django.utils import timezone
from autoreduce_webapp.icat_communication import ICATCommunication
from autoreduce_webapp.models import UserCache, InstrumentCache, ExperimentCache

CACHE_LIFETIME = 3600


class ICATCache(object):
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.icat = None
    
    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        if self.icat is not None:
            self.icat.__exit__()
            
    def open_icat(self):
        if self.icat is None:
            self.icat = ICATCommunication(**self.kwargs)
            
    def is_valid(self, cache_obj):
        return cache_obj.created + datetime.timedelta(seconds=CACHE_LIFETIME) > timezone.now()
        
    def to_list(self, l):
        return ",".join(map(str, l))
            
    def cull_invalid(self, list):
        rlist = []
        for obj in list:
            obj.delete() if not self.is_valid(obj) else rlist.append(obj)
        return rlist
        
    def update_cache(self, obj_type, obj_id):
        self.open_icat()
        
        new_obj = obj_type(**{attr:(getattr(self.icat, func)(obj_id) if typ is None else self.to_list(getattr(self.icat, func)(obj_id))) for (func, model, attr, typ) in func_list if model == obj_type})
        new_obj.id_name = obj_id
        new_obj.save()
        return new_obj
        
        
    def get_valid_experiments_for_instruments(self, user_number, instruments):
        return {instrument: self.get_valid_experiments_for_instrument(instrument) for instrument in instruments}
    
            

func_list = [ ("get_owned_instruments", UserCache, "owned_instruments", str)
            , ("get_valid_instruments", UserCache, "valid_instruments", str)
            , ("is_admin", UserCache, "is_admin", None)
            , ("is_instrument_scientist", UserCache, "is_instrument_scientist", None)
            , ("get_associated_experiments", UserCache, "associated_experiments", int)
            
            , ("get_upcoming_experiments_for_instrument", InstrumentCache, "upcoming_experiments", int)
            , ("get_valid_experiments_for_instrument", InstrumentCache, "valid_experiments", int)
            
            , ("get_experiment_details", ExperimentCache, "__dict__", None)
            ]
            
def make_member_func(member_name, obj_type, cache_attr, list_type):
    def member_func(self, object_id):
        # Remove expired objects, then check if the relevant object is in the cache, putting it in if it isn't.
        in_cache = self.cull_invalid(obj_type.objects.filter(id_name = object_id).order_by("-created"))
        new_obj = in_cache[0] if in_cache else self.update_cache(obj_type, object_id)
        
        # Get the attribute we want, parsing it as a list if we should.
        attr = getattr(new_obj, cache_attr)
        if list_type is not None:
            attr = map(list_type, attr.split(","))
        
        return attr
        
    setattr(ICATCache, member_name, member_func)
    
for t in func_list:
    make_member_func(*t)
        
            
# get_owned_instruments(int(request.user.username))
# get_valid_instruments(int(request.user.username))
# get_associated_experiments(int(request.user.username))
# get_upcoming_experiments_for_instrument
# is_admin(int(person['usernumber']))
# is_instrument_scientist(int(person['usernumber']))
# get_experiment_details(int(reference_number))


### get_valid_experiments_for_instruments(int(request.user.username), instrument_names))