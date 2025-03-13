import tritonclient.http as httpclient
import base64
import pickle
import numpy as np

# Создаем клиента
triton_client = httpclient.InferenceServerClient(url="localhost:8000")

# Подготавливаем данные для запроса
inputs = []
outputs = []
inputs.append(httpclient.InferInput("input", [1], "BYTES"))
outputs.append(httpclient.InferRequestedOutput("output"))

# Создаем случайный numpy массив и кодируем его
input_array = np.random.rand(5, 5, 3).astype('uint8')
encoded_input = base64.b64encode(pickle.dumps(input_array)).decode('utf-8')

# Устанавливаем значение для входного тензора
input_data = np.array([encoded_input], dtype=object)
inputs[0].set_data_from_numpy(input_data)


# Выполняем запрос
results = triton_client.infer(model_name="easyocr_detector", inputs=inputs, outputs=outputs)

# Получаем результат
output_data = results.as_numpy("output")
decoded_output = pickle.loads(base64.b64decode(output_data[0]))
print(f"Output: {decoded_output}")
