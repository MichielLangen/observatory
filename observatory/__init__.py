from observatory.tracking import start_run
from observatory.settings import configure
from observatory.serving import download_model


LABEL_PATTERN = '^(?![0-9]+$)(?!-)[a-zA-Z0-9-]{,63}(?<!-)$'