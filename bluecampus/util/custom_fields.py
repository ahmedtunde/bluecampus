from django.db import models
from django.utils.text import slugify
from django.utils.crypto import get_random_string

class TwelveDigitUUIDField(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 12)
        super().__init__(*args, **kwargs)

    def pre_save(self, model_instance, add):
        value = getattr(model_instance, self.attname, None)
        if not value:
            # Generate the 12-digit identifier if not set
            identifier = get_random_string(length=12, allowed_chars='0123456789')
            setattr(model_instance, self.attname, identifier)
        return super().pre_save(model_instance, add)