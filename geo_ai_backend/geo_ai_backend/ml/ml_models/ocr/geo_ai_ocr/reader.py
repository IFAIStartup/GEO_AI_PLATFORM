import base64
import pickle
import numpy as np
from typing import Tuple, List, Dict, Sequence, Any
import tritonclient.http as httpclient


class TritonEasyocrReader:
    def __init__(
            self, 
            client: httpclient.InferenceServerClient, 
            model_name: str) -> None:
        
        self.client = client
        self.model_name = model_name
        
    def __call__(self, img: np.ndarray, *args, **kwargs) -> Any:
        inputs = [httpclient.InferInput("input", [1], "BYTES")]
        outputs = [httpclient.InferRequestedOutput("output")]

        encoded_input = base64.b64encode(pickle.dumps(img)).decode('utf-8')
        input_data = np.array([encoded_input], dtype=object)
        inputs[0].set_data_from_numpy(input_data)

        results = self.client.infer(model_name=self.model_name, inputs=inputs, outputs=outputs)

        output_data = results.as_numpy("output")
        decoded_output = pickle.loads(base64.b64decode(output_data[0]))
        return decoded_output

