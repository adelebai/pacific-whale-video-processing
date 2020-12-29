
from PIL import Image

import torch
import torch.nn as nn
import torch.optim as optim
from torch import argmax
from torch.optim import lr_scheduler
from torchvision import datasets, models, transforms

from model.model_base import model_base

# implementation of model on pytorch.
class model_pytorch(model_base):
  def __init__(self, model_name):
    model_base.__init__(self) # init base class

    #set gpu
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    torch.set_default_tensor_type('torch.cuda.FloatTensor')

    model_ft = self.get_resnet18()
    model_ft = model_ft.to(device)
    model_ft.load_state_dict(torch.load(model_name))
    model_ft.eval() #this sets the model to "evaluate" mode.

    self.model = model_ft

    # set transformation - this will largely depend on the model and the transforms used during training.
    self.transforms = transforms.Compose([     
      transforms.Resize(256),
      transforms.CenterCrop(224),        
      transforms.ToTensor(),
      transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])

    print("Finished loading model from file {0}".format(model_name))


  def predict(self, image_path):
    image_pil = Image.open(image_path)
    input_image = self.transforms(image_pil).view(1,3,224,224).cuda()
    model_pred = self.model(input_image)
    _,preds = torch.max(model_pred,1)
    return preds[0]

  def get_resnet18(self):
    temp_model = models.resnet18(pretrained=True)
    num_ftrs = temp_model.fc.in_features
    temp_model.fc = nn.Linear(num_ftrs, 2)
    return temp_model