from django.db import models

class SeparatedValuesField(models.TextField):
    """
    Provide a list field type to be used by models
    See: http://cramer.io/2008/08/08/custom-fields-in-django/
    """
    __metaclass__ = models.SubfieldBase

    def __init__(self, *args, **kwargs):
        self.token = kwargs.pop('token', '|')
        super(SeparatedValuesField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if not value: return
        if isinstance(value, list):
            return value
        return value.split(self.token)

    def get_db_prep_value(self, value, connection=None, prepared=False):
        if not value: return
        assert(isinstance(value, list) or isinstance(value, tuple))
        return self.token.join([unicode(s) for s in value])

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return self.get_db_prep_value(value)

    def value_from_object(self, obj):
        value = super(SeparatedValuesField, self).value_from_object(obj)
        return self.get_db_prep_value(value)