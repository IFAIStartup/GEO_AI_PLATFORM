# Inference SuperResolution Demo

## Настройка среды

1. Убедитесь, что вы используете версию Docker, которая поддерживает GPU. Версия Docker должна быть 19.03 или выше.

2. Убедитесь, что вы установили драйвер NVIDIA в среду где запускается docker командой: 
$ nvidia-smi

В результате должна появится примерно следующее изображение:
<p align="center">
  <img src="../../../../geo_ai_superresolution/HAT/images/nvidia-smi.png" />
</p>

2.1. При отсутствии драйверов выполните шаг 2.1.1 или 2.1.2. 

2.1.1. Для выбора драйвера CUDA используем страницу: https://developer.nvidia.com/cuda-downloads

Пример для запуска под wsl2(Ubuntu20.04) и Ubuntu20.04:

$ wget https://developer.download.nvidia.com/compute/cuda/12.1.1/local_installers/cuda_12.1.1_530.30.02_linux.run
$ sudo sh cuda_12.1.1_530.30.02_linux.run 

2.1.2. Альтеративный сопособ(вместо шагов с CUDA):
Подобрать драйвера Nvidia под присутствующую видекарту можно по ссылке ниже:
https://www.nvidia.com/Download/index.aspx?lang=en-us

Пример для запуска под wsl2(Ubuntu20.04) и Ubuntu20.04:

$ wget https://us.download.nvidia.com/XFree86/Linux-x86_64/535.54.03/NVIDIA-Linux-x86_64-535.54.03.run
$ sudo sh NVIDIA-Linux-x86_64-535.54.03.run

3. Настройка NVIDIA Container Toolkit(в случае если это не делалось ранее).

Настройте репозиторий пакетов и ключ GPG:

$ distribution=$(. /etc/os-release;echo $ID$VERSION_ID) \
      && curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
      && curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
            sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
            sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list


Установите nvidia-container-toolkitпакет (и зависимости) после обновления списка пакетов:

$ sudo apt-get update

$ sudo apt-get install -y nvidia-container-toolkit

Настройте демон Docker для распознавания среды выполнения контейнеров NVIDIA:

$ sudo nvidia-ctk runtime configure --runtime=docker

Перезапустите демон Docker, чтобы завершить установку после установки среды выполнения по умолчанию:

$ sudo systemctl restart docker

На этом этапе рабочую настройку можно протестировать, запустив базовый контейнер CUDA:

sudo docker run --rm --runtime=nvidia --gpus all nvidia/cuda:10.1-base nvidia-smi

В результате должна появится примерно следующее изображение:
<p align="center">
  <img src="../../../../geo_ai_superresolution/HAT/images/nvidia-smi.png" />
</p>


## Настройка Docker образов

Инференс модели нейронной сети для Super Resolution происходит при помощи Nvidia Triton Inference Server и скриптов на Python. Сборка исходников осуществляется при помощи создания Docker образов.

Первоначально необходимо локально загрузить исходные файлы при помощи команды:

`git clone https://gitlab.compvisionsys.com/geo_ai/geo_ai_superresolution.git`


Далее необходимо перейти в каталог `/geo_ai_superresolution/HAT/inference` вставить входное изображение и создать директорию `/models_inference` куда загрузить модель 
и собрать образ командой:

`docker build -t hat_triton_inference -f Dockerfile .`

После этого необходимо загрузить образ nvidia triton (~12Gb) командой:

`docker pull nvcr.io/nvidia/tritonserver:22.08-py3`


Также необходимо создать общий network для связи запускаемых контейнеров:

`docker network create triton`





<!-- Также запускается образ самого инференса:

`sudo docker run --network triton_network --rm -it -v ./inputs:/superresolution/inputs -v ./outputs:/superresolution/outputs hat_triton_inference bash` -->

На этом создание и загрузка необходимых образов закончена

## Описание функций для инференса

За инференс отвечает файл `triton_inference.py`, который может быть использован как через его отдельные функции, так и вызван напрямую. Описание функций:

### *img_preproc*

Принимает на вход исходное изображение в виде матрицы (h x w x 3) формата BGR. На выходе возвращает тензор, преобразованный для входа в модель нейронной сети (1 x 3 x h x w) формата RGB.

### *img_postproc*

Принимает на вход выходной тензор модели нейронной сети (1 x 3 x H x W) формата RGB. На выходе возвращает стандартную матрицу изображения формата BGR, готовую для сохранения или дальнейшего использования средствами *OpenCV*.

### *inference_triton*

Проивзодит непосредственно инференс через выбранную и развёрнутую на Triton сервере модели нейронной сети. На вход принимает тензор преобразованного исходного изображения (1 x 3 x h x w), имя используемой модели и Triton клиент, получаемый при помощи функции:

```python
triton_client = httpclient.InferenceServerClient(url=triton_server_url)
```

В качестве *triton_server_url* обычно используются 172.18.0.2:8000 при запуске через docker, либо localhost:8000 при запуске без docker. Но также может быть необходима дополнительная проверка (см. ниже).

На выходе выдаёт тензор (1 x 3 x H x W), где H и W - увеличенные высота и ширина для исходного изображения. Далее тензор может быть преобразован в вид стандартного изображения при помощи функции *img_postproc*.

### *inference_pipeline*

Упрощённая функция для получения готового увеличенного изображения из исходного. На вход принимает исходное изображение в стандартном формате (h x w x 3), имя модели и URL Triton сервера. 
На выходе выдаёт увеличенное изображение также в стандартном формате (H x W x 3).

## Примеры использования

После сборки образов Docker для Triton и нашего репозитория, необходимо произвести от них запуск контейнеров. 

Сперва запускается контейнер для Triton Inference Server:

`docker run --gpus=all --network triton --name triton_server --rm -p 8000:8000 -p8001:8001 -p8002:8002 -v ./models_inference:/models nvcr.io/nvidia/tritonserver:22.08-py3 tritonserver --model-repository=/models`
, где `./models_inference` - путь к модели.

Успешно запущенное окно терминала может быть оставлено. Дальнейшие действия следует проводить в другом окне. 

Для проверки http адреса запущенного контейнера необходимо использовать команду:

`docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' triton_server`

Полученный результат необходимо исопльзовать как первую часть url адреса Triton сервера при запуске скрипта triton_inference.py.


Далее запускается образ самого инференса:

`docker run --network triton --rm -it -v ./inputs:/superresolution/inputs -v ./outputs:/superresolution/outputs hat_triton_inference bash`

В результате будет запущена bash оболочка контейнера, через которую можно осуществлять связь с инференс файлом через команду:

`python triton_inference.py --weights Aerial_HAT-L_SRx4_11980 --img_dst ./3768_320.png --img_save ./outputs/3768_320x4.png --url 172.19.0.2:8000 `

Опции: 

--weights - название модели(точное из models_inference)

--img_dst - путь к входному изображению

--img_save - путь к выходному изображению

--url - ip контейнера и порт

Название модели и путь ко входному и выходному изображениям может использоваться свой. Адрес сервера в большинстве случаев стандартный, но может отличаться (необходима предварительная проверка через `docker inspect`).

## Примеры изображений:

*Исходное изображение 320х320:*

<p align="center">
  <img src="../images/3768_320.png" />
</p>

___

_Обработанное изображение 1280х1280:_

<p align="center">
  <img src="../images/3768_320x4.png" />
</p>


<!-- #TODO: рассказать про все функции в скрипте для инфа, входные выходные данные, показать картинки, нарисовать схемки пайплайна и сетки, рассказать про струткутру каталогов для triton -->



