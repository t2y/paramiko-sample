import logging
import warnings

logging.getLogger('paramiko').setLevel(logging.WARNING)
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                    level=logging.INFO)
log = logging.getLogger(__file__)

warnings.filterwarnings(action='ignore', module='.*paramiko.*')
