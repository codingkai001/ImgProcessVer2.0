from django.shortcuts import render_to_response
from django.http import HttpResponse, StreamingHttpResponse, JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.urls import reverse
from .settings import MEDIA_ROOT, ALLOWED_SUFFIX, PRIMARY_KEY, BASE_DIR
import os
from datetime import datetime
import jwt
from jwt.exceptions import DecodeError
import json
from .exceptions import FileTypeError, EmptyFileError


@require_GET
def index(request):
    return render_to_response('index.html')


@require_POST
def license_upload(request):
    """
    接收前端发送的天猫（淘宝）营业执照图片（支持批量），加以处理并提取其中的所需信息，返回表格下载链接
    :param request:
    :return:JsonResponse()
    """
    request_detail = os.path.join(BASE_DIR, 'request_header.log')

    response = HttpResponse()
    response['Content-Type'] = 'application/json;charset=utf-8'
    images = request.FILES
    data = {}
    try:
        if not images:
            raise EmptyFileError("读取文件失败")

        # 记录最近一次请求的数据，方便调试
        with open(request_detail, 'wt', encoding='utf-8') as f:
            for k, v in request.META.items():
                f.write('{0:-<40}{1}\n'.format(k, v))
            for name, file in images.items():
                f.write('name:{0:-<20}filename:{1:-<20}size:{2}Byte\n'.format(name, file.name, file.size))

        upload_dir = os.path.join(MEDIA_ROOT, 'uploads/')
        download_dir = os.path.join(MEDIA_ROOT, 'downloads/')

        for source in images.values():
            suffix = source.name.split('.')[-1].lower()
            if suffix in ALLOWED_SUFFIX:
                file_path = upload_dir + datetime.now().strftime("%Y%m%d%H%M%S%f") + '.' + suffix
                with open(file_path, 'wb') as f:
                    if source.size != 0:
                        for block in source.chunks(1024 * 10):
                            f.write(block)
            else:
                raise FileTypeError("图片格式不支持")

        # 图像处理模块处理完成后将表格保存在 /media/downloads目录下，并且返回excel文件名，供视图调用
        filename = 'tianmao.xlsx'

        encoded_path = jwt.encode({'path': (download_dir + filename)}, PRIMARY_KEY, algorithm='HS256')
        download_link = reverse('license_download') + '?p=' + encoded_path.decode()

        data['status'] = 200
        data['data'] = {'download_link': download_link}
        data['error'] = None

    except EmptyFileError as e:
        data['status'] = 413
        data['data'] = None
        data['error'] = e.value

    except FileTypeError as e:
        data['status'] = 414
        data['data'] = None
        data['error'] = e.value

    except Exception as e:
        data['status'] = 500
        data['data'] = None
        data['error'] = "服务器内部异常:" + e.__str__()

    finally:
        response.write(content=json.dumps(data, ensure_ascii=False))
        return response


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
            decoded_path = jwt.decode(encoded_path, PRIMARY_KEY, algorithms=['HS256']).get('path')

            # 检查文件资源是否存在
            if not os.access(decoded_path, mode=0):
                raise FileNotFoundError

            def file_iterator(file=None, chunk_size=1024):
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
        return JsonResponse(data={'status': 410, 'error': '缺少请求参数'}, json_dumps_params={'ensure_ascii': False})
    except (DecodeError, IndexError):
        return JsonResponse(data={'status': 411, 'error': '请求参数无效'}, json_dumps_params={'ensure_ascii': False})
    except FileNotFoundError:
        return JsonResponse(data={'status': 412, 'error': '请求资源不存在'}, json_dumps_params={'ensure_ascii': False})
    except Exception as e:
        return JsonResponse(data={'status': 500, 'error': '服务器内部错误:' + e.__str__()},
                            json_dumps_params={'ensure_ascii': False})
