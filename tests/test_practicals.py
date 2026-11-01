import importlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch, Mock
import numpy as np
from PIL import Image
from fastapi.testclient import TestClient
ROOT=Path(__file__).resolve().parents[1]

def module(n,name):
    for key in list(sys.modules):
        if key=='app' or key.startswith('app.'): del sys.modules[key]
    sys.path.insert(0,str(ROOT/f'pr{n}'))
    try: return importlib.import_module('app.'+name)
    finally: sys.path.pop(0)

class WeatherTests(unittest.TestCase):
    def setUp(self): self.w=module(1,'weather')
    def test_current_and_params(self):
        city={'results':[{'name':'Київ','latitude':50,'longitude':30}]}
        weather={'current':{'temperature_2m':15,'wind_speed_10m':8,'time':'2026-01-01T12:00'}}
        with patch.object(self.w.requests,'get',side_effect=[Mock(status_code=200,json=lambda:city),Mock(status_code=200,json=lambda:weather)]) as get:
            self.assertEqual(self.w.get_current_weather('Київ')['temperature'],15)
            self.assertIn('timeout',get.call_args.kwargs)
            self.assertIn('params',get.call_args.kwargs)
    def test_empty_and_missing(self):
        with self.assertRaises(self.w.WeatherError) as c:self.w.find_city(' ')
        self.assertEqual(c.exception.status,422)
        with patch.object(self.w,'request_json',return_value={}):
            with self.assertRaises(self.w.WeatherError) as c:self.w.find_city('unknown')
            self.assertEqual(c.exception.status,404)
    def test_bad_json_timeout_status(self):
        cases=[(Mock(status_code=200,json=Mock(side_effect=ValueError())),502),(Mock(status_code=400),502),(Mock(status_code=500),503)]
        for response,status in cases:
            with patch.object(self.w.requests,'get',return_value=response):
                with self.assertRaises(self.w.WeatherError) as c:self.w.request_json('x',{})
                self.assertEqual(c.exception.status,status)
        with patch.object(self.w.requests,'get',side_effect=self.w.requests.Timeout()):
            with self.assertRaises(self.w.WeatherError) as c:self.w.request_json('x',{})
            self.assertEqual(c.exception.status,504)
    def test_nonfinite_data(self):
        for value in [None,True,float('nan'),'4']:
            with self.assertRaises(self.w.WeatherError):self.w.number(value)
    def test_endpoint(self):
        m=module(1,'main')
        with TestClient(m.app) as c:
            self.assertEqual(c.get('/').status_code,200)
            self.assertEqual(c.get('/api/weather?city=').status_code,422)

class DetectionTests(unittest.TestCase):
    def test_invalid_image(self):
        d=module(2,'detector')
        for data in [b'',b'not image']:
            with self.assertRaises(d.DetectionError):d.detect(data)
        with self.assertRaises(d.DetectionError):d.detect(b'x',2)
    def test_result_serialization(self):
        d=module(2,'detector');f=io.BytesIO();Image.new('RGB',(20,30)).save(f,format='PNG')
        box=Mock();box.cls.item.return_value=0;box.conf.item.return_value=.9;box.xyxy=[Mock()];box.xyxy[0].tolist.return_value=[1,2,10,20]
        model=Mock(names={0:'person'});model.predict.return_value=[Mock(boxes=[box])]
        with patch.object(d,'load_model',return_value=model):
            r=d.detect(f.getvalue());self.assertEqual(r['count'],1);self.assertEqual(r['objects'][0]['class'],'person')
    def test_upload_endpoint(self):
        m=module(2,'main')
        with TestClient(m.app) as c:
            self.assertEqual(c.get('/').status_code,200)
            self.assertEqual(c.post('/api/detect',files={'image':('bad.txt',b'bad')}).status_code,422)

class LLMTests(unittest.TestCase):
    def test_messages(self):
        m=module(3,'llm');messages=m.build_messages('q','policy')
        self.assertEqual(len(messages),3);self.assertEqual(messages[-1]['role'],'user')
        with self.assertRaises(m.LLMError):m.ask(' ','rules')
    def test_missing_key(self):
        m=module(3,'main')
        with patch.dict(os.environ,{'LLM_API_KEY':''}),TestClient(m.app) as c:
            self.assertEqual(c.post('/api/ask',json={'question':'q'}).status_code,503)
    def test_retry_and_auth(self):
        t=module(3,'transport')
        import httpx,openai
        req=httpx.Request('POST','https://example.test')
        rate=openai.RateLimitError('limited',response=httpx.Response(429,request=req),body=None)
        auth=openai.AuthenticationError('bad',response=httpx.Response(401,request=req),body=None)
        client=Mock();response=Mock();response.choices=[Mock(finish_reason='stop',message=Mock(content='ok'))]
        with patch.dict(os.environ,{'LLM_MODEL':'test'}),patch.object(t,'get_client',return_value=client),patch.object(t.time,'sleep'):
            client.chat.completions.create.side_effect=[rate,response]
            self.assertIs(t.complete([]),response)
            self.assertEqual(client.chat.completions.create.call_count,2)
            client.chat.completions.create.reset_mock();client.chat.completions.create.side_effect=auth
            with self.assertRaises(t.LLMError):t.complete([])
            self.assertEqual(client.chat.completions.create.call_count,1)
    def test_schema(self):
        s=module(4,'schema');valid={'reply':'Так','topic':'order','grounded':True,'needs_clarification':False,'handoff':False,'order_number':'123456'}
        self.assertEqual(s.validate(json.dumps(valid))['order_number'],'123456')
        for update in [{'extra':1},{'grounded':'yes'},{'order_number':'123'},{'topic':'anything'}]:
            with self.assertRaises(ValueError):s.validate(json.dumps({**valid,**update}))
    def test_budget(self):
        m=module(4,'llm');history=[{'role':r,'content':'x'*2000} for _ in range(20) for r in ['user','assistant']]
        with patch.dict(os.environ,{'LLM_TOKEN_BUDGET':'2000'}):
            messages=m.build_messages('q',history,'rules')
            self.assertLessEqual(m.estimate(messages),2000)
            self.assertEqual(messages[-1]['content'],'q')
            self.assertIn('rules',messages[1]['content'])
    def test_fabricated_order(self):
        m=module(4,'llm')
        raw=json.dumps({'reply':'ok','topic':'order','grounded':True,'needs_clarification':False,'handoff':False,'order_number':'999999'})
        response=Mock();response.choices=[Mock(message=Mock(content=raw))]
        with patch.object(m,'complete',return_value=response):
            with self.assertRaises(m.LLMError):m.ask('Мій номер 123456',[],'rules')
    def test_sessions_isolated_and_reset(self):
        m=module(4,'main');result={'result':{'reply':'ok'},'model':'fake','usage':{},'elapsed':0}
        with patch.object(m.llm,'ask',return_value=result) as ask,TestClient(m.app) as a,TestClient(m.app) as b:
            self.assertEqual(a.post('/api/chat',json={'message':'first'}).status_code,200)
            a.post('/api/chat',json={'message':'second'});self.assertEqual(len(ask.call_args.args[1]),2)
            b.post('/api/chat',json={'message':'other'});self.assertEqual(ask.call_args.args[1],[])
            a.post('/api/reset');a.post('/api/chat',json={'message':'new'});self.assertEqual(ask.call_args.args[1],[])
            self.assertEqual(a.post('/api/chat',json={'message':'x','history':[]}).status_code,422)

class SearchTests(unittest.TestCase):
    def test_chunks_preserve_sources(self):
        d=module(5,'documents');chunks=d.load_chunks()
        self.assertEqual(len({c.source for c in chunks}),16)
        self.assertTrue(all(c.text and c.metadata['title'] for c in chunks))
    def test_index_roundtrip_and_filter_before_topk(self):
        idx=module(5,'index');C=idx.Chunk
        chunks=[C('internal','a',{'audience':'персонал'}),C('public','b',{'audience':'клієнти'})]
        data=idx.build(chunks,np.array([[1,0],[.9,.1]]),'test')
        hit=idx.search(data,np.array([1.,0.]),1,{'audience':'клієнти'})
        self.assertEqual(hit[0].chunk.source,'b')
        with tempfile.TemporaryDirectory() as temp:
            idx.save(data,Path(temp));loaded=idx.load(Path(temp));self.assertEqual(loaded.model_name,'test')
            np.testing.assert_allclose(loaded.vectors,data.vectors)
        with self.assertRaises(ValueError):idx.search(data,np.array([1.,0.]),filters={'unknown':'x'})
    def test_keyword_exact_code(self):
        kw=module(5,'keyword');d=importlib.import_module('app.documents')
        hits=kw.search(kw.build(d.load_chunks()),'OR-X2-BLK',filters={'audience':'клієнти'})
        self.assertEqual(hits[0].chunk.source,'інструкція-навушники-оріон-x2.md')
    def test_no_index_and_bad_request(self):
        m=module(5,'main')
        with patch('app.search_service.index.load',side_effect=ValueError('build index')),TestClient(m.app) as c:
            self.assertFalse(c.get('/api/status').json()['ready'])
            self.assertEqual(c.post('/api/search',json={'query':'q'}).status_code,503)
            self.assertEqual(c.post('/api/search',json={'query':' ','mode':'bad'}).status_code,422)
    def test_access_policy(self):
        s=module(5,'search_service');service=s.SearchService();service.idx=Mock()
        with self.assertRaises(PermissionError):service.search('q','both',5,{'audience':'персонал'},None)

if __name__=='__main__':unittest.main()
