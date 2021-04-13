# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Chached data from the ICAT service
"""
import datetime
import logging

from django.utils import timezone

from .icat_communication import ICATCommunication
from .models import UserCache, InstrumentCache, ExperimentCache

from .settings import CACHE_LIFETIME

LOGGER = logging.getLogger("app")


class ICATConnectionException(Exception):
    """
    Used to handle exceptions that we might expect from ICAT
    """
    def __init__(self, message='ISIS ICAT is currently unavailable'):
        super().__init__(message)


class ICATCache:
    """
    A wrapper for ICATCommunication that caches information, and in the case of
    ICAT failure will try to use this cache.
    It stores Cache models in the database, and will get all fields from
    ICATCommunication if a model is requested but has expired or doesn't exist.
    Most of the methods it wraps from ICATCommunication are templated
    rather than declared explicitly; see below.
    """
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.icat = None
        self.cache_lifetime = CACHE_LIFETIME

    def __enter__(self):
        return self

    # pylint: disable=redefined-builtin
    def __exit__(self, type, value, traceback):
        if self.icat is not None:
            self.icat.__exit__(type, value, traceback)

    def open_icat(self):
        """ Try to open an ICAT session, if we don't have one already. """
        try:
            if self.icat is None:
                self.icat = ICATCommunication(**self.kwargs)
        except Exception as excep:
            # pylint: disable=no-member,protected-access
            LOGGER.error("Failed to connect to ICAT: %s - %s", type(excep).__name__, excep)
            raise ICATConnectionException() from excep

    def is_valid(self, cache_obj):
        """ Check whether a cache object is fresh and is not None. """
        return cache_obj and (cache_obj.created + datetime.timedelta(seconds=self.cache_lifetime) > timezone.now())

    @staticmethod
    def to_list(target_list):
        """Change list to map"""
        return ",".join(map(str, target_list))

    def cull_invalid(self, target_list):
        """ Removes all objects in the list that have expired. """
        rlist = []
        for obj in target_list:
            # pylint: disable=expression-not-assigned
            obj.delete() if not self.is_valid(obj) else rlist.append(obj)
        return rlist

    def update_cache(self, obj_type, obj_id):
        """
        Adds an object of type obj_type and id obj_id to the cache -
        querying ICAT - and returns the object.
        E.g., obj_type = InstrumentCache, obj_id = "WISH".
        """
        self.open_icat()  # Open an ICAT session if we don't have one open.

        if obj_type != ExperimentCache:
            # Check func_list for the attributes that each model should have,
            # and the corresponding ICATCommunication function to query for it;
            #  call it for each, building a dict, and then splice it into the constructor kwargs.
            new_obj = obj_type(
                **{
                    attr: (getattr(self.icat, func)
                           (obj_id) if typ is None else self.to_list(getattr(self.icat, func)(obj_id)))
                    for (func, model, attr, typ) in FUNC_LIST if model == obj_type
                })
        else:
            # In this case, ICATCommunication returns all the ExperimentCache
            # fields in one query, so we splice that into the constructor.
            new_obj = obj_type(
                **{
                    attr: str(val)
                    for attr, val in list(self.icat.get_experiment_details(obj_id).items())
                    if attr != "reference_number"
                })
        new_obj.id_name = obj_id
        new_obj.save()
        return new_obj

    def check_cache(self, obj_type, obj_id):
        """
        Checks the cache for an object of type obj_type and id obj_id -
        querying for a new one if there isn't a fresh copy - and returns it.
        If ICAT is unavailable, use a local copy if it exists.
        If we can't use anything, return None.
        """
        in_cache = obj_type.objects.filter(id_name=obj_id).order_by("-created")
        ret_obj = None
        if in_cache:
            ret_obj = in_cache[0]
        if not self.is_valid(ret_obj):
            try:
                ret_obj = self.update_cache(obj_type, obj_id)
                self.cull_invalid(in_cache)
            except ICATConnectionException:
                pass

        return ret_obj

    # pylint: disable=invalid-name
    def get_valid_experiments_for_instruments(self, user_number, instruments):
        """
        Get all experiments for given instrument associated with a particular user number
        :param user_number: number to search for
        :param instruments: name of instrument of interest
        :return: experiment details dictionary
        """
        experiment_dict = {}
        # pylint: disable=no-member
        user_experiments = set(self.get_associated_experiments(user_number))
        for instrument_name in instruments:
            instrument_experiments = self.get_valid_experiments_for_instrument(instrument_name)
            experiment_dict[instrument_name] = list(user_experiments.intersection(instrument_experiments))
        return experiment_dict

    def get_experiment_details(self, experiment_number):
        """
        Return experiment information as a dictionary
        """
        experiment = self.check_cache(ExperimentCache, experiment_number)
        return experiment.__dict__


# Here we define (ICATCommunication function to wrap, Cache object type,
# field of object to get, type of list element if the field is a list)
FUNC_LIST = [("get_owned_instruments", UserCache, "owned_instruments", str),
             ("get_valid_instruments", UserCache, "valid_instruments", str), ("is_admin", UserCache, "is_admin", None),
             ("is_instrument_scientist", UserCache, "is_instrument_scientist", None),
             ("get_associated_experiments", UserCache, "associated_experiments", int),
             ("get_upcoming_experiments_for_instrument", InstrumentCache, "upcoming_experiments", int),
             ("get_valid_experiments_for_instrument", InstrumentCache, "valid_experiments", int)]


def make_member_func(obj_type, cache_attr, list_type):
    """
    From the list we make a wrapping function for each ICATCommunication function.
    We create a make_ function to enclose the scope of the member function so that obj_type, etc.,
    are local to the function and not globals; i.e., these are closures.
    """
    def isvalid(obj_str):
        """
        Check object string validity
        """
        try:
            obj_type(obj_str)
            return bool(obj_str)
        # pylint: disable=bare-except
        except:
            return False

    def member_func(self, obj_id):
        """
        Remove expired objects, then check if the relevant object is in the cache,
        putting it in if it isn't.
        """
        new_obj = self.check_cache(obj_type, obj_id)

        # Get the attribute we want, parsing it as a list if we should.
        attr = getattr(new_obj, cache_attr)
        if list_type is not None:
            attr = map(list_type, filter(isvalid, attr.split(",")))

        return attr

    return member_func


# We add each of these functions as a member function to ICATCache.
for t in FUNC_LIST:
    setattr(ICATCache, t[0], make_member_func(*t[1:]))
