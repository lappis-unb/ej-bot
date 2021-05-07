import os
import time
import logging
import pathlib

# This script cleans trained models if there are more than 10

MODELS_LIMIT = 10
logger = logging.getLogger(__name__)

current_time = time.time()
current_path = pathlib.Path(__file__).parent.absolute()
back_directory = os.path.normpath(str(current_path) + os.sep + os.pardir)
models_path = os.path.join(str(back_directory), "bot/models")

models_file_list = os.listdir(models_path)
models_file_list_by_date = sorted(
    pathlib.Path(models_path).iterdir(), key=os.path.getmtime
)

total_models = len(models_file_list)
if len(models_file_list) > MODELS_LIMIT:
    # if there are more than 10 models, some must be deleted
    i = 0
    while i < (total_models - MODELS_LIMIT):
        print(models_file_list_by_date[i])
        file_path = os.path.join(models_path, models_file_list_by_date[i])
        os.unlink(file_path)
        logger.debug("{} removed".format(models_file_list_by_date[i]))
        i = i + 1
