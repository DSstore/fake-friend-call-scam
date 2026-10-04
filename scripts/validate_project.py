import _bootstrap
import json
from scamfilm.project import validate
from scamfilm.media import preflight

if __name__=='__main__':
    preflight()
    print(json.dumps(validate(),indent=2))
