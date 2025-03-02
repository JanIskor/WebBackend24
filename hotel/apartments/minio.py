from django.conf import settings
from minio import Minio
from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework.response import *

def process_file_upload(file_object: InMemoryUploadedFile, client, image_name):
    try:
        client.put_object('hotel', image_name, file_object, file_object.size)
        return f"http://127.0.0.1:9000/hotel/images/{image_name}"
    except Exception as e:
        return {"error": str(e)}

def add_pic(new_configuration_element, pic):
    client = Minio(           
           endpoint=settings.AWS_S3_ENDPOINT_URL,
           access_key=settings.AWS_ACCESS_KEY_ID,
           secret_key=settings.AWS_SECRET_ACCESS_KEY,
           secure=settings.MINIO_USE_SSL
    )
    i = new_configuration_element.id
    img_obj_name = f"{i}.png"

    if not pic:
        return Response({"error": "Нет файла для изображения логотипа."})
    result = process_file_upload(pic, client, img_obj_name)

    if 'error' in result:
        return Response(result)

    new_configuration_element.image = result
    new_configuration_element.save()

    return Response({"message": "success"})

def delete_pic(pic):
    client = Minio(
        endpoint=settings.AWS_S3_ENDPOINT_URL,
        access_key=settings.AWS_ACCESS_KEY_ID,
        secret_key=settings.AWS_SECRET_ACCESS_KEY,
        secure=settings.MINIO_USE_SSL
    )
    try:
        client.remove_object('hotel', pic)
        return {"message": "Изображение успешно удалено"}
    except Exception as e:
        return {"error": f"Ошибка при удалении изображения: {str(e)}"}