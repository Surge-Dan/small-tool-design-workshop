"""Embed tested model in a self-contained offline HTML, no build needed by end users."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parent
source=(ROOT/'screen.html').read_text(encoding='utf-8')
source=source.replace('</style>',(ROOT/'fidelity.css').read_text(encoding='utf-8')+'\n</style>',1)
core=(ROOT/'core.js').read_text(encoding='utf-8')
assert source.count('/*__CORE__*/')==1
target=ROOT/'index.html'
target.write_bytes(source.replace('/*__CORE__*/',core).encode('utf-8'))
(ROOT/'version.json').write_bytes((json.dumps({'html':'index.html','sha256':hashlib.sha256(target.read_bytes()).hexdigest()},indent=2)+'\n').encode('utf-8'))
print('Built',target.name,target.stat().st_size,'bytes')
