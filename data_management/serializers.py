from rest_framework import serializers

class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField(required=True)
    mode = serializers.ChoiceField(
        choices=["create_only", "update_only", "upsert"],
        default="upsert"
    )
