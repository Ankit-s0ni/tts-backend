import requests
import os
p_in = os.path.join(os.path.dirname(__file__), '..', 'test_inputs', 'hindi_priyamvada_2page.txt')
p_in = os.path.normpath(p_in)
p_out = os.path.join(os.path.dirname(__file__), '..', 'test_outputs', 'priyamvada_from_file_python.wav')
with open(p_in, 'r', encoding='utf8') as fh:
    txt = fh.read()
print('Read input length:', len(txt))
resp = requests.post('http://localhost:8001/tts/sync', json={'text': txt, 'voice': 'hi_IN-priyamvada-medium'}, timeout=300)
print('Status code:', resp.status_code)
if resp.status_code == 200:
    os.makedirs(os.path.dirname(p_out), exist_ok=True)
    with open(p_out, 'wb') as fh:
        fh.write(resp.content)
    print('WROTE:', os.path.abspath(p_out), os.path.getsize(p_out))
else:
    print('Response text:', resp.text)
