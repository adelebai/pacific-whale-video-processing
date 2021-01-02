
#base class for all ML models
class model_base:
  def __init__(self):
    pass

  def get_number_of_features(self):
  	return 0

  def predict(self, image):
    pass