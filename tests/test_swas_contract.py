"""Structural regression checks for the public SWAS contract; no network or runtime calls."""
from __future__ import annotations
import copy
import re
import sys
import unittest
from pathlib import Path
import yaml

ROOT = Path(sys.argv.pop(1)).resolve() if len(sys.argv) > 1 and not sys.argv[1].startswith('-') else Path(__file__).resolve().parents[1]
SPEC = ROOT / 'leaflow/swas/v1/openapi.yaml'
EXPECTED = {
 ('GET','/api/v1/catalog/plans'):'list-plans',
 ('POST','/api/v1/purchases'):'create-purchase',
 ('GET','/api/v1/purchases/{purchaseId}'):'get-purchase',
 ('GET','/api/v1/instances'):'list-instances',
 ('GET','/api/v1/instances/{instanceId}'):'get-instance',
 ('POST','/api/v1/instances/{instanceId}:start'):'start-instance',
 ('GET','/api/v1/instances/{instanceId}/operations/{operationId}'):'get-instance-operation',
 ('POST','/api/v1/instances/{instanceId}:stop'):'stop-instance',
 ('GET','/api/v1/instances/{instanceId}/cancellations/{cancellationId}/refund-progress'):'get-cancellation-refund-progress',
 ('POST','/api/v1/instances/{instanceId}:reboot'):'reboot-instance',
}
class Strict(yaml.SafeLoader): pass
def no_duplicates(loader,node,deep=False):
 seen=set()
 for key,_ in node.value:
  value=loader.construct_object(key,deep=deep)
  if value in seen: raise yaml.YAMLError('duplicate YAML key: '+str(value))
  seen.add(value)
 return yaml.SafeLoader.construct_mapping(loader,node,deep)
Strict.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,no_duplicates)
def load(path): return yaml.load(path.read_text(encoding='utf-8'),Loader=Strict)
def walk(value):
 if isinstance(value,dict):
  yield value
  for child in value.values(): yield from walk(child)
 elif isinstance(value,list):
  for child in value: yield from walk(child)
def resolve(ref,source=SPEC):
 file,sep,fragment=ref.partition('#')
 target=(source.parent/file).resolve() if file else source.resolve()
 target.relative_to(ROOT)
 value=load(target)
 for part in fragment.split('/')[1:]: value=value[part.replace('~1','/').replace('~0','~')]
 return value,target
def routes(doc):
 return {(method.upper(),path):operation['operationId'] for path,item in doc['paths'].items() for method,operation in item.items() if method in ('get','post','put','patch','delete')}
def require_contract(doc):
 assert routes(doc)==EXPECTED,'public method/path/operationId drift'
 schemas=doc['components']['schemas']
 assert schemas['Error']=={'$ref':'../../type/v1/error.yaml#/components/schemas/Error'},'shared Error required'
 assert schemas['InstancePagination']=={'$ref':'../../type/v1/pagination.yaml#/components/schemas/OffsetPagination'},'shared pagination required'
 return doc

class SWASContract(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  if not SPEC.is_file(): raise FileNotFoundError('SWAS public contract missing: '+str(SPEC))
  cls.doc=load(SPEC);cls.schemas=cls.doc['components']['schemas']
 def test_service_endpoint(self): self.assertEqual(self.doc['servers'],[{'url':'https://swas.leaflow.cloud','description':'SWAS API'}])
 def test_routes_and_operation_ids(self): require_contract(self.doc)
 def test_old_action_path_rejected(self):
  bad=copy.deepcopy(self.doc);bad['paths']['/api/v1/instances/{instanceId}/reboot']=bad['paths'].pop('/api/v1/instances/{instanceId}:reboot')
  with self.assertRaises(AssertionError):require_contract(bad)
 def test_old_error_and_pagination_rejected(self):
  for key,value in [('Error',{'type':'object','required':['code']}),('InstancePagination',{'type':'object','properties':{'total':{'type':'integer'}}})]:
   bad=copy.deepcopy(self.doc);bad['components']['schemas'][key]=value
   with self.assertRaises(AssertionError):require_contract(bad)
 def test_shared_error(self):
  error,_=resolve(self.schemas['Error']['$ref'])
  self.assertEqual(set(error['required']),{'status','message'});self.assertIs(error['additionalProperties'],False)
  self.assertEqual(error['properties']['status'],{'type':'integer','format':'int64'})
  self.assertEqual(error['properties']['message']['type'],'string')
  self.assertEqual(error['properties']['code']['type'],'string')
  self.assertEqual(error['properties']['meta']['type'],'object')
 def test_shared_pagination(self):
  value,_=resolve(self.schemas['InstancePagination']['$ref'])
  self.assertEqual(set(value['required']),{'page','page_size'});self.assertNotIn('total',value['properties'])
  self.assertEqual(value['properties']['total_count'],{'type':'integer','format':'int64','minimum':0})
  query=self.doc['paths']['/api/v1/instances']['get']['parameters']
  page,_=resolve(next(x['$ref'] for x in query if x.get('$ref','').endswith('/Page')))
  size,_=resolve(next(x['$ref'] for x in query if x.get('$ref','').endswith('/PageSize')))
  self.assertEqual(page['schema']['default'],1);self.assertEqual(page['schema']['maximum'],2147483647)
  self.assertEqual(size['schema']['default'],50);self.assertEqual(size['schema']['maximum'],200)
  self.assertEqual(self.schemas['InstanceList']['properties']['items']['maxItems'],size['schema']['maximum'])
 def test_money_precision(self):
  amount=self.schemas['DecimalAmount'];money,_=resolve(amount['allOf'][0]['$ref']);self.assertEqual(money['type'],'string')
  pattern=amount['allOf'][1]['pattern']
  for good in ('0','0.0000000001','999999999999999.9999999999'):self.assertIsNotNone(re.fullmatch(pattern,good))
  for bad in ('-1','1e3','01','1.00000000001','1000000000000000'):self.assertIsNone(re.fullmatch(pattern,bad))
 def test_unknown_refunds_are_not_zero_or_settled(self):
  refund=self.schemas['CustomerRefundProgress'];self.assertEqual(refund['properties']['state']['const'],'unknown')
  self.assertEqual(refund['properties']['amount'],{'type':'null'});self.assertEqual(refund['properties']['currency'],{'type':'null'})
  self.assertEqual(self.schemas['SupplierRefundProgress']['properties']['state']['const'],'not_observed')
 def test_auth_and_idempotency(self):
  self.assertEqual(self.doc['security'],[{'ScopedToken':[]}])
  self.assertEqual(self.doc['components']['securitySchemes']['ScopedToken'],{'$ref':'../../type/v1/security.yaml#/components/securitySchemes/ScopedToken'})
  for path,item in self.doc['paths'].items():
   if 'post' not in item:continue
   operation=item['post'];keys=[x for x in operation.get('parameters',[]) if x.get('name')=='Idempotency-Key']
   self.assertEqual(len(keys),1,path);self.assertTrue(keys[0]['required'])
   self.assertEqual(operation['responses']['202']['content']['application/json']['schema']['$ref'], '#/components/schemas/Purchase' if path=='/api/v1/purchases' else '#/components/schemas/ManagementOperation')
 def test_all_references_and_required_properties(self):
  documents={SPEC};seen=set()
  while documents:
   source=documents.pop()
   if source in seen:continue
   seen.add(source)
   for node in walk(load(source)):
    if '$ref' in node:
     _,target=resolve(node['$ref'],source);documents.add(target)
    if node.get('type')=='object' and 'properties' in node:
     self.assertTrue(set(node.get('required',[]))<=set(node['properties']))
  self.assertGreaterEqual(len(seen),5)
 def test_no_review_wrapper_or_private_extensions(self):
  self.assertEqual(self.doc['info']['title'],'Leaflow SWAS API')
  self.assertEqual(self.doc['openapi'],'3.2.1')
  self.assertNotIn('candidate',self.doc['info']['description'].lower())
  for node in walk(self.doc):self.assertFalse(any(str(k).startswith('x-') for k in node))
 def test_utc_timestamp_descriptions(self):
  fields=[x for x in walk(self.doc) if x.get('format')=='date-time'];self.assertGreater(len(fields),5)
  for field in fields:self.assertIn('UTC RFC 3339',field['description'])

if __name__=='__main__':unittest.main(verbosity=2)
