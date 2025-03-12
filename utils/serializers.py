from rest_framework import serializers

class CamelCaseSerializer(serializers.ModelSerializer):
    """
    A base serializer that converts snake_case field names to camelCase in API responses.
    """

    def to_representation(self, instance):
        """
        Converts all snake_case keys to camelCase in the response.
        """
        data = super().to_representation(instance)
        return {self._camel_case(key): value for key, value in data.items()}

    def _camel_case(self, snake_str):
        """
        Converts a snake_case string to camelCase.
        """
        components = snake_str.split('_')
        return components[0] + ''.join(x.title() for x in components[1:])
