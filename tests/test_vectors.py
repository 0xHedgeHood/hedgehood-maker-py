"""The canonical vectors of 0xHedgeHood/sdks (vectors/goldens.json), which every maker SDK and the Solidity, gateway
and desk implementations are pinned against: recompute them from their inputs, and check this repo's copies
(tests/goldens.py) against them. CI checks the hub out and sets HEDGEHOOD_VECTORS to that file."""

import json
import os

import goldens as G
import pytest
from eth_utils import keccak

from hedgehood_maker import eip712 as E
from hedgehood_maker.models import Quote, Series
from hedgehood_maker.settler import encode_fill

PATH = os.environ.get("HEDGEHOOD_VECTORS")
pytestmark = pytest.mark.skipif(not PATH, reason="HEDGEHOOD_VECTORS not set (vectors/goldens.json of 0xHedgeHood/sdks)")


@pytest.fixture(scope="module")
def hub():
    with open(PATH) as f:
        return json.load(f)


def hub_quote(v):
    s, q = v["series"], v["quote"]
    series = Series(underlying=s["underlying"], quote=s["quote"], oracle=s["oracle"], expiry=s["expiry"],
                    is_put=s["isPut"], strike=int(s["strike"]), physical=s["physical"])
    return Quote(maker=q["maker"], signer=q["signer"], taker=q["taker"], series=series, side=q["side"],
                 amount=int(q["amount"]), min_fill=int(q["minFill"]), premium=int(q["premium"]),
                 valid_until=q["validUntil"], nonce=int(q["nonce"]), epoch=int(q["epoch"]),
                 external_account=q["externalAccount"])


def test_recomputed_from_the_hub_inputs(hub):
    q = hub_quote(hub)
    assert E.quote_digest(q, hub["chainId"], hub["settler"]) == hub["digest"]
    assert str(E.series_id(q.series)) == hub["seriesId"]
    assert E.sign_quote(q, hub["chainId"], hub["settler"], hub["signerKey"]) == hub["signature"]
    for key, close in (("fillCalldataHash", False), ("closeCalldataHash", True)):
        data = encode_fill(q, hub["signature"], int(hub[key]["amount"]), close=close)
        assert "0x" + keccak(bytes.fromhex(data[2:])).hex() == hub[key]["hash"]
    sep = hub["testnetDomainSeparator"]
    assert "0x" + E.domain_separator(sep["chainId"], sep["settler"]).hex() == sep["value"]
    assert E.SERIES_TYPE_STRING == hub["typeStrings"]["series"]
    assert E.QUOTE_TYPE_STRING == hub["typeStrings"]["quote"]


def test_local_copies_match_the_hub(hub):
    assert hub_quote(hub) == G.QUOTE
    assert (G.CHAIN, G.SETTLER, str(G.SERIES_ID), G.DIGEST, G.SIGNATURE) == \
        (hub["chainId"], hub["settler"], hub["seriesId"], hub["digest"], hub["signature"])
    assert G.SELECTORS == hub["selectors"]
