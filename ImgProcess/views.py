from django.shortcuts import render_to_response
from django.http import HttpResponse, StreamingHttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.urls import reverse
from .settings import MEDIA_ROOT, ALLOWED_SUFFIX, PRIMARY_KEY, BASE_DIR
import os
from datetime import datetime
import jwt
from jwt.exceptions import DecodeError


@csrf_exempt
@require_GET
def index(request):
    return render_to_response('index.html')


@csrf_exempt
@require_POST
def license_upload(request):
    """
    接收前端发送的天猫（淘宝）营业执照图片（支持批量），加以处理并提取其中的所需信息，返回表格下载链接
    :param request:
    :return:JsonResponse()
    """
    request_detail = os.path.join(BASE_DIR, 'request_header.log')
    with open(request_detail, 'wt', encoding='utf-8') as fs:
        for k, v in request.META.items():
            fs.write('{0}---{1}\n'.format(k, v))

    response = HttpResponse()
    response['Content-Type'] = 'application/json'

    try:
        upload_dir = os.path.join(MEDIA_ROOT, 'uploads/')
        download_dir = os.path.join(MEDIA_ROOT, 'downloads/')
        # 前端验证文件是否非空，文件格式是否正确
        for source in request.FILES.values():
            suffix = source.name.split('.')[-1]
            if suffix in ALLOWED_SUFFIX:
                file_path = upload_dir + datetime.now().strftime("%Y%m%d%H%M%S%f") + '.' + suffix
                with open(file_path, 'wb') as f:
                    if source.size != 0:
                        for block in source.chunks():
                            f.write(block)

        # 图像处理模块处理完成后将表格保存在/media/downloads目录下，并且返回excel文件名，供视图调用
        filename = 'tianmao.xlsx'

        encoded_path = jwt.encode({'path': str(download_dir + filename)}, PRIMARY_KEY, algorithm='HS256')
        download_link = reverse('license_download') + '?p=' + encoded_path.__str__()

        response.write(content={
            'status': 200,
            'data': {
                'download_link': download_link,
            }
        })
        return response
    except Exception as e:
        print(e)
        response.write(content={
            'status': 500,
            'data': {}
        })


@csrf_exempt
@require_GET
def license_download(request):
    """
    天猫（淘宝）营业执照信息表格下载接口, 返回文件流
    :param request:
    :return: StreamingHttpResponse()
    """
    try:
        encoded_path = request.GET.get('p')
        if encoded_path:
            encoded_path = str(encoded_path).split("'")[1]
            decoded_path = jwt.decode(encoded_path, PRIMARY_KEY, algorithms=['HS256']).get('path')

            # 检查文件资源是否存在
            if not os.access(decoded_path, mode=0):
                raise FileNotFoundError

            def file_iterator(file=None, chunk_size=512):
                with open(file, 'rb') as f:
                    while True:
                        c = f.read(chunk_size)
                        if c:
                            yield c
                        else:
                            break

            response = StreamingHttpResponse(file_iterator(decoded_path))
            response['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            response['Content-Disposition'] = 'attachment; filename="{0}"' \
                .format(datetime.now().strftime("%Y%m%d%H%M%S") + '.xlsx')
            return response
        else:
            raise KeyError

    except KeyError:
        # 捕获参数p不存在异常
        return JsonResponse(data={'status': 410})
    except (DecodeError, IndexError):
        # 捕获参数值异常
        return JsonResponse(data={'status': 411})
    except FileNotFoundError:
        # 捕获文件不存在异常
        return JsonResponse(data={'status': 412})
    except Exception:
        # 未知异常
        return JsonResponse(data={'status': 500})
