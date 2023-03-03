import sys

from compiam.utils import get_tool_list
from compiam.data import models_dict

# Import tasks
from compiam.timbre.stroke_classification.mridangam_stroke_classification import (
    MridangamStrokeClassification,
)


# Show user the available tools
def list_tools():
    pre_trained_models = [
        x["class_name"] for x in list(models_dict.values())
    ]  # Get list of pre-trained_models
    return [
        tool + "*" if tool in pre_trained_models else tool
        for tool in get_tool_list(modules=sys.modules[__name__])
    ]
