#!/usr/bin/env python3
"""One fresh model context per item; only public observations and simulator replies.
The returned snapshot must equal TRACE_MODEL. Credentials are never archived.
"""
import json,os,sys,time,urllib.request,urllib.error

TRANSPORT_RULES='''Return exactly one JSON object, with no markdown or prose.
Submit one explanation using {"answer":{"cells":[integer cell IDs]}}.
If no explanation exists, submit {"answer":{"verdict":"no_explanation"}}.
Only when simulator probes are permitted, you may instead request
{"probe":{"changes":{"0":1}}}. Changes maps cell IDs to replacement 0/1 values;
omitted cells keep recorded values. You will receive the simulator result.
Use the original deadline. Do not request other tools.'''

def emit(obj):print(json.dumps(obj,separators=(',',':')),flush=True)

def main():
    first=json.loads(sys.stdin.readline());obs=first['observation']
    model=os.environ['TRACE_MODEL'];key=os.environ['TRACE_API_KEY']
    generation=json.loads(os.environ.get('TRACE_GENERATION_JSON','{}'))
    if not isinstance(generation,dict) or set(generation)-{'temperature','top_p','seed','max_completion_tokens','reasoning_effort'}:raise ValueError('Unsupported generation setting')
    if type(generation.get('max_completion_tokens')) is not int or generation['max_completion_tokens']<1:raise ValueError('Declare a positive max_completion_tokens budget')
    base=os.environ.get('TRACE_API_BASE','https://api.openai.com/v1').rstrip('/')
    messages=[{'role':'system','content':obs['instructions']+'\n'+TRANSPORT_RULES},
              {'role':'user','content':json.dumps(obs,separators=(',',':'))}]
    for _ in range(obs['limits']['probes']+1):
        remaining=obs['deadline']-time.time()
        if remaining<=0:return
        body={'model':model,'messages':messages,'store':False,**generation}
        req=urllib.request.Request(base+'/chat/completions',data=json.dumps(body).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer '+key})
        sent_at=time.time()
        audit={'requested_model':model,'generation':generation,'request_messages':messages.copy(),'request_started_at':sent_at}
        try:
            with urllib.request.urlopen(req,timeout=remaining) as response:
                result=json.load(response);request_id=response.headers.get('x-request-id')
        except urllib.error.HTTPError as error:
            audit.update(response_received_at=time.time(),http_status=error.code)
            emit({'technical_error':'Provider HTTP '+str(error.code),'_metadata':audit});return
        except (urllib.error.URLError,TimeoutError) as error:
            audit.update(response_received_at=time.time(),transport_error=type(error).__name__)
            emit({'technical_error':'Provider transport unavailable: '+type(error).__name__,'_metadata':audit});return
        audit.update(response_received_at=time.time(),provider_created_at=result.get('created'),returned_model=result.get('model'),request_id=request_id,usage=result.get('usage'))
        if result.get('model')!=model:
            emit({'technical_error':'Returned model snapshot is missing or differs from the registered TRACE_MODEL','_metadata':audit});return
        message=result['choices'][0]['message'];raw=message.get('content');finish=result['choices'][0].get('finish_reason')
        audit.update(finish_reason=finish,raw_content=raw,refusal=message.get('refusal'))
        if finish!='stop' or message.get('refusal'):
            emit({'answer':{'invalid_model_output':'Provider finish/refusal status: '+str(finish)},'_metadata':audit});return
        try:action=json.loads(raw)
        except (TypeError,ValueError):emit({'answer':{'invalid_model_output':raw},'_metadata':audit});return
        if not isinstance(action,dict) or set(action) not in ({'answer'},{'probe'}):emit({'answer':{'invalid_model_output':action},'_metadata':audit});return
        emit({**action,'_metadata':audit})
        if 'answer' in action:return
        reply=json.loads(sys.stdin.readline())
        messages += [{'role':'assistant','content':raw},{'role':'user','content':json.dumps(reply)}]
    emit({'answer':{'invalid_model_output':'No final answer within the action budget'}})

if __name__=='__main__':
    try:main()
    except (KeyError,ValueError,IndexError,TypeError) as error:
        # Avoid including provider bodies or environment values in error messages.
        emit({'technical_error':'Adapter configuration/provider schema error: '+type(error).__name__})
