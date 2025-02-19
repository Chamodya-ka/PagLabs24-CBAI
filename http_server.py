# import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import cgi
from unittest import removeResult
from urllib.parse import urlparse, parse_qs

import keras
import pickle
import pandas as pd
from sentence_transformers import SentenceTransformer


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    # def __init__(self):


    def do_preprocessing(self,dict):
        test_record = pd.DataFrame.from_dict(dict)
        with (open("./oheEncoder/encoder", "rb")) as openfile:
            loaded_enc = pickle.load(openfile)
            inference_encoded = loaded_enc.transform(test_record[["protocol","code"]])
            inference_feature_names = loaded_enc.get_feature_names_out(trans_columns)
            inference_encoded_df = pd.DataFrame(inference_encoded.toarray(),columns=inference_feature_names)
            inference_df = pd.concat([test_record[["retryCount","description"]],inference_encoded_df], axis=1)
            test_embeddings = embeddings_model.encode(test_record["description"])
            final_inf_date = pd.concat([inference_df, pd.DataFrame(test_embeddings)], axis=1)
            final_inf_date.pop("description")
            return loaded_model(final_inf_date)[0], loaded_model(final_inf_date)[1]

    def do_GET(self):
        print("processing...")
        url = urlparse(self.path)
        query_params = parse_qs(url.query)
        print(query_params)
        body = {}
        body['code'] = (query_params["code"] if ("code" in query_params) else "")
        body['protocol'] = query_params["protocol"] if ("protocol" in query_params) else ""
        body['description'] = query_params["description"] if ("description" in query_params) else ""
        body['retryCount'] = query_params["retryCount"] if ("retryCount" in query_params) else ""
        # ctype, pdict = cgi.parse_header(self.headers['content-type'])
        # pdict['boundary'] = bytes(pdict['boundary'], "utf-8")
        # body = cgi.parse_multipart(self.rfile, pdict)
        #
        print(body)

        print("preprocessing")
        result = self.do_preprocessing(body)

        self.send_response(200)
        self.end_headers()
        # self.wfile.write(json.dumps({'do_retry': result[0], 'timeout': result[1]}))
        # post process
        response = -1
        print(float(result[0]),float(result[1]))
        if (float(result[0])>0.5):
            response = float(result[1])
        self.wfile.write(bytes(str(response),"UTF-8"))


print("loading models")
trans_columns = ['protocol', 'code']
embeddings_model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
loaded_model = keras.saving.load_model("./model/modelsave.keras")

print("loaded models")
httpd = HTTPServer(('', 8000), SimpleHTTPRequestHandler)
httpd.serve_forever()