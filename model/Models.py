class Model():
    def __init__(self, model_id, file_path, trained_by, trained_at,
                 model_accuracy, model_precision, model_recall, model_f1_score,
                 is_active):
        self.model_id = model_id
        self.file_path = file_path
        self.trained_by = trained_by
        self.trained_at = trained_at
        self.model_accuracy = model_accuracy
        self.model_precision = model_precision
        self.model_recall = model_recall
        self.model_f1_score = model_f1_score
        self.is_active = is_active
