from datetime import datetime, timedelta
from typing import Dict, Optional, Union

from werkzeug.utils import cached_property

from kama_sdk.model.supplier.base.supplier import Supplier
from prom_kaml.main.prom_client import PromClient, prom_client
from prom_kaml.main.types import PromMatrix, PromVector


class PromDataSupplier(Supplier):

  @cached_property
  def client(self) -> Optional[PromClient]:
    print("INIT CONFIG")
    print(self.client_config_root)
    if config := self.client_config_root:
      return PromClient(config)
    else:
      return prom_client

  @cached_property
  def step(self) -> str:
    return self.get_prop(STEP_KEY, '1h')

  @cached_property
  def client_config_root(self) -> Optional[Dict]:
    return self.resolve_prop(CLIENT_CONFIG, depth=100)

  @cached_property
  def t0(self) -> datetime:
    offset = self.get_prop(T0_OFFSET_KEY, {'days': 7})
    return parse_from_now(offset)

  @cached_property
  def tn(self) -> datetime:
    offset = self.get_prop(TN_OFFSET_KEY, {})
    return parse_from_now(offset)

  @cached_property
  def serializer_type(self) -> str:
    return self.get_prop('serializer', 'legacy')

  @cached_property
  def _type(self) -> str:
    return self.resolve_prop(
      TYPE_KEY,
      backup='matrix',
      lookback=0
    )

  def resolve(self) -> Union[PromMatrix, PromVector]:
    if self._type == 'matrix':
      response = self.fetch_matrix()
    elif self._type == 'vector':
      response = self.fetch_vector()
    elif self._type == 'ping':
      response = self.ping()
    else:
      print(f"[kama_sdk:prom_supplier] bad req type {self._type}")
      response = None

    return response

  def fetch_matrix(self) -> Optional[PromMatrix]:
    prom_data = self.client.compute_matrix(
      self.source_data(),
      self.step,
      self.t0,
      self.tn
    )
    # print("RAW")
    # print(prom_data)
    return prom_data['result'] if prom_data else None

  def ping(self) -> bool:
    response = self.client.compute_vector("up")
    return response is not None

  def fetch_vector(self) -> Optional[PromVector]:
    prom_data = self.client.compute_vector(
      self.source_data(),
      self.tn
    )
    return prom_data['result'] if prom_data else None

def parse_from_now(expr: Dict) -> datetime:
  difference = {k: int(v) for k, v in expr.items()}
  return datetime.now() - timedelta(**difference)


TYPE_KEY = 'type'
STEP_KEY = 'step'
T0_OFFSET_KEY = 't0_offset'
TN_OFFSET_KEY = 'tn_offset'
CLIENT_CONFIG = 'client_config'
