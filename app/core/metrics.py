from typing import Dict, Any, Tuple
import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score


def calculate_metrics(
    y_true: np.ndarray, 
    y_pred: np.ndarray
) -> Dict[str, Any]:
    """
    Вычисляет основные метрики качества классификации.
    
    Args:
        y_true: Истинные метки
        y_pred: Предсказанные метки
    
    Returns:
        Словарь с метриками
    """
    # Основные метрики (weighted average)
    accuracy = float(accuracy_score(y_true, y_pred))
    precision = float(precision_score(y_true, y_pred, average='weighted'))
    recall = float(recall_score(y_true, y_pred, average='weighted'))
    f1 = float(f1_score(y_true, y_pred, average='weighted'))
    
    # Метрики по каждому классу
    class_names = np.unique(np.concatenate([y_true, y_pred])).astype(str)
    class_metrics = {}
    
    for cls in class_names:
        cls_idx = int(cls)
        true_binary = (y_true == cls_idx).astype(int)
        pred_binary = (y_pred == cls_idx).astype(int)
        
        class_metrics[cls] = {
            'precision': float(precision_score(true_binary, pred_binary)),
            'recall': float(recall_score(true_binary, pred_binary)),
            'f1_score': float(f1_score(true_binary, pred_binary)),
            'support': int(np.sum(true_binary))
        }
    
    return {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1_score': f1,
        'class_metrics': class_metrics,
        'total_samples': len(y_true)
    }
    
    

def prepare_evaluation_data(
    predictions: np.ndarray, 
    targets: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Подготавливает данные для оценки, преобразуя их в нужный формат.
    
    Args:
        predictions: Предсказания модели
        targets: Истинные значения
    
    Returns:
        Кортеж (y_true, y_pred)
    """
    y_pred = np.array(predictions).flatten()
    y_true = np.array(targets).flatten()
    
    return y_true, y_pred